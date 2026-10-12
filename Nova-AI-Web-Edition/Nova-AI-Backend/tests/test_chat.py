"""Tests for the chat and conversation endpoints."""
import pytest

pytestmark = pytest.mark.asyncio

# A valid 1x1 transparent PNG, used to test image (vision) input end-to-end.
_TINY_PNG_BASE64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk"
    "+A8AAQUBAScY42YAAAAASUVORK5CYII="
)


async def _auth_headers(client, unique_email, password="SuperSecret123"):
    await client.post("/auth/register", json={"email": unique_email, "password": password})
    login = await client.post("/auth/login", json={"email": unique_email, "password": password})

    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


async def test_chat_creates_new_conversation(client, unique_email):
    headers = await _auth_headers(client, unique_email)

    response = await client.post("/chat", json={"conversation_id": None, "message": "Hello Nova"}, headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert body["title"]
    assert body["user_message"]["content"] == "Hello Nova"
    assert body["assistant_message"]["role"] == "assistant"
    assert body["conversation_id"]


async def test_chat_continues_existing_conversation(client, unique_email):
    headers = await _auth_headers(client, unique_email)

    first = await client.post("/chat", json={"conversation_id": None, "message": "Hi"}, headers=headers)
    conversation_id = first.json()["conversation_id"]

    second = await client.post(
        "/chat",
        json={"conversation_id": conversation_id, "message": "How are you?"},
        headers=headers,
    )
    assert second.status_code == 200
    assert second.json()["conversation_id"] == conversation_id


async def test_list_conversations(client, unique_email):
    headers = await _auth_headers(client, unique_email)
    await client.post("/chat", json={"conversation_id": None, "message": "Hi"}, headers=headers)

    response = await client.get("/chat/conversations", headers=headers)
    assert response.status_code == 200
    assert len(response.json()) == 1


async def test_get_conversation_detail(client, unique_email):
    headers = await _auth_headers(client, unique_email)
    chat_response = await client.post("/chat", json={"conversation_id": None, "message": "Hi"}, headers=headers)
    conversation_id = chat_response.json()["conversation_id"]

    response = await client.get(f"/chat/conversations/{conversation_id}", headers=headers)
    assert response.status_code == 200
    assert len(response.json()["messages"]) == 2


async def test_delete_conversation(client, unique_email):
    headers = await _auth_headers(client, unique_email)
    chat_response = await client.post("/chat", json={"conversation_id": None, "message": "Hi"}, headers=headers)
    conversation_id = chat_response.json()["conversation_id"]

    delete_response = await client.delete(f"/chat/conversations/{conversation_id}", headers=headers)
    assert delete_response.status_code == 204

    get_response = await client.get(f"/chat/conversations/{conversation_id}", headers=headers)
    assert get_response.status_code == 404


async def test_chat_requires_auth(client):
    response = await client.post("/chat", json={"conversation_id": None, "message": "Hi"})
    assert response.status_code == 401


async def test_conversation_not_owned_is_forbidden(client, unique_email):
    headers_a = await _auth_headers(client, unique_email)
    chat_response = await client.post("/chat", json={"conversation_id": None, "message": "Hi"}, headers=headers_a)
    conversation_id = chat_response.json()["conversation_id"]

    headers_b = await _auth_headers(client, f"other-{unique_email}")
    response = await client.get(f"/chat/conversations/{conversation_id}", headers=headers_b)
    assert response.status_code == 403


async def test_chat_with_image_is_understood_and_persisted(client, unique_email):
    headers = await _auth_headers(client, unique_email)

    response = await client.post(
        "/chat",
        json={
            "conversation_id": None,
            "message": "What is in this picture?",
            "image_base64": _TINY_PNG_BASE64,
            "image_mime_type": "image/png",
        },
        headers=headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["user_message"]["image_mime_type"] == "image/png"
    assert body["user_message"]["image_base64"] == _TINY_PNG_BASE64
    assert "[saw image]" in body["assistant_message"]["content"]

    conversation_id = body["conversation_id"]
    detail = await client.get(f"/chat/conversations/{conversation_id}", headers=headers)
    stored_image = detail.json()["messages"][0]["image_base64"]
    assert stored_image == _TINY_PNG_BASE64


async def test_chat_with_unsupported_image_type_is_rejected(client, unique_email):
    headers = await _auth_headers(client, unique_email)

    response = await client.post(
        "/chat",
        json={
            "conversation_id": None,
            "message": "Hi",
            "image_base64": _TINY_PNG_BASE64,
            "image_mime_type": "image/gif",
        },
        headers=headers,
    )
    assert response.status_code == 400
    assert response.json()["error"] == "invalid_image"


async def test_chat_image_requires_both_fields(client, unique_email):
    headers = await _auth_headers(client, unique_email)

    response = await client.post(
        "/chat",
        json={"conversation_id": None, "message": "Hi", "image_base64": _TINY_PNG_BASE64},
        headers=headers,
    )
    assert response.status_code == 422


async def test_chat_persists_web_search_sources(client, unique_email):
    """When Gemini grounds its reply with a web search, sources are saved
    on the assistant message and returned in the chat response."""
    headers = await _auth_headers(client, unique_email)

    response = await client.post(
        "/chat",
        json={"conversation_id": None, "message": "search for today's news"},
        headers=headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["assistant_message"]["sources"] == [
        {"title": "Example Source", "url": "https://example.com/article"}
    ]


async def test_chat_without_search_trigger_has_no_sources(client, unique_email):
    headers = await _auth_headers(client, unique_email)

    response = await client.post(
        "/chat", json={"conversation_id": None, "message": "Hello Nova"}, headers=headers
    )
    assert response.status_code == 200
    body = response.json()
    assert body["assistant_message"]["sources"] is None


async def test_conversation_detail_includes_sources(client, unique_email):
    headers = await _auth_headers(client, unique_email)

    chat = await client.post(
        "/chat",
        json={"conversation_id": None, "message": "please search this for me"},
        headers=headers,
    )
    conversation_id = chat.json()["conversation_id"]

    detail = await client.get(f"/chat/conversations/{conversation_id}", headers=headers)
    assert detail.status_code == 200
    messages = detail.json()["messages"]
    assistant_msg = next(m for m in messages if m["role"] == "assistant")
    assert assistant_msg["sources"] == [
        {"title": "Example Source", "url": "https://example.com/article"}
    ]


async def test_web_search_disabled_after_daily_limit(client, unique_email, monkeypatch):
    """Once a plan's daily search quota is used up, further search-triggering
    messages get no sources since the tool is no longer offered.

    The quota itself is monkeypatched rather than assumed from
    app.core.plans.SEARCH_LIMITS, so this test keeps checking the
    enforcement *mechanism* even if the actual free-plan number changes
    (as it did: SEARCH_LIMITS used to say 5, out of sync with what
    SettingsPage.tsx advertises to users).
    """
    import app.core.plans as plans

    monkeypatch.setitem(plans.SEARCH_LIMITS, "free", 5)
    headers = await _auth_headers(client, unique_email)

    conversation_id = None
    for i in range(5):
        response = await client.post(
            "/chat",
            json={"conversation_id": conversation_id, "message": f"search for thing {i}"},
            headers=headers,
        )
        assert response.status_code == 200
        conversation_id = response.json()["conversation_id"]
        assert response.json()["assistant_message"]["sources"] is not None

    sixth = await client.post(
        "/chat",
        json={"conversation_id": conversation_id, "message": "search for thing 6"},
        headers=headers,
    )
    assert sixth.status_code == 200
    assert sixth.json()["assistant_message"]["sources"] is None
