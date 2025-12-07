from datetime import datetime

from pydantic import BaseModel

from ..models.user import UserAccessRequestStatus


class UserAccessRequestSchema(BaseModel):
    """Schema for user access request response."""

    id: int
    tgid: int
    name: str
    office: str
    username: str | None
    status: UserAccessRequestStatus
    created_at: datetime
    processed_at: datetime | None

    model_config = {"from_attributes": True}


class UserAccessRequestListSchema(BaseModel):
    """Schema for paginated list of user access requests."""

    items: list[UserAccessRequestSchema]
    total: int
    skip: int
    limit: int
