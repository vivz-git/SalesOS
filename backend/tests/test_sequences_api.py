from collections.abc import AsyncIterator
from datetime import UTC, datetime
from typing import Any
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.api.sequences import evaluate_sequence_stop_conditions_for_contact
from app.auth import Principal, get_current_principal
from app.db import get_db_session
from app.main import app
from app.models import CampaignModel, SequenceEnrollmentModel


def create_mock_session() -> MagicMock:
    session = MagicMock()
    tx_ctx = MagicMock()
    tx_ctx.__aenter__ = AsyncMock(return_value=session)
    tx_ctx.__aexit__ = AsyncMock(return_value=None)
    session.begin = MagicMock(return_value=tx_ctx)
    session.execute = AsyncMock()
    session.get = AsyncMock()
    session.scalar = AsyncMock()
    session.scalars = AsyncMock()
    session.flush = AsyncMock()
    session.refresh = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.add = MagicMock()
    return session


@pytest.fixture
def mock_principal() -> Principal:
    return Principal(
        user_id=uuid4(),
        email="manager@example.com",
        workspace_id=uuid4(),
        role="owner",
    )


def test_create_and_get_campaign_sequence(mock_principal: Principal) -> None:
    camp_id = uuid4()
    mock_campaign = CampaignModel(
        id=camp_id,
        workspace_id=mock_principal.workspace_id,
        name="Enterprise Outreach",
        status="active",
        created_by=mock_principal.user_id,
        target_segment="SaaS",
        icp_definition="VP Eng",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    mock_session = create_mock_session()
    mock_session.scalar.side_effect = [mock_campaign, None]

    async def _override_session() -> AsyncIterator[Any]:
        yield mock_session

    app.dependency_overrides[get_current_principal] = lambda: mock_principal
    app.dependency_overrides[get_db_session] = _override_session

    try:
        client = TestClient(app)

        res_post = client.post(
            f"/v1/campaigns/{camp_id}/sequences",
            json={
                "name": "Custom Sequence",
                "steps": [
                    {
                        "step_number": 1,
                        "delay_days": 0,
                        "channel": "email",
                        "step_type": "first_touch",
                        "template_subject": "Intro",
                        "template_body": "Hello {{first_name}}",
                    },
                    {
                        "step_number": 2,
                        "delay_days": 4,
                        "channel": "email",
                        "step_type": "follow_up",
                        "template_subject": "Follow up",
                        "template_body": "Checking in",
                    },
                ],
            },
        )
        assert res_post.status_code == 200
        data = res_post.json()
        assert data["name"] == "Custom Sequence"
        assert len(data["steps"]) == 2
        assert data["steps"][0]["step_number"] == 1
        assert data["steps"][1]["step_number"] == 2
        assert data["steps"][1]["delay_days"] == 4
    finally:
        app.dependency_overrides.clear()


def test_sequence_enrollment_lifecycle(mock_principal: Principal) -> None:
    enr_id = uuid4()
    camp_id = uuid4()
    contact_id = uuid4()
    seq_id = uuid4()

    mock_enrollment = SequenceEnrollmentModel(
        id=enr_id,
        workspace_id=mock_principal.workspace_id,
        campaign_id=camp_id,
        sequence_id=seq_id,
        contact_id=contact_id,
        current_step_number=1,
        status="active",
        stop_reason=None,
        enrolled_by=mock_principal.user_id,
        enrolled_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    mock_session = create_mock_session()
    mock_session.scalar.return_value = mock_enrollment

    async def _override_session() -> AsyncIterator[Any]:
        yield mock_session

    app.dependency_overrides[get_current_principal] = lambda: mock_principal
    app.dependency_overrides[get_db_session] = _override_session

    try:
        client = TestClient(app)

        # 1. Pause active enrollment
        res_pause = client.post(f"/v1/sequence-enrollments/{enr_id}/actions/pause")
        assert res_pause.status_code == 200
        assert res_pause.json()["status"] == "paused"
        assert mock_enrollment.status == "paused"

        # 2. Resume paused enrollment
        res_resume = client.post(f"/v1/sequence-enrollments/{enr_id}/actions/resume")
        assert res_resume.status_code == 200
        assert res_resume.json()["status"] == "active"
        assert mock_enrollment.status == "active"

        # 3. Stop enrollment with reason
        res_stop = client.post(
            f"/v1/sequence-enrollments/{enr_id}/actions/stop",
            json={"reason": "prospect_unsubscribed"},
        )
        assert res_stop.status_code == 200
        assert res_stop.json()["status"] == "stopped"
        assert res_stop.json()["stop_reason"] == "prospect_unsubscribed"
        assert mock_enrollment.status == "stopped"

        # 4. Attempting to pause stopped enrollment fails
        res_pause_invalid = client.post(f"/v1/sequence-enrollments/{enr_id}/actions/pause")
        assert res_pause_invalid.status_code == 400
        assert "cannot_pause_enrollment_in_stopped_state" in res_pause_invalid.text
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_evaluate_sequence_stop_conditions(mock_principal: Principal) -> None:
    contact_id = uuid4()
    mock_enrollment = SequenceEnrollmentModel(
        id=uuid4(),
        workspace_id=mock_principal.workspace_id,
        campaign_id=uuid4(),
        sequence_id=uuid4(),
        contact_id=contact_id,
        current_step_number=1,
        status="active",
        stop_reason=None,
        enrolled_by=mock_principal.user_id,
        enrolled_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    mock_session = create_mock_session()
    mock_session.scalars.return_value = [mock_enrollment]

    await evaluate_sequence_stop_conditions_for_contact(
        workspace_id=str(mock_principal.workspace_id),
        contact_id=str(contact_id),
        reason="inbound_reply_received",
        session=mock_session,
    )

    assert mock_enrollment.status == "stopped"
    assert mock_enrollment.stop_reason == "inbound_reply_received"
