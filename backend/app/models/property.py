"""
Property — Duplicate ilanların altında birleştiği gerçek mülk kimliği.
Birden fazla Listing aynı Property'ye bağlanabilir.
"""
import uuid
from sqlalchemy import String, DateTime, Float, Text, Boolean, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Property(Base):
    __tablename__ = "properties"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    canonical_address: Mapped[str | None] = mapped_column(String(500))
    latitude: Mapped[float | None] = mapped_column(Float)
    longitude: Mapped[float | None] = mapped_column(Float)
    neighborhood: Mapped[str | None] = mapped_column(String(200))
    district: Mapped[str | None] = mapped_column(String(100))

    # SİT / İmar durumu (TKGM API'den)
    sit_degree: Mapped[str | None] = mapped_column(String(50))   # "1. Derece", "2. Derece", None
    zoning_status: Mapped[str | None] = mapped_column(String(200))  # İmarsız, Tarım, Konut, vb.
    is_olive_grove: Mapped[bool] = mapped_column(Boolean, default=False)
    legal_notes: Mapped[str | None] = mapped_column(Text)

    # Piyasa istatistikleri
    avg_sale_price_per_m2: Mapped[float | None] = mapped_column(Float)
    avg_sale_days: Mapped[float | None] = mapped_column(Float)  # O mahallede ort. satış süresi
    guaranteed_value: Mapped[float | None] = mapped_column(Float)  # Ekspertiz/garantili değer

    extra_data: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
