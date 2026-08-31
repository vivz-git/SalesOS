from typing import Any
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from app.api.reports import compute_workspace_metrics
from app.auth import Principal, get_current_principal
from app.core.config import Settings
from app.db import get_db_session
from app.main import app

pytestmark = pytest.mark.asyncio


async def test_compute_workspace_metrics_contacts_gt_zero_enrollments_zero() -> None:
    """Regression test: workspace with contacts > 0 and sequence enrollments == 0
    must report contacts_enrolled_count == 0, NOT falling back to contacts_cnt.
    """
    ws_id = uuid4()
    principal = Principal(
        user_id=uuid4(),
        email="test@example.com",
        workspace_id=ws_id,
        role="owner",
    )
    settings = Settings(environment="test")

    mock_session = AsyncMock()
    mock_session.scalar.side_effect = [
        1,  # campaigns
        2,  # accounts
        0,  # sequence enrollments (0 enrolled)
        3,  # drafts generated
        2,  # drafts submitted
        1,  # drafts approved
        1,  # emails sent
        1,  # emails delivered
        0,  # bounced
        0,  # complained
        1,  # replies
        1,  # interested replies
        0,  # opt-outs
    ]

    metrics = await compute_workspace_metrics(principal, settings, mock_session)

    assert metrics.accounts_researched_count == 2
    assert metrics.contacts_enrolled_count == 0
    assert metrics.campaigns_count == 1
    assert metrics.drafts_submitted_count == 2
    assert metrics.drafts_approved_count == 1
    assert metrics.approval_rate == 50.0
    assert metrics.delivery_rate == 100.0
    assert metrics.reply_rate == 100.0
    assert metrics.interested_reply_rate == 100.0


async def test_compute_workspace_metrics_with_enrollments() -> None:
    """Verify that a workspace with enrollments > 0 reports the exact enrollment count."""
    ws_id = uuid4()
    principal = Principal(
        user_id=uuid4(),
        email="test@example.com",
        workspace_id=ws_id,
        role="owner",
    )
    settings = Settings(environment="test")

    mock_session = AsyncMock()
    mock_session.scalar.side_effect = [
        2,  # campaigns
        10,  # accounts
        7,  # sequence enrollments
        5,  # drafts generated
        4,  # drafts submitted
        3,  # drafts approved
        10,  # emails sent
        9,  # emails delivered
        1,  # bounced
        0,  # complained
        2,  # replies
        1,  # interested replies
        0,  # opt-outs
    ]

    metrics = await compute_workspace_metrics(principal, settings, mock_session)

    assert metrics.contacts_enrolled_count == 7
    assert metrics.accounts_researched_count == 10
    assert metrics.drafts_submitted_count == 4
    assert metrics.drafts_approved_count == 3
    assert metrics.approval_rate == 75.0
    assert metrics.emails_sent_count == 10
    assert metrics.emails_delivered_count == 9
    assert metrics.delivery_rate == 90.0
    assert metrics.replies_received_count == 2
    assert metrics.reply_rate == 22.2
    assert metrics.interested_reply_rate == 50.0


async def test_reports_api_generate_and_list() -> None:
    """Test generating a report digest and listing reports via API."""
    ws_id = uuid4()
    principal = Principal(
        user_id=uuid4(),
        email="test@example.com",
        workspace_id=ws_id,
        role="owner",
    )

    mock_session = AsyncMock()
    mock_session.scalar.return_value = 0

    async def _override_session() -> Any:
        yield mock_session

    app.dependency_overrides[get_current_principal] = lambda: principal
    app.dependency_overrides[get_db_session] = _override_session

    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # Generate report
            res = await client.post("/v1/reports/weekly/actions/generate")
            assert res.status_code == 200
            data = res.json()
            assert data["workspace_id"] == str(ws_id)
            assert "metrics_snapshot" in data
            assert data["metrics_snapshot"]["contacts_enrolled_count"] == 0
            assert data["metrics_snapshot"]["approval_rate"] == 0.0

            # List reports
            list_res = await client.get("/v1/reports/weekly")
            assert list_res.status_code == 200
            reports = list_res.json()
            assert len(reports) >= 1
            assert reports[0]["workspace_id"] == str(ws_id)
    finally:
        app.dependency_overrides.clear()
