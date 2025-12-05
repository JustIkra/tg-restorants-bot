from datetime import date, datetime, time, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..repositories.deadline import DeadlineRepository
from ..schemas.deadline import (
    AvailabilityResponse,
    DeadlineItem,
    DeadlineSchedule,
    DeadlineScheduleUpdate,
    WeekAvailabilityResponse,
)


class DeadlineService:
    def __init__(self, session: AsyncSession):
        self.repo = DeadlineRepository(session)

    async def get_schedule(self, cafe_id: int) -> DeadlineSchedule:
        deadlines = await self.repo.get_for_cafe(cafe_id)
        return DeadlineSchedule(
            cafe_id=cafe_id,
            schedule=[
                DeadlineItem(
                    weekday=d.weekday,
                    deadline_time=d.deadline_time,
                    is_enabled=d.is_enabled,
                    advance_days=d.advance_days,
                )
                for d in deadlines
            ],
        )

    async def update_schedule(
        self, cafe_id: int, data: DeadlineScheduleUpdate
    ) -> DeadlineSchedule:
        # Delete existing deadlines
        await self.repo.delete_for_cafe(cafe_id)

        # Create new deadlines
        items = [item.model_dump() for item in data.schedule]
        await self.repo.bulk_create(cafe_id, items)

        return await self.get_schedule(cafe_id)

    async def check_availability(
        self, cafe_id: int, order_date: date
    ) -> AvailabilityResponse:
        """
        Check if ordering is available for a specific date.

        Logic:
        1. Find deadline for order_date's weekday
        2. If not enabled, can't order
        3. Calculate actual deadline datetime considering advance_days
        4. Compare with current time
        """
        weekday = order_date.weekday()
        deadline = await self.repo.get_for_weekday(cafe_id, weekday)

        if not deadline:
            return AvailabilityResponse(
                date=order_date,
                can_order=False,
                reason="No delivery on this day",
            )

        if not deadline.is_enabled:
            return AvailabilityResponse(
                date=order_date,
                can_order=False,
                reason="Ordering disabled for this day",
            )

        # Parse deadline time
        hour, minute = map(int, deadline.deadline_time.split(":"))
        deadline_time = time(hour, minute)

        # Calculate deadline datetime
        # If advance_days > 0, deadline is advance_days before order_date
        deadline_date = order_date - timedelta(days=deadline.advance_days)
        deadline_dt = datetime.combine(deadline_date, deadline_time, tzinfo=timezone.utc)

        now = datetime.now(timezone.utc)

        if now > deadline_dt:
            return AvailabilityResponse(
                date=order_date,
                can_order=False,
                deadline=deadline_dt,
                reason="Deadline has passed",
            )

        return AvailabilityResponse(
            date=order_date,
            can_order=True,
            deadline=deadline_dt,
        )

    async def get_week_availability(self, cafe_id: int) -> WeekAvailabilityResponse:
        """Get availability for the next 7 days."""
        today = date.today()
        availability = []

        for i in range(7):
            day = today + timedelta(days=i)
            avail = await self.check_availability(cafe_id, day)
            availability.append(avail)

        return WeekAvailabilityResponse(
            cafe_id=cafe_id,
            availability=availability,
        )

    async def validate_order_deadline(self, cafe_id: int, order_date: date) -> None:
        """
        Validate that ordering is still possible.
        Raises HTTPException if deadline has passed.
        """
        avail = await self.check_availability(cafe_id, order_date)
        if not avail.can_order:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=avail.reason or "Cannot order for this date",
            )
