from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.cafe import LinkRequestStatus
from ..repositories.cafe_link import CafeLinkRepository
from ..schemas.cafe_link import CreateLinkRequestSchema


class CafeLinkService:
    def __init__(self, session: AsyncSession):
        self.repo = CafeLinkRepository(session)

    async def create_link_request(self, cafe_id: int, data: CreateLinkRequestSchema):
        """Create a new cafe link request."""
        # Check if cafe exists
        cafe = await self.repo.get_cafe(cafe_id)
        if not cafe:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cafe not found",
            )

        # Check if cafe is already linked
        if cafe.tg_chat_id is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cafe is already linked to a Telegram account",
            )

        # Check if there's already a pending request for this cafe
        requests, _ = await self.repo.list_requests(status=LinkRequestStatus.PENDING)
        for req in requests:
            if req.cafe_id == cafe_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="There is already a pending request for this cafe",
                )

        return await self.repo.create_request(
            cafe_id=cafe_id,
            tg_chat_id=data.tg_chat_id,
            tg_username=data.tg_username,
        )

    async def list_requests(
        self,
        skip: int = 0,
        limit: int = 100,
        status: str | None = None,
    ):
        """List link requests with pagination."""
        items, total = await self.repo.list_requests(skip=skip, limit=limit, status=status)
        return {
            "items": items,
            "total": total,
            "skip": skip,
            "limit": limit,
        }

    async def get_request(self, request_id: int):
        """Get a link request by ID."""
        request = await self.repo.get_request(request_id)
        if not request:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Link request not found",
            )
        return request

    async def approve_request(self, request_id: int):
        """Approve a link request and update the cafe."""
        request = await self.get_request(request_id)

        if request.status != LinkRequestStatus.PENDING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Request is already {request.status}",
            )

        # Get the cafe
        cafe = await self.repo.get_cafe(request.cafe_id)
        if not cafe:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cafe not found",
            )

        # Check if cafe is already linked to another account
        if cafe.tg_chat_id is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cafe is already linked to a Telegram account",
            )

        # Update cafe with Telegram data
        await self.repo.update_cafe_telegram(
            cafe,
            tg_chat_id=request.tg_chat_id,
            tg_username=request.tg_username,
            linked_at=datetime.now(),
            notifications_enabled=True,
        )

        # Update request status
        await self.repo.update_request(
            request,
            status=LinkRequestStatus.APPROVED,
            processed_at=datetime.now(),
        )

        return request

    async def reject_request(self, request_id: int):
        """Reject a link request."""
        request = await self.get_request(request_id)

        if request.status != LinkRequestStatus.PENDING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Request is already {request.status}",
            )

        await self.repo.update_request(
            request,
            status=LinkRequestStatus.REJECTED,
            processed_at=datetime.now(),
        )

        return request

    async def update_notifications(self, cafe_id: int, enabled: bool):
        """Update notification settings for a cafe."""
        cafe = await self.repo.get_cafe(cafe_id)
        if not cafe:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cafe not found",
            )

        if cafe.tg_chat_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cafe is not linked to a Telegram account",
            )

        await self.repo.update_cafe_telegram(cafe, notifications_enabled=enabled)
        return cafe

    async def unlink_cafe(self, cafe_id: int):
        """Unlink Telegram from cafe."""
        cafe = await self.repo.get_cafe(cafe_id)
        if not cafe:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cafe not found",
            )

        if cafe.tg_chat_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cafe is not linked to a Telegram account",
            )

        await self.repo.clear_cafe_link(cafe)
        return cafe
