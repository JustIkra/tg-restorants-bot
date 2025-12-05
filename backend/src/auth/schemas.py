from pydantic import BaseModel


class TelegramAuthRequest(BaseModel):
    init_data: str
    office: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    tgid: int
    name: str
    office: str
    role: str
    is_active: bool

    model_config = {"from_attributes": True}


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
