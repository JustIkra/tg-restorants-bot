from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import UserAccessRequest
from ..models.user import UserAccessRequestStatus

# Whitelist of fields that can be updated via repository
ALLOWED_UPDATE_FIELDS = {"status", "processed_at"}


class UserRequestRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_request(self, request_id: int) -> UserAccessRequest | None:
        """Get a user access request by ID."""
        result = await self.session.execute(
            select(UserAccessRequest).where(UserAccessRequest.id == request_id)
        )
        return result.scalar_one_or_none()

    async def get_by_tgid(self, tgid: int) -> UserAccessRequest | None:
        """Get a user access request by Telegram ID."""
        result = await self.session.execute(
            select(UserAccessRequest).where(UserAccessRequest.tgid == tgid)
        )
        return result.scalar_one_or_none()

    async def list_requests(
        self,
        skip: int = 0,
        limit: int = 100,
        status: UserAccessRequestStatus | None = None,
    ) -> tuple[list[UserAccessRequest], int]:
        """List user access requests with pagination and optional status filter."""
        query = select(UserAccessRequest)

        if status:
            query = query.where(UserAccessRequest.status == status)

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.session.execute(count_query)
        total = total_result.scalar_one()

        # Get paginated results
        query = query.offset(skip).limit(limit).order_by(UserAccessRequest.created_at.desc())
        result = await self.session.execute(query)
        items = list(result.scalars().all())

        return items, total

    async def create_request(
        self,
        tgid: int,
        name: str,
        office: str,
        username: str | None = None,
    ) -> UserAccessRequest:
        """Create a new user access request."""
        request = UserAccessRequest(
            tgid=tgid,
            name=name,
            office=office,
            username=username,
            status=UserAccessRequestStatus.PENDING,
        )
        self.session.add(request)
        await self.session.flush()
        return request

    async def update_request(self, request: UserAccessRequest, **kwargs) -> UserAccessRequest:
        """Update a user access request."""
        for key, value in kwargs.items():
            if key not in ALLOWED_UPDATE_FIELDS:
                raise ValueError(f"Field '{key}' cannot be updated")
            setattr(request, key, value)
        await self.session.flush()
        return request
