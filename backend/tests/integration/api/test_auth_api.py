"""Integration tests for Auth API."""

import hashlib
import hmac
import json
import time
from urllib.parse import urlencode

import pytest


def generate_telegram_init_data(user_data: dict, bot_token: str) -> str:
    """Generate valid Telegram WebApp initData."""
    auth_date = int(time.time())

    data = {
        "auth_date": str(auth_date),
        "user": json.dumps(user_data),
    }

    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(data.items()))

    secret_key = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    calculated_hash = hmac.new(
        secret_key, data_check_string.encode(), hashlib.sha256
    ).hexdigest()

    data["hash"] = calculated_hash
    return urlencode(data)


@pytest.mark.asyncio
async def test_telegram_auth_success(client, db_session, manager_auth_headers):
    """Test successful Telegram authentication for approved user."""
    # Manager creates user manually
    user_data_for_creation = {
        "tgid": 111222333,
        "name": "Alice Smith",
        "office": "Office B",
        "role": "user",
    }
    await client.post(
        "/api/v1/users",
        headers=manager_auth_headers,
        json=user_data_for_creation,
    )

    # Now user can authenticate via Telegram
    user_data = {
        "id": 111222333,
        "first_name": "Alice",
        "last_name": "Smith",
        "username": "alicesmith",
        "language_code": "en",
    }

    init_data = generate_telegram_init_data(
        user_data, "123456789:ABCdefGHIjklMNOpqrsTUVwxyz1234567890"
    )

    response = await client.post(
        "/api/v1/auth/telegram",
        json={"init_data": init_data, "office": "Office B"},
    )

    assert response.status_code == 200
    data = response.json()

    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert "user" in data
    assert data["user"]["tgid"] == 111222333
    assert data["user"]["name"] == "Alice Smith"
    assert data["user"]["office"] == "Office B"


@pytest.mark.asyncio
async def test_telegram_auth_invalid_hash(client):
    """Test authentication fails with invalid hash."""
    response = await client.post(
        "/api/v1/auth/telegram",
        json={
            "init_data": "hash=invalid&user={}&auth_date=123456",
            "office": "Office A",
        },
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_telegram_auth_existing_user(client, test_user):
    """Test authentication with existing user."""
    user_data = {
        "id": test_user.tgid,
        "first_name": "Test",
        "last_name": "User",
        "username": "testuser",
    }

    init_data = generate_telegram_init_data(
        user_data, "123456789:ABCdefGHIjklMNOpqrsTUVwxyz1234567890"
    )

    response = await client.post(
        "/api/v1/auth/telegram",
        json={"init_data": init_data, "office": "Office A"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["user"]["tgid"] == test_user.tgid


@pytest.mark.asyncio
async def test_new_user_creates_access_request(client):
    """Test POST /auth/telegram for new user creates access request and returns 403."""
    user_data = {
        "id": 444555666,
        "first_name": "New",
        "last_name": "User",
        "username": "newuser",
    }

    init_data = generate_telegram_init_data(
        user_data, "123456789:ABCdefGHIjklMNOpqrsTUVwxyz1234567890"
    )

    response = await client.post(
        "/api/v1/auth/telegram",
        json={"init_data": init_data, "office": "Office F"},
    )

    assert response.status_code == 403
    detail = response.json()["detail"].lower()
    assert "access request" in detail or "pending" in detail or "approval" in detail


@pytest.mark.asyncio
async def test_pending_user_gets_pending_message(client):
    """Test repeated auth for pending request returns 403 with pending message."""
    user_data = {
        "id": 333444555,
        "first_name": "Pending",
        "last_name": "User",
    }

    init_data = generate_telegram_init_data(
        user_data, "123456789:ABCdefGHIjklMNOpqrsTUVwxyz1234567890"
    )

    # First attempt creates request
    await client.post(
        "/api/v1/auth/telegram",
        json={"init_data": init_data, "office": "Office G"},
    )

    # Second attempt should still return pending
    response = await client.post(
        "/api/v1/auth/telegram",
        json={"init_data": init_data, "office": "Office G"},
    )

    assert response.status_code == 403
    detail = response.json()["detail"].lower()
    assert "pending" in detail


@pytest.mark.asyncio
async def test_rejected_user_gets_rejected_message(client, manager_auth_headers):
    """Test user with rejected request gets 403 with rejected message."""
    user_data = {
        "id": 222333444,
        "first_name": "Rejected",
        "last_name": "User",
    }

    init_data = generate_telegram_init_data(
        user_data, "123456789:ABCdefGHIjklMNOpqrsTUVwxyz1234567890"
    )

    # Create request
    await client.post(
        "/api/v1/auth/telegram",
        json={"init_data": init_data, "office": "Office H"},
    )

    # Get request ID and reject it
    response = await client.get("/api/v1/user-requests", headers=manager_auth_headers)
    requests = response.json()["items"]
    request_item = next(r for r in requests if r["tgid"] == 222333444)
    request_id = request_item["id"]

    await client.post(
        f"/api/v1/user-requests/{request_id}/reject",
        headers=manager_auth_headers,
    )

    # Try to auth
    response = await client.post(
        "/api/v1/auth/telegram",
        json={"init_data": init_data, "office": "Office H"},
    )

    assert response.status_code == 403
    detail = response.json()["detail"].lower()
    assert "rejected" in detail


@pytest.mark.asyncio
async def test_approved_user_can_authenticate(client, manager_auth_headers):
    """Test approved user can successfully authenticate."""
    user_data = {
        "id": 111222444,
        "first_name": "Approved",
        "last_name": "User",
    }

    init_data = generate_telegram_init_data(
        user_data, "123456789:ABCdefGHIjklMNOpqrsTUVwxyz1234567890"
    )

    # Create request
    await client.post(
        "/api/v1/auth/telegram",
        json={"init_data": init_data, "office": "Office I"},
    )

    # Get request ID and approve it
    response = await client.get("/api/v1/user-requests", headers=manager_auth_headers)
    requests = response.json()["items"]
    request_item = next(r for r in requests if r["tgid"] == 111222444)
    request_id = request_item["id"]

    await client.post(
        f"/api/v1/user-requests/{request_id}/approve",
        headers=manager_auth_headers,
    )

    # Now user can authenticate
    response = await client.post(
        "/api/v1/auth/telegram",
        json={"init_data": init_data, "office": "Office I"},
    )

    assert response.status_code == 200
    assert "access_token" in response.json()
