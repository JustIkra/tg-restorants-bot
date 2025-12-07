from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth.dependencies import ManagerUser
from ..database import get_db
from ..models.user import UserAccessRequestStatus
from ..schemas.user_request import UserAccessRequestListSchema, UserAccessRequestSchema
from ..services.user_request import UserRequestService

router = APIRouter(prefix="/user-requests", tags=["user-requests"])


def get_user_request_service(db: Annotated[AsyncSession, Depends(get_db)]) -> UserRequestService:
    return UserRequestService(db)


@router.get("", response_model=UserAccessRequestListSchema)
async def list_user_requests(
    manager: ManagerUser,
    service: Annotated[UserRequestService, Depends(get_user_request_service)],
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: UserAccessRequestStatus | None = Query(None),
):
    """
    List all user access requests (manager only).

    Supports pagination and filtering by status.
    """
    return await service.list_requests(skip=skip, limit=limit, status=status)


@router.post("/{request_id}/approve", response_model=UserAccessRequestSchema)
async def approve_user_request(
    request_id: int,
    manager: ManagerUser,
    service: Annotated[UserRequestService, Depends(get_user_request_service)],
):
    """
    Approve a user access request (manager only).

    This will create a new user with data from the request
    and mark the request as approved.
    """
    return await service.approve_request(request_id)


@router.post("/{request_id}/reject", response_model=UserAccessRequestSchema)
async def reject_user_request(
    request_id: int,
    manager: ManagerUser,
    service: Annotated[UserRequestService, Depends(get_user_request_service)],
):
    """
    Reject a user access request (manager only).

    This will mark the request as rejected without creating a user.
    """
    return await service.reject_request(request_id)
