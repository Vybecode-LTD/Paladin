import uuid
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field


class DemoRequestCreate(BaseModel):
    """max_length caps mirror the DemoRequest DB columns (models/demo_request.py)
    exactly, so an oversized value is always a clean 422 here, never a raw
    DB truncation error."""
    full_name: str = Field(max_length=200)
    company: str = Field(max_length=200)
    email: EmailStr = Field(max_length=320)
    phone: str = Field(default="", max_length=50)
    role: str = Field(default="", max_length=100)
    team_size: str = Field(default="", max_length=50)
    message: str = Field(default="", max_length=2000)


class DemoRequestUpdate(BaseModel):
    is_handled: bool


class DemoRequestOut(BaseModel):
    id: uuid.UUID
    full_name: str
    company: str
    email: EmailStr
    phone: str
    role: str
    team_size: str
    message: str
    is_handled: bool
    created_at: datetime

    class Config:
        from_attributes = True
