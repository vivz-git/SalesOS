import json
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.adapters.groq_provider import GroqLLMProvider
from app.adapters.llm_provider import ResearchSynthesisRequest
from app.models import AccountModel, ContactModel, JobModel, ResearchBriefModel
from app.worker import _execute_research_generation_job


def test_groq_provider_research_synthesis_success() -> None:
    req = ResearchSynthesisRequest(
        account_name="Acme Health",
        account_domain="acmehealth.com",
        industry="Healthcare Technology",
        description="Provides cloud EHR systems.",
        contact_name="Alice Smith",
        contact_title="Chief Technology Officer",
        sources=[
            {
                "url": "https://acmehealth.com/news/1",
                "title": "EHR Launch",
                "snippet": "Acme launches new cloud platform.",
                "source_type": "website",
            }
        ],
    )

    with patch("app.adapters.groq_provider.Groq") as mock_groq_class:
        mock_client = MagicMock()
        mock_groq_class.return_value = mock_client

        mock_payload = {
            "summary": "Acme Health is expanding cloud EHR solutions.",
            "key_findings": [
                "Launched next-gen cloud EHR",
                "Scaling engineering leadership under CTO Alice Smith",
            ],
            "confidence_score": 0.92,
            "confidence_reason": "Direct evidence from company announcements.",
        }

        mock_choice = MagicMock()
        mock_choice.message.content = json.dumps(mock_payload)
        mock_usage = MagicMock()
        mock_usage.total_tokens = 280
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_response.usage = mock_usage

        mock_client.chat.completions.create.return_value = mock_response

        provider = GroqLLMProvider(api_key="gsk_valid_key_123")
        result = provider.generate_research_synthesis(req)

        assert result.summary == "Acme Health is expanding cloud EHR solutions."
        assert len(result.key_findings) == 2
        assert result.confidence_score == 0.92
        assert result.provider == "groq"
        assert result.token_usage == 280


@pytest.mark.asyncio
async def test_worker_research_generation_fallback_when_no_api_key() -> None:
    brief_id = uuid4()
    account_id = uuid4()
    contact_id = uuid4()
    job_id = uuid4()

    mock_job = JobModel(
        id=job_id,
        workspace_id=uuid4(),
        job_type="research_generation",
        payload={"brief_id": str(brief_id)},
        status="running",
    )

    mock_brief = ResearchBriefModel(
        id=brief_id,
        workspace_id=mock_job.workspace_id,
        account_id=account_id,
        contact_id=contact_id,
        status="pending",
    )

    mock_account = AccountModel(
        id=account_id,
        workspace_id=mock_job.workspace_id,
        name="Fintech Solutions",
        domain="fintech.example.com",
        industry="Financial Services",
    )

    mock_contact = ContactModel(
        id=contact_id,
        workspace_id=mock_job.workspace_id,
        first_name="Bob",
        last_name="Johnson",
        title="VP of Sales",
    )

    mock_session = AsyncMock()
    mock_session.scalar.side_effect = [mock_brief, mock_account, mock_contact]
    mock_session.scalars.return_value = []

    with patch("app.worker.get_settings") as mock_get_settings:
        # Settings with groq_api_key = None
        mock_settings = MagicMock()
        mock_settings.groq_api_key = None
        mock_get_settings.return_value = mock_settings

        await _execute_research_generation_job(mock_session, mock_job)

        assert mock_brief.status == "completed"
        assert "Fintech Solutions" in (mock_brief.summary or "")
        assert mock_brief.confidence_score == 0.75
        assert mock_brief.provider == "system"
        assert len(mock_brief.key_findings) >= 2
