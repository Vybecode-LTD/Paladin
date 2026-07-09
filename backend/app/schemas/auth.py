import uuid
from pydantic import BaseModel, EmailStr, Field
from app.models.user import UserRole

# Matches the login page's own minimum expectation and current industry
# baseline (NIST 800-63B: length over complexity rules). Not a full policy
# engine — just a floor against trivially-guessable passwords.
PASSWORD_MIN_LENGTH = 8


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=PASSWORD_MIN_LENGTH, max_length=128)
    full_name: str = Field(default="", max_length=200)
    role: UserRole = UserRole.author


class UserUpdate(BaseModel):
    role: UserRole | None = None
    is_active: bool | None = None


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(min_length=PASSWORD_MIN_LENGTH, max_length=128)


class ChangeEmailRequest(BaseModel):
    current_password: str
    new_email: EmailStr


class UserOut(BaseModel):
    id: uuid.UUID
    email: EmailStr
    full_name: str
    role: UserRole
    is_active: bool

    class Config:
        from_attributes = True


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserOut


class RefreshRequest(BaseModel):
    refresh_token: str
