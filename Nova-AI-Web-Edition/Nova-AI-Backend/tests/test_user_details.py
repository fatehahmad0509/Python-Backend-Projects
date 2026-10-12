"""Tests for the user details feature (info Nova uses to personalize replies)."""
import pytest

from tests.test_chat import _auth_headers

pytestmark = pytest.mark.asyncio


async def test_get_me_has_no_details_by_default(client, unique_email):
    headers = await _auth_headers(client, unique_email)

    response = await client.get("/users/me", headers=headers)
    assert response.status_code == 200
    assert response.json()["details"] is None


async def test_update_details_persists_and_is_returned(client, unique_email):
    headers = await _auth_headers(client, unique_email)

    update = await client.put(
        "/users/me/details",
        json={"details": "Adım Ahmet, 28 yaşındayım, İstanbul'da yaşıyorum."},
        headers=headers,
    )
    assert update.status_code == 200
    assert update.json()["details"] == "Adım Ahmet, 28 yaşındayım, İstanbul'da yaşıyorum."

    me = await client.get("/users/me", headers=headers)
    assert me.json()["details"] == "Adım Ahmet, 28 yaşındayım, İstanbul'da yaşıyorum."


async def test_details_are_sent_to_nova_on_chat(client, unique_email):
    headers = await _auth_headers(client, unique_email)
    await client.put("/users/me/details", json={"details": "Benim adım Ahmet."}, headers=headers)

    response = await client.post(
        "/chat", json={"conversation_id": None, "message": "Merhaba"}, headers=headers
    )
    assert response.status_code == 200
    assert "[knows: Benim adım Ahmet.]" in response.json()["assistant_message"]["content"]


async def test_clearing_details_with_empty_string(client, unique_email):
    headers = await _auth_headers(client, unique_email)
    await client.put("/users/me/details", json={"details": "Bir bilgi"}, headers=headers)

    clear = await client.put("/users/me/details", json={"details": ""}, headers=headers)
    assert clear.status_code == 200
    assert clear.json()["details"] is None


async def test_update_details_requires_auth(client):
    response = await client.put("/users/me/details", json={"details": "test"})
    assert response.status_code == 401
