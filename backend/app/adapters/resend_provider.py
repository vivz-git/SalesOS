import time
from typing import Any, cast

import resend

from app.adapters.email_provider import (
    EmailDeliverySendRequest,
    EmailDeliverySendResult,
    EmailProviderInterface,
)


class ResendEmailProvider(EmailProviderInterface):
    """Resend email provider concrete adapter using official resend 2.35.0 Python SDK.

    Isolates all resend SDK calls behind EmailProviderInterface.
    """

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key.strip() if api_key else None
        if self.api_key:
            resend.api_key = self.api_key

    def send_email(self, request: EmailDeliverySendRequest) -> EmailDeliverySendResult:
        if not self.api_key:
            raise ValueError("resend_api_key_not_configured")

        resend.api_key = self.api_key
        start_time = time.perf_counter()

        params: resend.Emails.SendParams = {
            "from": request.from_email,
            "to": [request.recipient_email],
            "subject": request.subject,
            "html": request.body_html or f"<pre style='font-family:sans-serif;'>{request.body_text}</pre>",
            "text": request.body_text,
            "headers": {
                "Idempotency-Key": request.idempotency_key,
                "X-Entity-Ref-ID": request.idempotency_key,
            },
        }

        if request.tags:
            params["tags"] = [{"name": k, "value": v} for k, v in request.tags.items()]

        try:
            resp = resend.Emails.send(params)
            duration_ms = int((time.perf_counter() - start_time) * 1000)

            # Response object or dict
            provider_message_id = ""
            raw_dict: dict[str, Any] = {}
            if isinstance(resp, dict):
                provider_message_id = str(resp.get("id", ""))
                raw_dict = cast(dict[str, Any], resp)
            elif hasattr(resp, "id"):
                provider_message_id = str(getattr(resp, "id", ""))
                raw_dict = {"id": provider_message_id}

            if not provider_message_id:
                raise ValueError("resend_returned_empty_message_id")

            return EmailDeliverySendResult(
                provider="resend",
                provider_message_id=provider_message_id,
                status="sent",
                idempotency_key=request.idempotency_key,
                duration_ms=duration_ms,
                raw_response=raw_dict,
            )
        except Exception as err:
            raise ValueError(f"resend_delivery_failed: {err}") from err
