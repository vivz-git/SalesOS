from collections.abc import AsyncIterator
from datetime import UTC, datetime
from typing import Any
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.auth import Principal, get_current_principal
from app.db import get_db_session
from app.main import app
from app.models import CampaignModel, ContactModel, OutreachDraftModel


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
        email="reviewer@example.com",
        workspace_id=uuid4(),
        role="admin",
    )


def test_list_approvals_and_queue_alias(mock_principal: Principal) -> None:
    draft_id = uuid4()
    mock_draft = OutreachDraftModel(
        id=draft_id,
        workspace_id=mock_principal.workspace_id,
        campaign_id=uuid4(),
        contact_id=uuid4(),
        sequence_enrollment_id=None,
        sequence_step_number=None,
        research_brief_id=None,
        current_version_id=uuid4(),
        current_version_number=1,
        current_subject="Review Subject",
        current_body="Review Body",
        status="ready_for_review",
        created_by=mock_principal.user_id,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        deleted_at=None,
    )

    mock_session = create_mock_session()
    mock_result = MagicMock()
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = [mock_draft]
    mock_result.scalars.return_value = mock_scalars
    mock_session.execute.return_value = mock_result

    async def _override_session() -> AsyncIterator[Any]:
        yield mock_session

    app.dependency_overrides[get_current_principal] = lambda: mock_principal
    app.dependency_overrides[get_db_session] = _override_session

    try:
        client = TestClient(app)

        # 1. Test /v1/approvals
        res1 = client.get("/v1/approvals")
        assert res1.status_code == 200
        data1 = res1.json()
        assert len(data1) == 1
        assert data1[0]["id"] == str(draft_id)
        assert data1[0]["status"] == "ready_for_review"

        # 2. Test /v1/approvals/queue
        res2 = client.get("/v1/approvals/queue")
        assert res2.status_code == 200
        data2 = res2.json()
        assert len(data2) == 1
        assert data2[0]["id"] == str(draft_id)
    finally:
        app.dependency_overrides.clear()


def test_get_approval_item_detail(mock_principal: Principal) -> None:
    draft_id = uuid4()
    camp_id = uuid4()
    contact_id = uuid4()

    mock_draft = OutreachDraftModel(
        id=draft_id,
        workspace_id=mock_principal.workspace_id,
        campaign_id=camp_id,
        contact_id=contact_id,
        sequence_enrollment_id=None,
        sequence_step_number=None,
        research_brief_id=None,
        current_version_id=uuid4(),
        current_version_number=1,
        current_subject="Subject 1",
        current_body="Body 1",
        status="ready_for_review",
        created_by=mock_principal.user_id,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        deleted_at=None,
    )

    mock_campaign = CampaignModel(
        id=camp_id,
        workspace_id=mock_principal.workspace_id,
        name="Q3 Outbound",
        status="active",
        created_by=mock_principal.user_id,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    mock_contact = ContactModel(
        id=contact_id,
        workspace_id=mock_principal.workspace_id,
        first_name="Jane",
        last_name="Doe",
        email="jane@example.com",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    mock_session = create_mock_session()
    mock_session.get.side_effect = lambda model, id_val: (
        mock_draft if model == OutreachDraftModel else (mock_campaign if model == CampaignModel else (mock_contact if model == ContactModel else None))
    )

    mock_hist_result = MagicMock()
    mock_hist_scalars = MagicMock()
    mock_hist_scalars.all.return_value = []
    mock_hist_result.scalars.return_value = mock_hist_scalars
    mock_session.execute.return_value = mock_hist_result

    async def _override_session() -> AsyncIterator[Any]:
        yield mock_session

    app.dependency_overrides[get_current_principal] = lambda: mock_principal
    app.dependency_overrides[get_db_session] = _override_session

    try:
        client = TestClient(app)

        # Test GET /v1/approvals/{draft_id}
        res = client.get(f"/v1/approvals/{draft_id}")
        assert res.status_code == 200
        data = res.json()
        assert data["draft"]["id"] == str(draft_id)
        assert data["campaign_name"] == "Q3 Outbound"
        assert data["contact_name"] == "Jane Doe"
        assert data["contact_email"] == "jane@example.com"

        # Test GET /v1/approvals/items/{draft_id}
        res_items = client.get(f"/v1/approvals/items/{draft_id}")
        assert res_items.status_code == 200
        assert res_items.json()["draft"]["id"] == str(draft_id)
    finally:
        app.dependency_overrides.clear()


def test_approval_actions_state_transitions(mock_principal: Principal) -> None:
    draft_id = uuid4()
    mock_draft = OutreachDraftModel(
        id=draft_id,
        workspace_id=mock_principal.workspace_id,
        campaign_id=uuid4(),
        contact_id=uuid4(),
        sequence_enrollment_id=None,
        sequence_step_number=None,
        research_brief_id=None,
        current_version_id=uuid4(),
        current_version_number=1,
        current_subject="Review Subject",
        current_body="Review Body",
        status="ready_for_review",
        created_by=mock_principal.user_id,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        deleted_at=None,
    )

    mock_session = create_mock_session()
    mock_exec_result = MagicMock()
    mock_exec_result.scalar_one_or_none.return_value = mock_draft
    mock_session.execute.return_value = mock_exec_result

    async def _override_session() -> AsyncIterator[Any]:
        yield mock_session

    app.dependency_overrides[get_current_principal] = lambda: mock_principal
    app.dependency_overrides[get_db_session] = _override_session

    try:
        client = TestClient(app)

        # 1. Action: approve
        res_approve = client.post(
            f"/v1/approvals/{draft_id}/actions/approve",
            json={"notes": "Approved for dispatch"},
        )
        assert res_approve.status_code == 200
        app_data = res_approve.json()
        assert app_data["decision"] == "approved"
        assert app_data["notes"] == "Approved for dispatch"
        assert mock_draft.status == "approved"

        # Reset draft status for next test
        mock_draft.status = "ready_for_review"

        # 2. Action: reject
        res_reject = client.post(
            f"/v1/approvals/{draft_id}/actions/reject",
            json={"notes": "Needs more context"},
        )
        assert res_reject.status_code == 200
        rej_data = res_reject.json()
        assert rej_data["decision"] == "rejected"
        assert mock_draft.status == "rejected"

        # Reset draft status for return-to-draft test
        mock_draft.status = "ready_for_review"

        # 3. Action: return-to-draft
        res_ret = client.post(
            f"/v1/approvals/{draft_id}/actions/return-to-draft",
            json={"notes": "Revise greeting"},
        )
        assert res_ret.status_code == 200
        ret_data = res_ret.json()
        assert ret_data["decision"] == "returned_to_draft"
        assert mock_draft.status == "draft"

        # Reset draft status for decision endpoint compatibility
        mock_draft.status = "ready_for_review"

        # 4. Action: decision endpoint compatibility
        res_dec = client.post(
            f"/v1/approvals/items/{draft_id}/decision",
            json={"decision": "approved", "notes": "Legacy decision endpoint test"},
        )
        assert res_dec.status_code == 200
        assert res_dec.json()["decision"] == "approved"
        assert mock_draft.status == "approved"
    finally:
        app.dependency_overrides.clear()


def test_approval_decision_invalid_state_rejection(mock_principal: Principal) -> None:
    draft_id = uuid4()
    # Draft is already in 'approved' status, not 'ready_for_review'
    mock_draft = OutreachDraftModel(
        id=draft_id,
        workspace_id=mock_principal.workspace_id,
        campaign_id=uuid4(),
        contact_id=uuid4(),
        sequence_enrollment_id=None,
        sequence_step_number=None,
        research_brief_id=None,
        current_version_id=uuid4(),
        current_version_number=1,
        current_subject="Approved Subject",
        current_body="Approved Body",
        status="approved",
        created_by=mock_principal.user_id,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        deleted_at=None,
    )

    mock_session = create_mock_session()
    mock_exec_result = MagicMock()
    mock_exec_result.scalar_one_or_none.return_value = mock_draft
    mock_session.execute.return_value = mock_exec_result

    async def _override_session() -> AsyncIterator[Any]:
        yield mock_session

    app.dependency_overrides[get_current_principal] = lambda: mock_principal
    app.dependency_overrides[get_db_session] = _override_session

    try:
        client = TestClient(app)
        res = client.post(f"/v1/approvals/{draft_id}/actions/approve", json={"notes": "Duplicate"})
        assert res.status_code == 400
        assert "cannot_decide_on_draft_in_approved_state" in res.text
    finally:
        app.dependency_overrides.clear()
