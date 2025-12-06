from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Cafe, CafeLinkRequest
from ..models.cafe import LinkRequestStatus

# Whitelist of fields that can be updated via repository
ALLOWED_UPDATE_FIELDS = {"status", "processed_at"}
ALLOWED_CAFE_TELEGRAM_FIELDS = {"tg_chat_id", "tg_username", "linked_at", "notifications_enabled"}


class CafeLinkRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_request(self, request_id: int) -> CafeLinkRequest | None:
        """Get a link request by ID."""
        result = await self.session.execute(
            select(CafeLinkRequest).where(CafeLinkRequest.id == request_id)
        )
        return result.scalar_one_or_none()

    async def list_requests(
        self,
        skip: int = 0,
        limit: int = 100,
        status: LinkRequestStatus | None = None,
    ) -> tuple[list[CafeLinkRequest], int]:
        """List link requests with pagination and optional status filter."""
        query = select(CafeLinkRequest)

        if status:
            query = query.where(CafeLinkRequest.status == status)

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.session.execute(count_query)
        total = total_result.scalar_one()

        # Get paginated results
        query = query.offset(skip).limit(limit).order_by(CafeLinkRequest.created_at.desc())
        result = await self.session.execute(query)
        items = list(result.scalars().all())

        return items, total

    async def create_request(
        self,
        cafe_id: int,
        tg_chat_id: int,
        tg_username: str | None = None,
    ) -> CafeLinkRequest:
        """Create a new link request."""
        request = CafeLinkRequest(
            cafe_id=cafe_id,
            tg_chat_id=tg_chat_id,
            tg_username=tg_username,
            status=LinkRequestStatus.PENDING,
        )
        self.session.add(request)
        await self.session.flush()
        return request

    async def update_request(self, request: CafeLinkRequest, **kwargs) -> CafeLinkRequest:
        """Update a link request."""
        for key, value in kwargs.items():
            if key not in ALLOWED_UPDATE_FIELDS:
                raise ValueError(f"Field '{key}' cannot be updated")
            setattr(request, key, value)
        await self.session.flush()
        return request

    async def get_cafe(self, cafe_id: int) -> Cafe | None:
        """Get a cafe by ID."""
        result = await self.session.execute(
            select(Cafe).where(Cafe.id == cafe_id)
        )
        return result.scalar_one_or_none()

    async def update_cafe_telegram(self, cafe: Cafe, **kwargs) -> Cafe:
        """Update cafe's Telegram-related fields."""
        for key, value in kwargs.items():
            if key not in ALLOWED_CAFE_TELEGRAM_FIELDS:
                raise ValueError(f"Field '{key}' cannot be updated")
            setattr(cafe, key, value)
        await self.session.flush()
        return cafe

    async def clear_cafe_link(self, cafe: Cafe) -> Cafe:
        """Clear Telegram link from cafe."""
        cafe.tg_chat_id = None
        cafe.tg_username = None
        cafe.linked_at = None
        cafe.notifications_enabled = True
        await self.session.flush()
        return cafe
