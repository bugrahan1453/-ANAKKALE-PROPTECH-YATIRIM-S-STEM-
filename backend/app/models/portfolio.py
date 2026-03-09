"""Portföy — Danışmanın sorumlu olduğu ilanlar."""
import uuid
from sqlalchemy import String, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Portfolio(Base):
    __tablename__ = "portfolios"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("tenants.id"), index=True)
    advisor_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"))
    listing_id: Mapped[str] = mapped_column(String(36), ForeignKey("listings.id"))

    notes: Mapped[str | None] = mapped_column(Text)
    is_exclusive: Mapped[bool] = mapped_column(Boolean, default=False)  # Özel portföy
    assigned_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    advisor: Mapped["User"] = relationship("User", back_populates="portfolios")
