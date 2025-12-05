from pydantic import BaseModel


class CafeBase(BaseModel):
    name: str
    description: str | None = None


class CafeCreate(CafeBase):
    pass


class CafeUpdate(BaseModel):
    name: str | None = None
    description: str | None = None


class CafeResponse(BaseModel):
    id: int
    name: str
    description: str | None
    is_active: bool

    model_config = {"from_attributes": True}


class CafeStatusUpdate(BaseModel):
    is_active: bool
