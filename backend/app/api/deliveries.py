from datetime import UTC, datetime, timedelta
from typing import Any, Literal, cast
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, status
from pydantic import BaseModel, Field
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.email_provider import (
    DeliveryStatus,
    EmailDeliverySendRequest,
    EmailProviderInterface,
)
from app.adapters.resend_provider import ResendEmailProvider
from app.api.outreach import get_outreach_draft
from app.auth import Principal, _clients, get_current_principal
from app.core.config import Settings, get_settings
from app.db import get_db_session
from app.models import DeliveryModel, JobModel, SequenceEnrollmentModel, SequenceStepModel

router = APIRouter(prefix="/v1", tags=["deliveries"])


class DeliveryCreatePayload(BaseModel):
    draft_id: UUID
    override_recipient_email: str | None = Field(default=None, max_length=255)


class EmailDelivery(BaseModel):
    id: UUID
    workspace_id: UUID
    draft_id: UUID
    version_id: UUID
    version_number: int
    contact_id: UUID
    recipient_email: str
    subject: str
    body: str
    provider: str = "resend"
    provider_message_id: str | None = None
    status: DeliveryStatus = "queued"
    idempotency_key: str
    created_by: UUID
    created_at: datetime
    updated_at: datetime
    error_message: str | None = None


class DeliveryJob(BaseModel):
    id: UUID
    workspace_id: UUID
    delivery_id: UUID
    status: Literal["queued", "running", "sent", "failed", "cancelled"] = "queued"
    created_at: datetime
    completed_at: datetime | None = None
    error_message: str | None = None
    delivery: EmailDelivery | None = None


def get_email_provider(settings: Settings = Depends(get_settings)) -> EmailProviderInterface:
    return ResendEmailProvider(api_key=settings.resend_api_key)


def _model_to_delivery(model: DeliveryModel) -> EmailDelivery:
    return EmailDelivery(
        id=model.id,
        workspace_id=model.workspace_id,
        draft_id=model.draft_id,
        version_id=model.version_id or uuid4(),  # Type hint safety fallback
        version_number=model.version_number,
        contact_id=model.contact_id,
        recipient_email=model.recipient_email,
        subject=model.subject or "(No Subject)",
        body=model.body or "",
        provider=model.provider,
        provider_message_id=model.provider_message_id,
        status=cast(DeliveryStatus, model.status),
        idempotency_key=model.idempotency_key,
        created_by=model.created_by or uuid4(),  # Type hint safety fallback
        created_at=model.created_at,
        updated_at=model.updated_at,
        error_message=model.error_message,
    )


@router.post("/deliveries", response_model=EmailDelivery)
async def create_delivery(
    payload: DeliveryCreatePayload,
    principal: Principal = Depends(get_current_principal),
    settings: Settings = Depends(get_settings),
    email_provider: EmailProviderInterface = Depends(get_email_provider),
    session: AsyncSession = Depends(get_db_session),
) -> EmailDelivery:
    await session.execute(text("SELECT set_config('salesos.app_workspace_id', :ws, true)"), {"ws": str(principal.workspace_id)})

    # 1. Fetch Draft & Validate Workspace Membership
    draft = get_outreach_draft(payload.draft_id, principal=principal, settings=settings)

    if draft.status != "approved":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"cannot_deliver_unapproved_draft_in_{draft.status}_state",
        )

    if not draft.current_version_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="approved_draft_has_no_version",
        )

    _, admin_client = _clients(settings)

    # 3. Load Contact Details & Verify Workspace Scoping
    contact_rows = cast(
        list[dict[str, Any]],
        admin_client.table("contacts")
        .select("*")
        .eq("id", str(draft.contact_id))
        .eq("workspace_id", str(principal.workspace_id))
        .execute()
        .data
        or [],
    )
    if not contact_rows:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="contact_not_found_in_workspace",
        )
    contact = contact_rows[0]
    recipient_email = payload.override_recipient_email or cast(str | None, contact.get("email"))
    if not recipient_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="contact_has_no_email_address",
        )

    idempotency_key = f"{principal.workspace_id}:{draft.id}:{draft.current_version_number}"

    # TRANSACTION 1 (Prepare)
    existing_delivery = await session.scalar(select(DeliveryModel).filter_by(idempotency_key=idempotency_key))
    if existing_delivery and existing_delivery.status in ("sent", "delivered", "running", "queued"):
        return _model_to_delivery(existing_delivery)

    delivery_id = uuid4()
    now_dt = datetime.now(UTC)
    
    delivery_model = DeliveryModel(
        id=delivery_id,
        workspace_id=principal.workspace_id,
        draft_id=draft.id,
        version_id=draft.current_version_id,
        version_number=draft.current_version_number,
        contact_id=draft.contact_id,
        recipient_email=recipient_email,
        subject=draft.current_subject or "(No Subject)",
        body=draft.current_body or "",
        provider="resend",
        status="queued",
        idempotency_key=idempotency_key,
        created_by=principal.user_id,
        created_at=now_dt,
        updated_at=now_dt
    )

    try:
        session.add(delivery_model)
        await session.commit()
    except IntegrityError:
        await session.rollback()
        existing_delivery = await session.scalar(select(DeliveryModel).filter_by(idempotency_key=idempotency_key))
        if existing_delivery and existing_delivery.status in ("sent", "delivered", "running", "queued"):
            return _model_to_delivery(existing_delivery)
        delivery_model = existing_delivery

    # 6. Execute Provider Send Operation
    send_req = EmailDeliverySendRequest(
        idempotency_key=idempotency_key,
        from_email=settings.resend_from_email,
        recipient_email=recipient_email,
        subject=draft.current_subject or "(No Subject)",
        body_text=draft.current_body or "",
    )

    try:
        send_result = email_provider.send_email(send_req)
        new_status = send_result.status
        provider_message_id = send_result.provider_message_id
        error_message = None
    except Exception as err:
        new_status = "failed"
        provider_message_id = None
        error_message = str(err)

    # TRANSACTION 2 (Finalize)
    delivery_model.status = new_status
    delivery_model.provider_message_id = provider_message_id
    delivery_model.error_message = error_message
    delivery_model.updated_at = datetime.now(UTC)

    if new_status == "sent" and draft.sequence_enrollment_id:
        enrollment = await session.scalar(select(SequenceEnrollmentModel).filter_by(id=draft.sequence_enrollment_id))
        if enrollment and enrollment.status == "active":
            enrollment.current_step_number += 1
            next_step = await session.scalar(select(SequenceStepModel).filter_by(sequence_id=enrollment.sequence_id, step_number=enrollment.current_step_number))
            
            if next_step:
                enrollment.next_step_due_at = datetime.now(UTC) + timedelta(days=next_step.delay_days)
                job = JobModel(
                    id=uuid4(),
                    workspace_id=principal.workspace_id,
                    job_type="execute_sequence_step",
                    payload={"enrollment_id": str(enrollment.id), "step_number": enrollment.current_step_number},
                    status="pending",
                    available_at=enrollment.next_step_due_at,
                    created_at=datetime.now(UTC),
                    updated_at=datetime.now(UTC)
                )
                session.add(job)
            else:
                enrollment.status = "completed"

    await session.commit()
    return _model_to_delivery(delivery_model)


@router.get("/deliveries", response_model=list[EmailDelivery])
async def list_deliveries(
    status_filter: str = Query("all", alias="status"),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    principal: Principal = Depends(get_current_principal),
    session: AsyncSession = Depends(get_db_session),
) -> list[EmailDelivery]:
    await session.execute(text("SELECT set_config('salesos.app_workspace_id', :ws, true)"), {"ws": str(principal.workspace_id)})

    q = select(DeliveryModel).filter_by(workspace_id=principal.workspace_id)
    if status_filter != "all":
        q = q.filter_by(status=status_filter)
    
    q = q.order_by(DeliveryModel.created_at.desc()).offset(offset).limit(limit)
    
    result = await session.scalars(q)
    return [_model_to_delivery(d) for d in result]


@router.get("/deliveries/{delivery_id}", response_model=EmailDelivery)
async def get_delivery_detail(
    delivery_id: UUID,
    principal: Principal = Depends(get_current_principal),
    session: AsyncSession = Depends(get_db_session),
) -> EmailDelivery:
    await session.execute(text("SELECT set_config('salesos.app_workspace_id', :ws, true)"), {"ws": str(principal.workspace_id)})

    delivery = await session.scalar(select(DeliveryModel).filter_by(id=delivery_id, workspace_id=principal.workspace_id))
    if not delivery:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="delivery_record_not_found",
        )
    return _model_to_delivery(delivery)


@router.post("/deliveries/{delivery_id}/actions/cancel", response_model=EmailDelivery)
async def cancel_delivery(
    delivery_id: UUID,
    principal: Principal = Depends(get_current_principal),
    session: AsyncSession = Depends(get_db_session),
) -> EmailDelivery:
    await session.execute(text("SELECT set_config('salesos.app_workspace_id', :ws, true)"), {"ws": str(principal.workspace_id)})

    delivery = await session.scalar(select(DeliveryModel).filter_by(id=delivery_id, workspace_id=principal.workspace_id))
    if not delivery:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="delivery_record_not_found",
        )
    
    if delivery.status not in ("queued", "running"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"cannot_cancel_delivery_in_{delivery.status}_state",
        )

    delivery.status = "cancelled"
    delivery.updated_at = datetime.now(UTC)
    await session.commit()

    return _model_to_delivery(delivery)


@router.post("/deliveries/webhooks/resend")
async def resend_webhook_handler(
    request: Request,
    svix_id: str | None = Header(default=None, alias="svix-id"),
    svix_timestamp: str | None = Header(default=None, alias="svix-timestamp"),
    svix_signature: str | None = Header(default=None, alias="svix-signature"),
    settings: Settings = Depends(get_settings),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, Any]:
    raw_body = await request.body()
    body_str = raw_body.decode("utf-8")

    if settings.resend_webhook_secret:
        if not svix_id or not svix_timestamp or not svix_signature:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="missing_webhook_signature_headers",
            )
        try:
            import resend
            options: resend.VerifyWebhookOptions = {
                "payload": body_str,
                "headers": cast(
                    Any,
                    {
                        "svix-id": svix_id,
                        "svix-timestamp": svix_timestamp,
                        "svix-signature": svix_signature,
                        "id": svix_id,
                        "timestamp": svix_timestamp,
                        "signature": svix_signature,
                    },
                ),
                "webhook_secret": settings.resend_webhook_secret,
            }
            resend.Webhooks.verify(options)
        except Exception as err:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"invalid_webhook_signature: {err}",
            ) from err

    try:
        import json
        payload_json = json.loads(body_str)
    except Exception:
        payload_json = {}

    event_type = str(payload_json.get("type", ""))
    data = payload_json.get("data", {})
    provider_msg_id = str(data.get("email_id") or data.get("id") or "")

    if event_type == "email.received":
        from app.adapters.reply_classifier import DeterministicReplyClassifier
        from app.api.conversations import InboundReplyPayload, ingest_inbound_reply

        sender = str(data.get("from") or data.get("sender") or "")
        recipient = str(data.get("to") or data.get("recipient") or "")
        subject = str(data.get("subject") or "")
        text_body = str(data.get("text") or data.get("html") or "")
        in_reply_to = str(data.get("headers", {}).get("in-reply-to") or data.get("in_reply_to") or "")

        if not text_body and provider_msg_id and settings.resend_api_key:
            try:
                import resend
                resend.api_key = settings.resend_api_key
                recv_detail = resend.EmailsReceiving.get(provider_msg_id)
                if isinstance(recv_detail, dict):
                    text_body = str(recv_detail.get("text") or recv_detail.get("html") or "")
                elif hasattr(recv_detail, "text"):
                    text_body = str(getattr(recv_detail, "text", "") or getattr(recv_detail, "html", ""))
            except Exception:
                pass

        if sender and recipient:
            await ingest_inbound_reply(
                InboundReplyPayload(
                    sender_email=sender,
                    recipient_email=recipient,
                    subject=subject,
                    body=text_body,
                    provider_message_id=provider_msg_id,
                    in_reply_to_provider_message_id=in_reply_to or None,
                ),
                classifier=DeterministicReplyClassifier(),
                settings=settings,
                session=session,
            )
        return {"received": True, "event": event_type, "status": "ingested"}

    status_mapping: dict[str, DeliveryStatus] = {
        "email.delivered": "delivered",
        "email.bounced": "bounced",
        "email.complained": "complained",
        "email.failed": "failed",
    }

    new_status = status_mapping.get(event_type)
    if new_status and provider_msg_id:
        # Cannot easily enforce RLS here without workspace_id, so query by provider_message_id globally
        delivery = await session.scalar(select(DeliveryModel).filter_by(provider_message_id=provider_msg_id))
        if delivery:
            delivery.status = new_status
            delivery.updated_at = datetime.now(UTC)
            await session.commit()

    return {"received": True, "event": event_type, "status": "processed"}
