"""Internal API — Scraper'dan gelen ilan verilerini işle. Dış erişime kapalı."""
from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.models.listing import Listing, ListingPriceHistory, ListingPhoto, ListingStatus
from app.schemas.listing import ListingIngest

router = APIRouter(prefix="/internal", tags=["internal"])


def _verify_internal(request: Request):
    """Sadece Docker ağından erişime izin ver."""
    host = request.client.host if request.client else ""
    # Docker compose ağından gelen istekler
    if not host.startswith(("172.", "10.", "192.168.", "127.")):
        raise HTTPException(status_code=403, detail="Internal only")


@router.post("/listings/ingest")
async def ingest_listing(
    payload: ListingIngest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Scraper servisinden gelen yeni ilan verisi."""
    _verify_internal(request)

    # Daha önce var mı kontrol et
    q = await db.execute(
        select(Listing).where(
            Listing.source_site == payload.source_site,
            Listing.source_id == payload.source_id,
        )
    )
    existing = q.scalar_one_or_none()

    if existing:
        # Fiyat değişimi kontrolü
        if existing.price != payload.price:
            change_pct = ((payload.price - existing.price) / existing.price) * 100
            history = ListingPriceHistory(
                listing_id=existing.id,
                price=payload.price,
                change_pct=round(change_pct, 2),
            )
            db.add(history)
            existing.price = payload.price

        existing.days_on_market += 1
        if payload.is_repost:
            existing.status = ListingStatus.REPOSTED
            existing.real_days_on_market = payload.real_days_on_market

        await db.flush()
        return {"status": "updated", "listing_id": existing.id}

    # Yeni ilan oluştur
    # tenant_id'yi default tenant olarak ata (production'da yapılandırılır)
    listing = Listing(
        tenant_id="default",
        source_site=payload.source_site,
        source_id=payload.source_id,
        source_url=payload.source_url,
        title=payload.title,
        description=payload.description,
        listing_type=payload.listing_type,
        price=payload.price,
        currency=payload.currency,
        area_m2=payload.area_m2,
        room_count=payload.room_count,
        floor=payload.floor,
        total_floors=payload.total_floors,
        building_age=payload.building_age,
        city=payload.city or "Çanakkale",
        district=payload.district,
        neighborhood=payload.neighborhood,
        address_raw=payload.address_raw,
        latitude=payload.latitude,
        longitude=payload.longitude,
        is_fsbo=payload.is_fsbo,
        photo_hash=payload.photo_hash,
        address_hash=payload.address_hash,
        property_id=payload.property_id,
        real_days_on_market=payload.real_days_on_market,
    )

    if payload.is_repost:
        listing.status = ListingStatus.REPOSTED

    db.add(listing)
    await db.flush()
    await db.refresh(listing)

    # Fotoğrafları kaydet
    for i, url in enumerate(payload.photo_urls):
        photo = ListingPhoto(listing_id=listing.id, url=url, order_index=i)
        db.add(photo)

    # İlk fiyat kaydı
    db.add(ListingPriceHistory(listing_id=listing.id, price=payload.price))

    await db.flush()

    # AI görevlerini tetikle (async)
    from app.workers.tasks.scrape_tasks import process_new_listing
    process_new_listing.delay({
        "id": listing.id,
        "description": payload.description,
        "photo_urls": payload.photo_urls,
        "neighborhood": payload.neighborhood,
        "area_m2": payload.area_m2,
        "price": payload.price,
    })

    return {"status": "created", "listing_id": listing.id}
