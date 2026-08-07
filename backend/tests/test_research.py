from unittest.mock import MagicMock, patch
from uuid import uuid4

from fastapi.testclient import TestClient

from app.auth import Principal, get_current_principal
from app.main import app


def test_create_research_brief_endpoint() -> None:
    user_id = uuid4()
    workspace_id = uuid4()
    account_id = uuid4()
    contact_id = uuid4()

    mock_principal = Principal(
        user_id=user_id,
        email="user@example.com",
        workspace_id=workspace_id,
        role="owner",
    )

    app.dependency_overrides[get_current_principal] = lambda: mock_principal

    mock_admin = MagicMock()
    mock_admin.table.return_value.insert.return_value.execute.return_value.data = []

    with patch("app.api.research._clients", return_value=(MagicMock(), mock_admin)):
        client = TestClient(app)
        response = client.post(
            "/v1/research/briefs",
            json={
                "account_id": str(account_id),
                "contact_id": str(contact_id),
                "summary": "Initial company intelligence summary",
                "key_findings": ["Growing 40% YoY", "Expanding EU team"],
            },
            headers={"Authorization": "Bearer fake-token"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["account_id"] == str(account_id)
        assert data["contact_id"] == str(contact_id)
        assert data["status"] == "pending"
        assert data["workspace_id"] == str(workspace_id)
        assert data["key_findings"] == ["Growing 40% YoY", "Expanding EU team"]

    app.dependency_overrides.clear()


def test_append_source_provenance_and_list() -> None:
    user_id = uuid4()
    workspace_id = uuid4()
    account_id = uuid4()
    brief_id = uuid4()
    source_id = uuid4()

    mock_principal = Principal(
        user_id=user_id,
        email="user@example.com",
        workspace_id=workspace_id,
        role="admin",
    )

    app.dependency_overrides[get_current_principal] = lambda: mock_principal

    sample_brief = {
        "id": str(brief_id),
        "workspace_id": str(workspace_id),
        "account_id": str(account_id),
        "contact_id": None,
        "summary": "Research brief",
        "key_findings": ["Expansion"],
        "status": "pending",
        "confidence_score": 0.85,
        "confidence_reason": "High quality primary source website verified",
        "created_by": str(user_id),
        "created_at": "2026-08-07T12:00:00+00:00",
        "updated_at": "2026-08-07T12:00:00+00:00",
        "deleted_at": None,
    }

    sample_source = {
        "id": str(source_id),
        "workspace_id": str(workspace_id),
        "brief_id": str(brief_id),
        "url": "https://acme.com/news/expansion",
        "title": "Acme Q3 Press Release",
        "source_type": "website",
        "snippet": "Acme expands product engineering team",
        "confidence": 0.95,
        "raw_content_hash": "sha256:abc123hash",
        "retrieved_at": "2026-08-07T12:00:00+00:00",
    }

    mock_brief_table = MagicMock()
    mock_brief_table.select.return_value.eq.return_value.execute.return_value.data = [sample_brief]
    mock_brief_table.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = [sample_brief]

    mock_source_table = MagicMock()
    mock_source_table.insert.return_value.execute.return_value.data = []
    mock_source_table.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = [sample_source]

    def table_router(table_name: str) -> MagicMock:
        if table_name == "research_briefs":
            return mock_brief_table
        return mock_source_table

    mock_admin = MagicMock()
    mock_admin.table.side_effect = table_router

    with patch("app.api.research._clients", return_value=(MagicMock(), mock_admin)):
        client = TestClient(app)

        # Append source
        src_res = client.post(
            f"/v1/research/briefs/{brief_id}/sources",
            json={
                "url": "https://acme.com/news/expansion",
                "title": "Acme Q3 Press Release",
                "source_type": "website",
                "snippet": "Acme expands product engineering team",
                "confidence": 0.95,
                "raw_content_hash": "sha256:abc123hash",
            },
            headers={"Authorization": "Bearer fake-token"},
        )
        assert src_res.status_code == 201
        assert src_res.json()["url"] == "https://acme.com/news/expansion"

        # List sources
        list_src_res = client.get(
            f"/v1/research/briefs/{brief_id}/sources",
            headers={"Authorization": "Bearer fake-token"},
        )
        assert list_src_res.status_code == 200
        assert len(list_src_res.json()) == 1

    app.dependency_overrides.clear()


def test_trigger_research_job_action() -> None:
    user_id = uuid4()
    workspace_id = uuid4()
    account_id = uuid4()
    brief_id = uuid4()

    mock_principal = Principal(
        user_id=user_id,
        email="user@example.com",
        workspace_id=workspace_id,
        role="owner",
    )

    app.dependency_overrides[get_current_principal] = lambda: mock_principal

    sample_brief = {
        "id": str(brief_id),
        "workspace_id": str(workspace_id),
        "account_id": str(account_id),
        "contact_id": None,
        "summary": "Pending brief",
        "status": "pending",
        "created_by": str(user_id),
        "created_at": "2026-08-07T12:00:00+00:00",
        "updated_at": "2026-08-07T12:00:00+00:00",
        "deleted_at": None,
    }

    mock_admin = MagicMock()
    mock_select = mock_admin.table.return_value.select.return_value
    mock_select.eq.return_value.execute.return_value.data = [sample_brief]
    mock_select.eq.return_value.eq.return_value.execute.return_value.data = [sample_brief]
    mock_admin.table.return_value.update.return_value.eq.return_value.execute.return_value.data = []

    with patch("app.api.research._clients", return_value=(MagicMock(), mock_admin)):
        client = TestClient(app)
        trig_res = client.post(
            f"/v1/research/briefs/{brief_id}/actions/trigger",
            headers={"Authorization": "Bearer fake-token"},
        )
        assert trig_res.status_code == 200
        job_data = trig_res.json()
        assert job_data["status"] == "queued"
        assert job_data["brief_id"] == str(brief_id)

    app.dependency_overrides.clear()
