from abc import ABC, abstractmethod
from typing import Any, Literal

from pydantic import BaseModel, Field

DeliveryStatus = Literal[
    "queued",
    "running",
    "sent",
    "delivered",
    "failed",
    "bounced",
    "complained",
    "cancelled",
]


class EmailDeliverySendRequest(BaseModel):
    idempotency_key: str
    from_email: str
    recipient_email: str
    subject: str
    body_text: str
    body_html: str | None = None
    tags: dict[str, str] = Field(default_factory=dict)


class EmailDeliverySendResult(BaseModel):
    provider: str = "resend"
    provider_message_id: str
    status: DeliveryStatus = "sent"
    idempotency_key: str
    duration_ms: int | None = None
    raw_response: dict[str, Any] = Field(default_factory=dict)


class EmailProviderInterface(ABC):
    """Abstract interface for outbound email delivery providers.

    Decouples core SalesOS FastAPI logic and delivery state machine from specific
    vendor SDKs (Resend, SendGrid, etc.).
    """

    @abstractmethod
    def send_email(self, request: EmailDeliverySendRequest) -> EmailDeliverySendResult:
        """Send an outbound email and return normalized provider response."""
        pass
