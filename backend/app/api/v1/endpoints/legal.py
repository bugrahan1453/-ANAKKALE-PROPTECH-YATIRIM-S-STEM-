"""
Hukuki Kalkan — İmar ve SİT Dedektifi
TKGM Parsel API + Çanakkale Belediyesi entegrasyonu.
"""
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.config import settings
from app.models.listing import Listing
from app.models.property import Property
from app.models.user import User

router = APIRouter(prefix="/legal", tags=["legal"])
logger = logging.getLogger(__name__)


@router.get("/check/{listing_id}")
async def check_legal_status(
    listing_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    İlan adresindeki arazinin hukuki durumunu kontrol et:
    - 1./2./3. Derece SİT alanı mı?
    - Zeytinlik mi?
    - İmarsız tarım arazisi mi?
    - İmar planı durumu
    """
    q = await db.execute(
        select(Listing).where(
            Listing.id == listing_id, Listing.tenant_id == current_user.tenant_id
        )
    )
    listing = q.scalar_one_or_none()
    if not listing:
        raise HTTPException(status_code=404, detail="İlan bulunamadı")

    # Property kaydını kontrol et veya oluştur
    property_data = None
    if listing.property_id:
        prop_q = await db.execute(select(Property).where(Property.id == listing.property_id))
        property_data = prop_q.scalar_one_or_none()

    # TKGM ve belediye API kontrolü
    tkgm_result = await _check_tkgm(listing.latitude, listing.longitude, listing.address_raw)
    zoning_result = await _check_zoning(listing.district, listing.address_raw)

    # Property kaydını güncelle
    if property_data:
        property_data.sit_degree = tkgm_result.get("sit_degree")
        property_data.zoning_status = zoning_result.get("zoning_status")
        property_data.is_olive_grove = tkgm_result.get("is_olive_grove", False)
        property_data.legal_notes = tkgm_result.get("notes", "")
        await db.flush()

    warnings = []
    risk_level = "low"

    if tkgm_result.get("sit_degree"):
        degree = tkgm_result["sit_degree"]
        warnings.append(f"⚠️ {degree} SİT alanında — yapılaşma kısıtlaması var")
        risk_level = "high" if "1." in degree else "medium"

    if tkgm_result.get("is_olive_grove"):
        warnings.append("⚠️ Zeytinlik alanı — 3573 Sayılı Kanun kapsamında yapılaşma yasağı")
        risk_level = "high"

    if zoning_result.get("is_agricultural"):
        warnings.append("⚠️ İmarsız tarım arazisi — konut yapılamaz")
        risk_level = "high"

    if not warnings:
        warnings.append("✅ Bilinen hukuki risk tespit edilmedi")

    return {
        "listing_id": listing_id,
        "address": listing.address_raw,
        "risk_level": risk_level,
        "warnings": warnings,
        "tkgm_data": tkgm_result,
        "zoning_data": zoning_result,
    }


async def _check_tkgm(lat: float | None, lng: float | None, address: str | None) -> dict:
    """TKGM Parsel Sorgulama API."""
    import httpx

    if not settings.TKGM_API_KEY:
        return {
            "sit_degree": None,
            "is_olive_grove": False,
            "notes": "TKGM API key yapılandırılmamış — manuel kontrol gerekli",
            "parcel_id": None,
        }

    try:
        async with httpx.AsyncClient() as client:
            # TKGM API endpoint (gerçek endpoint ile değiştirilmeli)
            response = await client.get(
                "https://cbsservis.tkgm.gov.tr/megsiswebapi.v2/api/parselsorgu",
                params={"lat": lat, "lon": lng},
                headers={"Authorization": f"Bearer {settings.TKGM_API_KEY}"},
                timeout=15,
            )
        if response.status_code == 200:
            data = response.json()
            return {
                "sit_degree": data.get("sitDerece"),
                "is_olive_grove": data.get("zeytinlik", False),
                "parcel_id": data.get("parselNo"),
                "notes": data.get("aciklama", ""),
            }
    except Exception as e:
        logger.error(f"TKGM API hatası: {e}")

    return {"sit_degree": None, "is_olive_grove": False, "notes": "API bağlantı hatası"}


async def _check_zoning(district: str | None, address: str | None) -> dict:
    """Çanakkale Belediyesi imar durumu sorgulaması."""
    # Production'da belediye API'sine bağlanır
    # Şimdilik bilinen zeytinlik/tarım alanları listesi
    agricultural_areas = [
        "Kumkale", "Ayvacık", "Bayramiç", "Ezine",
    ]

    is_agricultural = False
    if district and district in agricultural_areas:
        is_agricultural = True

    return {
        "zoning_status": "tarım arazisi" if is_agricultural else "konut imarlı",
        "is_agricultural": is_agricultural,
        "district": district,
    }
