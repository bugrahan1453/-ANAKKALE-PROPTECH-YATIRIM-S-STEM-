"""CRM Müşteri modeli — KVKK uyumlu şifreli kişisel veriler."""
import uuid
from sqlalchemy import String, Boolean, DateTime, ForeignKey, Integer, Float, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Customer(Base):
    __tablename__ = "customers"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("tenants.id"), index=True)
    assigned_advisor_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"))

    # Kişisel veri — Fernet şifreli
    full_name_encrypted: Mapped[str] = mapped_column(String(500))
    phone_encrypted: Mapped[str] = mapped_column(String(500))
    email_encrypted: Mapped[str | None] = mapped_column(String(500))

    # Arama Kriterleri
    budget_min: Mapped[float | None] = mapped_column(Float)
    budget_max: Mapped[float | None] = mapped_column(Float)
    preferred_rooms: Mapped[str | None] = mapped_column(String(100))  # "2+1,3+1"
    preferred_districts: Mapped[str | None] = mapped_column(String(500))
    notes_encrypted: Mapped[str | None] = mapped_column(Text)  # Şifreli özel notlar

    # Eşleştirme
    matched_listing_ids: Mapped[list | None] = mapped_column(JSON)
    last_matched_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True))

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    last_contact_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True))

    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="customers")
