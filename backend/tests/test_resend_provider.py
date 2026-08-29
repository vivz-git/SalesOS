from unittest.mock import MagicMock, patch

import pytest

from app.adapters.email_provider import EmailDeliverySendRequest
from app.adapters.resend_provider import ResendEmailProvider


def _sample_send_request() -> EmailDeliverySendRequest:
    return EmailDeliverySendRequest(
        idempotency_key="idemp_key_12345",
        from_email="outbound@acme.com",
        recipient_email="prospect@targetcorp.com",
        subject="Accelerating Outbound with SalesOS",
        body_text="Hi Alex, wanted to follow up on sales platform scaling.",
        body_html="<p>Hi Alex, wanted to follow up on sales platform scaling.</p>",
        tags={"campaign_id": "camp_99", "channel": "cold_outreach"},
    )


def test_resend_provider_missing_key_raises() -> None:
    provider = ResendEmailProvider(api_key=None)
    req = _sample_send_request()
    with pytest.raises(ValueError, match="resend_api_key_not_configured"):
        provider.send_email(req)


def test_resend_provider_whitespace_key_raises() -> None:
    provider = ResendEmailProvider(api_key="   ")
    req = _sample_send_request()
    with pytest.raises(ValueError, match="resend_api_key_not_configured"):
        provider.send_email(req)


@patch("app.adapters.resend_provider.resend.Emails.send")
def test_resend_provider_send_success_dict_response(mock_send: MagicMock) -> None:
    mock_send.return_value = {"id": "res_msg_abc123"}

    provider = ResendEmailProvider(api_key="re_test_key_123")
    req = _sample_send_request()

    result = provider.send_email(req)

    assert result.provider == "resend"
    assert result.provider_message_id == "res_msg_abc123"
    assert result.status == "sent"
    assert result.idempotency_key == "idemp_key_12345"
    assert result.duration_ms is not None and result.duration_ms >= 0
    assert result.raw_response == {"id": "res_msg_abc123"}

    mock_send.assert_called_once()
    call_args = mock_send.call_args[0][0]
    assert call_args["from"] == "outbound@acme.com"
    assert call_args["to"] == ["prospect@targetcorp.com"]
    assert call_args["subject"] == "Accelerating Outbound with SalesOS"
    assert call_args["headers"]["Idempotency-Key"] == "idemp_key_12345"
    assert call_args["headers"]["X-Entity-Ref-ID"] == "idemp_key_12345"
    assert call_args["tags"] == [
        {"name": "campaign_id", "value": "camp_99"},
        {"name": "channel", "value": "cold_outreach"},
    ]


@patch("app.adapters.resend_provider.resend.Emails.send")
def test_resend_provider_send_success_object_response(mock_send: MagicMock) -> None:
    class MockResendResponse:
        id = "res_msg_obj456"

    mock_send.return_value = MockResendResponse()

    provider = ResendEmailProvider(api_key="re_test_key_123")
    req = _sample_send_request()

    result = provider.send_email(req)

    assert result.provider == "resend"
    assert result.provider_message_id == "res_msg_obj456"
    assert result.status == "sent"
    assert result.idempotency_key == "idemp_key_12345"


@patch("app.adapters.resend_provider.resend.Emails.send")
def test_resend_provider_empty_message_id_raises_value_error(mock_send: MagicMock) -> None:
    mock_send.return_value = {"id": ""}

    provider = ResendEmailProvider(api_key="re_test_key_123")
    req = _sample_send_request()

    with pytest.raises(ValueError, match="resend_returned_empty_message_id"):
        provider.send_email(req)


@patch("app.adapters.resend_provider.resend.Emails.send")
def test_resend_provider_api_error_raises_value_error(mock_send: MagicMock) -> None:
    mock_send.side_effect = RuntimeError("Domain not verified")

    provider = ResendEmailProvider(api_key="re_test_key_123")
    req = _sample_send_request()

    with pytest.raises(ValueError, match="resend_delivery_failed: Domain not verified"):
        provider.send_email(req)
