from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel, Field


class EvidenceItem(BaseModel):
    url: str | None = None
    title: str | None = None
    snippet: str | None = None
    source_type: str = "website"


class OutreachDraftStructuredOutput(BaseModel):
    subject: str = Field(..., description="Concise, personalized B2B outreach email subject line")
    body: str = Field(..., description="Personalized B2B outbound email body grounded strictly in supplied research context")
    evidence_references: list[EvidenceItem] = Field(default_factory=list, description="List of evidence sources referenced in generating this message")
    rationale: str | None = Field(default=None, description="Brief explanation of why this personalization strategy was chosen")


class LLMGenerationRequest(BaseModel):
    campaign_name: str
    campaign_description: str | None = None
    target_segment: str | None = None
    icp_definition: str | None = None
    contact_name: str
    contact_title: str | None = None
    contact_department: str | None = None
    account_name: str | None = None
    account_domain: str | None = None
    research_summary: str | None = None
    research_key_findings: list[str] = Field(default_factory=list)
    research_sources: list[dict[str, Any]] = Field(default_factory=list)
    prompt_version: str = "v1.0.0"


class LLMGenerationResult(BaseModel):
    subject: str
    body: str
    generation_source: str = "ai_generated"
    provider: str
    model: str
    prompt_version: str
    evidence_references: list[dict[str, Any]] = Field(default_factory=list)
    token_usage: int | None = None
    estimated_cost: float | None = None
    duration_ms: int | None = None


class LLMProviderInterface(ABC):
    """Abstract interface for LLM message generation providers.

    Allows plugging in Gemini, OpenAI, Anthropic, or local model adapters
    without modifying FastAPI core domain rules or draft lifecycle logic.
    """

    @abstractmethod
    def generate_outreach_draft(self, request: LLMGenerationRequest) -> LLMGenerationResult:
        """Generate a structured B2B outreach draft based on request context."""
        pass
