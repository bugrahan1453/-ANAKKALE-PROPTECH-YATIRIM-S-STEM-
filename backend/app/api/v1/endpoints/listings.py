"""İlan API — Filtreleme, arama, radar uyarıları."""
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from typing import Optional

from app.core.database import get_db
from app.core.deps import get_current_user, require_broker
from app.models.listing import Listing, ListingStatus, PriceSignal
from app.models.user import User

router = APIRouter(prefix="/listings", tags=["listings"])


@router.get("/")
async def get_listings(
    district: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    rooms: Optional[str] = None,
    is_fsbo: Optional[bool] = None,
    price_signal: Optional[PriceSignal] = None,
    is_hidden_gem: Optional[bool] = None,
    status: Optional[ListingStatus] = ListingStatus.ACTIVE,
    min_motivation_score: Optional[int] = None,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    filters = [Listing.tenant_id == current_user.tenant_id]
    if status:
        filters.append(Listing.status == status)
    if district:
        filters.append(Listing.district == district)
    if min_price:
        filters.append(Listing.price >= min_price)
    if max_price:
        filters.append(Listing.price <= max_price)
    if rooms:
        filters.append(Listing.room_count == rooms)
    if is_fsbo is not None:
        filters.append(Listing.is_fsbo == is_fsbo)
    if price_signal:
        filters.append(Listing.price_signal == price_signal)
    if is_hidden_gem is not None:
        filters.append(Listing.is_hidden_gem == is_hidden_gem)
    if min_motivation_score:
        filters.append(Listing.motivation_score >= min_motivation_score)

    total_q = await db.execute(select(func.count()).select_from(Listing).where(and_(*filters)))
    total = total_q.scalar()

    q = await db.execute(
        select(Listing)
        .where(and_(*filters))
        .order_by(Listing.motivation_score.desc().nullslast(), Listing.first_seen_at.desc())
        .offset((page - 1) * size)
        .limit(size)
    )
    items = q.scalars().all()

    return {"total": total, "page": page, "size": size, "items": [_serialize(l) for l in items]}


@router.get("/radar/bloody-market")
async def bloody_market_radar(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_broker),
):
    """Garantili değerin %20 ve altına düşen ilanlar — Yalnızca Broker."""
    q = await db.execute(
        select(Listing).join(
            Listing.property
        ).where(
            and_(
                Listing.tenant_id == current_user.tenant_id,
                Listing.status == ListingStatus.ACTIVE,
            )
        )
    )
    # Gerçek filtreleme Property.guaranteed_value üzerinden servis katmanında yapılır
    listings = q.scalars().all()
    radar = [l for l in listings if _is_below_threshold(l, 0.20)]
    return {"count": len(radar), "items": [_serialize(l) for l in radar]}


@router.get("/{listing_id}")
async def get_listing(
    listing_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = await db.execute(
        select(Listing).where(
            Listing.id == listing_id,
            Listing.tenant_id == current_user.tenant_id,
        )
    )
    listing = q.scalar_one_or_none()
    if not listing:
        raise HTTPException(status_code=404, detail="İlan bulunamadı")
    return _serialize(listing)


def _is_below_threshold(listing: Listing, threshold: float) -> bool:
    if not listing.property or not listing.property.guaranteed_value:
        return False
    ratio = listing.price / listing.property.guaranteed_value
    return ratio <= (1 - threshold)


def _serialize(l: Listing) -> dict:
    return {
        "id": l.id,
        "title": l.title,
        "price": l.price,
        "area_m2": l.area_m2,
        "room_count": l.room_count,
        "district": l.district,
        "neighborhood": l.neighborhood,
        "source_site": l.source_site,
        "source_url": l.source_url,
        "is_fsbo": l.is_fsbo,
        "status": l.status,
        "days_on_market": l.days_on_market,
        "real_days_on_market": l.real_days_on_market,
        "motivation_score": l.motivation_score,
        "price_signal": l.price_signal,
        "is_hidden_gem": l.is_hidden_gem,
        "roi_years": l.roi_years,
        "first_seen_at": l.first_seen_at,
    }
