"""
Pazarlama ve Rapor Üretimi
- "Gerçeklik Tokadı" Ekspertiz PDF
- Alıcı-Portföy Çöpçatanı
- Tek tıkla sosyal medya
"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from io import BytesIO

from app.core.database import get_db
from app.core.deps import get_current_user, require_broker_or_advisor
from app.models.listing import Listing, ListingPriceHistory
from app.models.customer import Customer
from app.models.user import User, UserRole
from app.core.security import decrypt_field

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/reality-slap/{listing_id}")
async def generate_reality_slap_pdf(
    listing_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_broker_or_advisor),
):
    """
    "Gerçeklik Tokadı" Ekspertiz PDF'i:
    - Silinen ilanlar ve son fiyatları
    - Mahallenin gerçek m2 fiyatı
    - Ortalama satış süresi
    """
    q = await db.execute(
        select(Listing).where(
            Listing.id == listing_id, Listing.tenant_id == current_user.tenant_id
        )
    )
    listing = q.scalar_one_or_none()
    if not listing:
        raise HTTPException(status_code=404, detail="İlan bulunamadı")

    # Fiyat geçmişi
    history_q = await db.execute(
        select(ListingPriceHistory).where(ListingPriceHistory.listing_id == listing_id)
        .order_by(ListingPriceHistory.recorded_at)
    )
    price_history = history_q.scalars().all()

    # Aynı mahalledeki kapanan ilanlar
    comps_q = await db.execute(
        select(Listing).where(
            and_(
                Listing.tenant_id == current_user.tenant_id,
                Listing.neighborhood == listing.neighborhood,
                Listing.status == "deleted",
                Listing.last_price_before_delete != None,
            )
        ).limit(10)
    )
    comps = comps_q.scalars().all()

    pdf_bytes = _build_reality_slap_pdf(listing, price_history, comps)

    return StreamingResponse(
        BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="ekspertiz_{listing_id}.pdf"'},
    )


@router.get("/buyer-match/{listing_id}")
async def find_matching_buyers(
    listing_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_broker_or_advisor),
):
    """
    Alıcı-Portföy Çöpçatanı:
    Yeni ilan → eski müşteri kayıtlarını tarayıp eşleşen müşterileri bul.
    """
    q = await db.execute(
        select(Listing).where(
            Listing.id == listing_id, Listing.tenant_id == current_user.tenant_id
        )
    )
    listing = q.scalar_one_or_none()
    if not listing:
        raise HTTPException(status_code=404, detail="İlan bulunamadı")

    # RBAC: Danışman sadece kendi müşterilerini
    filters = [Customer.tenant_id == current_user.tenant_id, Customer.is_active == True]
    if current_user.role == UserRole.ADVISOR:
        filters.append(Customer.assigned_advisor_id == current_user.id)

    cust_q = await db.execute(select(Customer).where(and_(*filters)))
    customers = cust_q.scalars().all()

    matches = []
    for c in customers:
        reasons = []
        # Bütçe kontrolü
        if c.budget_min and c.budget_max:
            if c.budget_min <= listing.price <= c.budget_max:
                reasons.append("Bütçe aralığına uyuyor")
        elif c.budget_max and listing.price <= c.budget_max:
            reasons.append("Bütçe limiti altında")

        # İlçe kontrolü
        if c.preferred_districts and listing.district:
            if listing.district.lower() in c.preferred_districts.lower():
                reasons.append(f"İstediği ilçe: {listing.district}")

        # Oda sayısı kontrolü
        if c.preferred_rooms and listing.room_count:
            if listing.room_count in c.preferred_rooms:
                reasons.append(f"İstediği oda: {listing.room_count}")

        if reasons:
            matches.append({
                "customer_id": c.id,
                "customer_name": decrypt_field(c.full_name_encrypted),
                "phone": decrypt_field(c.phone_encrypted),
                "match_reasons": reasons,
                "match_score": len(reasons),
            })

    matches.sort(key=lambda x: x["match_score"], reverse=True)
    return {
        "listing_title": listing.title,
        "matches_count": len(matches),
        "matches": matches[:20],
    }


@router.post("/social-media/{listing_id}")
async def generate_social_media_posts(
    listing_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_broker_or_advisor),
):
    """
    Tek Tıkla Sosyal Medya:
    Instagram Story, WhatsApp mesajı, cam afişi taslağı üretimi.
    """
    q = await db.execute(
        select(Listing).where(
            Listing.id == listing_id, Listing.tenant_id == current_user.tenant_id
        )
    )
    listing = q.scalar_one_or_none()
    if not listing:
        raise HTTPException(status_code=404, detail="İlan bulunamadı")

    price_formatted = f"{listing.price:,.0f}".replace(",", ".")
    area = listing.area_m2 or "?"

    instagram_caption = (
        f"🏠 {listing.district} / {listing.neighborhood}\n"
        f"📐 {area} m² · {listing.room_count or '?'}\n"
        f"💰 {price_formatted} TL\n\n"
        f"📞 Detay için DM veya arayın!\n"
        f"#çanakkale #emlak #satılık #proptech"
    )

    whatsapp_message = (
        f"🏠 *{listing.title}*\n\n"
        f"📍 {listing.district} - {listing.neighborhood}\n"
        f"📐 {area} m² | {listing.room_count or '-'}\n"
        f"💰 *{price_formatted} TL*\n\n"
        f"Detaylı bilgi ve randevu için bizimle iletişime geçin."
    )

    window_poster = {
        "title": listing.title,
        "location": f"{listing.district} / {listing.neighborhood}",
        "area": f"{area} m²",
        "rooms": listing.room_count or "-",
        "price": f"{price_formatted} TL",
        "qr_content": listing.source_url,
    }

    return {
        "instagram": {"caption": instagram_caption, "suggested_hashtags": "#çanakkale #emlak #yatırım"},
        "whatsapp": {"message": whatsapp_message},
        "window_poster": window_poster,
    }


def _build_reality_slap_pdf(listing, price_history, comps) -> bytes:
    """WeasyPrint veya ReportLab ile PDF oluştur."""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import cm
    from reportlab.pdfgen import canvas
    from reportlab.lib.colors import HexColor

    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    # Başlık
    c.setFillColor(HexColor("#1e40af"))
    c.rect(0, height - 3 * cm, width, 3 * cm, fill=1)
    c.setFillColor(HexColor("#ffffff"))
    c.setFont("Helvetica-Bold", 18)
    c.drawString(2 * cm, height - 2 * cm, "Piyasa Ekspertiz Raporu")
    c.setFont("Helvetica", 10)
    c.drawString(2 * cm, height - 2.6 * cm, "Canakkale PropTech Yatirim Sistemi")

    # İlan bilgileri
    y = height - 4.5 * cm
    c.setFillColor(HexColor("#111827"))
    c.setFont("Helvetica-Bold", 13)
    c.drawString(2 * cm, y, f"Ilan: {listing.title[:60]}")
    y -= 0.7 * cm
    c.setFont("Helvetica", 10)

    price_str = f"{listing.price:,.0f}".replace(",", ".")
    info_lines = [
        f"Fiyat: {price_str} TL",
        f"Konum: {listing.district or '-'} / {listing.neighborhood or '-'}",
        f"Alan: {listing.area_m2 or '-'} m2 | Oda: {listing.room_count or '-'}",
        f"Piyasada Gecen Sure: {listing.real_days_on_market} gun",
        f"Kaynak: {listing.source_site}",
    ]
    for line in info_lines:
        c.drawString(2 * cm, y, line)
        y -= 0.5 * cm

    # Fiyat geçmişi
    y -= 0.5 * cm
    c.setFont("Helvetica-Bold", 12)
    c.drawString(2 * cm, y, "Fiyat Gecmisi")
    y -= 0.5 * cm
    c.setFont("Helvetica", 9)
    for ph in price_history[:10]:
        ph_price = f"{ph.price:,.0f}".replace(",", ".")
        change = f" ({ph.change_pct:+.1f}%)" if ph.change_pct else ""
        c.drawString(2.5 * cm, y, f"{ph.recorded_at.strftime('%d.%m.%Y')}  -  {ph_price} TL{change}")
        y -= 0.4 * cm

    # Emsal kapanan ilanlar
    y -= 0.5 * cm
    c.setFont("Helvetica-Bold", 12)
    c.drawString(2 * cm, y, "Mahallede Kapanan Ilanlar (Emsal)")
    y -= 0.5 * cm
    c.setFont("Helvetica", 9)
    for comp in comps[:8]:
        comp_price = f"{comp.last_price_before_delete:,.0f}".replace(",", ".") if comp.last_price_before_delete else "?"
        c.drawString(2.5 * cm, y, f"{comp.title[:40]}  -  Son Fiyat: {comp_price} TL  -  {comp.days_on_market} gun")
        y -= 0.4 * cm

    # Alt bilgi
    c.setFont("Helvetica", 7)
    c.setFillColor(HexColor("#6b7280"))
    c.drawString(2 * cm, 1 * cm, "Bu rapor Canakkale PropTech AI sistemi tarafindan otomatik uretilmistir.")

    c.save()
    buffer.seek(0)
    return buffer.read()
