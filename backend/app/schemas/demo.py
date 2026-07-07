import uuid
from datetime import datetime
from pydantic import BaseModel, EmailStr


class DemoRequestCreate(BaseModel):
    full_name: str
    company: str
    email: EmailStr
    phone: str = ""
    role: str = ""
    team_size: str = ""
    message: str = ""


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
