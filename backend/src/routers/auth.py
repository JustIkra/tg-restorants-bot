from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth.jwt import create_access_token
from ..auth.schemas import AuthResponse, TelegramAuthRequest, UserResponse
from ..auth.telegram import TelegramAuthError, validate_telegram_init_data
from ..config import settings
from ..database import get_db
from ..models import User

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/telegram", response_model=AuthResponse)
async def authenticate_telegram(
    request: TelegramAuthRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AuthResponse:
    """
    Authenticate user via Telegram WebApp initData.

    - Validates initData using HMAC-SHA256
    - Creates or updates user in database
    - Returns JWT access token
    """
    # Validate Telegram initData
    try:
        tg_user = validate_telegram_init_data(
            request.init_data,
            settings.TELEGRAM_BOT_TOKEN
        )
    except TelegramAuthError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Telegram authentication failed: {e}",
        )

    tgid = tg_user["id"]
    if not tgid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Telegram user data",
        )

    # Find or create user
    result = await db.execute(select(User).where(User.tgid == tgid))
    user = result.scalar_one_or_none()

    name = f"{tg_user['first_name']} {tg_user.get('last_name', '')}".strip()

    if user is None:
        # Create new user
        user = User(
            tgid=tgid,
            name=name or f"User {tgid}",
            office=request.office,
            role="user",
            is_active=True,
        )
        db.add(user)
        await db.flush()
    else:
        # Update name if changed
        if name and user.name != name:
            user.name = name
        # Update office if changed
        if request.office and user.office != request.office:
            user.office = request.office

    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is deactivated",
        )

    # Create JWT token
    access_token = create_access_token(
        data={"tgid": user.tgid, "role": user.role}
    )

    return AuthResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.model_validate(user),
    )
