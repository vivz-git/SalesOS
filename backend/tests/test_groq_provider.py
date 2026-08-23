import json
from unittest.mock import MagicMock, patch

import pytest

from app.adapters.groq_provider import GroqLLMProvider
from app.adapters.llm_provider import LLMGenerationRequest


def _sample_request() -> LLMGenerationRequest:
    return LLMGenerationRequest(
        campaign_name="Q3 Expansion",
        campaign_description="Outreach to VP of Engineering",
        target_segment="Enterprise Fintech",
        icp_definition="Series B+ Fintechs in North America",
        contact_name="Sarah Connor",
        contact_title="VP of Engineering",
        contact_department="Engineering",
        account_name="Cyberdyne Systems",
        account_domain="cyberdyne.example.com",
        research_summary="Cyberdyne is modernizing core banking APIs and expanding infrastructure.",
        research_key_findings=["Hiring 20+ distributed backend engineers", "Migrating legacy payments"],
        research_sources=[
            {
                "url": "https://cyberdyne.example.com/press/series-b",
                "title": "Series B Funding Announcement",
                "snippet": "Cyberdyne secures $50M to scale developer platform.",
                "source_type": "website",
            },
            {
                "url": "https://cyberdyne.example.com/careers",
                "title": "Careers at Cyberdyne",
                "snippet": "Now hiring Senior Distributed Systems Engineers.",
                "source_type": "website",
            },
        ],
        prompt_version="v1.0.0",
    )


def test_groq_provider_missing_key_raises() -> None:
    provider = GroqLLMProvider(api_key=None)
    req = _sample_request()
    with pytest.raises(ValueError, match="groq_api_key_not_configured"):
        provider.generate_outreach_draft(req)


@patch("app.adapters.groq_provider.Groq")
def test_groq_provider_successful_generation(mock_groq_class: MagicMock) -> None:
    mock_client = MagicMock()
    mock_groq_class.return_value = mock_client

    mock_chat = MagicMock()
    mock_client.chat = mock_chat

    # Structured JSON response from model
    mock_payload = {
        "subject": "Scaling Cyberdyne's Distributed Systems & Payments API",
        "body": "Hi Sarah,\n\nCongrats on the $50M Series B. Noticed Cyberdyne is scaling backend infrastructure.",
        "evidence_references": [
            {
                "url": "https://cyberdyne.example.com/press/series-b",
                "title": "Series B Funding Announcement",
                "snippet": "Cyberdyne secures $50M to scale developer platform.",
                "source_type": "website",
            }
        ],
        "rationale": "Leveraged Series B funding and engineering hiring signals.",
    }

    mock_choice = MagicMock()
    mock_choice.message.content = json.dumps(mock_payload)

    mock_usage = MagicMock()
    mock_usage.total_tokens = 342

    mock_response = MagicMock()
    mock_response.choices = [mock_choice]
    mock_response.usage = mock_usage

    mock_chat.completions.create.return_value = mock_response

    provider = GroqLLMProvider(api_key="gsk_test_key_123", model="llama-3.3-70b-versatile")
    req = _sample_request()

    result = provider.generate_outreach_draft(req)

    assert result.provider == "groq"
    assert result.model == "llama-3.3-70b-versatile"
    assert result.subject == "Scaling Cyberdyne's Distributed Systems & Payments API"
    assert "Congrats on the $50M Series B" in result.body
    assert result.token_usage == 342
    assert result.duration_ms is not None and result.duration_ms >= 0
    assert len(result.evidence_references) == 1
    assert result.evidence_references[0]["url"] == "https://cyberdyne.example.com/press/series-b"

    # Verify chat completion call arguments
    mock_chat.completions.create.assert_called_once()
    kwargs = mock_chat.completions.create.call_args[1]
    assert kwargs["model"] == "llama-3.3-70b-versatile"
    assert kwargs["response_format"] == {"type": "json_object"}
    assert len(kwargs["messages"]) == 2
    assert kwargs["messages"][0]["role"] == "system"
    assert kwargs["messages"][1]["role"] == "user"


@patch("app.adapters.groq_provider.Groq")
def test_groq_provider_fallback_evidence_when_model_omits(mock_groq_class: MagicMock) -> None:
    mock_client = MagicMock()
    mock_groq_class.return_value = mock_client

    mock_payload = {
        "subject": "Quick inquiry regarding engineering scale",
        "body": "Hi Sarah, wanted to connect on engineering platform scale.",
        "evidence_references": [],
        "rationale": "Direct executive outreach",
    }

    mock_choice = MagicMock()
    mock_choice.message.content = json.dumps(mock_payload)
    mock_response = MagicMock()
    mock_response.choices = [mock_choice]
    mock_response.usage = None

    mock_client.chat.completions.create.return_value = mock_response

    provider = GroqLLMProvider(api_key="gsk_test_key_123", model="llama-3.3-70b-versatile")
    req = _sample_request()

    result = provider.generate_outreach_draft(req)

    # Fallback populates up to 3 valid research sources
    assert len(result.evidence_references) == 2
    assert result.evidence_references[0]["url"] == "https://cyberdyne.example.com/press/series-b"


@patch("app.adapters.groq_provider.Groq")
def test_groq_provider_invalid_json_raises_value_error(mock_groq_class: MagicMock) -> None:
    mock_client = MagicMock()
    mock_groq_class.return_value = mock_client

    mock_choice = MagicMock()
    mock_choice.message.content = "Not a valid JSON payload {"
    mock_response = MagicMock()
    mock_response.choices = [mock_choice]

    mock_client.chat.completions.create.return_value = mock_response

    provider = GroqLLMProvider(api_key="gsk_test_key_123")
    req = _sample_request()

    with pytest.raises(ValueError, match="groq_generation_failed"):
        provider.generate_outreach_draft(req)


@patch("app.adapters.groq_provider.Groq")
def test_groq_provider_api_error_raises_value_error(mock_groq_class: MagicMock) -> None:
    mock_client = MagicMock()
    mock_groq_class.return_value = mock_client

    mock_client.chat.completions.create.side_effect = RuntimeError("Groq rate limit exceeded")

    provider = GroqLLMProvider(api_key="gsk_test_key_123")
    req = _sample_request()

    with pytest.raises(ValueError, match="groq_generation_failed: Groq rate limit exceeded"):
        provider.generate_outreach_draft(req)
