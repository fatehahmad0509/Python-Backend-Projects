"""Tests for the GET /users/me/usage endpoint (today's token/search usage + limits)."""
import pytest

from tests.conftest import set_user_field
from tests.test_chat import _auth_headers

pytestmark = pytest.mark.asyncio


async def test_usage_defaults_to_zero_for_fresh_user(client, unique_email):
    headers = await _auth_headers(client, unique_email)

    response = await client.get("/users/me/usage", headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert body["plan"] == "free"
    assert body["tokens_used_today"] == 0
    assert body["token_limit"] == 30_000
    assert body["searches_used_today"] == 0
    assert body["search_limit"] == 1


async def test_usage_reflects_recorded_chat_activity(client, unique_email):
    headers = await _auth_headers(client, unique_email)

    await client.post("/chat", json={"conversation_id": None, "message": "Hi"}, headers=headers)

    response = await client.get("/users/me/usage", headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert body["tokens_used_today"] > 0


async def test_usage_limits_scale_with_plan(client, unique_email):
    headers = await _auth_headers(client, unique_email)
    await set_user_field(client, unique_email, plan="pro")

    response = await client.get("/users/me/usage", headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert body["plan"] == "pro"
    assert body["token_limit"] == 120_000
    assert body["search_limit"] == 20


async def test_usage_is_unlimited_for_developer_plan(client, unique_email):
    headers = await _auth_headers(client, unique_email)
    await set_user_field(client, unique_email, plan="developer")

    response = await client.get("/users/me/usage", headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert body["token_limit"] is None
    assert body["search_limit"] is None


async def test_usage_requires_auth(client):
    response = await client.get("/users/me/usage")
    assert response.status_code == 401
