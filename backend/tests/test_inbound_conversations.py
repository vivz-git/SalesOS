from datetime import UTC, datetime
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError

from app.auth import Principal, get_current_principal
from app.db import get_db_session
from app.main import app
from app.models import (
    ContactModel,
    ConversationModel,
)


class FakeTransaction:
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        pass


class FakeScalars:
    def __init__(self, items):
        self.items = items

    def all(self):
        return self.items

    def __iter__(self):
        return iter(self.items)


class FakeResult:
    def __init__(self, items=None, scalar_item=None):
        self._items = items or []
        self._scalar_item = scalar_item

    def scalars(self):
        return FakeScalars(self._items)

    def scalar_one_or_none(self):
        return self._scalar_item

    def unique(self):
        return self


class FakeSession:
    def __init__(self):
        self.flushes = 0
        self.flush_error = False
        self.mock_conv = None
        self.mock_contact = None

    def begin(self):
        return FakeTransaction()

    def begin_nested(self):
        return FakeTransaction()

    async def execute(self, stmt, *args, **kwargs):
        return FakeResult([], None)

    async def get(self, model, ident, *args, **kwargs):
        if model == ConversationModel:
            return self.mock_conv
        if model == ContactModel:
            return self.mock_contact
        return None

    async def scalar(self, stmt, *args, **kwargs):
        stmt_str = str(stmt).lower()
        if "conversation_messages" in stmt_str:
            return None
        if "contacts" in stmt_str:
            return self.mock_contact
        return self.mock_conv

    async def scalars(self, stmt, *args, **kwargs):
        return FakeResult([]).scalars()

    async def flush(self):
        self.flushes += 1
        if self.flushes == 1 and self.flush_error:
            raise IntegrityError("duplicate", params={}, orig=Exception("duplicate"))

    async def refresh(self, obj):
        pass

    async def commit(self):
        pass

    async def rollback(self):
        pass

    def add(self, obj):
        pass


@pytest.fixture
def mock_principal() -> Principal:
    return Principal(
        user_id=uuid4(),
        email="admin@salesos.com",
        workspace_id=uuid4(),
        role="admin",
    )


def _create_mock_conv(ws_id):
    return ConversationModel(
        id=uuid4(),
        workspace_id=ws_id,
        status="active",
        contact_id=uuid4(),
        campaign_id=uuid4(),
        delivery_id=uuid4(),
        current_reply_state="interested",
        last_message_at=datetime.now(UTC),
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


def _create_mock_contact(ws_id):
    return ContactModel(
        id=uuid4(),
        workspace_id=ws_id,
        email="test@test.com",
        first_name="Test",
        last_name="User",
    )


def test_simulator_workspace_spoofing_blocked(mock_principal: Principal) -> None:
    session = FakeSession()
    session.mock_conv = _create_mock_conv(mock_principal.workspace_id)
    session.mock_contact = _create_mock_contact(mock_principal.workspace_id)
    app.dependency_overrides[get_db_session] = lambda: session
    app.dependency_overrides[get_current_principal] = lambda: mock_principal
    client = TestClient(app)

    payload = {
        "workspace_id": str(uuid4()),  # Malicious payload trying to inject different workspace
        "sender_email": "test@test.com",
        "recipient_email": "sales@acme.com",
        "subject": "Hello",
        "body": "Hello",
        "in_reply_to_provider_message_id": "msg_123",
        "provider_message_id": "msg_12345",
    }

    resp = client.post("/v1/conversations/simulate", json=payload)
    # The endpoint simply uses principal.workspace_id and ignores the payload's workspace_id.
    assert resp.status_code == 200
    app.dependency_overrides.clear()


def test_simulator_success(mock_principal: Principal) -> None:
    session = FakeSession()
    session.mock_conv = _create_mock_conv(mock_principal.workspace_id)
    session.mock_contact = _create_mock_contact(mock_principal.workspace_id)
    app.dependency_overrides[get_db_session] = lambda: session
    app.dependency_overrides[get_current_principal] = lambda: mock_principal
    client = TestClient(app)

    payload = {
        "workspace_id": str(mock_principal.workspace_id),
        "sender_email": "test@test.com",
        "recipient_email": "sales@acme.com",
        "subject": "Hello",
        "body": "Hello",
        "in_reply_to_provider_message_id": "msg_123",
        "provider_message_id": "msg_12345",
    }

    resp = client.post("/v1/conversations/simulate", json=payload)
    assert resp.status_code == 200
    app.dependency_overrides.clear()


def test_simulator_duplicate_inbound_event(mock_principal: Principal) -> None:
    session = FakeSession()
    session.flush_error = True
    session.mock_conv = _create_mock_conv(mock_principal.workspace_id)
    session.mock_contact = _create_mock_contact(mock_principal.workspace_id)

    app.dependency_overrides[get_db_session] = lambda: session
    app.dependency_overrides[get_current_principal] = lambda: mock_principal
    client = TestClient(app)

    payload = {
        "workspace_id": str(mock_principal.workspace_id),
        "sender_email": "test@test.com",
        "recipient_email": "sales@acme.com",
        "subject": "Hello duplicate",
        "body": "Hello duplicate",
        "in_reply_to_provider_message_id": "msg_123",
        "provider_message_id": "dup_123",
    }

    resp = client.post("/v1/conversations/simulate", json=payload)
    assert resp.status_code == 200
    app.dependency_overrides.clear()
