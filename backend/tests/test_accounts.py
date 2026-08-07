from unittest.mock import MagicMock, patch
from uuid import uuid4

from fastapi.testclient import TestClient

from app.auth import Principal, get_current_principal
from app.main import app


def test_create_account_endpoint() -> None:
    user_id = uuid4()
    workspace_id = uuid4()
    campaign_id = uuid4()

    mock_principal = Principal(
        user_id=user_id,
        email="user@example.com",
        workspace_id=workspace_id,
        role="owner",
    )

    app.dependency_overrides[get_current_principal] = lambda: mock_principal

    mock_admin = MagicMock()
    mock_admin.table.return_value.insert.return_value.execute.return_value.data = []

    with patch("app.api.accounts._clients", return_value=(MagicMock(), mock_admin)):
        client = TestClient(app)
        response = client.post(
            "/v1/accounts",
            json={
                "name": "Acme Technologies",
                "domain": "acme.com",
                "industry": "Software",
                "employee_count": "100-250",
                "campaign_id": str(campaign_id),
                "status": "target",
            },
            headers={"Authorization": "Bearer fake-token"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Acme Technologies"
        assert data["domain"] == "acme.com"
        assert data["status"] == "target"
        assert data["workspace_id"] == str(workspace_id)
        assert data["campaign_id"] == str(campaign_id)

    app.dependency_overrides.clear()


def test_list_and_search_accounts_endpoint() -> None:
    user_id = uuid4()
    workspace_id = uuid4()
    account_id = uuid4()

    mock_principal = Principal(
        user_id=user_id,
        email="user@example.com",
        workspace_id=workspace_id,
        role="admin",
    )

    app.dependency_overrides[get_current_principal] = lambda: mock_principal

    sample_account = {
        "id": str(account_id),
        "workspace_id": str(workspace_id),
        "campaign_id": None,
        "name": "Stripe Inc",
        "domain": "stripe.com",
        "industry": "Fintech",
        "employee_count": "5000+",
        "city": "San Francisco",
        "state": "CA",
        "country": "USA",
        "status": "qualified",
        "created_by": str(user_id),
        "created_at": "2026-08-07T12:00:00+00:00",
        "updated_at": "2026-08-07T12:00:00+00:00",
        "deleted_at": None,
    }

    mock_admin = MagicMock()
    mock_select = mock_admin.table.return_value.select.return_value
    mock_select.eq.return_value.execute.return_value.data = [sample_account]
    mock_select.eq.return_value.eq.return_value.execute.return_value.data = [sample_account]

    with patch("app.api.accounts._clients", return_value=(MagicMock(), mock_admin)):
        client = TestClient(app)
        list_res = client.get(
            "/v1/accounts?search=stripe", headers={"Authorization": "Bearer fake-token"}
        )
        assert list_res.status_code == 200
        assert len(list_res.json()) == 1
        assert list_res.json()[0]["name"] == "Stripe Inc"

    app.dependency_overrides.clear()


def test_account_archive_and_restore() -> None:
    user_id = uuid4()
    workspace_id = uuid4()
    account_id = uuid4()

    mock_principal = Principal(
        user_id=user_id,
        email="user@example.com",
        workspace_id=workspace_id,
        role="owner",
    )

    app.dependency_overrides[get_current_principal] = lambda: mock_principal

    sample_account = {
        "id": str(account_id),
        "workspace_id": str(workspace_id),
        "campaign_id": None,
        "name": "Beta LLC",
        "status": "target",
        "created_by": str(user_id),
        "created_at": "2026-08-07T12:00:00+00:00",
        "updated_at": "2026-08-07T12:00:00+00:00",
        "deleted_at": None,
    }

    mock_admin = MagicMock()
    mock_select = mock_admin.table.return_value.select.return_value
    mock_select.eq.return_value.execute.return_value.data = [sample_account]
    mock_select.eq.return_value.eq.return_value.execute.return_value.data = [sample_account]
    mock_admin.table.return_value.update.return_value.eq.return_value.execute.return_value.data = []

    with patch("app.api.accounts._clients", return_value=(MagicMock(), mock_admin)):
        client = TestClient(app)
        archive_res = client.post(
            f"/v1/accounts/{account_id}/actions/archive",
            headers={"Authorization": "Bearer fake-token"},
        )
        assert archive_res.status_code == 200

        restore_res = client.post(
            f"/v1/accounts/{account_id}/actions/restore",
            headers={"Authorization": "Bearer fake-token"},
        )
        assert restore_res.status_code == 200

    app.dependency_overrides.clear()
