from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth.dependencies import ManagerUser
from ..database import get_db
from ..models.cafe import LinkRequestStatus
from ..schemas.cafe import CafeResponse
from ..schemas.cafe_link import (
    CreateLinkRequestSchema,
    LinkRequestListSchema,
    LinkRequestSchema,
    UpdateNotificationsSchema,
)
from ..services.cafe_link import CafeLinkService

# Router for cafe-specific endpoints (with /cafes prefix)
cafe_links_router = APIRouter(prefix="/cafes", tags=["cafe-links"])

# Router for cafe-requests endpoints (no prefix, to get /api/v1/cafe-requests)
cafe_requests_router = APIRouter(tags=["cafe-requests"])


def get_cafe_link_service(db: Annotated[AsyncSession, Depends(get_db)]) -> CafeLinkService:
    return CafeLinkService(db)


@cafe_links_router.post("/{cafe_id}/link-request", response_model=LinkRequestSchema, status_code=201)
async def create_link_request(
    cafe_id: int,
    data: CreateLinkRequestSchema,
    service: Annotated[CafeLinkService, Depends(get_cafe_link_service)],
):
    """
    Create a cafe link request (public endpoint for Telegram bot).

    This endpoint is called by the Telegram bot when a cafe owner wants to
    link their Telegram account to receive notifications.
    """
    return await service.create_link_request(cafe_id, data)


@cafe_requests_router.get("/cafe-requests", response_model=LinkRequestListSchema)
async def list_cafe_requests(
    manager: ManagerUser,
    service: Annotated[CafeLinkService, Depends(get_cafe_link_service)],
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: LinkRequestStatus | None = Query(None),
):
    """
    List all cafe link requests (manager only).

    Supports pagination and filtering by status.
    """
    return await service.list_requests(skip=skip, limit=limit, status=status)


@cafe_requests_router.post("/cafe-requests/{request_id}/approve", response_model=LinkRequestSchema)
async def approve_cafe_request(
    request_id: int,
    manager: ManagerUser,
    service: Annotated[CafeLinkService, Depends(get_cafe_link_service)],
):
    """
    Approve a cafe link request (manager only).

    This will update the cafe with Telegram credentials from the request
    and mark the request as approved.
    """
    return await service.approve_request(request_id)


@cafe_requests_router.post("/cafe-requests/{request_id}/reject", response_model=LinkRequestSchema)
async def reject_cafe_request(
    request_id: int,
    manager: ManagerUser,
    service: Annotated[CafeLinkService, Depends(get_cafe_link_service)],
):
    """
    Reject a cafe link request (manager only).

    This will mark the request as rejected without updating the cafe.
    """
    return await service.reject_request(request_id)


@cafe_links_router.patch("/{cafe_id}/notifications", response_model=CafeResponse)
async def update_cafe_notifications(
    cafe_id: int,
    data: UpdateNotificationsSchema,
    manager: ManagerUser,
    service: Annotated[CafeLinkService, Depends(get_cafe_link_service)],
):
    """
    Enable or disable notifications for a cafe (manager only).

    The cafe must be linked to a Telegram account first.
    """
    return await service.update_notifications(cafe_id, data.enabled)


@cafe_links_router.delete("/{cafe_id}/link", response_model=CafeResponse)
async def unlink_cafe_telegram(
    cafe_id: int,
    manager: ManagerUser,
    service: Annotated[CafeLinkService, Depends(get_cafe_link_service)],
):
    """
    Unlink Telegram from a cafe (manager only).

    This will clear all Telegram-related fields from the cafe.
    """
    return await service.unlink_cafe(cafe_id)
