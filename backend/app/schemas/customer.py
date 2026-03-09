from pydantic import BaseModel
from datetime import datetime


class CustomerCreate(BaseModel):
    full_name: str
    phone: str
    email: str | None = None
    budget_min: float | None = None
    budget_max: float | None = None
    preferred_rooms: str | None = None
    preferred_districts: str | None = None
    notes: str | None = None


class CustomerUpdate(BaseModel):
    full_name: str | None = None
    phone: str | None = None
    email: str | None = None
    budget_min: float | None = None
    budget_max: float | None = None
    preferred_rooms: str | None = None
    preferred_districts: str | None = None
    notes: str | None = None


class CustomerOut(BaseModel):
    id: str
    full_name: str  # Çözümlenmiş (decrypted)
    phone: str      # Çözümlenmiş
    email: str | None = None
    budget_min: float | None = None
    budget_max: float | None = None
    preferred_rooms: str | None = None
    preferred_districts: str | None = None
    is_active: bool
    created_at: datetime | None = None
    last_contact_at: datetime | None = None
    matched_listing_ids: list[str] | None = None


class BuyerMatchOut(BaseModel):
    customer: CustomerOut
    listing_id: str
    listing_title: str
    match_reason: str
