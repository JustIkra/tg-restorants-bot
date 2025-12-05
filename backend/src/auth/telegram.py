import hashlib
import hmac
import json
import time
from urllib.parse import parse_qsl


class TelegramAuthError(Exception):
    pass


def validate_telegram_init_data(init_data: str, bot_token: str) -> dict:
    """
    Validate Telegram WebApp initData and extract user info.

    Algorithm:
    1. Parse init_data as query string
    2. Extract hash
    3. Create data_check_string (sorted key=value pairs except hash)
    4. Generate secret_key = HMAC-SHA256("WebAppData", bot_token)
    5. Compute check_hash = HMAC-SHA256(secret_key, data_check_string)
    6. Compare hashes

    Returns dict with user info on success.
    Raises TelegramAuthError on failure.
    """
    try:
        parsed = dict(parse_qsl(init_data, keep_blank_values=True))
    except Exception as e:
        raise TelegramAuthError(f"Failed to parse init_data: {e}")

    if "hash" not in parsed:
        raise TelegramAuthError("Missing hash in init_data")

    # Validate auth_date expiration
    auth_date_str = parsed.get("auth_date", "0")
    try:
        auth_date = int(auth_date_str)
    except ValueError:
        raise TelegramAuthError("Invalid auth_date")

    current_time = int(time.time())
    if current_time - auth_date > 86400:  # 24 hours
        raise TelegramAuthError("Authentication data expired")

    received_hash = parsed.pop("hash")

    # Create data check string (sorted key=value pairs)
    data_check_string = "\n".join(
        f"{k}={v}" for k, v in sorted(parsed.items())
    )

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

    if not hmac.compare_digest(calculated_hash, received_hash):
        raise TelegramAuthError("Invalid hash")

    # Extract user info
    if "user" not in parsed:
        raise TelegramAuthError("Missing user in init_data")

    try:
        user_data = json.loads(parsed["user"])
    except json.JSONDecodeError as e:
        raise TelegramAuthError(f"Invalid user JSON: {e}")

    # Validate user ID
    user_id = user_data.get("id")
    if not isinstance(user_id, int) or user_id <= 0:
        raise TelegramAuthError("Invalid user ID")

    return {
        "id": user_id,
        "first_name": user_data.get("first_name", ""),
        "last_name": user_data.get("last_name", ""),
        "username": user_data.get("username", ""),
        "language_code": user_data.get("language_code", "en"),
    }
