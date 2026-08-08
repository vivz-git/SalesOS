from uuid import uuid4

from fastapi.testclient import TestClient

from app.adapters.reply_classifier import DeterministicReplyClassifier
from app.auth import Principal, get_current_principal
from app.main import app


def test_classifier_6_state_taxonomy() -> None:
    classifier = DeterministicReplyClassifier()

    # 1. Unsubscribe
    r1 = classifier.classify("Please unsubscribe me from this list.")
    assert r1.reply_state == "unsubscribe"
    assert r1.needs_human_action is True

    # 2. Out of Office
    r2 = classifier.classify("I am currently out of the office on vacation.")
    assert r2.reply_state == "out_of_office"
    assert r2.needs_human_action is False

    # 3. Referral
    r3 = classifier.classify("You should speak with my colleague Jane.")
    assert r3.reply_state == "referral"

    # 4. Not Now
    r4 = classifier.classify("Not right now, please check back next quarter.")
    assert r4.reply_state == "not_now"

    # 5. Interested
    r5 = classifier.classify("Sounds good, let's schedule a call next week.")
    assert r5.reply_state == "interested"

    # 6. Ambiguous
    r6 = classifier.classify("Interesting observation about our stack.")
    assert r6.reply_state == "ambiguous"
    assert r6.needs_human_action is True


def test_inbound_reply_ingestion_and_classification() -> None:
    ws_id = uuid4()
    mock_principal = Principal(
        user_id=uuid4(),
        email="user@example.com",
        workspace_id=ws_id,
        role="admin",
    )
    app.dependency_overrides[get_current_principal] = lambda: mock_principal

    client = TestClient(app)
    inbound_payload = {
        "workspace_id": str(ws_id),
        "sender_email": "prospect@example.com",
        "recipient_email": "rep@company.com",
        "subject": "Re: Outreach Opportunity",
        "body": "Sounds good, let's chat next Tuesday!",
    }

    resp = client.post("/v1/conversations/inbound", json=inbound_payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["current_reply_state"] == "interested"
    assert data["status"] == "active"
    assert len(data["messages"]) == 1

    conv_id = data["id"]

    # Retrieve Detail via GET /v1/conversations/{id}
    detail_resp = client.get(f"/v1/conversations/{conv_id}")
    assert detail_resp.status_code == 200
    assert detail_resp.json()["id"] == conv_id

    app.dependency_overrides.clear()


def test_unsubscribe_forces_opt_out_status() -> None:
    ws_id = uuid4()
    mock_principal = Principal(
        user_id=uuid4(),
        email="user@example.com",
        workspace_id=ws_id,
        role="admin",
    )
    app.dependency_overrides[get_current_principal] = lambda: mock_principal

    client = TestClient(app)
    resp = client.post(
        "/v1/conversations/inbound",
        json={
            "workspace_id": str(ws_id),
            "sender_email": "optout@example.com",
            "recipient_email": "rep@company.com",
            "subject": "Re: Outreach",
            "body": "Please remove me and stop emailing.",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["current_reply_state"] == "unsubscribe"
    assert data["status"] == "opt_out"

    app.dependency_overrides.clear()


def test_manual_classification_override() -> None:
    ws_id = uuid4()
    mock_principal = Principal(
        user_id=uuid4(),
        email="user@example.com",
        workspace_id=ws_id,
        role="admin",
    )
    app.dependency_overrides[get_current_principal] = lambda: mock_principal

    client = TestClient(app)
    # 1. Ingest ambiguous message
    resp = client.post(
        "/v1/conversations/inbound",
        json={
            "workspace_id": str(ws_id),
            "sender_email": "prospect2@example.com",
            "recipient_email": "rep@company.com",
            "subject": "Re: Inquiry",
            "body": "Hmm strange email.",
        },
    )
    conv_id = resp.json()["id"]

    # 2. Reclassify as interested
    override_resp = client.post(
        f"/v1/conversations/{conv_id}/actions/classify",
        json={
            "reply_state": "interested",
            "explanation": "User confirmed prospect wants to meet",
        },
    )
    assert override_resp.status_code == 200
    assert override_resp.json()["current_reply_state"] == "interested"

    app.dependency_overrides.clear()


def test_cross_workspace_conversation_access_denied() -> None:
    ws_id1 = uuid4()
    ws_id2 = uuid4()

    mock_principal1 = Principal(
        user_id=uuid4(),
        email="user1@example.com",
        workspace_id=ws_id1,
        role="admin",
    )
    app.dependency_overrides[get_current_principal] = lambda: mock_principal1
    client = TestClient(app)

    # Ingest for workspace 1
    resp = client.post(
        "/v1/conversations/inbound",
        json={
            "workspace_id": str(ws_id1),
            "sender_email": "p1@example.com",
            "recipient_email": "r1@company.com",
            "subject": "Hello",
            "body": "Hi there",
        },
    )
    conv_id = resp.json()["id"]

    # Switch to workspace 2 principal
    mock_principal2 = Principal(
        user_id=uuid4(),
        email="user2@example.com",
        workspace_id=ws_id2,
        role="admin",
    )
    app.dependency_overrides[get_current_principal] = lambda: mock_principal2

    detail_resp = client.get(f"/v1/conversations/{conv_id}")
    assert detail_resp.status_code == 404

    app.dependency_overrides.clear()
