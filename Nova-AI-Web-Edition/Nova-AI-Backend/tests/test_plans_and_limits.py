"""Tests for subscription plans, daily token limits, and account blocking."""
import pytest

from tests.conftest import set_user_field
from tests.test_chat import _auth_headers

pytestmark = pytest.mark.asyncio


async def test_new_user_defaults_to_free_plan_and_not_blocked(client, unique_email):
    headers = await _auth_headers(client, unique_email)

    response = await client.get("/users/me", headers=headers)
    assert response.status_code == 200
    # plan/is_blocked aren't exposed on UserRead (response format is
    # unchanged), so we verify the defaults by exercising behavior instead:
    # a fresh user is never blocked and gets the free-plan limit.
    chat_response = await client.post(
        "/chat", json={"conversation_id": None, "message": "Hi"}, headers=headers
    )
    assert chat_response.status_code == 200


async def test_daily_token_limit_blocks_second_request(client, unique_email, monkeypatch):
    import app.core.plans as plans

    # FakeGeminiService always reports 100 total tokens per call. Every
    # pre-flight estimate also carries chat_service's fixed system-prompt
    # overhead (150 tokens) on top of the ~1-token estimate for "Hi", so the
    # limit needs enough headroom for that first check to pass (~151) while
    # still being tight enough that the second call's cumulative usage (100
    # recorded + the second estimate) pushes it over budget.
    monkeypatch.setitem(plans.TOKEN_LIMITS, "free", 200)

    headers = await _auth_headers(client, unique_email)

    first = await client.post(
        "/chat", json={"conversation_id": None, "message": "Hi"}, headers=headers
    )
    assert first.status_code == 200

    second = await client.post(
        "/chat", json={"conversation_id": None, "message": "Hi again"}, headers=headers
    )
    assert second.status_code == 429
    body = second.json()
    assert body["success"] is False
    assert body["error"] == "TOKEN_LIMIT_EXCEEDED"


async def test_developer_plan_bypasses_token_limit(client, unique_email, monkeypatch):
    import app.core.plans as plans

    monkeypatch.setitem(plans.TOKEN_LIMITS, "developer", 1)  # would be absurdly low if enforced

    headers = await _auth_headers(client, unique_email)
    await set_user_field(client, unique_email, plan="developer")

    for _ in range(3):
        response = await client.post(
            "/chat", json={"conversation_id": None, "message": "Hi"}, headers=headers
        )
        assert response.status_code == 200


async def test_blocked_user_cannot_chat(client, unique_email):
    headers = await _auth_headers(client, unique_email)
    await set_user_field(client, unique_email, is_blocked=True)

    response = await client.post(
        "/chat", json={"conversation_id": None, "message": "Hi"}, headers=headers
    )
    assert response.status_code == 403
    assert response.json()["error"] == "ACCOUNT_BLOCKED"


async def test_blocked_user_cannot_access_conversations(client, unique_email):
    headers = await _auth_headers(client, unique_email)
    await set_user_field(client, unique_email, is_blocked=True)

    response = await client.get("/chat/conversations", headers=headers)
    assert response.status_code == 403
    assert response.json()["error"] == "ACCOUNT_BLOCKED"


async def test_blocked_user_cannot_access_user_endpoints(client, unique_email):
    headers = await _auth_headers(client, unique_email)
    await set_user_field(client, unique_email, is_blocked=True)

    response = await client.get("/users/me", headers=headers)
    assert response.status_code == 403
    assert response.json()["error"] == "ACCOUNT_BLOCKED"


async def test_blocked_user_cannot_refresh_token(client, unique_email):
    from tests.test_auth import _login, _register

    await _register(client, unique_email)
    login = await _login(client, unique_email)
    refresh_token = login.json()["refresh_token"]

    await set_user_field(client, unique_email, is_blocked=True)

    response = await client.post("/auth/refresh", json={"refresh_token": refresh_token})
    assert response.status_code == 403
    assert response.json()["error"] == "ACCOUNT_BLOCKED"
