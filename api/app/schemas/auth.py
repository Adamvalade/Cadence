from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    username: str = Field(min_length=3, max_length=30, pattern=r"^[a-zA-Z0-9_]+$")
    password: str = Field(min_length=8, max_length=128)
    display_name: str = Field(default="", max_length=50)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str = Field(min_length=10, max_length=256)
    new_password: str = Field(min_length=8, max_length=128)


class MessageResponse(BaseModel):
    message: str


class AuthResponse(BaseModel):
    message: str
    user: "UserBrief"
    # Also returned for SPAs when the browser cannot send cross-site cookies (e.g. localhost → 127.0.0.1).
    access_token: str


class UserBrief(BaseModel):
    id: str
    email: str
    username: str
    display_name: str
    avatar_url: str | None = None

    model_config = {"from_attributes": True}
