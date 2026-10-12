"""Tests for registration, login, refresh, and logout."""
import pytest

pytestmark = pytest.mark.asyncio


async def _register(client, email, password="SuperSecret123"):
    return await client.post("/auth/register", json={"email": email, "password": password})


async def _login(client, email, password="SuperSecret123"):
    return await client.post("/auth/login", json={"email": email, "password": password})


async def test_register_creates_user(client, unique_email):
    response = await _register(client, unique_email)
    assert response.status_code == 201
    assert response.json()["email"] == unique_email.lower()


async def test_register_duplicate_email_conflicts(client, unique_email):
    payload = {"email": unique_email, "password": "SuperSecret123"}
    await _register(client, unique_email)

    second = await client.post("/auth/register", json=payload)
    assert second.status_code == 409


async def test_login_issues_tokens(client, unique_email):
    await _register(client, unique_email)

    response = await _login(client, unique_email)
    assert response.status_code == 200
    body = response.json()
    assert body["access_token"]
    assert body["refresh_token"]


async def test_login_wrong_password_unauthorized(client, unique_email):
    await _register(client, unique_email)

    response = await client.post("/auth/login", json={"email": unique_email, "password": "WrongPassword"})
    assert response.status_code == 401


async def test_refresh_returns_new_access_token(client, unique_email):
    await _register(client, unique_email)
    login = await _login(client, unique_email)
    refresh_token = login.json()["refresh_token"]

    response = await client.post("/auth/refresh", json={"refresh_token": refresh_token})
    assert response.status_code == 200
    assert response.json()["access_token"]


async def test_logout_revokes_refresh_token(client, unique_email):
    await _register(client, unique_email)
    login = await _login(client, unique_email)
    refresh_token = login.json()["refresh_token"]

    logout_response = await client.post("/auth/logout", json={"refresh_token": refresh_token})
    assert logout_response.status_code == 204

    refresh_response = await client.post("/auth/refresh", json={"refresh_token": refresh_token})
    assert refresh_response.status_code == 401


async def test_get_me_requires_auth(client):
    response = await client.get("/users/me")
    assert response.status_code == 401


async def test_get_me_returns_profile(client, unique_email):
    await _register(client, unique_email)
    login = await _login(client, unique_email)
    access_token = login.json()["access_token"]

    response = await client.get("/users/me", headers={"Authorization": f"Bearer {access_token}"})
    assert response.status_code == 200
    assert response.json()["email"] == unique_email.lower()
