from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Index, Integer, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class WorkspaceModel(Base):
    __tablename__ = "workspaces"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class MembershipModel(Base):
    __tablename__ = "memberships"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    workspace_id: Mapped[UUID] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), nullable=False
    )  # references auth.users(id)
    role: Mapped[str] = mapped_column(
        Enum("owner", "admin", "manager", "contributor", "viewer", name="membership_role"),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class CampaignModel(Base):
    __tablename__ = "campaigns"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    workspace_id: Mapped[UUID] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str | None] = mapped_column(String(1000))
    target_segment: Mapped[str | None] = mapped_column(String(255))
    icp_definition: Mapped[str | None] = mapped_column(String(2000))
    status: Mapped[str] = mapped_column(
        Enum("draft", "active", "paused", "archived", name="campaign_status"),
        nullable=False,
        default="draft",
    )
    created_by: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True)
    )  # references auth.users(id)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class AccountModel(Base):
    __tablename__ = "accounts"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    workspace_id: Mapped[UUID] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False
    )
    campaign_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("campaigns.id", ondelete="SET NULL")
    )
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    domain: Mapped[str | None] = mapped_column(String(255))
    industry: Mapped[str | None] = mapped_column(String(100))
    employee_count: Mapped[str | None] = mapped_column(String(50))
    city: Mapped[str | None] = mapped_column(String(100))
    state: Mapped[str | None] = mapped_column(String(100))
    country: Mapped[str | None] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(
        Enum("target", "qualified", "disqualified", "archived", name="account_status"),
        nullable=False,
        default="target",
    )
    created_by: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True)
    )  # references auth.users(id)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class ContactModel(Base):
    __tablename__ = "contacts"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    workspace_id: Mapped[UUID] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False
    )
    account_id: Mapped[UUID | None] = mapped_column(ForeignKey("accounts.id", ondelete="SET NULL"))
    campaign_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("campaigns.id", ondelete="SET NULL")
    )
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255))
    phone: Mapped[str | None] = mapped_column(String(50))
    title: Mapped[str | None] = mapped_column(String(100))
    department: Mapped[str | None] = mapped_column(String(100))
    linkedin_url: Mapped[str | None] = mapped_column(String(255))
    is_primary: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    status: Mapped[str] = mapped_column(
        Enum("active", "unresponsive", "opted_out", "archived", name="contact_status"),
        nullable=False,
        default="active",
    )
    created_by: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True)
    )  # references auth.users(id)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class SequenceDefinitionModel(Base):
    __tablename__ = "sequence_definitions"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    workspace_id: Mapped[UUID] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False
    )
    campaign_id: Mapped[UUID] = mapped_column(
        ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    version_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class SequenceStepModel(Base):
    __tablename__ = "sequence_steps"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    sequence_id: Mapped[UUID] = mapped_column(
        ForeignKey("sequence_definitions.id", ondelete="CASCADE"), nullable=False
    )
    step_number: Mapped[int] = mapped_column(Integer, nullable=False)
    delay_days: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    channel: Mapped[str] = mapped_column(String(50), nullable=False, default="email")
    step_type: Mapped[str] = mapped_column(
        Enum("first_touch", "follow_up", name="sequence_step_type"),
        nullable=False,
        default="first_touch",
    )
    template_subject: Mapped[str | None] = mapped_column(String(255))
    template_body: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class SequenceEnrollmentModel(Base):
    __tablename__ = "sequence_enrollments"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    workspace_id: Mapped[UUID] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False
    )
    campaign_id: Mapped[UUID] = mapped_column(
        ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False
    )
    sequence_id: Mapped[UUID] = mapped_column(
        ForeignKey("sequence_definitions.id", ondelete="CASCADE"), nullable=False
    )
    contact_id: Mapped[UUID] = mapped_column(
        ForeignKey("contacts.id", ondelete="CASCADE"), nullable=False
    )
    current_step_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    status: Mapped[str] = mapped_column(
        Enum(
            "pending_approval",
            "active",
            "paused",
            "stopped",
            "completed",
            "failed",
            name="sequence_status",
        ),
        nullable=False,
        default="pending_approval",
    )
    stop_reason: Mapped[str | None] = mapped_column(String(255))
    next_step_due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    enrolled_by: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True))
    enrolled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class JobModel(Base):
    __tablename__ = "jobs"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    workspace_id: Mapped[UUID] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False
    )
    job_type: Mapped[str] = mapped_column(String(100), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default={})
    status: Mapped[str] = mapped_column(
        Enum("pending", "running", "failed", "completed", name="job_status"),
        nullable=False,
        default="pending",
    )
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    max_attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    available_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    locked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_error: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class OutreachDraftModel(Base):
    __tablename__ = "outreach_drafts"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    workspace_id: Mapped[UUID] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False
    )
    campaign_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("campaigns.id", ondelete="SET NULL")
    )
    contact_id: Mapped[UUID] = mapped_column(
        ForeignKey("contacts.id", ondelete="CASCADE"), nullable=False
    )
    sequence_enrollment_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("sequence_enrollments.id", ondelete="SET NULL")
    )
    sequence_step_number: Mapped[int | None] = mapped_column(Integer)
    research_brief_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True))
    current_version_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("draft_versions.id", ondelete="SET NULL")
    )
    current_version_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    current_subject: Mapped[str | None] = mapped_column(String(255))
    current_body: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(
        Enum(
            "draft",
            "ready_for_review",
            "approved",
            "rejected",
            "superseded",
            "archived",
            name="draft_status",
        ),
        nullable=False,
        default="draft",
    )
    created_by: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class DraftVersionModel(Base):
    __tablename__ = "draft_versions"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    workspace_id: Mapped[UUID] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False
    )
    draft_id: Mapped[UUID] = mapped_column(
        ForeignKey("outreach_drafts.id", ondelete="CASCADE"), nullable=False
    )
    version_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    subject: Mapped[str | None] = mapped_column(String(255))
    body: Mapped[str] = mapped_column(Text, nullable=False)
    generation_source: Mapped[str] = mapped_column(
        Enum("human", "ai_generated", "template", "ai_assisted", name="draft_generation_source"),
        nullable=False,
        default="human",
    )
    provider: Mapped[str | None] = mapped_column(String(100))
    model: Mapped[str | None] = mapped_column(String(100))
    prompt_version: Mapped[str | None] = mapped_column(String(50))
    research_brief_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True))
    research_brief_version: Mapped[int | None] = mapped_column(Integer)
    evidence_references: Mapped[list[dict[str, Any]] | None] = mapped_column(JSONB)
    created_by: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class DeliveryModel(Base):
    __tablename__ = "deliveries"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    workspace_id: Mapped[UUID] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False
    )
    draft_id: Mapped[UUID] = mapped_column(
        ForeignKey("outreach_drafts.id", ondelete="CASCADE"), nullable=False
    )
    version_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("draft_versions.id", ondelete="SET NULL")
    )
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    contact_id: Mapped[UUID] = mapped_column(
        ForeignKey("contacts.id", ondelete="CASCADE"), nullable=False
    )
    recipient_email: Mapped[str] = mapped_column(String(255), nullable=False)
    subject: Mapped[str | None] = mapped_column(String(255))
    body: Mapped[str | None] = mapped_column(Text)
    provider: Mapped[str] = mapped_column(String(100), nullable=False, default="resend")
    provider_message_id: Mapped[str | None] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(
        Enum(
            "queued",
            "running",
            "sent",
            "delivered",
            "failed",
            "bounced",
            "complained",
            name="delivery_status",
        ),
        nullable=False,
        default="queued",
    )
    idempotency_key: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    error_message: Mapped[str | None] = mapped_column(Text)
    created_by: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class ConversationModel(Base):
    __tablename__ = "conversations"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    workspace_id: Mapped[UUID] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False
    )
    contact_id: Mapped[UUID] = mapped_column(
        ForeignKey("contacts.id", ondelete="CASCADE"), nullable=False
    )
    campaign_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("campaigns.id", ondelete="SET NULL")
    )
    delivery_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("deliveries.id", ondelete="SET NULL")
    )
    status: Mapped[str] = mapped_column(
        Enum("active", "needs_human_action", "closed", "opt_out", name="conversation_status"),
        nullable=False,
        default="active",
    )
    current_reply_state: Mapped[str | None] = mapped_column(
        Enum(
            "interested",
            "not_now",
            "referral",
            "unsubscribe",
            "out_of_office",
            "ambiguous",
            "positive",
            "objection",
            "question",
            "not_applicable",
            name="reply_state",
        )
    )
    last_message_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class ConversationMessageModel(Base):
    __tablename__ = "conversation_messages"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    workspace_id: Mapped[UUID] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False
    )
    conversation_id: Mapped[UUID] = mapped_column(
        ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False
    )
    direction: Mapped[str] = mapped_column(
        Enum("inbound", "outbound", name="conversation_direction"),
        nullable=False,
        default="inbound",
    )
    sender_email: Mapped[str] = mapped_column(String(255), nullable=False)
    recipient_email: Mapped[str] = mapped_column(String(255), nullable=False)
    subject: Mapped[str | None] = mapped_column(Text)
    body: Mapped[str | None] = mapped_column(Text)
    provider_message_id: Mapped[str | None] = mapped_column(String(255))
    delivery_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("deliveries.id", ondelete="SET NULL")
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        Index(
            "uq_conversation_msg_provider",
            "workspace_id",
            "provider_message_id",
            unique=True,
            postgresql_where=text("provider_message_id IS NOT NULL"),
        ),
    )


class ReplyClassificationModel(Base):
    __tablename__ = "reply_classifications"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    workspace_id: Mapped[UUID] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False
    )
    conversation_id: Mapped[UUID] = mapped_column(
        ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False
    )
    message_id: Mapped[UUID] = mapped_column(
        ForeignKey("conversation_messages.id", ondelete="CASCADE"), nullable=False
    )
    reply_state: Mapped[str] = mapped_column(
        Enum(
            "interested",
            "not_now",
            "referral",
            "unsubscribe",
            "out_of_office",
            "ambiguous",
            "positive",
            "objection",
            "question",
            "not_applicable",
            name="reply_state",
        ),
        nullable=False,
    )
    confidence_score: Mapped[float | None] = mapped_column(nullable=True, default=1.0)
    explanation: Mapped[str | None] = mapped_column(Text)
    needs_human_action: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    classified_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class ResearchBriefModel(Base):
    __tablename__ = "research_briefs"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    workspace_id: Mapped[UUID] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False
    )
    account_id: Mapped[UUID] = mapped_column(
        ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False
    )
    contact_id: Mapped[UUID | None] = mapped_column(ForeignKey("contacts.id", ondelete="CASCADE"))
    summary: Mapped[str | None] = mapped_column(Text)
    key_findings: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    status: Mapped[str] = mapped_column(
        Enum("pending", "in_progress", "completed", "failed", name="research_status"),
        nullable=False,
        default="pending",
    )
    confidence_score: Mapped[float | None] = mapped_column(nullable=True)
    confidence_reason: Mapped[str | None] = mapped_column(Text)
    provider: Mapped[str | None] = mapped_column(String(100))
    model: Mapped[str | None] = mapped_column(String(100))
    prompt_version: Mapped[str | None] = mapped_column(String(50))
    generated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    token_usage: Mapped[int | None] = mapped_column(Integer)
    estimated_cost: Mapped[float | None] = mapped_column(nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer)
    created_by: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class ResearchSourceModel(Base):
    __tablename__ = "research_sources"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    workspace_id: Mapped[UUID] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False
    )
    brief_id: Mapped[UUID] = mapped_column(
        ForeignKey("research_briefs.id", ondelete="CASCADE"), nullable=False
    )
    url: Mapped[str | None] = mapped_column(String(500))
    title: Mapped[str | None] = mapped_column(String(255))
    source_type: Mapped[str] = mapped_column(String(50), nullable=False, default="website")
    snippet: Mapped[str | None] = mapped_column(Text)
    confidence: Mapped[float | None] = mapped_column(nullable=True, default=1.0)
    raw_content_hash: Mapped[str | None] = mapped_column(String(128))
    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class ApprovalDecisionModel(Base):
    __tablename__ = "approval_decisions"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    workspace_id: Mapped[UUID] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False
    )
    draft_id: Mapped[UUID] = mapped_column(
        ForeignKey("outreach_drafts.id", ondelete="CASCADE"), nullable=False
    )
    version_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("draft_versions.id", ondelete="SET NULL")
    )
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    reviewer_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True))
    decision: Mapped[str] = mapped_column(
        Enum("approved", "rejected", "returned_to_draft", name="approval_decision_type"),
        nullable=False,
    )
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class AuditEventModel(Base):
    __tablename__ = "audit_events"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    workspace_id: Mapped[UUID] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False
    )
    actor_type: Mapped[str] = mapped_column(String(50), nullable=False)
    actor_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True))
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    resource_type: Mapped[str] = mapped_column(String(100), nullable=False)
    resource_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True))
    metadata_payload: Mapped[dict[str, Any]] = mapped_column(
        "metadata", JSONB, nullable=False, default={}
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
