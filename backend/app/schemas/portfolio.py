from pydantic import BaseModel
from datetime import datetime


class PortfolioCreate(BaseModel):
    listing_id: str
    advisor_id: str
    notes: str | None = None
    is_exclusive: bool = False


class PortfolioOut(BaseModel):
    id: str
    listing_id: str
    advisor_id: str
    advisor_name: str | None = None
    notes: str | None = None
    is_exclusive: bool
    assigned_at: datetime | None = None

    class Config:
        from_attributes = True


class PortfolioReassign(BaseModel):
    new_advisor_id: str
