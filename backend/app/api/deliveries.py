from datetime import UTC, datetime
from typing import Any, Literal, cast
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, status
from pydantic import BaseModel, Field

from app.adapters.email_provider import (
    DeliveryStatus,
    EmailDeliverySendRequest,
    EmailProviderInterface,
)
from app.adapters.resend_provider import ResendEmailProvider
from app.api.outreach import get_outreach_draft
from app.auth import Principal, _clients, get_current_principal
from app.core.config import Settings, get_settings

router = APIRouter(prefix="/v1", tags=["deliveries"])

# In-memory store for deliveries when database table is unavailable
_DELIVERIES_STORE: list[dict[str, Any]] = []


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


def _row_to_delivery(row: dict[str, Any]) -> EmailDelivery:
    created_at_val = str(row.get("created_at", datetime.now(UTC).isoformat()))
    updated_at_val = str(row.get("updated_at", created_at_val))

    return EmailDelivery(
        id=UUID(str(row["id"])),
        workspace_id=UUID(str(row["workspace_id"])),
        draft_id=UUID(str(row["draft_id"])),
        version_id=UUID(str(row["version_id"])),
        version_number=int(row.get("version_number", 1)),
        contact_id=UUID(str(row["contact_id"])),
        recipient_email=str(row.get("recipient_email", "")),
        subject=str(row.get("subject", "")),
        body=str(row.get("body", "")),
        provider=str(row.get("provider", "resend")),
        provider_message_id=cast(str | None, row.get("provider_message_id")),
        status=cast(DeliveryStatus, row.get("status", "queued")),
        idempotency_key=str(row.get("idempotency_key", "")),
        created_by=UUID(str(row.get("created_by", uuid4()))),
        created_at=datetime.fromisoformat(created_at_val),
        updated_at=datetime.fromisoformat(updated_at_val),
        error_message=cast(str | None, row.get("error_message")),
    )


def _find_delivery_by_idempotency(workspace_id: UUID, idempotency_key: str) -> EmailDelivery | None:
    for row in _DELIVERIES_STORE:
        if str(row.get("workspace_id")) == str(workspace_id) and row.get("idempotency_key") == idempotency_key:
            return _row_to_delivery(row)
    return None


@router.post("/deliveries", response_model=EmailDelivery)
def create_delivery(
    payload: DeliveryCreatePayload,
    principal: Principal = Depends(get_current_principal),
    settings: Settings = Depends(get_settings),
    email_provider: EmailProviderInterface = Depends(get_email_provider),
) -> EmailDelivery:
    # 1. Fetch Draft & Validate Workspace Membership
    draft = get_outreach_draft(payload.draft_id, principal=principal, settings=settings)

    # 2. CRITICAL APPROVAL SAFETY GATE: Status MUST be 'approved'
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

    # 4. Generate Stable Idempotency Key
    idempotency_key = f"{principal.workspace_id}:{draft.id}:{draft.current_version_number}"

    # 5. Check Idempotency to prevent duplicate external sends
    existing_delivery = _find_delivery_by_idempotency(principal.workspace_id, idempotency_key)
    if existing_delivery and existing_delivery.status in ("sent", "delivered", "running", "queued"):
        return existing_delivery

    delivery_id = uuid4()
    now_iso = datetime.now(UTC).isoformat()

    delivery_dict: dict[str, Any] = {
        "id": str(delivery_id),
        "workspace_id": str(principal.workspace_id),
        "draft_id": str(draft.id),
        "version_id": str(draft.current_version_id),
        "version_number": draft.current_version_number,
        "contact_id": str(draft.contact_id),
        "recipient_email": recipient_email,
        "subject": draft.current_subject or "(No Subject)",
        "body": draft.current_body or "",
        "provider": "resend",
        "provider_message_id": None,
        "status": "queued",
        "idempotency_key": idempotency_key,
        "created_by": str(principal.user_id),
        "created_at": now_iso,
        "updated_at": now_iso,
        "error_message": None,
    }

    _DELIVERIES_STORE.append(delivery_dict)

    # Attempt database persist if available
    try:
        admin_client.table("deliveries").insert(cast(Any, delivery_dict)).execute()
    except Exception:
        pass

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
        delivery_dict["status"] = send_result.status
        delivery_dict["provider_message_id"] = send_result.provider_message_id
        delivery_dict["updated_at"] = datetime.now(UTC).isoformat()
    except Exception as err:
        delivery_dict["status"] = "failed"
        delivery_dict["error_message"] = str(err)
        delivery_dict["updated_at"] = datetime.now(UTC).isoformat()

    # Update database record if available
    try:
        admin_client.table("deliveries").update({
            "status": delivery_dict["status"],
            "provider_message_id": delivery_dict["provider_message_id"],
            "error_message": delivery_dict["error_message"],
            "updated_at": delivery_dict["updated_at"],
        }).eq("id", str(delivery_id)).execute()
    except Exception:
        pass

    return _row_to_delivery(delivery_dict)


@router.get("/deliveries", response_model=list[EmailDelivery])
def list_deliveries(
    status_filter: str = Query("all", alias="status"),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    principal: Principal = Depends(get_current_principal),
) -> list[EmailDelivery]:
    results: list[EmailDelivery] = []
    for row in _DELIVERIES_STORE:
        if str(row.get("workspace_id")) == str(principal.workspace_id):
            if status_filter == "all" or row.get("status") == status_filter:
                results.append(_row_to_delivery(row))

    results.sort(key=lambda d: d.created_at, reverse=True)
    return results[offset : offset + limit]


@router.get("/deliveries/{delivery_id}", response_model=EmailDelivery)
def get_delivery_detail(
    delivery_id: UUID,
    principal: Principal = Depends(get_current_principal),
) -> EmailDelivery:
    for row in _DELIVERIES_STORE:
        if str(row.get("id")) == str(delivery_id) and str(row.get("workspace_id")) == str(principal.workspace_id):
            return _row_to_delivery(row)

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="delivery_record_not_found",
    )


@router.post("/deliveries/{delivery_id}/actions/cancel", response_model=EmailDelivery)
def cancel_delivery(
    delivery_id: UUID,
    principal: Principal = Depends(get_current_principal),
) -> EmailDelivery:
    for row in _DELIVERIES_STORE:
        if str(row.get("id")) == str(delivery_id) and str(row.get("workspace_id")) == str(principal.workspace_id):
            current_status = row.get("status")
            if current_status not in ("queued", "running"):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"cannot_cancel_delivery_in_{current_status}_state",
                )
            row["status"] = "cancelled"
            row["updated_at"] = datetime.now(UTC).isoformat()
            return _row_to_delivery(row)

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="delivery_record_not_found",
    )


@router.post("/deliveries/webhooks/resend")
async def resend_webhook_handler(
    request: Request,
    svix_id: str | None = Header(default=None, alias="svix-id"),
    svix_timestamp: str | None = Header(default=None, alias="svix-timestamp"),
    svix_signature: str | None = Header(default=None, alias="svix-signature"),
    settings: Settings = Depends(get_settings),
) -> dict[str, Any]:
    raw_body = await request.body()
    body_str = raw_body.decode("utf-8")

    # Verify webhook signature if secret is configured
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

    # Parse JSON payload
    try:
        import json
        payload_json = json.loads(body_str)
    except Exception:
        payload_json = {}

    event_type = str(payload_json.get("type", ""))
    data = payload_json.get("data", {})
    provider_msg_id = str(data.get("email_id") or data.get("id") or "")

    status_mapping: dict[str, DeliveryStatus] = {
        "email.delivered": "delivered",
        "email.bounced": "bounced",
        "email.complained": "complained",
        "email.failed": "failed",
    }

    new_status = status_mapping.get(event_type)
    if new_status and provider_msg_id:
        for row in _DELIVERIES_STORE:
            if row.get("provider_message_id") == provider_msg_id:
                row["status"] = new_status
                row["updated_at"] = datetime.now(UTC).isoformat()

    return {"received": True, "event": event_type, "status": "processed"}
