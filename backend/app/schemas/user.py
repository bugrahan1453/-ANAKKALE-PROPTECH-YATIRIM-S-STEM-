from pydantic import BaseModel, EmailStr
from datetime import datetime


class UserCreate(BaseModel):
    email: EmailStr
    full_name: str
    password: str
    phone: str | None = None
    role: str = "advisor"


class UserOut(BaseModel):
    id: str
    email: str
    full_name: str
    role: str
    is_active: bool
    created_at: datetime | None = None
    last_login: datetime | None = None

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    full_name: str | None = None
    email: EmailStr | None = None
    phone: str | None = None
    role: str | None = None
    is_active: bool | None = None


class TenantCreate(BaseModel):
    name: str
    slug: str
    plan: str = "starter"


class TenantOut(BaseModel):
    id: str
    name: str
    slug: str
    is_active: bool
    plan: str
    created_at: datetime | None = None

    class Config:
        from_attributes = True
