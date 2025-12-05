from decimal import Decimal

from pydantic import BaseModel


class UserBase(BaseModel):
    name: str
    office: str


class UserCreate(UserBase):
    tgid: int


class UserUpdate(BaseModel):
    name: str | None = None
    office: str | None = None


class UserResponse(BaseModel):
    tgid: int
    name: str
    office: str
    role: str
    is_active: bool
    weekly_limit: Decimal | None = None

    model_config = {"from_attributes": True}


class UserAccessUpdate(BaseModel):
    is_active: bool


class BalanceResponse(BaseModel):
    tgid: int
    weekly_limit: Decimal | None
    spent_this_week: Decimal
    remaining: Decimal | None


class BalanceLimitUpdate(BaseModel):
    weekly_limit: Decimal | None
