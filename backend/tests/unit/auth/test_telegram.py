"""Tests for Telegram authentication."""

import hashlib
import hmac
import json
import time
from urllib.parse import urlencode

import pytest

from src.auth.telegram import TelegramAuthError, validate_telegram_init_data

BOT_TOKEN = "test_bot_token_123456:ABCdefGHIjklMNOpqrsTUVwxyz"


def generate_valid_init_data(user_data: dict, bot_token: str) -> str:
    """
    Generate valid Telegram WebApp initData for testing.

    Algorithm (same as validate_telegram_init_data):
    1. Create data dict with user and auth_date
    2. Create data_check_string (sorted key=value pairs)
    3. Generate secret_key = HMAC-SHA256("WebAppData", bot_token)
    4. Compute hash = HMAC-SHA256(secret_key, data_check_string)
    5. Add hash to data dict
    6. Return as query string
    """
    auth_date = int(time.time())

    # Create data dict
    data = {
        "auth_date": str(auth_date),
        "user": json.dumps(user_data),
    }

    # Create data_check_string (sorted key=value pairs, excluding hash)
    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(data.items()))

    # Generate secret key
    secret_key = hmac.new(
        b"WebAppData",
        bot_token.encode(),
        hashlib.sha256
    ).digest()

    # Calculate hash
    calculated_hash = hmac.new(
        secret_key,
        data_check_string.encode(),
        hashlib.sha256
    ).hexdigest()

    # Add hash to data
    data["hash"] = calculated_hash

    # Return as query string
    return urlencode(data)


def test_validate_telegram_init_data_success():
    """Test successful validation of Telegram initData."""
    user_data = {
        "id": 123456789,
        "first_name": "John",
        "last_name": "Doe",
        "username": "johndoe",
        "language_code": "en",
    }

    init_data = generate_valid_init_data(user_data, BOT_TOKEN)
    result = validate_telegram_init_data(init_data, BOT_TOKEN)

    assert result["id"] == 123456789
    assert result["first_name"] == "John"
    assert result["last_name"] == "Doe"
    assert result["username"] == "johndoe"
    assert result["language_code"] == "en"


def test_validate_telegram_init_data_invalid_hash():
    """Test validation fails with invalid hash."""
    user_data = {
        "id": 123456789,
        "first_name": "John",
    }

    init_data = generate_valid_init_data(user_data, BOT_TOKEN)
    # Tamper with hash
    init_data = init_data.replace("hash=", "hash=invalid")

    with pytest.raises(TelegramAuthError, match="Invalid hash"):
        validate_telegram_init_data(init_data, BOT_TOKEN)


def test_validate_telegram_init_data_expired():
    """Test validation fails with expired auth_date."""
    user_data = {
        "id": 123456789,
        "first_name": "John",
    }

    # Generate init_data with old auth_date
    auth_date = int(time.time()) - 86401  # 1 day + 1 second ago

    data = {
        "auth_date": str(auth_date),
        "user": json.dumps(user_data),
    }

    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(data.items()))

    secret_key = hmac.new(
        b"WebAppData",
        BOT_TOKEN.encode(),
        hashlib.sha256
    ).digest()

    calculated_hash = hmac.new(
        secret_key,
        data_check_string.encode(),
        hashlib.sha256
    ).hexdigest()

    data["hash"] = calculated_hash
    init_data = urlencode(data)

    with pytest.raises(TelegramAuthError, match="Authentication data expired"):
        validate_telegram_init_data(init_data, BOT_TOKEN)


def test_validate_telegram_init_data_missing_hash():
    """Test validation fails when hash is missing."""
    user_data = {
        "id": 123456789,
        "first_name": "John",
    }

    data = {
        "auth_date": str(int(time.time())),
        "user": json.dumps(user_data),
    }

    init_data = urlencode(data)

    with pytest.raises(TelegramAuthError, match="Missing hash in init_data"):
        validate_telegram_init_data(init_data, BOT_TOKEN)


def test_validate_telegram_init_data_missing_user():
    """Test validation fails when user is missing."""
    auth_date = int(time.time())

    data = {
        "auth_date": str(auth_date),
    }

    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(data.items()))

    secret_key = hmac.new(
        b"WebAppData",
        BOT_TOKEN.encode(),
        hashlib.sha256
    ).digest()

    calculated_hash = hmac.new(
        secret_key,
        data_check_string.encode(),
        hashlib.sha256
    ).hexdigest()

    data["hash"] = calculated_hash
    init_data = urlencode(data)

    with pytest.raises(TelegramAuthError, match="Missing user in init_data"):
        validate_telegram_init_data(init_data, BOT_TOKEN)


def test_validate_telegram_init_data_invalid_user_json():
    """Test validation fails when user JSON is invalid."""
    auth_date = int(time.time())

    data = {
        "auth_date": str(auth_date),
        "user": "invalid json",
    }

    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(data.items()))

    secret_key = hmac.new(
        b"WebAppData",
        BOT_TOKEN.encode(),
        hashlib.sha256
    ).digest()

    calculated_hash = hmac.new(
        secret_key,
        data_check_string.encode(),
        hashlib.sha256
    ).hexdigest()

    data["hash"] = calculated_hash
    init_data = urlencode(data)

    with pytest.raises(TelegramAuthError, match="Invalid user JSON"):
        validate_telegram_init_data(init_data, BOT_TOKEN)


def test_validate_telegram_init_data_invalid_user_id():
    """Test validation fails when user ID is invalid."""
    user_data = {
        "id": -1,  # Invalid ID
        "first_name": "John",
    }

    init_data = generate_valid_init_data(user_data, BOT_TOKEN)

    with pytest.raises(TelegramAuthError, match="Invalid user ID"):
        validate_telegram_init_data(init_data, BOT_TOKEN)


def test_validate_telegram_init_data_optional_fields():
    """Test validation works with minimal user data."""
    user_data = {
        "id": 123456789,
        # only required field
    }

    init_data = generate_valid_init_data(user_data, BOT_TOKEN)
    result = validate_telegram_init_data(init_data, BOT_TOKEN)

    assert result["id"] == 123456789
    assert result["first_name"] == ""
    assert result["last_name"] == ""
    assert result["username"] == ""
    assert result["language_code"] == "en"
