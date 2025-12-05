from datetime import datetime, timedelta, timezone

from jose import JWTError as JoseJWTError
from jose import jwt

from ..config import settings


class JWTError(Exception):
    pass


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """Create JWT access token."""
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(days=settings.JWT_EXPIRE_DAYS)

    to_encode.update({
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "sub": str(data.get("tgid", "")),
        "aud": "lunch-bot-api",
        "iss": "lunch-bot-backend",
    })

    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt


def verify_token(token: str) -> dict:
    """
    Verify JWT token and return payload.
    Raises JWTError on invalid token.
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
            audience="lunch-bot-api",
            issuer="lunch-bot-backend",
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise JWTError("Token has expired")
    except JoseJWTError as e:
        raise JWTError(f"Invalid token: {e}")
