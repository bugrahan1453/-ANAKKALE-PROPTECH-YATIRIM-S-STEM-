from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ListingOut(BaseModel):
    id: str
    title: str
    price: float
    currency: str = "TRY"
    area_m2: float | None = None
    room_count: str | None = None
    floor: int | None = None
    total_floors: int | None = None
    building_age: int | None = None
    district: str | None = None
    neighborhood: str | None = None
    source_site: str
    source_url: str
    is_fsbo: bool
    status: str
    days_on_market: int
    real_days_on_market: int
    motivation_score: int | None = None
    visual_premium_score: float | None = None
    photo_quality_score: float | None = None
    price_signal: str | None = None
    is_hidden_gem: bool
    arv_estimate: float | None = None
    roi_years: float | None = None
    features: dict | None = None
    first_seen_at: datetime | None = None
    last_seen_at: datetime | None = None

    class Config:
        from_attributes = True


class ListingListResponse(BaseModel):
    total: int
    page: int
    size: int
    items: list[ListingOut]


class ListingIngest(BaseModel):
    """Scraper'dan gelen ham ilan verisi."""
    source_site: str
    source_id: str
    source_url: str
    title: str
    description: str | None = None
    listing_type: str = "sale"
    price: float
    currency: str = "TRY"
    area_m2: float | None = None
    room_count: str | None = None
    floor: int | None = None
    total_floors: int | None = None
    building_age: int | None = None
    city: str | None = None
    district: str | None = None
    neighborhood: str | None = None
    address_raw: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    is_fsbo: bool = False
    photo_urls: list[str] = []
    address_hash: str | None = None
    photo_hash: str | None = None
    property_id: str | None = None
    is_repost: bool = False
    real_days_on_market: int = 0


class PriceHistoryOut(BaseModel):
    price: float
    recorded_at: datetime
    change_pct: float | None = None

    class Config:
        from_attributes = True


class ARVResponse(BaseModel):
    listing_id: str
    current_price: float
    arv: float
    renovation_cost: float
    net_profit: float
    roi_pct: float


class ROIResponse(BaseModel):
    listing_id: str
    price: float
    monthly_rent: float
    annual_rent: float
    roi_years: float
    is_cash_cow: bool


class MacroAlertOut(BaseModel):
    alert_type: str
    message: str
    action: str
    created_at: datetime
