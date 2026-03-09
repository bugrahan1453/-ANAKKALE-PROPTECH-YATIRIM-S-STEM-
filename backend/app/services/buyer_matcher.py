"""Alıcı-Portföy Çöpçatanı — Müşteri kriterleriyle ilan eşleştirme."""
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.models.listing import Listing, ListingStatus
from app.models.customer import Customer
from app.core.security import decrypt_field

logger = logging.getLogger(__name__)


async def match_listing_to_buyers(
    listing: Listing, tenant_id: str, db: AsyncSession
) -> list[dict]:
    """Yeni ilan → mevcut müşterilerle eşleştir."""
    q = await db.execute(
        select(Customer).where(
            and_(
                Customer.tenant_id == tenant_id,
                Customer.is_active == True,
            )
        )
    )
    customers = q.scalars().all()
    matches = []

    for c in customers:
        score = 0
        reasons = []

        # Bütçe kontrolü
        if c.budget_min and c.budget_max:
            if c.budget_min <= listing.price <= c.budget_max:
                score += 3
                reasons.append("Bütçe aralığına uyuyor")
        elif c.budget_max and listing.price <= c.budget_max:
            score += 2
            reasons.append("Bütçe limiti altında")

        # İlçe kontrolü
        if c.preferred_districts and listing.district:
            districts = [d.strip().lower() for d in c.preferred_districts.split(",")]
            if listing.district.lower() in districts:
                score += 3
                reasons.append(f"İstediği ilçe: {listing.district}")

        # Oda sayısı
        if c.preferred_rooms and listing.room_count:
            rooms = [r.strip() for r in c.preferred_rooms.split(",")]
            if listing.room_count in rooms:
                score += 2
                reasons.append(f"İstediği oda: {listing.room_count}")

        if score >= 3:
            matches.append({
                "customer_id": c.id,
                "customer_name": decrypt_field(c.full_name_encrypted),
                "score": score,
                "reasons": reasons,
                "advisor_id": c.assigned_advisor_id,
            })

    matches.sort(key=lambda x: x["score"], reverse=True)
    return matches[:20]


async def match_all_new_listings(tenant_id: str, db: AsyncSession) -> int:
    """Tüm yeni ilanları mevcut müşterilerle eşleştir (saatlik görev)."""
    q = await db.execute(
        select(Listing).where(
            and_(
                Listing.tenant_id == tenant_id,
                Listing.status == ListingStatus.ACTIVE,
            )
        ).order_by(Listing.first_seen_at.desc()).limit(50)
    )
    new_listings = q.scalars().all()
    total_matches = 0

    for listing in new_listings:
        matches = await match_listing_to_buyers(listing, tenant_id, db)
        total_matches += len(matches)

    logger.info(f"Toplam {total_matches} alıcı-ilan eşleşmesi bulundu")
    return total_matches
