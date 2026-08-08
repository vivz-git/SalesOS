from datetime import UTC, datetime
from typing import Any, Literal, cast
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.adapters.reply_classifier import (
    ClassificationResult,
    DeterministicReplyClassifier,
    ReplyClassifierInterface,
    ReplyState,
)
from app.api.deliveries import _DELIVERIES_STORE
from app.auth import Principal, _clients, get_current_principal
from app.core.config import Settings, get_settings

router = APIRouter(prefix="/v1", tags=["conversations"])

ConversationStatus = Literal["active", "needs_human_action", "closed", "opt_out"]


class ConversationMessage(BaseModel):
    id: UUID
    workspace_id: UUID
    conversation_id: UUID
    direction: Literal["inbound", "outbound"]
    sender_email: str
    recipient_email: str
    subject: str
    body: str
    provider_message_id: str | None = None
    delivery_id: UUID | None = None
    created_at: datetime


class ReplyClassification(BaseModel):
    id: UUID
    conversation_id: UUID
    message_id: UUID
    reply_state: ReplyState
    confidence_score: float
    explanation: str
    needs_human_action: bool
    classified_at: datetime


class Conversation(BaseModel):
    id: UUID
    workspace_id: UUID
    contact_id: UUID
    contact_name: str | None = None
    contact_email: str | None = None
    account_name: str | None = None
    campaign_id: UUID | None = None
    delivery_id: UUID | None = None
    status: ConversationStatus = "active"
    current_reply_state: ReplyState | None = None
    last_message_at: datetime
    created_at: datetime
    updated_at: datetime
    messages: list[ConversationMessage] = Field(default_factory=list)
    last_classification: ReplyClassification | None = None


class InboundReplyPayload(BaseModel):
    workspace_id: UUID | None = None
    sender_email: str
    recipient_email: str
    subject: str
    body: str
    provider_message_id: str | None = Field(default=None, max_length=255)
    in_reply_to_provider_message_id: str | None = Field(default=None, max_length=255)


class ClassifyOverridePayload(BaseModel):
    reply_state: ReplyState
    explanation: str | None = None


class StatusUpdatePayload(BaseModel):
    status: ConversationStatus


_CONVERSATIONS_STORE: list[dict[str, Any]] = []
_CONVERSATION_MESSAGES_STORE: list[dict[str, Any]] = []
_CLASSIFICATIONS_STORE: list[dict[str, Any]] = []


def get_reply_classifier() -> ReplyClassifierInterface:
    return DeterministicReplyClassifier()


def _row_to_conversation(conv_dict: dict[str, Any]) -> Conversation:
    conv_id = UUID(str(conv_dict["id"]))
    ws_id = UUID(str(conv_dict["workspace_id"]))

    messages: list[ConversationMessage] = []
    for msg in _CONVERSATION_MESSAGES_STORE:
        if str(msg.get("conversation_id")) == str(conv_id):
            messages.append(
                ConversationMessage(
                    id=UUID(str(msg["id"])),
                    workspace_id=ws_id,
                    conversation_id=conv_id,
                    direction=cast(Literal["inbound", "outbound"], msg.get("direction", "inbound")),
                    sender_email=str(msg.get("sender_email", "")),
                    recipient_email=str(msg.get("recipient_email", "")),
                    subject=str(msg.get("subject", "")),
                    body=str(msg.get("body", "")),
                    provider_message_id=cast(str | None, msg.get("provider_message_id")),
                    delivery_id=UUID(str(msg["delivery_id"])) if msg.get("delivery_id") else None,
                    created_at=datetime.fromisoformat(str(msg["created_at"])),
                )
            )
    messages.sort(key=lambda m: m.created_at)

    last_class: ReplyClassification | None = None
    class_rows = [c for c in _CLASSIFICATIONS_STORE if str(c.get("conversation_id")) == str(conv_id)]
    if class_rows:
        class_rows.sort(key=lambda c: str(c.get("classified_at", "")), reverse=True)
        c_raw = class_rows[0]
        last_class = ReplyClassification(
            id=UUID(str(c_raw["id"])),
            conversation_id=conv_id,
            message_id=UUID(str(c_raw["message_id"])),
            reply_state=cast(ReplyState, c_raw["reply_state"]),
            confidence_score=float(c_raw.get("confidence_score", 1.0)),
            explanation=str(c_raw.get("explanation", "")),
            needs_human_action=bool(c_raw.get("needs_human_action", False)),
            classified_at=datetime.fromisoformat(str(c_raw["classified_at"])),
        )

    return Conversation(
        id=conv_id,
        workspace_id=ws_id,
        contact_id=UUID(str(conv_dict["contact_id"])),
        contact_name=cast(str | None, conv_dict.get("contact_name")),
        contact_email=cast(str | None, conv_dict.get("contact_email")),
        account_name=cast(str | None, conv_dict.get("account_name")),
        campaign_id=UUID(str(conv_dict["campaign_id"])) if conv_dict.get("campaign_id") else None,
        delivery_id=UUID(str(conv_dict["delivery_id"])) if conv_dict.get("delivery_id") else None,
        status=cast(ConversationStatus, conv_dict.get("status", "active")),
        current_reply_state=cast(ReplyState | None, conv_dict.get("current_reply_state")),
        last_message_at=datetime.fromisoformat(str(conv_dict["last_message_at"])),
        created_at=datetime.fromisoformat(str(conv_dict["created_at"])),
        updated_at=datetime.fromisoformat(str(conv_dict["updated_at"])),
        messages=messages,
        last_classification=last_class,
    )


@router.post("/conversations/inbound", response_model=Conversation)
def ingest_inbound_reply(
    payload: InboundReplyPayload,
    classifier: ReplyClassifierInterface = Depends(get_reply_classifier),
    settings: Settings = Depends(get_settings),
) -> Conversation:
    # 1. Match referenced outbound delivery or recipient contact
    matched_delivery: dict[str, Any] | None = None
    if payload.in_reply_to_provider_message_id:
        for del_row in _DELIVERIES_STORE:
            if del_row.get("provider_message_id") == payload.in_reply_to_provider_message_id:
                matched_delivery = del_row
                break

    resolved_ws_id: str | None = None
    resolved_contact_id: str | None = None
    resolved_campaign_id: str | None = None
    resolved_delivery_id: str | None = None

    if matched_delivery:
        resolved_ws_id = str(matched_delivery["workspace_id"])
        resolved_contact_id = str(matched_delivery["contact_id"])
        resolved_delivery_id = str(matched_delivery["id"])
    elif payload.workspace_id:
        resolved_ws_id = str(payload.workspace_id)

    # 2. Query contact by email if not resolved via delivery
    if not resolved_contact_id and resolved_ws_id:
        if settings.supabase_url and settings.supabase_publishable_key and settings.supabase_service_role_key:
            try:
                _, admin_client = _clients(settings)
                contacts = (
                    admin_client.table("contacts")
                    .select("*")
                    .eq("workspace_id", resolved_ws_id)
                    .eq("email", payload.sender_email)
                    .execute()
                    .data
                )
                if contacts and isinstance(contacts, list) and len(contacts) > 0:
                    first_c = cast(dict[str, Any], contacts[0])
                    resolved_contact_id = str(first_c.get("id", ""))
            except Exception:
                pass

    if not resolved_ws_id:
        resolved_ws_id = str(uuid4())
    if not resolved_contact_id:
        resolved_contact_id = str(uuid4())

    now_iso = datetime.now(UTC).isoformat()

    # 3. Find or create conversation for this prospect
    existing_conv: dict[str, Any] | None = None
    for c in _CONVERSATIONS_STORE:
        if c.get("workspace_id") == resolved_ws_id and c.get("contact_id") == resolved_contact_id:
            existing_conv = c
            break

    if not existing_conv:
        conv_id = str(uuid4())
        existing_conv = {
            "id": conv_id,
            "workspace_id": resolved_ws_id,
            "contact_id": resolved_contact_id,
            "contact_email": payload.sender_email,
            "contact_name": payload.sender_email.split("@")[0].replace(".", " ").title(),
            "account_name": "Target Account",
            "campaign_id": resolved_campaign_id,
            "delivery_id": resolved_delivery_id,
            "status": "active",
            "current_reply_state": None,
            "last_message_at": now_iso,
            "created_at": now_iso,
            "updated_at": now_iso,
        }
        _CONVERSATIONS_STORE.append(existing_conv)

    conv_id = str(existing_conv["id"])

    # 4. Append Inbound Message Record
    msg_id = str(uuid4())
    msg_dict: dict[str, Any] = {
        "id": msg_id,
        "workspace_id": resolved_ws_id,
        "conversation_id": conv_id,
        "direction": "inbound",
        "sender_email": payload.sender_email,
        "recipient_email": payload.recipient_email,
        "subject": payload.subject,
        "body": payload.body,
        "provider_message_id": payload.provider_message_id,
        "delivery_id": resolved_delivery_id,
        "created_at": now_iso,
    }
    _CONVERSATION_MESSAGES_STORE.append(msg_dict)

    # 5. Execute Classification Engine
    classification_result: ClassificationResult = classifier.classify(payload.body, payload.subject)

    class_id = str(uuid4())
    class_dict: dict[str, Any] = {
        "id": class_id,
        "conversation_id": conv_id,
        "message_id": msg_id,
        "reply_state": classification_result.reply_state,
        "confidence_score": classification_result.confidence_score,
        "explanation": classification_result.explanation,
        "needs_human_action": classification_result.needs_human_action,
        "classified_at": now_iso,
    }
    _CLASSIFICATIONS_STORE.append(class_dict)

    # 6. Update Thread Status & Reply State
    existing_conv["current_reply_state"] = classification_result.reply_state
    existing_conv["last_message_at"] = now_iso
    existing_conv["updated_at"] = now_iso

    if classification_result.reply_state == "unsubscribe":
        existing_conv["status"] = "opt_out"
    elif classification_result.needs_human_action:
        existing_conv["status"] = "needs_human_action"
    else:
        existing_conv["status"] = "active"

    return _row_to_conversation(existing_conv)


@router.get("/conversations", response_model=list[Conversation])
def list_conversations(
    status_filter: str = Query("all", alias="status"),
    reply_state_filter: str = Query("all", alias="reply_state"),
    search: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    principal: Principal = Depends(get_current_principal),
) -> list[Conversation]:
    results: list[Conversation] = []
    for row in _CONVERSATIONS_STORE:
        if str(row.get("workspace_id")) == str(principal.workspace_id):
            if status_filter != "all" and row.get("status") != status_filter:
                continue
            if reply_state_filter != "all" and row.get("current_reply_state") != reply_state_filter:
                continue

            conv_obj = _row_to_conversation(row)
            if search:
                query = search.lower()
                c_name = (conv_obj.contact_name or "").lower()
                c_email = (conv_obj.contact_email or "").lower()
                a_name = (conv_obj.account_name or "").lower()
                matches = query in c_name or query in c_email or query in a_name
                if not matches:
                    continue

            results.append(conv_obj)

    results.sort(key=lambda c: c.last_message_at, reverse=True)
    return results[offset : offset + limit]


@router.get("/conversations/{conversation_id}", response_model=Conversation)
def get_conversation_detail(
    conversation_id: UUID,
    principal: Principal = Depends(get_current_principal),
) -> Conversation:
    for row in _CONVERSATIONS_STORE:
        if str(row.get("id")) == str(conversation_id) and str(row.get("workspace_id")) == str(principal.workspace_id):
            return _row_to_conversation(row)

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="conversation_thread_not_found",
    )


@router.post("/conversations/{conversation_id}/actions/classify", response_model=Conversation)
def override_classification(
    conversation_id: UUID,
    payload: ClassifyOverridePayload,
    principal: Principal = Depends(get_current_principal),
) -> Conversation:
    for row in _CONVERSATIONS_STORE:
        if str(row.get("id")) == str(conversation_id) and str(row.get("workspace_id")) == str(principal.workspace_id):
            now_iso = datetime.now(UTC).isoformat()
            row["current_reply_state"] = payload.reply_state
            row["updated_at"] = now_iso

            if payload.reply_state == "unsubscribe":
                row["status"] = "opt_out"
            elif payload.reply_state == "ambiguous":
                row["status"] = "needs_human_action"

            # Create manual override classification record
            class_id = str(uuid4())
            msg_id = str(uuid4())
            if row.get("messages"):
                msg_id = str(row["messages"][-1].id)

            _CLASSIFICATIONS_STORE.append({
                "id": class_id,
                "conversation_id": str(conversation_id),
                "message_id": msg_id,
                "reply_state": payload.reply_state,
                "confidence_score": 1.0,
                "explanation": payload.explanation or f"Manually reclassified by user {principal.email}",
                "needs_human_action": payload.reply_state == "ambiguous",
                "classified_at": now_iso,
            })

            return _row_to_conversation(row)

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="conversation_thread_not_found",
    )


@router.post("/conversations/{conversation_id}/actions/update-status", response_model=Conversation)
def update_conversation_status(
    conversation_id: UUID,
    payload: StatusUpdatePayload,
    principal: Principal = Depends(get_current_principal),
) -> Conversation:
    for row in _CONVERSATIONS_STORE:
        if str(row.get("id")) == str(conversation_id) and str(row.get("workspace_id")) == str(principal.workspace_id):
            row["status"] = payload.status
            row["updated_at"] = datetime.now(UTC).isoformat()
            return _row_to_conversation(row)

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="conversation_thread_not_found",
    )
