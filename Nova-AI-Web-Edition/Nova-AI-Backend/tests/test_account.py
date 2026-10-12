"""Tests for account deletion."""
import pytest

from tests.test_chat import _auth_headers

pytestmark = pytest.mark.asyncio


async def test_delete_me_wrong_password_unauthorized(client, unique_email):
    headers = await _auth_headers(client, unique_email)

    response = await client.request(
        "DELETE", "/users/me", json={"password": "WrongPassword"}, headers=headers
    )
    assert response.status_code == 401


async def test_delete_me_removes_account_and_data(client, unique_email):
    headers = await _auth_headers(client, unique_email)

    await client.post("/chat", json={"conversation_id": None, "message": "Hi"}, headers=headers)

    response = await client.request(
        "DELETE", "/users/me", json={"password": "SuperSecret123"}, headers=headers
    )
    assert response.status_code == 200
    assert response.json()["success"] is True

    me_response = await client.get("/users/me", headers=headers)
    assert me_response.status_code == 401

    register_response = await client.post(
        "/auth/register", json={"email": unique_email, "password": "AnotherPassword1"}
    )
    assert register_response.status_code == 201
