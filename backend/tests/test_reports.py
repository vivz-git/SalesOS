from datetime import UTC, datetime
from unittest.mock import MagicMock, patch
from uuid import uuid4

from fastapi.testclient import TestClient

from app.api.conversations import _CONVERSATIONS_STORE
from app.api.deliveries import _DELIVERIES_STORE
from app.auth import Principal, get_current_principal
from app.main import app


def test_compute_workspace_metrics_and_generate_report() -> None:
    user_id = uuid4()
    ws_id = uuid4()
    now_iso = datetime.now(UTC).isoformat()

    mock_principal = Principal(
        user_id=user_id,
        email="admin@company.com",
        workspace_id=ws_id,
        role="admin",
    )
    app.dependency_overrides[get_current_principal] = lambda: mock_principal

    # Mock outreach drafts
    mock_d1 = MagicMock()
    mock_d1.status = "approved"
    mock_d2 = MagicMock()
    mock_d2.status = "ready_for_review"

    # 1. Populate workspace stores with sample data
    _DELIVERIES_STORE.append({
        "id": str(uuid4()),
        "workspace_id": str(ws_id),
        "status": "delivered",
        "created_at": now_iso,
    })
    _DELIVERIES_STORE.append({
        "id": str(uuid4()),
        "workspace_id": str(ws_id),
        "status": "delivered",
        "created_at": now_iso,
    })

    _CONVERSATIONS_STORE.append({
        "id": str(uuid4()),
        "workspace_id": str(ws_id),
        "contact_id": str(uuid4()),
        "status": "active",
        "current_reply_state": "interested",
        "created_at": now_iso,
    })

    with patch("app.api.reports.list_outreach_drafts", return_value=[mock_d1, mock_d2]):
        client = TestClient(app)
        # Generate Report
        gen_resp = client.post("/v1/reports/weekly/actions/generate")
        assert gen_resp.status_code == 200
        report_data = gen_resp.json()

        assert report_data["workspace_id"] == str(ws_id)
        snapshot = report_data["metrics_snapshot"]

        # Verify deterministic metric calculations
        assert snapshot["drafts_generated_count"] == 2
        assert snapshot["drafts_submitted_count"] == 2
        assert snapshot["drafts_approved_count"] == 1
        assert snapshot["approval_rate"] == 50.0

        assert snapshot["emails_sent_count"] >= 2
        assert snapshot["emails_delivered_count"] >= 2
        assert snapshot["delivery_rate"] == 100.0

        assert snapshot["replies_received_count"] >= 1
        assert snapshot["interested_replies_count"] >= 1
        assert snapshot["interested_reply_rate"] == 100.0

    app.dependency_overrides.clear()


def test_list_and_get_weekly_report_detail() -> None:
    user_id = uuid4()
    ws_id = uuid4()

    mock_principal = Principal(
        user_id=user_id,
        email="admin@company.com",
        workspace_id=ws_id,
        role="admin",
    )
    app.dependency_overrides[get_current_principal] = lambda: mock_principal
    client = TestClient(app)

    # List reports (auto-generates initial report if list empty)
    list_resp = client.get("/v1/reports/weekly")
    assert list_resp.status_code == 200
    reports = list_resp.json()
    assert len(reports) >= 1

    report_id = reports[0]["id"]

    # Detail view
    detail_resp = client.get(f"/v1/reports/weekly/{report_id}")
    assert detail_resp.status_code == 200
    assert detail_resp.json()["id"] == report_id

    app.dependency_overrides.clear()
