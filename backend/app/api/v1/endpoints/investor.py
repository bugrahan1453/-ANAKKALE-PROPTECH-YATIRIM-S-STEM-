"""
Broker & Yatırımcı Otopilotu (Private Equity Module)
ARV, ROI, kiralıktan satılığa, makro tetikleyiciler.
Sadece Broker rolü erişebilir.
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.core.database import get_db
from app.core.deps import require_broker
from app.models.listing import Listing, ListingStatus, ListingType
from app.models.property import Property
from app.models.user import User
from app.schemas.listing import ARVResponse, ROIResponse, MacroAlertOut

router = APIRouter(prefix="/investor", tags=["investor"])

# ─── Çanakkale yerel veriler (production'da DB'den gelir) ─────
RENOVATION_COST_PER_M2 = 8_000  # TL
DISTRICT_RENOVATED_AVG = {
    "Kepez": 35_000, "Barbaros": 40_000, "Güzelyalı": 45_000,
    "Çanakkale Merkez": 38_000, "Çan": 25_000, "Biga": 22_000,
}
DAILY_AIRBNB_RATES = {
    "Kepez": 1_500, "Barbaros": 2_000, "Güzelyalı": 2_200,
    "Çanakkale Merkez": 1_800, "Çan": 800, "Biga": 700,
}
STUDENT_MONTHLY_RENT = {
    "Kepez": 8_000, "Barbaros": 10_000, "Güzelyalı": 12_000,
    "Çanakkale Merkez": 9_000,
}


@router.get("/arv/{listing_id}", response_model=ARVResponse)
async def calculate_arv(
    listing_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_broker),
):
    """ARV (After Repair Value) — Tadilat sonrası net kar hesabı."""
    q = await db.execute(
        select(Listing).where(
            Listing.id == listing_id, Listing.tenant_id == current_user.tenant_id
        )
    )
    listing = q.scalar_one_or_none()
    if not listing:
        return ARVResponse(listing_id=listing_id, current_price=0, arv=0, renovation_cost=0, net_profit=0, roi_pct=0)

    area = listing.area_m2 or 100
    district = listing.district or "Çanakkale Merkez"
    renovated_avg = DISTRICT_RENOVATED_AVG.get(district, 30_000)

    arv = area * renovated_avg
    renovation_cost = area * RENOVATION_COST_PER_M2
    net_profit = arv - listing.price - renovation_cost
    total_investment = listing.price + renovation_cost
    roi_pct = (net_profit / total_investment) * 100 if total_investment > 0 else 0

    return ARVResponse(
        listing_id=listing_id,
        current_price=listing.price,
        arv=arv,
        renovation_cost=renovation_cost,
        net_profit=net_profit,
        roi_pct=round(roi_pct, 1),
    )


@router.get("/roi/{listing_id}", response_model=ROIResponse)
async def calculate_roi(
    listing_id: str,
    rental_type: str = Query("student", enum=["student", "airbnb"]),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_broker),
):
    """Kısa Dönem ROI / Amortisman Arbitrajı — Cash-cow tespiti."""
    q = await db.execute(
        select(Listing).where(
            Listing.id == listing_id, Listing.tenant_id == current_user.tenant_id
        )
    )
    listing = q.scalar_one_or_none()
    if not listing:
        return ROIResponse(listing_id=listing_id, price=0, monthly_rent=0, annual_rent=0, roi_years=99, is_cash_cow=False)

    district = listing.district or "Çanakkale Merkez"

    if rental_type == "airbnb":
        daily_rate = DAILY_AIRBNB_RATES.get(district, 1_000)
        # Yıllık %60 doluluk oranı (Çanakkale turizm + öğrenci)
        annual_rent = daily_rate * 365 * 0.60
        monthly_rent = annual_rent / 12
    else:
        monthly_rent = STUDENT_MONTHLY_RENT.get(district, 8_000)
        annual_rent = monthly_rent * 12

    roi_years = listing.price / annual_rent if annual_rent > 0 else 99
    is_cash_cow = roi_years <= 15  # 15 yıldan kısa amortisman

    return ROIResponse(
        listing_id=listing_id,
        price=listing.price,
        monthly_rent=round(monthly_rent),
        annual_rent=round(annual_rent),
        roi_years=round(roi_years, 1),
        is_cash_cow=is_cash_cow,
    )


@router.get("/cash-cows")
async def list_cash_cows(
    max_roi_years: float = Query(15.0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_broker),
):
    """ROI ≤ 15 yıl olan "Nakit İneği" mülkler."""
    q = await db.execute(
        select(Listing).where(
            and_(
                Listing.tenant_id == current_user.tenant_id,
                Listing.status == ListingStatus.ACTIVE,
                Listing.listing_type == ListingType.SALE,
                Listing.roi_years != None,
                Listing.roi_years <= max_roi_years,
            )
        ).order_by(Listing.roi_years.asc()).limit(50)
    )
    return q.scalars().all()


@router.get("/rental-to-sale")
async def rental_to_sale_opportunities(
    min_days_vacant: int = Query(45),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_broker),
):
    """45+ gündür kiracısız mülkler — satışa dönüştürme fırsatları."""
    q = await db.execute(
        select(Listing).where(
            and_(
                Listing.tenant_id == current_user.tenant_id,
                Listing.listing_type == ListingType.RENT,
                Listing.status == ListingStatus.ACTIVE,
                Listing.days_on_market >= min_days_vacant,
            )
        ).order_by(Listing.days_on_market.desc()).limit(50)
    )
    listings = q.scalars().all()
    return {
        "count": len(listings),
        "message": f"{len(listings)} mülk {min_days_vacant}+ gündür kiracısını bulamıyor",
        "items": listings,
    }


@router.get("/macro-alerts", response_model=list[MacroAlertOut])
async def get_macro_alerts(
    current_user: User = Depends(require_broker),
):
    """
    Makro tetikleyiciler — Faiz değişimleri, piyasa alarmları.
    Production'da TCMB API'den çekilir.
    """
    from datetime import datetime, timezone
    # Placeholder — gerçekte scheduled task ile güncellenir
    return [
        MacroAlertOut(
            alert_type="interest_rate",
            message="TCMB politika faizi %5 düştü — konut kredisi ucuzlayacak",
            action="3 Milyon TL altı 2+1 evleri hemen ara, piyasa hızlanacak",
            created_at=datetime.now(timezone.utc),
        ),
    ]
