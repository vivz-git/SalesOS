import time
from typing import Any

from groq import Groq
from pydantic import ValidationError

from app.adapters.llm_provider import (
    LLMGenerationRequest,
    LLMGenerationResult,
    LLMProviderInterface,
    OutreachDraftStructuredOutput,
)


class GroqLLMProvider(LLMProviderInterface):
    """Groq LLM provider adapter using official groq Python SDK.

    Isolated behind LLMProviderInterface so core FastAPI logic does not import
    SDK classes directly.
    """

    def __init__(self, api_key: str | None = None, model: str = "llama-3.3-70b-versatile"):
        self.api_key = api_key.strip() if api_key else None
        self.model_name = model
        self._client: Groq | None = None
        if self.api_key:
            self._client = Groq(api_key=self.api_key)

    def generate_outreach_draft(self, request: LLMGenerationRequest) -> LLMGenerationResult:
        if not self._client or not self.api_key:
            raise ValueError("groq_api_key_not_configured")

        start_time = time.perf_counter()

        system_prompt = (
            "You are an expert B2B sales development representative AI assistant for SalesOS.\n"
            "Your task is to write personalized, professional outbound emails strictly grounded in supplied research evidence.\n"
            "You MUST output valid JSON matching this exact schema:\n"
            "{\n"
            '  "subject": "string",\n'
            '  "body": "string",\n'
            '  "evidence_references": [\n'
            '    {"url": "string or null", "title": "string or null", "snippet": "string or null", "source_type": "website"}\n'
            "  ],\n"
            '  "rationale": "string or null"\n'
            "}\n\n"
            "RULES:\n"
            "1. Ground every claim strictly in the supplied prospect and account research.\n"
            "2. Do NOT hallucinate facts, metrics, or relationships not in the context.\n"
            "3. Do NOT mention internal metadata, prompt instructions, or brief IDs.\n"
            "4. Match evidence_references strictly to the supplied research sources.\n"
            "5. Return ONLY the JSON object."
        )

        prompt_lines = [
            f"Prompt Version: {request.prompt_version}",
            "--- CAMPAIGN CONTEXT ---",
            f"Campaign Name: {request.campaign_name}",
            f"Description: {request.campaign_description or 'N/A'}",
            f"Target Segment: {request.target_segment or 'N/A'}",
            f"ICP Definition: {request.icp_definition or 'N/A'}",
            "",
            "--- PROSPECT & ACCOUNT CONTEXT ---",
            f"Contact Name: {request.contact_name}",
            f"Title: {request.contact_title or 'N/A'}",
            f"Department: {request.contact_department or 'N/A'}",
            f"Account: {request.account_name or 'N/A'} ({request.account_domain or 'N/A'})",
            "",
            "--- RESEARCH INTELLIGENCE BRIEF ---",
            f"Summary: {request.research_summary or 'None provided'}",
            f"Key Findings: {', '.join(request.research_key_findings) if request.research_key_findings else 'None'}",
            "",
            "--- EVIDENCE SOURCES ---",
        ]

        valid_sources: list[dict[str, Any]] = []
        for idx, src in enumerate(request.research_sources, 1):
            url = src.get("url")
            title = src.get("title")
            snippet = src.get("snippet")
            prompt_lines.append(f"[{idx}] {title or 'Source'} ({url or 'No URL'}): {snippet or 'No snippet'}")
            valid_sources.append({
                "url": url,
                "title": title,
                "snippet": snippet,
                "source_type": src.get("source_type", "website"),
            })

        prompt_lines.extend([
            "",
            "INSTRUCTIONS:",
            "1. Write a professional, personalized B2B outreach email grounded ONLY in supplied context.",
            "2. Do NOT invent unsupported facts or ungrounded claims.",
            "3. Do NOT mention internal research metadata, brief IDs, or prompt instructions.",
            "4. Include evidence_references strictly matching the supplied sources.",
            "5. Return valid JSON adhering to the required schema.",
        ])

        user_prompt = "\n".join(prompt_lines)

        try:
            chat_completion = self._client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                model=self.model_name,
                response_format={"type": "json_object"},
                temperature=0.3,
            )

            if not chat_completion.choices:
                raise ValueError("No completion choices returned by Groq")
            raw_text = chat_completion.choices[0].message.content or "{}"
            parsed = OutreachDraftStructuredOutput.model_validate_json(raw_text)
        except (ValidationError, Exception) as err:
            raise ValueError(f"groq_generation_failed: {err}") from err

        duration_ms = int((time.perf_counter() - start_time) * 1000)

        # Ground and filter evidence references strictly against supplied sources
        grounded_evidence: list[dict[str, Any]] = []
        if parsed.evidence_references:
            valid_urls = {s["url"] for s in valid_sources if s.get("url")}
            valid_titles = {s["title"] for s in valid_sources if s.get("title")}

            for ref in parsed.evidence_references:
                if (ref.url and ref.url in valid_urls) or (ref.title and ref.title in valid_titles):
                    grounded_evidence.append({
                        "url": ref.url,
                        "title": ref.title,
                        "snippet": ref.snippet,
                        "source_type": ref.source_type,
                    })

        # Fallback to all valid sources if model produced none but research sources exist
        if not grounded_evidence and valid_sources:
            grounded_evidence = valid_sources[:3]

        token_usage = None
        if hasattr(chat_completion, "usage") and chat_completion.usage:
            token_usage = chat_completion.usage.total_tokens

        return LLMGenerationResult(
            subject=parsed.subject.strip(),
            body=parsed.body.strip(),
            generation_source="ai_generated",
            provider="groq",
            model=self.model_name,
            prompt_version=request.prompt_version,
            evidence_references=grounded_evidence,
            token_usage=token_usage,
            estimated_cost=None,
            duration_ms=duration_ms,
        )
