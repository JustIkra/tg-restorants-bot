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
async def test_telegram_auth_success(client, db_session):
    """Test successful Telegram authentication."""
    user_data = {
        "id": 111222333,
        "first_name": "Alice",
        "last_name": "Smith",
        "username": "alicesmith",
        "language_code": "en",
    }

    init_data = generate_telegram_init_data(
        user_data, "test_bot_token_123456:ABCdefGHIjklMNOpqrsTUVwxyz"
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
        user_data, "test_bot_token_123456:ABCdefGHIjklMNOpqrsTUVwxyz"
    )

    response = await client.post(
        "/api/v1/auth/telegram",
        json={"init_data": init_data, "office": "Office A"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["user"]["tgid"] == test_user.tgid
