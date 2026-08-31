"""End-to-End Acceptance Workflow Integration Tests for SalesOS.

Executes and verifies the complete 11-stage user journey:
  Stage 1:  Authentication and Workspace Context (X-SalesOS-Workspace-Id, role resolution)
  Stage 2:  Accounts API (create, retrieve, list, update)
  Stage 3:  Contacts API (create, assign to account/campaign, retrieve, list)
  Stage 4:  Campaign Brief and ICP Setup (create, activate, pause, reactivate)
  Stage 5:  Research Brief Generation and Source Citation (briefs, sources, trigger)
  Stage 6:  AI Outreach Draft Generation (Groq adapter / structured output)
  Stage 7:  Submit Draft for Review (ready_for_review, unapproved delivery guard)
  Stage 8:  Approval Queue Review and Approval Action (queue, item detail, approve)
  Stage 9:  Delivery Scheduling and Execution (Resend idempotency, delivery record)
  Stage 10: Inbound Reply Ingestion and Deterministic Reply Classification (interested, unsubscribe)
  Stage 11: HubSpot CRM Sync Trigger and Weekly Reporting Metrics Snapshot
"""

from collections.abc import AsyncGenerator
from typing import Any
from uuid import UUID, uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import event
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.pool import StaticPool

from app.adapters.email_provider import (
    EmailDeliverySendRequest,
    EmailDeliverySendResult,
    EmailProviderInterface,
)
from app.adapters.llm_provider import (
    LLMGenerationRequest,
    LLMGenerationResult,
    LLMProviderInterface,
    ResearchSynthesisRequest,
    ResearchSynthesisResult,
)
from app.api.deliveries import get_email_provider
from app.api.outreach import get_llm_provider
from app.auth import AuthUser, Principal, get_current_principal, get_current_user
from app.core.config import Settings, get_settings
from app.db import get_db_session
from app.main import app
from app.models import Base


# Compiler adaptations for in-memory SQLite test harness
@compiles(JSONB, "sqlite")
def compile_jsonb_sqlite(type_: Any, compiler: Any, **kw: Any) -> str:
    return "JSON"


@compiles(PGUUID, "sqlite")
def compile_pguuid_sqlite(type_: Any, compiler: Any, **kw: Any) -> str:
    return "CHAR(36)"


pytestmark = pytest.mark.asyncio


class MockLLMProvider(LLMProviderInterface):
    """Deterministic LLM Provider Mock for E2E testing."""

    def generate_outreach_draft(self, request: LLMGenerationRequest) -> LLMGenerationResult:
        evidence = []
        if request.research_sources:
            for s in request.research_sources[:2]:
                evidence.append(
                    {
                        "url": s.get("url"),
                        "title": s.get("title"),
                        "snippet": s.get("snippet"),
                        "source_type": s.get("source_type", "website"),
                    }
                )

        return LLMGenerationResult(
            subject=f"Accelerating {request.account_name or 'Your'} Core Platform",
            body=(
                f"Hi {request.contact_name},\n\n"
                f"I noticed {request.account_name} is actively focusing on {request.target_segment or 'engineering'}. "
                f"Given your role as {request.contact_title or 'leader'}, our solution helps streamline outbound sales "
                f"with governed human-in-the-loop workflows.\n\nBest regards,\nSalesOS Team"
            ),
            generation_source="ai_generated",
            provider="groq",
            model="llama-3.3-70b-versatile",
            prompt_version=request.prompt_version,
            evidence_references=evidence,
            token_usage=256,
            estimated_cost=0.00015,
            duration_ms=420,
        )

    def generate_research_synthesis(
        self, request: ResearchSynthesisRequest
    ) -> ResearchSynthesisResult:
        return ResearchSynthesisResult(
            summary=f"Synthesized research for {request.account_name}",
            key_insights=[
                f"Active in {request.account_industry or 'Tech'}",
                "Growing outbound motion",
            ],
            confidence_score=0.92,
            recommended_hooks=[f"Mention scale at {request.account_name}"],
            provider="groq",
            model="llama-3.3-70b-versatile",
            prompt_version=request.prompt_version,
            token_usage=180,
            estimated_cost=0.0001,
            duration_ms=350,
        )


class MockEmailProvider(EmailProviderInterface):
    """Deterministic Email Provider Mock for E2E testing."""

    def __init__(self) -> None:
        self.sent_requests: list[EmailDeliverySendRequest] = []

    def send_email(self, request: EmailDeliverySendRequest) -> EmailDeliverySendResult:
        self.sent_requests.append(request)
        return EmailDeliverySendResult(
            provider="resend",
            provider_message_id=f"msg_resend_mock_{uuid4().hex[:12]}",
            status="sent",
            idempotency_key=request.idempotency_key,
            duration_ms=150,
            raw_response={"id": "mock_resend_id", "from": request.from_email},
        )


@pytest.fixture
async def e2e_harness() -> AsyncGenerator[dict[str, Any], None]:
    """Sets up an isolated in-memory test database and dependencies for E2E workflow testing."""
    engine = create_async_engine(
        "sqlite+aiosqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine.sync_engine, "connect")
    def register_sqlite_functions(dbapi_conn: Any, _: Any) -> None:
        dbapi_conn.create_function("set_config", 3, lambda name, val, is_local: val)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )

    workspace_id = uuid4()
    user_id = uuid4()
    owner_principal = Principal(
        user_id=user_id,
        email="owner@acme-salesos.dev",
        workspace_id=workspace_id,
        role="owner",
    )
    auth_user = AuthUser(user_id=user_id, email="owner@acme-salesos.dev")

    mock_llm = MockLLMProvider()
    mock_email = MockEmailProvider()
    mock_settings = Settings(
        environment="test",
        resend_from_email="outreach@acme-salesos.dev",
        frontend_url="https://app.salesos.dev",
    )

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db_session] = override_get_db
    app.dependency_overrides[get_current_principal] = lambda: owner_principal
    app.dependency_overrides[get_current_user] = lambda: auth_user
    app.dependency_overrides[get_llm_provider] = lambda: mock_llm
    app.dependency_overrides[get_email_provider] = lambda: mock_email
    app.dependency_overrides[get_settings] = lambda: mock_settings

    yield {
        "workspace_id": workspace_id,
        "user_id": user_id,
        "principal": owner_principal,
        "mock_llm": mock_llm,
        "mock_email": mock_email,
        "session_factory": session_factory,
    }

    app.dependency_overrides.clear()
    await engine.dispose()


async def test_complete_11_stage_acceptance_workflow(e2e_harness: dict[str, Any]) -> None:
    """Executes the complete 11-stage user journey and asserts all lifecycle invariants."""
    workspace_id: UUID = e2e_harness["workspace_id"]
    user_id: UUID = e2e_harness["user_id"]
    mock_email: MockEmailProvider = e2e_harness["mock_email"]

    headers = {
        "X-SalesOS-Workspace-Id": str(workspace_id),
        "Authorization": "Bearer mock_jwt_token",
    }

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # =========================================================================
        # STAGE 1: Authentication and Workspace Context
        # =========================================================================
        me_resp = await client.get("/v1/me", headers=headers)
        assert me_resp.status_code == 200, f"Stage 1 failed: {me_resp.text}"
        me_data = me_resp.json()
        assert me_data["user_id"] == str(user_id)
        assert me_data["workspace_id"] == str(workspace_id)
        assert me_data["role"] == "owner"

        # =========================================================================
        # STAGE 2: Accounts API (Create, Retrieve, List, Update)
        # =========================================================================
        create_account_payload = {
            "name": "Stark Industries",
            "domain": "starkindustries.com",
            "industry": "Aerospace and Defense",
            "employee_count": "1000-5000",
            "city": "New York",
            "state": "NY",
            "country": "USA",
        }
        acc_create_resp = await client.post(
            "/v1/accounts", json=create_account_payload, headers=headers
        )
        assert acc_create_resp.status_code == 201, (
            f"Stage 2 (Create Account) failed: {acc_create_resp.text}"
        )
        account = acc_create_resp.json()
        account_id = account["id"]
        assert account["name"] == "Stark Industries"
        assert account["domain"] == "starkindustries.com"
        assert account["status"] == "target"
        assert account["workspace_id"] == str(workspace_id)

        # Retrieve Account
        acc_get_resp = await client.get(f"/v1/accounts/{account_id}", headers=headers)
        assert acc_get_resp.status_code == 200
        assert acc_get_resp.json()["id"] == account_id

        # Update Account
        acc_patch_resp = await client.patch(
            f"/v1/accounts/{account_id}",
            json={"employee_count": "5000+", "status": "qualified"},
            headers=headers,
        )
        assert acc_patch_resp.status_code == 200
        assert acc_patch_resp.json()["employee_count"] == "5000+"
        assert acc_patch_resp.json()["status"] == "qualified"

        # List Accounts
        acc_list_resp = await client.get("/v1/accounts", headers=headers)
        assert acc_list_resp.status_code == 200
        assert any(a["id"] == account_id for a in acc_list_resp.json())

        # =========================================================================
        # STAGE 3: Contacts API (Create, Assign, Retrieve, List)
        # =========================================================================
        create_contact_payload = {
            "first_name": "Pepper",
            "last_name": "Potts",
            "account_id": account_id,
            "email": "pepper.potts@starkindustries.com",
            "phone": "+1-555-0199",
            "title": "Chief Executive Officer",
            "department": "Executive",
            "is_primary": True,
        }
        contact_create_resp = await client.post(
            "/v1/contacts", json=create_contact_payload, headers=headers
        )
        assert contact_create_resp.status_code == 201, (
            f"Stage 3 (Create Contact) failed: {contact_create_resp.text}"
        )
        contact = contact_create_resp.json()
        contact_id = contact["id"]
        assert contact["first_name"] == "Pepper"
        assert contact["email"] == "pepper.potts@starkindustries.com"
        assert contact["account_id"] == account_id
        assert contact["is_primary"] is True
        assert contact["status"] == "active"

        # Retrieve Contact
        contact_get_resp = await client.get(f"/v1/contacts/{contact_id}", headers=headers)
        assert contact_get_resp.status_code == 200
        assert contact_get_resp.json()["id"] == contact_id

        # List Contacts by Account
        contact_list_resp = await client.get(
            f"/v1/contacts?account_id={account_id}", headers=headers
        )
        assert contact_list_resp.status_code == 200
        assert len(contact_list_resp.json()) == 1
        assert contact_list_resp.json()[0]["id"] == contact_id

        # =========================================================================
        # STAGE 4: Campaign Brief and ICP Setup (Create, Activate, Pause, Reactivate)
        # =========================================================================
        create_campaign_payload = {
            "name": "Q3 Enterprise Defense Modernization",
            "description": "Outreach targeting C-level executives at defense tech leaders",
            "target_segment": "Enterprise Aerospace and Defense",
            "icp_definition": "Series C+ or Public Aerospace enterprises modernizing supply chain platforms",
        }
        camp_create_resp = await client.post(
            "/v1/campaigns", json=create_campaign_payload, headers=headers
        )
        assert camp_create_resp.status_code == 201, (
            f"Stage 4 (Create Campaign) failed: {camp_create_resp.text}"
        )
        campaign = camp_create_resp.json()
        campaign_id = campaign["id"]
        assert campaign["name"] == "Q3 Enterprise Defense Modernization"
        assert campaign["status"] == "draft"

        # Activate Campaign
        activate_resp = await client.post(
            f"/v1/campaigns/{campaign_id}/actions/activate", headers=headers
        )
        assert activate_resp.status_code == 200
        assert activate_resp.json()["status"] == "active"

        # Pause Campaign
        pause_resp = await client.post(
            f"/v1/campaigns/{campaign_id}/actions/pause", headers=headers
        )
        assert pause_resp.status_code == 200
        assert pause_resp.json()["status"] == "paused"

        # Reactivate Campaign
        reactivate_resp = await client.post(
            f"/v1/campaigns/{campaign_id}/actions/activate", headers=headers
        )
        assert reactivate_resp.status_code == 200
        assert reactivate_resp.json()["status"] == "active"

        # Assign Campaign to Contact
        await client.patch(
            f"/v1/contacts/{contact_id}", json={"campaign_id": campaign_id}, headers=headers
        )

        # =========================================================================
        # STAGE 5: Research Brief Generation and Source Citation
        # =========================================================================
        create_brief_payload = {
            "account_id": account_id,
            "contact_id": contact_id,
            "summary": "Stark Industries is expanding clean-energy arc reactor infrastructure and defense cloud systems.",
            "key_findings": [
                "Deploying new automated supply chain logistics",
                "Hiring 50+ cloud infrastructure engineers",
                "Recent $100M initiative for next-generation defense analytics",
            ],
        }
        brief_create_resp = await client.post(
            "/v1/research/briefs", json=create_brief_payload, headers=headers
        )
        assert brief_create_resp.status_code == 201, (
            f"Stage 5 (Create Brief) failed: {brief_create_resp.text}"
        )
        brief = brief_create_resp.json()
        brief_id = brief["id"]
        assert brief["status"] == "pending"
        assert len(brief["key_findings"]) == 3

        # Add Source Citations
        source_1_payload = {
            "url": "https://starkindustries.example.com/press/arc-expansion",
            "title": "Stark Industries Announces Clean Energy Expansion",
            "source_type": "website",
            "snippet": "CEO Pepper Potts announces $100M investment in automated logistics platform.",
            "confidence": 0.95,
        }
        source_2_payload = {
            "url": "https://starkindustries.example.com/careers/cloud",
            "title": "Careers at Stark Industries",
            "source_type": "website",
            "snippet": "Seeking Senior Platform Engineers to modernize supply-chain microservices.",
            "confidence": 0.90,
        }
        s1_resp = await client.post(
            f"/v1/research/briefs/{brief_id}/sources", json=source_1_payload, headers=headers
        )
        assert s1_resp.status_code == 201
        s2_resp = await client.post(
            f"/v1/research/briefs/{brief_id}/sources", json=source_2_payload, headers=headers
        )
        assert s2_resp.status_code == 201

        # Trigger Research Job
        trigger_resp = await client.post(
            f"/v1/research/briefs/{brief_id}/actions/trigger", headers=headers
        )
        assert trigger_resp.status_code == 200
        assert trigger_resp.json()["status"] == "queued"

        # Update Brief to completed state
        brief_update_resp = await client.patch(
            f"/v1/research/briefs/{brief_id}",
            json={
                "status": "completed",
                "confidence_score": 0.94,
                "confidence_reason": "High-confidence executive signals from official press releases and hiring boards",
            },
            headers=headers,
        )
        assert brief_update_resp.status_code == 200
        assert brief_update_resp.json()["status"] == "completed"

        # List Sources for Brief
        sources_list_resp = await client.get(
            f"/v1/research/briefs/{brief_id}/sources", headers=headers
        )
        assert sources_list_resp.status_code == 200
        assert len(sources_list_resp.json()) == 2

        # =========================================================================
        # STAGE 6: AI Outreach Draft Generation (Structured Output / Provider)
        # =========================================================================
        create_draft_payload = {
            "campaign_id": campaign_id,
            "contact_id": contact_id,
            "research_brief_id": brief_id,
            "subject": "Initial Scaffold Subject",
            "body": "Initial Scaffold Body",
            "generation_source": "human",
        }
        draft_create_resp = await client.post(
            "/v1/outreach/drafts", json=create_draft_payload, headers=headers
        )
        assert draft_create_resp.status_code == 201, (
            f"Stage 6 (Create Draft) failed: {draft_create_resp.text}"
        )
        draft = draft_create_resp.json()
        draft_id = draft["id"]
        assert draft["status"] == "draft"
        assert draft["current_version_number"] == 1

        # Execute AI Generation Action
        gen_resp = await client.post(
            f"/v1/outreach/drafts/{draft_id}/actions/generate", headers=headers
        )
        assert gen_resp.status_code == 200, f"Stage 6 (Generate AI Draft) failed: {gen_resp.text}"
        generated_draft = gen_resp.json()
        assert generated_draft["current_version_number"] == 2
        assert "Stark Industries" in generated_draft["current_subject"]
        assert "Pepper" in generated_draft["current_body"]
        assert generated_draft["status"] == "draft"

        # Verify Draft Version Details and Evidence References
        versions_resp = await client.get(
            f"/v1/outreach/drafts/{draft_id}/versions", headers=headers
        )
        assert versions_resp.status_code == 200
        versions = versions_resp.json()
        assert len(versions) == 2
        v2 = [v for v in versions if v["version_number"] == 2][0]
        assert v2["generation_source"] == "ai_generated"
        assert v2["provider"] == "groq"
        assert len(v2["evidence_references"]) == 2
        assert (
            v2["evidence_references"][0]["url"]
            == "https://starkindustries.example.com/press/arc-expansion"
        )

        # =========================================================================
        # STAGE 7: Submit Draft for Review and Unapproved Delivery Guard
        # =========================================================================
        # Guard Check: Attempting delivery while status is 'draft' MUST fail with 400
        guard_draft_resp = await client.post(
            "/v1/deliveries",
            json={"draft_id": draft_id},
            headers=headers,
        )
        assert guard_draft_resp.status_code == 400
        assert "cannot_deliver_unapproved_draft" in guard_draft_resp.text

        # Submit draft for review
        submit_resp = await client.post(
            f"/v1/outreach/drafts/{draft_id}/actions/submit-review", headers=headers
        )
        assert submit_resp.status_code == 200, f"Stage 7 (Submit Review) failed: {submit_resp.text}"
        assert submit_resp.json()["status"] == "ready_for_review"

        # Guard Check: Attempting delivery while status is 'ready_for_review' MUST fail with 400
        guard_review_resp = await client.post(
            "/v1/deliveries",
            json={"draft_id": draft_id},
            headers=headers,
        )
        assert guard_review_resp.status_code == 400
        assert "cannot_deliver_unapproved_draft" in guard_review_resp.text

        # =========================================================================
        # STAGE 8: Approval Queue Review and Approval Action
        # =========================================================================
        queue_resp = await client.get("/v1/approvals/queue", headers=headers)
        assert queue_resp.status_code == 200, f"Stage 8 (Approval Queue) failed: {queue_resp.text}"
        queue_items = queue_resp.json()
        assert any(item["id"] == draft_id for item in queue_items)

        # Get Approval Item Detail (context verification)
        item_detail_resp = await client.get(f"/v1/approvals/items/{draft_id}", headers=headers)
        assert item_detail_resp.status_code == 200
        item_detail = item_detail_resp.json()
        assert item_detail["campaign_name"] == "Q3 Enterprise Defense Modernization"
        assert item_detail["contact_name"] == "Pepper Potts"
        assert item_detail["account_name"] == "Stark Industries"
        assert item_detail["draft"]["id"] == draft_id

        # Submit Human Approval Decision
        decision_payload = {
            "decision": "approved",
            "notes": "Tone, personalization, and evidence references verified by Sales Director.",
        }
        decision_resp = await client.post(
            f"/v1/approvals/items/{draft_id}/decision",
            json=decision_payload,
            headers=headers,
        )
        assert decision_resp.status_code == 200, (
            f"Stage 8 (Approval Decision) failed: {decision_resp.text}"
        )
        audit_record = decision_resp.json()
        assert audit_record["decision"] == "approved"
        assert audit_record["version_number"] == 2

        # Verify draft status is now approved
        approved_draft_resp = await client.get(f"/v1/outreach/drafts/{draft_id}", headers=headers)
        assert approved_draft_resp.status_code == 200
        assert approved_draft_resp.json()["status"] == "approved"

        # =========================================================================
        # STAGE 9: Delivery Scheduling and Execution (Resend Idempotency)
        # =========================================================================
        delivery_resp = await client.post(
            "/v1/deliveries",
            json={"draft_id": draft_id},
            headers=headers,
        )
        assert delivery_resp.status_code == 200, f"Stage 9 (Delivery) failed: {delivery_resp.text}"
        delivery = delivery_resp.json()
        delivery_id = delivery["id"]
        provider_message_id = delivery["provider_message_id"]
        assert delivery["status"] == "sent"
        assert delivery["recipient_email"] == "pepper.potts@starkindustries.com"
        assert delivery["version_number"] == 2
        assert delivery["idempotency_key"] == f"{workspace_id}:{draft_id}:2"
        assert len(mock_email.sent_requests) == 1

        # IDEMPOTENCY TEST: Submitting same delivery again MUST return existing record without re-sending
        idempotent_resp = await client.post(
            "/v1/deliveries",
            json={"draft_id": draft_id},
            headers=headers,
        )
        assert idempotent_resp.status_code == 200
        assert idempotent_resp.json()["id"] == delivery_id
        assert len(mock_email.sent_requests) == 1, "Idempotency failed: duplicate email was sent!"

        # Retrieve Delivery Detail
        deliv_get_resp = await client.get(f"/v1/deliveries/{delivery_id}", headers=headers)
        assert deliv_get_resp.status_code == 200
        assert deliv_get_resp.json()["id"] == delivery_id

        # List Deliveries
        deliv_list_resp = await client.get("/v1/deliveries", headers=headers)
        assert deliv_list_resp.status_code == 200
        assert any(d["id"] == delivery_id for d in deliv_list_resp.json())

        # =========================================================================
        # STAGE 10: Inbound Reply Ingestion and Deterministic Classification
        # =========================================================================
        # 10A: Positive / Interested Inbound Reply
        interested_inbound_payload = {
            "workspace_id": str(workspace_id),
            "sender_email": "pepper.potts@starkindustries.com",
            "recipient_email": "outreach@acme-salesos.dev",
            "subject": "Re: Accelerating Stark Industries Core Platform",
            "body": "Hi, thanks for reaching out. This sounds very interesting! Let's schedule a call next Tuesday to discuss.",
            "provider_message_id": "inbound_msg_interested_001",
            "in_reply_to_provider_message_id": provider_message_id,
        }
        inbound_resp1 = await client.post(
            "/v1/conversations/simulate", json=interested_inbound_payload, headers=headers
        )
        assert inbound_resp1.status_code == 200, (
            f"Stage 10A (Inbound Interested) failed: {inbound_resp1.text}"
        )
        conv1 = inbound_resp1.json()
        assert conv1["current_reply_state"] == "interested"
        assert conv1["contact_id"] == str(contact_id)

        # Verify conversation contains message
        conv_id = conv1["id"]
        conv_detail_resp = await client.get(f"/v1/conversations/{conv_id}", headers=headers)
        assert conv_detail_resp.status_code == 200
        conv_detail = conv_detail_resp.json()
        assert conv_detail["current_reply_state"] == "interested"
        assert len(conv_detail["messages"]) >= 1

        # 10B: Opt-Out / Unsubscribe Inbound Reply
        unsubscribe_inbound_payload = {
            "workspace_id": str(workspace_id),
            "sender_email": "pepper.potts@starkindustries.com",
            "recipient_email": "outreach@acme-salesos.dev",
            "subject": "Re: Accelerating Stark Industries Core Platform",
            "body": "Please remove me from your list and unsubscribe immediately.",
            "provider_message_id": "inbound_msg_unsub_002",
            "in_reply_to_provider_message_id": provider_message_id,
        }
        inbound_resp2 = await client.post(
            "/v1/conversations/simulate", json=unsubscribe_inbound_payload, headers=headers
        )
        assert inbound_resp2.status_code == 200, (
            f"Stage 10B (Inbound Unsubscribe) failed: {inbound_resp2.text}"
        )
        conv2 = inbound_resp2.json()
        assert conv2["current_reply_state"] == "unsubscribe"
        assert conv2["status"] == "opt_out"

        # =========================================================================
        # STAGE 11: HubSpot CRM Sync and Weekly Reporting Metrics Snapshot
        # =========================================================================
        # 11A: HubSpot Integration OAuth and Sync
        auth_resp = await client.post("/v1/integrations/hubspot/actions/authorize", headers=headers)
        assert auth_resp.status_code == 200, (
            f"Stage 11A (HubSpot Authorize) failed: {auth_resp.text}"
        )
        auth_data = auth_resp.json()
        assert "https://app.hubspot.com/oauth/authorize" in auth_data["authorization_url"]
        assert str(workspace_id) in auth_data["state"]

        # OAuth Callback Simulation
        callback_resp = await client.get(
            f"/v1/integrations/hubspot/oauth/callback?code=mock_oauth_code_123&state={auth_data['state']}",
            headers=headers,
        )
        assert callback_resp.status_code == 200
        assert callback_resp.json()["status"] == "connected"
        assert "access_token" not in callback_resp.json(), (
            "Security leak: raw token exposed in response!"
        )

        # Trigger CRM Export Sync
        sync_resp = await client.post(
            "/v1/integrations/hubspot/actions/sync",
            json={"direction": "export_to_crm", "campaign_id": campaign_id},
            headers=headers,
        )
        assert sync_resp.status_code == 200
        sync_data = sync_resp.json()
        assert sync_data["status"] == "completed"
        assert sync_data["records_processed"] == 5

        # 11B: Weekly Performance Metrics Digest Generation
        report_gen_resp = await client.post("/v1/reports/weekly/actions/generate", headers=headers)
        assert report_gen_resp.status_code == 200, (
            f"Stage 11B (Generate Report) failed: {report_gen_resp.text}"
        )
        report = report_gen_resp.json()
        metrics = report["metrics_snapshot"]

        assert metrics["campaigns_count"] >= 1
        assert metrics["accounts_researched_count"] >= 1
        assert metrics["contacts_enrolled_count"] == 0
        assert metrics["drafts_generated_count"] >= 1
        assert metrics["drafts_approved_count"] >= 1
        assert metrics["approval_rate"] > 0.0
        assert metrics["emails_sent_count"] >= 1
        assert metrics["replies_received_count"] >= 1
        assert metrics["crm_synced_records_count"] >= 5
        assert len(report["recommended_actions"]) >= 1

        # List Reports
        reports_list_resp = await client.get("/v1/reports/weekly", headers=headers)
        assert reports_list_resp.status_code == 200
        assert len(reports_list_resp.json()) >= 1
