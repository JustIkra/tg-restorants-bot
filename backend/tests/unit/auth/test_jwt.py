"""Tests for JWT token creation and verification."""

import time
from datetime import timedelta

import pytest

from src.auth.jwt import JWTError, create_access_token, verify_token


def test_create_access_token_success():
    """Test JWT token is created with correct claims."""
    data = {"tgid": 123456789, "role": "user"}
    token = create_access_token(data)

    assert isinstance(token, str)
    assert len(token) > 0

    # Verify token contains expected claims
    payload = verify_token(token)
    assert payload["sub"] == "123456789"
    assert payload["tgid"] == 123456789
    assert payload["role"] == "user"
    assert payload["aud"] == "lunch-bot-api"
    assert payload["iss"] == "lunch-bot-backend"
    assert "exp" in payload
    assert "iat" in payload


def test_create_access_token_with_custom_expiration():
    """Test JWT token with custom expiration."""
    data = {"tgid": 123456789, "role": "user"}
    expires_delta = timedelta(seconds=10)
    token = create_access_token(data, expires_delta=expires_delta)

    payload = verify_token(token)
    # exp should be within 10 seconds from now
    current_time = int(time.time())
    assert payload["exp"] - current_time <= 10


def test_verify_token_success():
    """Test successful token verification."""
    data = {"tgid": 987654321, "role": "manager"}
    token = create_access_token(data)

    payload = verify_token(token)

    assert payload["tgid"] == 987654321
    assert payload["role"] == "manager"


def test_verify_token_expired():
    """Test verification fails for expired token."""
    data = {"tgid": 123456789, "role": "user"}
    # Create token that expires immediately
    token = create_access_token(data, expires_delta=timedelta(seconds=-1))

    with pytest.raises(JWTError, match="Token has expired"):
        verify_token(token)


def test_verify_token_invalid():
    """Test verification fails for invalid token."""
    invalid_token = "invalid.token.here"

    with pytest.raises(JWTError, match="Invalid token"):
        verify_token(invalid_token)


def test_verify_token_tampered():
    """Test verification fails for tampered token."""
    data = {"tgid": 123456789, "role": "user"}
    token = create_access_token(data)

    # Tamper with token
    parts = token.split(".")
    if len(parts) == 3:
        parts[1] = parts[1][::-1]  # Reverse middle part
        tampered_token = ".".join(parts)

        with pytest.raises(JWTError, match="Invalid token"):
            verify_token(tampered_token)


def test_token_contains_all_standard_claims():
    """Test token contains all required standard claims."""
    data = {"tgid": 123456789, "role": "user", "custom_field": "value"}
    token = create_access_token(data)

    payload = verify_token(token)

    # Standard claims
    assert "sub" in payload  # subject (tgid as string)
    assert "exp" in payload  # expiration
    assert "iat" in payload  # issued at
    assert "aud" in payload  # audience
    assert "iss" in payload  # issuer

    # Custom claims
    assert "tgid" in payload
    assert "role" in payload
    assert "custom_field" in payload


def test_multiple_tokens_independent():
    """Test that multiple tokens are independent."""
    user1_token = create_access_token({"tgid": 111, "role": "user"})
    user2_token = create_access_token({"tgid": 222, "role": "manager"})

    assert user1_token != user2_token

    payload1 = verify_token(user1_token)
    payload2 = verify_token(user2_token)

    assert payload1["tgid"] == 111
    assert payload1["role"] == "user"
    assert payload2["tgid"] == 222
    assert payload2["role"] == "manager"
