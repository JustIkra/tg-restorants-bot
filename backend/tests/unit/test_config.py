"""Tests for configuration module."""

import os

import pytest
from pydantic import ValidationError


def test_config_telegram_mini_app_url_default():
    """Test TELEGRAM_MINI_APP_URL has correct default value."""
    from src.config import settings

    # Should have default value if not set in env
    assert settings.TELEGRAM_MINI_APP_URL == "http://localhost"


def test_config_backend_api_url_default():
    """Test BACKEND_API_URL has correct default for Docker."""
    from src.config import settings

    # Should use Docker hostname for inter-container communication
    assert settings.BACKEND_API_URL == "http://backend:8000/api/v1"


def test_config_cors_origins_default():
    """Test CORS_ORIGINS has correct default values."""
    from src.config import settings

    # Should have localhost as default
    assert "http://localhost:3000" in settings.CORS_ORIGINS


def test_config_jwt_secret_key_validation():
    """Test JWT_SECRET_KEY validation (minimum 32 characters)."""
    # Current test env has valid key (set in conftest.py)
    from src.config import settings

    assert len(settings.JWT_SECRET_KEY) >= 32


def test_config_jwt_secret_key_too_short():
    """Test JWT_SECRET_KEY validation fails for short keys."""
    # Save current env
    old_key = os.environ.get("JWT_SECRET_KEY")
    old_telegram_token = os.environ.get("TELEGRAM_BOT_TOKEN")

    try:
        # Set short key
        os.environ["JWT_SECRET_KEY"] = "short"
        os.environ["TELEGRAM_BOT_TOKEN"] = "test_token"

        # Force reload of settings module
        import importlib
        import src.config
        importlib.reload(src.config)

        # Should raise ValidationError
        pytest.fail("Expected ValidationError for short JWT_SECRET_KEY")

    except ValidationError as e:
        # Expected - validation should fail
        assert "JWT_SECRET_KEY must be at least 32 characters" in str(e)

    finally:
        # Restore env
        if old_key:
            os.environ["JWT_SECRET_KEY"] = old_key
        if old_telegram_token:
            os.environ["TELEGRAM_BOT_TOKEN"] = old_telegram_token

        # Reload config with correct env
        import importlib
        import src.config
        importlib.reload(src.config)


def test_config_gemini_keys_list_parsing():
    """Test gemini_keys_list property parses comma-separated keys."""
    from src.config import settings

    # Should parse comma-separated keys from env (set in conftest.py)
    keys = settings.gemini_keys_list

    assert isinstance(keys, list)
    assert len(keys) == 3
    assert "test_key_1" in keys
    assert "test_key_2" in keys
    assert "test_key_3" in keys


def test_config_gemini_model_default():
    """Test GEMINI_MODEL has correct default."""
    from src.config import settings

    assert settings.GEMINI_MODEL == "gemini-2.0-flash-exp"


def test_config_gemini_max_requests_default():
    """Test GEMINI_MAX_REQUESTS_PER_KEY has correct default."""
    from src.config import settings

    assert settings.GEMINI_MAX_REQUESTS_PER_KEY == 195
