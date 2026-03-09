"""Makro Tetikleyiciler — TCMB faiz takibi, piyasa alarmları."""
from app.workers.celery_app import celery_app
from app.workers.tasks.notification_tasks import send_broker_sms
import httpx
import json
import logging
from datetime import datetime, timezone, timedelta

logger = logging.getLogger(__name__)

# TCMB EVDS API — Konut kredi faiz serisi (TP.KK.D2.Y.S.TR.TRY.A)
TCMB_EVDS_URL = (
    "https://evds2.tcmb.gov.tr/service/evds/"
    "series=TP.KK.D2.Y.S.TR.TRY.A"
    "&startDate={start}&endDate={end}"
    "&type=json"
)
# Son okunan faiz oranı Redis'te saklanır; yoksa basit dosya cache kullanılır
_RATE_CACHE_KEY = "macro:last_interest_rate"


def _get_cached_rate() -> float | None:
    try:
        import redis
        from app.core.config import settings
        r = redis.from_url(settings.REDIS_URL, decode_responses=True)
        val = r.get(_RATE_CACHE_KEY)
        return float(val) if val else None
    except Exception:
        return None


def _save_cached_rate(rate: float):
    try:
        import redis
        from app.core.config import settings
        r = redis.from_url(settings.REDIS_URL, decode_responses=True)
        r.set(_RATE_CACHE_KEY, str(rate), ex=86400 * 7)
    except Exception:
        pass


def _get_sync_session():
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from app.core.config import settings
    sync_url = settings.DATABASE_URL.replace("+asyncpg", "")
    engine = create_engine(sync_url)
    return sessionmaker(bind=engine)()


@celery_app.task(name="app.workers.tasks.macro_tasks.check_interest_rate")
def check_interest_rate():
    """
    Konut kredi faizini TCMB EVDS'den çek.
    %1+ düşüşte broker'larına alarm SMS gönder.
    """
    from app.core.config import settings
    from app.models.user import User, UserRole
    from app.models.tenant import Tenant
    from sqlalchemy import select

    try:
        today = datetime.now(timezone.utc)
        start = (today - timedelta(days=60)).strftime("%d-%m-%Y")
        end = today.strftime("%d-%m-%Y")

        headers = {}
        if settings.TKGM_API_KEY:  # EVDS aynı API key'i kullanabilir
            headers["key"] = settings.TKGM_API_KEY

        url = TCMB_EVDS_URL.format(start=start, end=end)
        response = httpx.get(url, headers=headers, timeout=20)

        current_rate = None
        if response.status_code == 200:
            data = response.json()
            items = data.get("items", [])
            # En son değeri al
            for item in reversed(items):
                val = item.get("TP_KK_D2_Y_S_TR_TRY_A")
                if val and val != "":
                    try:
                        current_rate = float(str(val).replace(",", "."))
                        break
                    except ValueError:
                        continue

        if current_rate is None:
            logger.warning("TCMB EVDS: faiz oranı parse edilemedi")
            return

        previous_rate = _get_cached_rate()
        _save_cached_rate(current_rate)

        logger.info(f"Konut kredi faizi: %{current_rate:.2f} (önceki: %{previous_rate})")

        if previous_rate and (previous_rate - current_rate) >= 1.0:
            drop = previous_rate - current_rate
            msg = (
                f"FAİZ DÜŞTÜ! Konut kredisi: %{previous_rate:.1f} → %{current_rate:.1f} "
                f"({drop:.1f} puan düşüş). 3M altı 2+1 evleri hemen ara — piyasa hızlanacak!"
            )
            session = _get_sync_session()
            try:
                tenants = session.execute(select(Tenant).where(Tenant.is_active == True)).scalars().all()
                for tenant in tenants:
                    brokers = session.execute(
                        select(User).where(User.tenant_id == tenant.id, User.role == UserRole.BROKER)
                    ).scalars().all()
                    for broker in brokers:
                        send_broker_sms.delay(msg)
                        logger.info(f"Faiz alarm SMS gönderildi: tenant={tenant.id}")
            finally:
                session.close()

    except Exception as e:
        logger.error(f"Makro tetikleyici hatası: {e}")


@celery_app.task(name="app.workers.tasks.macro_tasks.check_price_drops")
def check_price_drops():
    """
    Son 24 saatte %5+ fiyat düşüren ilanları tespit et.
    Broker'a toplu SMS raporu gönder.
    """
    from app.models.listing import Listing, ListingStatus
    from app.models.listing import ListingPriceHistory
    from app.models.user import User, UserRole
    from app.models.tenant import Tenant
    from sqlalchemy import select, and_
    from sqlalchemy.orm import joinedload

    logger.info("Fiyat düşüşü analizi çalışıyor...")

    session = _get_sync_session()
    try:
        cutoff = datetime.now(timezone.utc) - timedelta(hours=24)

        # Son 24 saatte kayıt edilen fiyat geçmişlerini çek
        price_histories = session.execute(
            select(ListingPriceHistory)
            .where(ListingPriceHistory.recorded_at >= cutoff)
            .order_by(ListingPriceHistory.recorded_at.desc())
        ).scalars().all()

        # change_pct <= -5 olanlar → %5+ düşüş
        drops_by_tenant: dict[str, list[str]] = {}
        seen_listings: set[str] = set()

        for ph in price_histories:
            lid = ph.listing_id
            if lid in seen_listings:
                continue
            seen_listings.add(lid)

            if ph.change_pct is not None and ph.change_pct <= -5:
                listing = session.get(Listing, lid)
                if listing and listing.status == ListingStatus.ACTIVE:
                    tid = listing.tenant_id
                    if tid not in drops_by_tenant:
                        drops_by_tenant[tid] = []
                    drops_by_tenant[tid].append(
                        f"{listing.title[:40]} — %{abs(ph.change_pct):.0f} düştü ({int(listing.price/1000)}K)"
                    )

        if not drops_by_tenant:
            logger.info("Son 24 saatte %5+ fiyat düşüşü yok")
            return

        # Her tenant broker'ına rapor SMS gönder
        tenants = session.execute(select(Tenant).where(Tenant.is_active == True)).scalars().all()
        for tenant in tenants:
            drops = drops_by_tenant.get(tenant.id, [])
            if not drops:
                continue

            brokers = session.execute(
                select(User).where(User.tenant_id == tenant.id, User.role == UserRole.BROKER)
            ).scalars().all()

            msg = f"FİYAT DÜŞÜŞ RADARI ({len(drops)} ilan):\n" + "\n".join(drops[:5])
            if len(drops) > 5:
                msg += f"\n...ve {len(drops)-5} ilan daha"

            for broker in brokers:
                send_broker_sms.delay(msg)

        logger.info(f"Fiyat düşüş raporu gönderildi: {sum(len(v) for v in drops_by_tenant.values())} ilan")

    except Exception as e:
        logger.error(f"Fiyat düşüş analizi hatası: {e}")
    finally:
        session.close()
