from datetime import date, datetime

from pydantic import BaseModel


class DeadlineItem(BaseModel):
    weekday: int  # 0-6 (Monday-Sunday)
    deadline_time: str  # "HH:MM"
    is_enabled: bool = True
    advance_days: int = 0


class DeadlineSchedule(BaseModel):
    cafe_id: int
    schedule: list[DeadlineItem]

    model_config = {"from_attributes": True}


class DeadlineScheduleUpdate(BaseModel):
    schedule: list[DeadlineItem]


class AvailabilityResponse(BaseModel):
    date: date
    can_order: bool
    deadline: datetime | None = None
    reason: str | None = None


class WeekAvailabilityResponse(BaseModel):
    cafe_id: int
    availability: list[AvailabilityResponse]
