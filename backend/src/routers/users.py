from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth.dependencies import CurrentUser, ManagerUser
from ..database import get_db
from ..schemas.user import (
    BalanceLimitUpdate,
    BalanceResponse,
    UserAccessUpdate,
    UserCreate,
    UserResponse,
    UserUpdate,
)
from ..services.user import UserService

router = APIRouter(prefix="/users", tags=["users"])


def get_user_service(db: Annotated[AsyncSession, Depends(get_db)]) -> UserService:
    return UserService(db)


@router.get("", response_model=list[UserResponse])
async def list_users(
    manager: ManagerUser,
    service: Annotated[UserService, Depends(get_user_service)],
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: str | None = None,
    role: str | None = None,
):
    """List all users (manager only)."""
    return await service.list_users(skip=skip, limit=limit, search=search, role=role)


@router.post("", response_model=UserResponse, status_code=201)
async def create_user(
    data: UserCreate,
    manager: ManagerUser,
    service: Annotated[UserService, Depends(get_user_service)],
):
    """Create a new user (manager only)."""
    return await service.create_user(data, role="user")


@router.post("/managers", response_model=UserResponse, status_code=201)
async def create_manager(
    data: UserCreate,
    manager: ManagerUser,
    service: Annotated[UserService, Depends(get_user_service)],
):
    """Create a new manager (manager only)."""
    return await service.create_user(data, role="manager")


@router.get("/{tgid}", response_model=UserResponse)
async def get_user(
    tgid: int,
    current_user: CurrentUser,
    service: Annotated[UserService, Depends(get_user_service)],
):
    """Get user by tgid (self or manager)."""
    if current_user.role != "manager" and current_user.tgid != tgid:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )
    return await service.get_user(tgid)


@router.patch("/{tgid}", response_model=UserResponse)
async def update_user(
    tgid: int,
    data: UserUpdate,
    manager: ManagerUser,
    service: Annotated[UserService, Depends(get_user_service)],
):
    """Update user (name, office, role) (manager only)."""
    return await service.update_user(tgid, data)


@router.delete("/{tgid}", status_code=204)
async def delete_user(
    tgid: int,
    manager: ManagerUser,
    service: Annotated[UserService, Depends(get_user_service)],
):
    """Delete user (manager only)."""
    await service.delete_user(tgid)


@router.patch("/{tgid}/access", response_model=UserResponse)
async def update_user_access(
    tgid: int,
    data: UserAccessUpdate,
    manager: ManagerUser,
    service: Annotated[UserService, Depends(get_user_service)],
):
    """Enable/disable user access (manager only)."""
    return await service.update_access(tgid, data.is_active)


@router.get("/{tgid}/balance", response_model=BalanceResponse)
async def get_user_balance(
    tgid: int,
    current_user: CurrentUser,
    service: Annotated[UserService, Depends(get_user_service)],
):
    """Get user balance (self or manager)."""
    if current_user.role != "manager" and current_user.tgid != tgid:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )
    return await service.get_balance(tgid)


@router.patch("/{tgid}/balance/limit", response_model=UserResponse)
async def update_balance_limit(
    tgid: int,
    data: BalanceLimitUpdate,
    manager: ManagerUser,
    service: Annotated[UserService, Depends(get_user_service)],
):
    """Set weekly balance limit (manager only)."""
    return await service.update_balance_limit(tgid, data.weekly_limit)
