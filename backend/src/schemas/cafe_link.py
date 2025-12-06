from datetime import datetime

from pydantic import BaseModel

from ..models.cafe import LinkRequestStatus


class CreateLinkRequestSchema(BaseModel):
    """Schema for creating a cafe link request."""

    tg_chat_id: int
    tg_username: str | None = None


class LinkRequestSchema(BaseModel):
    """Schema for cafe link request response."""

    id: int
    cafe_id: int
    tg_chat_id: int
    tg_username: str | None
    status: LinkRequestStatus
    created_at: datetime
    processed_at: datetime | None

    model_config = {"from_attributes": True}


class LinkRequestListSchema(BaseModel):
    """Schema for paginated list of link requests."""

    items: list[LinkRequestSchema]
    total: int
    skip: int
    limit: int


class UpdateNotificationsSchema(BaseModel):
    """Schema for updating cafe notification settings."""

    enabled: bool
