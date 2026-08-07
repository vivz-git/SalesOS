from unittest.mock import MagicMock, patch
from uuid import uuid4

from fastapi.testclient import TestClient

from app.auth import Principal, get_current_principal
from app.main import app


def test_create_contact_endpoint() -> None:
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

    mock_admin = MagicMock()
    mock_admin.table.return_value.insert.return_value.execute.return_value.data = []

    with patch("app.api.contacts._clients", return_value=(MagicMock(), mock_admin)):
        client = TestClient(app)
        response = client.post(
            "/v1/contacts",
            json={
                "first_name": "Jane",
                "last_name": "Doe",
                "email": "jane.doe@acme.com",
                "phone": "+1-555-0199",
                "title": "VP of Engineering",
                "department": "Engineering",
                "linkedin_url": "https://linkedin.com/in/janedoe",
                "account_id": str(account_id),
                "is_primary": True,
                "status": "active",
            },
            headers={"Authorization": "Bearer fake-token"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["first_name"] == "Jane"
        assert data["last_name"] == "Doe"
        assert data["email"] == "jane.doe@acme.com"
        assert data["is_primary"] is True
        assert data["workspace_id"] == str(workspace_id)
        assert data["account_id"] == str(account_id)

    app.dependency_overrides.clear()


def test_list_and_search_contacts_endpoint() -> None:
    user_id = uuid4()
    workspace_id = uuid4()
    contact_id = uuid4()

    mock_principal = Principal(
        user_id=user_id,
        email="user@example.com",
        workspace_id=workspace_id,
        role="admin",
    )

    app.dependency_overrides[get_current_principal] = lambda: mock_principal

    sample_contact = {
        "id": str(contact_id),
        "workspace_id": str(workspace_id),
        "account_id": None,
        "first_name": "John",
        "last_name": "Smith",
        "email": "john@stripe.com",
        "phone": "+1-555-0100",
        "title": "Chief Technology Officer",
        "department": "Product",
        "linkedin_url": "https://linkedin.com/in/johnsmith",
        "is_primary": False,
        "status": "active",
        "created_by": str(user_id),
        "created_at": "2026-08-07T12:00:00+00:00",
        "updated_at": "2026-08-07T12:00:00+00:00",
        "deleted_at": None,
    }

    mock_admin = MagicMock()
    mock_select = mock_admin.table.return_value.select.return_value
    mock_select.eq.return_value.execute.return_value.data = [sample_contact]
    mock_select.eq.return_value.eq.return_value.execute.return_value.data = [sample_contact]

    with patch("app.api.contacts._clients", return_value=(MagicMock(), mock_admin)):
        client = TestClient(app)
        list_res = client.get(
            "/v1/contacts?search=smith", headers={"Authorization": "Bearer fake-token"}
        )
        assert list_res.status_code == 200
        assert len(list_res.json()) == 1
        assert list_res.json()[0]["last_name"] == "Smith"

    app.dependency_overrides.clear()


def test_contact_archive_and_restore() -> None:
    user_id = uuid4()
    workspace_id = uuid4()
    contact_id = uuid4()

    mock_principal = Principal(
        user_id=user_id,
        email="user@example.com",
        workspace_id=workspace_id,
        role="owner",
    )

    app.dependency_overrides[get_current_principal] = lambda: mock_principal

    sample_contact = {
        "id": str(contact_id),
        "workspace_id": str(workspace_id),
        "account_id": None,
        "first_name": "Alex",
        "last_name": "Taylor",
        "is_primary": False,
        "status": "active",
        "created_by": str(user_id),
        "created_at": "2026-08-07T12:00:00+00:00",
        "updated_at": "2026-08-07T12:00:00+00:00",
        "deleted_at": None,
    }

    mock_admin = MagicMock()
    mock_select = mock_admin.table.return_value.select.return_value
    mock_select.eq.return_value.execute.return_value.data = [sample_contact]
    mock_select.eq.return_value.eq.return_value.execute.return_value.data = [sample_contact]
    mock_admin.table.return_value.update.return_value.eq.return_value.execute.return_value.data = []

    with patch("app.api.contacts._clients", return_value=(MagicMock(), mock_admin)):
        client = TestClient(app)
        archive_res = client.post(
            f"/v1/contacts/{contact_id}/actions/archive",
            headers={"Authorization": "Bearer fake-token"},
        )
        assert archive_res.status_code == 200

        restore_res = client.post(
            f"/v1/contacts/{contact_id}/actions/restore",
            headers={"Authorization": "Bearer fake-token"},
        )
        assert restore_res.status_code == 200

    app.dependency_overrides.clear()
