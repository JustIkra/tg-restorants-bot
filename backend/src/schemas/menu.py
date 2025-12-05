from decimal import Decimal

from pydantic import BaseModel


# Combo schemas
class ComboBase(BaseModel):
    name: str
    categories: list[str]
    price: Decimal


class ComboCreate(ComboBase):
    pass


class ComboUpdate(BaseModel):
    name: str | None = None
    categories: list[str] | None = None
    price: Decimal | None = None
    is_available: bool | None = None


class ComboResponse(BaseModel):
    id: int
    cafe_id: int
    name: str
    categories: list[str]
    price: Decimal
    is_available: bool

    model_config = {"from_attributes": True}


# MenuItem schemas
class MenuItemBase(BaseModel):
    name: str
    description: str | None = None
    category: str
    price: Decimal | None = None


class MenuItemCreate(MenuItemBase):
    pass


class MenuItemUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    category: str | None = None
    price: Decimal | None = None
    is_available: bool | None = None


class MenuItemResponse(BaseModel):
    id: int
    cafe_id: int
    name: str
    description: str | None
    category: str
    price: Decimal | None
    is_available: bool

    model_config = {"from_attributes": True}
