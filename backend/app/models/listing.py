"""
İlan modeli — Scraper'dan gelen ham veriler + AI skorları
TimescaleDB için ListingPriceHistory zaman serisi tablosu ayrılmıştır.
"""
import enum
import uuid
from sqlalchemy import (
    String, Boolean, DateTime, ForeignKey, Integer, Float,
    Text, Enum as SAEnum, JSON
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.core.database import Base


class ListingStatus(str, enum.Enum):
    ACTIVE = "active"
    DELETED = "deleted"     # Silindi ama hafızada
    SOLD = "sold"
    REPOSTED = "reposted"   # Silinip yeniden yüklendi


class ListingType(str, enum.Enum):
    SALE = "sale"
    RENT = "rent"


class PriceSignal(str, enum.Enum):
    GREEN = "green"     # Fırsat
    YELLOW = "yellow"   # Normal
    RED = "red"         # Şişirilmiş


class Listing(Base):
    __tablename__ = "listings"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("tenants.id"), index=True)
    property_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("properties.id"))  # Duplicate eşleştirme

    # Kaynak
    source_site: Mapped[str] = mapped_column(String(100))   # sahibinden, hepsiemlak, vb.
    source_id: Mapped[str] = mapped_column(String(200))      # Sitedeki ilanın ID'si
    source_url: Mapped[str] = mapped_column(String(1000))
    is_fsbo: Mapped[bool] = mapped_column(Boolean, default=False)  # Sahibinden mi?

    # Mülk Bilgileri
    title: Mapped[str] = mapped_column(String(500))
    description: Mapped[str | None] = mapped_column(Text)
    listing_type: Mapped[ListingType] = mapped_column(SAEnum(ListingType))
    price: Mapped[float] = mapped_column(Float)
    currency: Mapped[str] = mapped_column(String(10), default="TRY")
    area_m2: Mapped[float | None] = mapped_column(Float)
    room_count: Mapped[str | None] = mapped_column(String(20))  # 2+1, 3+1
    floor: Mapped[int | None] = mapped_column(Integer)
    total_floors: Mapped[int | None] = mapped_column(Integer)
    building_age: Mapped[int | None] = mapped_column(Integer)

    # Konum
    city: Mapped[str | None] = mapped_column(String(100))
    district: Mapped[str | None] = mapped_column(String(100))
    neighborhood: Mapped[str | None] = mapped_column(String(200))
    address_raw: Mapped[str | None] = mapped_column(String(500))
    latitude: Mapped[float | None] = mapped_column(Float)
    longitude: Mapped[float | None] = mapped_column(Float)

    # Durum
    status: Mapped[ListingStatus] = mapped_column(SAEnum(ListingStatus), default=ListingStatus.ACTIVE)
    days_on_market: Mapped[int] = mapped_column(Integer, default=0)       # Görünen DOM
    real_days_on_market: Mapped[int] = mapped_column(Integer, default=0)  # Gerçek DOM (yeniden yüklemeler dahil)
    last_price_before_delete: Mapped[float | None] = mapped_column(Float)

    # AI Skorları
    motivation_score: Mapped[int | None] = mapped_column(Integer)         # 1-100 satıcı panik puanı
    visual_premium_score: Mapped[float | None] = mapped_column(Float)     # Görsel şerefiye %
    photo_quality_score: Mapped[float | None] = mapped_column(Float)      # 0-1 fotoğraf kalitesi
    price_signal: Mapped[PriceSignal | None] = mapped_column(SAEnum(PriceSignal))
    is_hidden_gem: Mapped[bool] = mapped_column(Boolean, default=False)   # Gizli cevher mi?
    arv_estimate: Mapped[float | None] = mapped_column(Float)             # Tadilat sonrası değer
    roi_years: Mapped[float | None] = mapped_column(Float)                # Amortisman yılı

    # Ekstra Özellikler (JSON)
    features: Mapped[dict | None] = mapped_column(JSON)  # havuz, şömine, manzara, vb.

    # Hash (Duplicate tespiti)
    photo_hash: Mapped[str | None] = mapped_column(String(100))
    address_hash: Mapped[str | None] = mapped_column(String(100))

    first_seen_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    last_seen_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    deleted_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True))

    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="listings")
    price_history: Mapped[list["ListingPriceHistory"]] = relationship("ListingPriceHistory", back_populates="listing")
    photos: Mapped[list["ListingPhoto"]] = relationship("ListingPhoto", back_populates="listing")


class ListingPriceHistory(Base):
    """TimescaleDB hypertable — fiyat değişim logları."""
    __tablename__ = "listing_price_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    listing_id: Mapped[str] = mapped_column(String(36), ForeignKey("listings.id"), index=True)
    price: Mapped[float] = mapped_column(Float)
    recorded_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
    change_pct: Mapped[float | None] = mapped_column(Float)  # Önceki fiyata göre % değişim

    listing: Mapped["Listing"] = relationship("Listing", back_populates="price_history")


class ListingPhoto(Base):
    __tablename__ = "listing_photos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    listing_id: Mapped[str] = mapped_column(String(36), ForeignKey("listings.id"), index=True)
    url: Mapped[str] = mapped_column(String(1000))
    local_path: Mapped[str | None] = mapped_column(String(500))
    perceptual_hash: Mapped[str | None] = mapped_column(String(100))
    order_index: Mapped[int] = mapped_column(Integer, default=0)

    listing: Mapped["Listing"] = relationship("Listing", back_populates="photos")
