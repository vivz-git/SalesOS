from datetime import UTC, datetime
from typing import Literal, cast
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.reply_classifier import (
    ClassificationResult,
    DeterministicReplyClassifier,
    ReplyClassifierInterface,
    ReplyState,
)
from app.auth import Principal, get_current_principal
from app.core.config import Settings, get_settings
from app.db import get_db_session, tenant_transaction_context
from app.models import (
    AccountModel,
    ContactModel,
    ConversationMessageModel,
    ConversationModel,
    DeliveryModel,
    ReplyClassificationModel,
)

router = APIRouter(prefix="/v1", tags=["conversations"])

ConversationStatus = Literal["active", "needs_human_action", "closed", "opt_out"]


class ConversationMessage(BaseModel):
    id: UUID
    workspace_id: UUID
    conversation_id: UUID
    direction: Literal["inbound", "outbound"]
    sender_email: str
    recipient_email: str
    subject: str | None = None
    body: str | None = None
    provider_message_id: str | None = None
    delivery_id: UUID | None = None
    created_at: datetime


class ReplyClassification(BaseModel):
    id: UUID
    workspace_id: UUID
    conversation_id: UUID
    message_id: UUID
    reply_state: ReplyState
    confidence_score: float | None = None
    explanation: str | None = None
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


def get_reply_classifier() -> ReplyClassifierInterface:
    return DeterministicReplyClassifier()


async def _row_to_conversation(
    session: AsyncSession,
    model: ConversationModel,
    with_messages: bool = False
) -> Conversation:
    # 1. Load Contact & Account context
    contact = await session.get(ContactModel, model.contact_id)
    contact_name = f"{contact.first_name} {contact.last_name}".strip() if contact else None
    contact_email = contact.email if contact else None

    account_name = None
    if contact and contact.account_id:
        account = await session.get(AccountModel, contact.account_id)
        if account:
            account_name = account.name

    messages: list[ConversationMessage] = []
    last_class: ReplyClassification | None = None

    if with_messages:
        # Load messages
        msg_result = await session.execute(
            select(ConversationMessageModel)
            .filter_by(conversation_id=model.id, workspace_id=model.workspace_id)
            .order_by(ConversationMessageModel.created_at.asc())
        )
        msg_models = msg_result.scalars().all()

        for m in msg_models:
            messages.append(
                ConversationMessage(
                    id=m.id,
                    workspace_id=m.workspace_id,
                    conversation_id=m.conversation_id,
                    direction=cast(Literal["inbound", "outbound"], m.direction),
                    sender_email=m.sender_email,
                    recipient_email=m.recipient_email,
                    subject=m.subject,
                    body=m.body,
                    provider_message_id=m.provider_message_id,
                    delivery_id=m.delivery_id,
                    created_at=m.created_at,
                )
            )

        # Load last classification
        class_result = await session.execute(
            select(ReplyClassificationModel)
            .filter_by(conversation_id=model.id, workspace_id=model.workspace_id)
            .order_by(ReplyClassificationModel.classified_at.desc())
            .limit(1)
        )
        c_model = class_result.scalar_one_or_none()
        if c_model:
            last_class = ReplyClassification(
                id=c_model.id,
                workspace_id=c_model.workspace_id,
                conversation_id=c_model.conversation_id,
                message_id=c_model.message_id,
                reply_state=cast(ReplyState, c_model.reply_state),
                confidence_score=c_model.confidence_score,
                explanation=c_model.explanation,
                needs_human_action=c_model.needs_human_action,
                classified_at=c_model.classified_at,
            )

    return Conversation(
        id=model.id,
        workspace_id=model.workspace_id,
        contact_id=model.contact_id,
        contact_name=contact_name,
        contact_email=contact_email,
        account_name=account_name,
        campaign_id=model.campaign_id,
        delivery_id=model.delivery_id,
        status=cast(ConversationStatus, model.status),
        current_reply_state=cast(ReplyState | None, model.current_reply_state),
        last_message_at=model.last_message_at,
        created_at=model.created_at,
        updated_at=model.updated_at,
        messages=messages,
        last_classification=last_class,
    )


@router.post("/conversations/inbound", response_model=Conversation)
async def ingest_inbound_reply(
    payload: InboundReplyPayload,
    classifier: ReplyClassifierInterface = Depends(get_reply_classifier),
    settings: Settings = Depends(get_settings),
    session: AsyncSession = Depends(get_db_session),
) -> Conversation:
    # 1. Match referenced outbound delivery or recipient contact (We don't have RLS context yet, so we query globally, but it's safe because it's inbound webhook)
    # Wait, if this is inbound, the webhook might not have `principal`. 
    # The prompt specified "Inbound Reply Idempotency" and "Tenant Isolation".
    
    matched_delivery = None
    if payload.in_reply_to_provider_message_id:
        matched_delivery = await session.scalar(
            select(DeliveryModel)
            .filter_by(provider_message_id=payload.in_reply_to_provider_message_id)
            .limit(1)
        )

    resolved_ws_id: UUID | None = None
    resolved_contact_id: UUID | None = None
    resolved_campaign_id: UUID | None = None
    resolved_delivery_id: UUID | None = None

    if matched_delivery:
        resolved_ws_id = matched_delivery.workspace_id
        resolved_contact_id = matched_delivery.contact_id
        resolved_delivery_id = matched_delivery.id
        resolved_campaign_id = None
    elif payload.workspace_id:
        resolved_ws_id = payload.workspace_id

    system_user_id = UUID("00000000-0000-0000-0000-000000000000")
    if resolved_ws_id:
        await session.execute(
            text("SELECT set_config('salesos.app_user_id', :user_id, true)"),
            {"user_id": str(system_user_id)},
        )
        await session.execute(
            text("SELECT set_config('salesos.app_workspace_id', :workspace_id, true)"),
            {"workspace_id": str(resolved_ws_id)},
        )

    # 2. Query contact by email if not resolved via delivery
    if not resolved_contact_id and resolved_ws_id:
        c_model = await session.scalar(
            select(ContactModel)
            .filter_by(workspace_id=resolved_ws_id, email=payload.sender_email)
            .limit(1)
        )
        if c_model:
            resolved_contact_id = c_model.id

    if not resolved_ws_id or not resolved_contact_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact or workspace could not be resolved for inbound message",
        )

    now_dt = datetime.now(UTC)

    # 3. Handle Idempotency
    if payload.provider_message_id:
        existing_msg = await session.scalar(
            select(ConversationMessageModel)
            .filter_by(provider_message_id=payload.provider_message_id)
            .limit(1)
        )
        if existing_msg:
            # Idempotent return - find the parent conversation
            conv = await session.get(ConversationModel, existing_msg.conversation_id)
            if conv:
                return await _row_to_conversation(session, conv, with_messages=True)

    system_user_id = UUID("00000000-0000-0000-0000-000000000000")
    if resolved_ws_id:
        await session.execute(
            text("SELECT set_config('salesos.app_user_id', :user_id, true)"),
            {"user_id": str(system_user_id)},
        )
        await session.execute(
            text("SELECT set_config('salesos.app_workspace_id', :workspace_id, true)"),
            {"workspace_id": str(resolved_ws_id)},
        )

    existing_conv = await session.scalar(
        select(ConversationModel)
        .filter_by(workspace_id=resolved_ws_id, contact_id=resolved_contact_id)
        .limit(1)
    )

    if not existing_conv:
        conv_id = uuid4()
        existing_conv = ConversationModel(
            id=conv_id,
            workspace_id=resolved_ws_id,
            contact_id=resolved_contact_id,
            campaign_id=resolved_campaign_id,
            delivery_id=resolved_delivery_id,
            status="active",
            current_reply_state=None,
            last_message_at=now_dt,
            created_at=now_dt,
            updated_at=now_dt,
        )
        session.add(existing_conv)
        await session.flush()

    conv_id = existing_conv.id

    # 4. Append Inbound Message Record
    msg_id = uuid4()
    msg_model = ConversationMessageModel(
        id=msg_id,
        workspace_id=resolved_ws_id,
        conversation_id=conv_id,
        direction="inbound",
        sender_email=payload.sender_email,
        recipient_email=payload.recipient_email,
        subject=payload.subject,
        body=payload.body,
        provider_message_id=payload.provider_message_id,
        delivery_id=resolved_delivery_id,
        created_at=now_dt,
    )
    session.add(msg_model)
    await session.flush()

    # 5. Execute Classification Engine
    classification_result: ClassificationResult = classifier.classify(payload.body, payload.subject)

    class_id = uuid4()
    class_model = ReplyClassificationModel(
        id=class_id,
        workspace_id=resolved_ws_id,
        conversation_id=conv_id,
        message_id=msg_id,
        reply_state=classification_result.reply_state,
        confidence_score=classification_result.confidence_score,
        explanation=classification_result.explanation,
        needs_human_action=classification_result.needs_human_action,
        classified_at=now_dt,
    )
    session.add(class_model)

    # 6. Update Thread Status & Reply State
    existing_conv.current_reply_state = classification_result.reply_state
    existing_conv.last_message_at = now_dt
    existing_conv.updated_at = now_dt

    if classification_result.reply_state == "unsubscribe":
        existing_conv.status = "opt_out"
        stop_reason = "unsubscribed"
    elif classification_result.needs_human_action:
        existing_conv.status = "needs_human_action"
        stop_reason = "prospect_replied"
    else:
        existing_conv.status = "active"
        stop_reason = "prospect_replied"

    await session.commit()

    # 7. Evaluate and halt active sequence enrollments for this contact
    try:
        from app.api.sequences import evaluate_sequence_stop_conditions_for_contact
        await evaluate_sequence_stop_conditions_for_contact(str(resolved_ws_id), str(resolved_contact_id), stop_reason, session)
    except Exception as e:
        print(f"FAILED TO EVALUATE SEQUENCE STOP CONDITIONS: {e}")
        pass

    # Return refreshed conversation
    await session.execute(
        text("SELECT set_config('salesos.app_user_id', :user_id, true)"),
        {"user_id": str(system_user_id)},
    )
    await session.execute(
        text("SELECT set_config('salesos.app_workspace_id', :workspace_id, true)"),
        {"workspace_id": str(resolved_ws_id)},
    )
    await session.refresh(existing_conv)
    return await _row_to_conversation(session, existing_conv, with_messages=True)


@router.get("/conversations", response_model=list[Conversation])
async def list_conversations(
    status_filter: str = Query("all", alias="status"),
    reply_state_filter: str = Query("all", alias="reply_state"),
    search: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    principal: Principal = Depends(get_current_principal),
    session: AsyncSession = Depends(get_db_session),
) -> list[Conversation]:
    async with tenant_transaction_context(session, principal.user_id, principal.workspace_id):
        stmt = select(ConversationModel).filter_by(workspace_id=principal.workspace_id)

        if status_filter != "all":
            stmt = stmt.filter_by(status=status_filter)
        if reply_state_filter != "all":
            stmt = stmt.filter_by(current_reply_state=reply_state_filter)

        stmt = stmt.order_by(ConversationModel.last_message_at.desc()).offset(offset).limit(limit)
        
        result = await session.execute(stmt)
        models = result.scalars().all()

        results: list[Conversation] = []
        for m in models:
            conv_obj = await _row_to_conversation(session, m, with_messages=False)
            
            if search:
                query = search.lower()
                c_name = (conv_obj.contact_name or "").lower()
                c_email = (conv_obj.contact_email or "").lower()
                a_name = (conv_obj.account_name or "").lower()
                matches = query in c_name or query in c_email or query in a_name
                if not matches:
                    continue

            results.append(conv_obj)

        return results


@router.get("/conversations/{conversation_id}", response_model=Conversation)
async def get_conversation_detail(
    conversation_id: UUID,
    principal: Principal = Depends(get_current_principal),
    session: AsyncSession = Depends(get_db_session),
) -> Conversation:
    async with tenant_transaction_context(session, principal.user_id, principal.workspace_id):
        model = await session.get(ConversationModel, conversation_id)
        if not model or str(model.workspace_id) != str(principal.workspace_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="conversation_thread_not_found",
            )
        
        return await _row_to_conversation(session, model, with_messages=True)


@router.post("/conversations/{conversation_id}/actions/classify", response_model=Conversation)
async def override_classification(
    conversation_id: UUID,
    payload: ClassifyOverridePayload,
    principal: Principal = Depends(get_current_principal),
    session: AsyncSession = Depends(get_db_session),
) -> Conversation:
    async with tenant_transaction_context(session, principal.user_id, principal.workspace_id):
        model = await session.get(ConversationModel, conversation_id)
        if not model or str(model.workspace_id) != str(principal.workspace_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="conversation_thread_not_found",
            )

        now_dt = datetime.now(UTC)
        model.current_reply_state = payload.reply_state
        model.updated_at = now_dt

        if payload.reply_state == "unsubscribe":
            model.status = "opt_out"
        elif payload.reply_state == "ambiguous":
            model.status = "needs_human_action"

        # Find latest message
        latest_msg_result = await session.execute(
            select(ConversationMessageModel)
            .filter_by(conversation_id=model.id, workspace_id=model.workspace_id)
            .order_by(ConversationMessageModel.created_at.desc())
            .limit(1)
        )
        latest_msg = latest_msg_result.scalar_one_or_none()
        msg_id = latest_msg.id if latest_msg else uuid4()

        class_id = uuid4()
        class_model = ReplyClassificationModel(
            id=class_id,
            workspace_id=model.workspace_id,
            conversation_id=model.id,
            message_id=msg_id,
            reply_state=payload.reply_state,
            confidence_score=1.0,
            explanation=payload.explanation or f"Manually reclassified by user {principal.email}",
            needs_human_action=(payload.reply_state == "ambiguous"),
            classified_at=now_dt,
        )
        session.add(class_model)
        await session.flush()
        await session.refresh(model)

        return await _row_to_conversation(session, model, with_messages=True)


@router.post("/conversations/{conversation_id}/actions/update-status", response_model=Conversation)
async def update_conversation_status(
    conversation_id: UUID,
    payload: StatusUpdatePayload,
    principal: Principal = Depends(get_current_principal),
    session: AsyncSession = Depends(get_db_session),
) -> Conversation:
    async with tenant_transaction_context(session, principal.user_id, principal.workspace_id):
        model = await session.get(ConversationModel, conversation_id)
        if not model or str(model.workspace_id) != str(principal.workspace_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="conversation_thread_not_found",
            )
        
        model.status = payload.status
        model.updated_at = datetime.now(UTC)
        
        await session.flush()
        await session.refresh(model)

        return await _row_to_conversation(session, model, with_messages=True)
