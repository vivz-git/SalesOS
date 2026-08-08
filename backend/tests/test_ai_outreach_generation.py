from typing import Any
from unittest.mock import MagicMock, patch
from uuid import uuid4

from fastapi.testclient import TestClient

from app.adapters.llm_provider import (
    LLMGenerationRequest,
    LLMGenerationResult,
    LLMProviderInterface,
)
from app.api.outreach import get_llm_provider
from app.auth import Principal, get_current_principal
from app.main import app


class MockLLMProvider(LLMProviderInterface):
    def generate_outreach_draft(self, request: LLMGenerationRequest) -> LLMGenerationResult:
        return LLMGenerationResult(
            subject=f"AI Subject for {request.contact_name}",
            body=f"AI Generated body for {request.contact_name} at {request.account_name or 'Company'}.",
            generation_source="ai_generated",
            provider="gemini",
            model="gemini-2.5-flash",
            prompt_version=request.prompt_version,
            evidence_references=[
                {
                    "url": "https://example.com/news",
                    "title": "Expansion Announcement",
                    "snippet": "Company raised Series B",
                    "source_type": "website",
                }
            ],
            token_usage=250,
            estimated_cost=0.001,
            duration_ms=450,
        )


class FailingLLMProvider(LLMProviderInterface):
    def generate_outreach_draft(self, request: LLMGenerationRequest) -> LLMGenerationResult:
        raise ValueError("API quota exceeded")


def test_ai_outreach_generation_endpoint_success() -> None:
    user_id = uuid4()
    workspace_id = uuid4()
    draft_id = uuid4()
    campaign_id = uuid4()
    contact_id = uuid4()
    brief_id = uuid4()
    v1_id = uuid4()

    mock_principal = Principal(
        user_id=user_id,
        email="contributor@example.com",
        workspace_id=workspace_id,
        role="contributor",
    )

    app.dependency_overrides[get_current_principal] = lambda: mock_principal
    app.dependency_overrides[get_llm_provider] = lambda: MockLLMProvider()

    sample_draft_v1: dict[str, Any] = {
        "id": str(draft_id),
        "workspace_id": str(workspace_id),
        "campaign_id": str(campaign_id),
        "contact_id": str(contact_id),
        "research_brief_id": str(brief_id),
        "current_version_id": str(v1_id),
        "current_version_number": 1,
        "current_subject": "Human Subject V1",
        "current_body": "Human Body V1",
        "status": "draft",
        "created_by": str(user_id),
        "created_at": "2026-08-08T10:00:00+00:00",
        "updated_at": "2026-08-08T10:00:00+00:00",
        "deleted_at": None,
    }

    sample_draft_v2: dict[str, Any] = {
        **sample_draft_v1,
        "current_version_number": 2,
        "current_subject": "AI Subject for Jane Doe",
        "current_body": "AI Generated body for Jane Doe at Acme Inc.",
        "updated_at": "2026-08-08T10:05:00+00:00",
    }

    sample_campaign = {"id": str(campaign_id), "name": "Q3 Enterprise Campaign"}
    sample_contact = {"id": str(contact_id), "first_name": "Jane", "last_name": "Doe", "account_id": str(uuid4())}
    sample_account = {"id": sample_contact["account_id"], "name": "Acme Inc"}
    sample_brief = {"id": str(brief_id), "summary": "Acme Inc expanding SaaS platform.", "key_findings": ["Raised Series B"]}
    sample_sources = [{"id": str(uuid4()), "url": "https://example.com/news", "title": "Expansion Announcement"}]

    mock_admin = MagicMock()
    mock_select = mock_admin.table.return_value.select.return_value

    mock_select.eq.return_value.eq.return_value.execute.side_effect = [
        MagicMock(data=[sample_draft_v1]),
        MagicMock(data=[sample_campaign]),
        MagicMock(data=[sample_contact]),
        MagicMock(data=[sample_account]),
        MagicMock(data=[sample_brief]),
        MagicMock(data=sample_sources),
        MagicMock(data=[sample_draft_v2]),
    ]
    mock_select.eq.return_value.eq.return_value.order.return_value.execute.return_value.data = [
        {"id": str(uuid4()), "workspace_id": str(workspace_id), "draft_id": str(draft_id), "version_number": 2, "subject": "AI Subject for Jane Doe", "body": "AI Generated body", "generation_source": "ai_generated"}
    ]

    mock_admin.table.return_value.insert.return_value.execute.return_value.data = []
    mock_admin.table.return_value.update.return_value.eq.return_value.execute.return_value.data = []

    with patch("app.api.outreach._clients", return_value=(MagicMock(), mock_admin)):
        client = TestClient(app)
        response = client.post(
            f"/v1/outreach/drafts/{draft_id}/actions/generate",
            headers={"Authorization": "Bearer fake-token"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["current_version_number"] == 2
        assert data["current_subject"] == "AI Subject for Jane Doe"

    app.dependency_overrides.clear()


def test_ai_generation_provider_failure_returns_502() -> None:
    user_id = uuid4()
    workspace_id = uuid4()
    draft_id = uuid4()

    mock_principal = Principal(
        user_id=user_id,
        email="contributor@example.com",
        workspace_id=workspace_id,
        role="contributor",
    )

    app.dependency_overrides[get_current_principal] = lambda: mock_principal
    app.dependency_overrides[get_llm_provider] = lambda: FailingLLMProvider()

    sample_draft: dict[str, Any] = {
        "id": str(draft_id),
        "workspace_id": str(workspace_id),
        "campaign_id": str(uuid4()),
        "contact_id": str(uuid4()),
        "status": "draft",
        "current_version_number": 1,
    }

    mock_admin = MagicMock()
    mock_select = mock_admin.table.return_value.select.return_value
    mock_select.eq.return_value.eq.return_value.execute.return_value.data = [sample_draft]

    with patch("app.api.outreach._clients", return_value=(MagicMock(), mock_admin)):
        client = TestClient(app)
        response = client.post(
            f"/v1/outreach/drafts/{draft_id}/actions/generate",
            headers={"Authorization": "Bearer fake-token"},
        )
        assert response.status_code == 502
        assert "ai_draft_generation_failed" in response.json()["detail"]

    app.dependency_overrides.clear()


def test_cannot_generate_approved_or_archived_draft() -> None:
    user_id = uuid4()
    workspace_id = uuid4()
    draft_id = uuid4()

    mock_principal = Principal(
        user_id=user_id,
        email="contributor@example.com",
        workspace_id=workspace_id,
        role="contributor",
    )

    app.dependency_overrides[get_current_principal] = lambda: mock_principal

    approved_draft: dict[str, Any] = {
        "id": str(draft_id),
        "workspace_id": str(workspace_id),
        "campaign_id": str(uuid4()),
        "contact_id": str(uuid4()),
        "status": "approved",
        "current_version_number": 1,
    }

    mock_admin = MagicMock()
    mock_select = mock_admin.table.return_value.select.return_value
    mock_select.eq.return_value.eq.return_value.execute.return_value.data = [approved_draft]

    with patch("app.api.outreach._clients", return_value=(MagicMock(), mock_admin)):
        client = TestClient(app)
        response = client.post(
            f"/v1/outreach/drafts/{draft_id}/actions/generate",
            headers={"Authorization": "Bearer fake-token"},
        )
        assert response.status_code == 400
        assert "cannot_generate_draft_in_approved_state" in response.json()["detail"]

    app.dependency_overrides.clear()
