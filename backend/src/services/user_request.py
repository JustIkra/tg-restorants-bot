from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import User
from ..models.user import UserAccessRequestStatus
from ..repositories.user_request import UserRequestRepository


class UserRequestService:
    def __init__(self, session: AsyncSession):
        self.repo = UserRequestRepository(session)
        self.session = session

    async def list_requests(
        self,
        skip: int = 0,
        limit: int = 100,
        status: UserAccessRequestStatus | None = None,
    ):
        """List user access requests with pagination."""
        items, total = await self.repo.list_requests(skip=skip, limit=limit, status=status)
        return {
            "items": items,
            "total": total,
            "skip": skip,
            "limit": limit,
        }

    async def get_request(self, request_id: int):
        """Get a user access request by ID."""
        request = await self.repo.get_request(request_id)
        if not request:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Access request not found",
            )
        return request

    async def approve_request(self, request_id: int):
        """Approve a user access request and create the user."""
        request = await self.get_request(request_id)

        if request.status != UserAccessRequestStatus.PENDING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Request is already {request.status}",
            )

        # Create user with data from request
        user = User(
            tgid=request.tgid,
            name=request.name,
            office=request.office,
            role="user",
            is_active=True,
        )
        self.session.add(user)

        # Update request status
        await self.repo.update_request(
            request,
            status=UserAccessRequestStatus.APPROVED,
            processed_at=datetime.now(),
        )

        return request

    async def reject_request(self, request_id: int):
        """Reject a user access request."""
        request = await self.get_request(request_id)

        if request.status != UserAccessRequestStatus.PENDING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Request is already {request.status}",
            )

        await self.repo.update_request(
            request,
            status=UserAccessRequestStatus.REJECTED,
            processed_at=datetime.now(),
        )

        return request
