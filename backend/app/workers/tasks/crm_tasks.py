"""CRM Görevleri — Günlük görev üretimi, alıcı-portföy eşleştirme, komşu radar."""
from app.workers.celery_app import celery_app
from app.services.script_generator import generate_script
import logging
import uuid
from datetime import datetime, timezone, date

logger = logging.getLogger(__name__)


def _get_sync_session():
    """Celery sync worker'lar için senkron DB bağlantısı."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from app.core.config import settings
    # asyncpg → psycopg2 dönüştür
    sync_url = settings.DATABASE_URL.replace("+asyncpg", "")
    engine = create_engine(sync_url)
    return sessionmaker(bind=engine)()


@celery_app.task(name="app.workers.tasks.crm_tasks.generate_daily_tasks")
def generate_daily_tasks():
    """
    Her sabah 08:00'de çalışır:
    1. Motivasyon skoru ≥50 olan sahibinden ilanlar → Soğuk arama görevi
    2. 90+ gün DOM ilanlar → Takip görevi
    3. Yeni ilanlar → Alıcı eşleştirme görevi
    """
    from app.models.listing import Listing, ListingStatus
    from app.models.task import Task, TaskType, TaskStatus
    from app.models.user import User, UserRole
    from app.models.tenant import Tenant
    from sqlalchemy import select, and_

    session = _get_sync_session()
    try:
        # Tüm aktif tenant'lar
        tenants = session.execute(select(Tenant).where(Tenant.is_active == True)).scalars().all()

        total_tasks = 0
        for tenant in tenants:
            # Bu tenant'ın danışmanlarını bul
            advisors = session.execute(
                select(User).where(
                    and_(User.tenant_id == tenant.id, User.role == UserRole.ADVISOR, User.is_active == True)
                )
            ).scalars().all()
            if not advisors:
                continue

            # 1. Motivasyonlu sahibinden ilanlar → Cold Call
            hot_fsbo = session.execute(
                select(Listing).where(
                    and_(
                        Listing.tenant_id == tenant.id,
                        Listing.status == ListingStatus.ACTIVE,
                        Listing.is_fsbo == True,
                        Listing.motivation_score >= 50,
                    )
                ).order_by(Listing.motivation_score.desc()).limit(10)
            ).scalars().all()

            for i, listing in enumerate(hot_fsbo):
                advisor = advisors[i % len(advisors)]  # Round-robin atama
                script = generate_script("cold_call", {
                    "is_fsbo": True,
                    "advisor_name": advisor.full_name,
                    "district": listing.district,
                    "room_count": listing.room_count,
                    "dom": listing.real_days_on_market,
                })
                task = Task(
                    id=str(uuid.uuid4()),
                    tenant_id=tenant.id,
                    assigned_to_id=advisor.id,
                    listing_id=listing.id,
                    task_type=TaskType.COLD_CALL,
                    status=TaskStatus.PENDING,
                    title=f"Sahibinden Ara: {listing.title[:50]} (Motivasyon: {listing.motivation_score})",
                    script=script,
                    priority=max(1, 10 - listing.motivation_score // 10),
                )
                session.add(task)
                total_tasks += 1

            # 2. 90+ gün ilanlar → Follow Up
            stale_listings = session.execute(
                select(Listing).where(
                    and_(
                        Listing.tenant_id == tenant.id,
                        Listing.status == ListingStatus.ACTIVE,
                        Listing.real_days_on_market >= 90,
                    )
                ).order_by(Listing.real_days_on_market.desc()).limit(10)
            ).scalars().all()

            for i, listing in enumerate(stale_listings):
                advisor = advisors[i % len(advisors)]
                script = generate_script("cold_call_expired", {
                    "advisor_name": advisor.full_name,
                    "district": listing.district,
                    "dom": listing.real_days_on_market,
                })
                task = Task(
                    id=str(uuid.uuid4()),
                    tenant_id=tenant.id,
                    assigned_to_id=advisor.id,
                    listing_id=listing.id,
                    task_type=TaskType.FOLLOW_UP,
                    status=TaskStatus.PENDING,
                    title=f"Takip: {listing.title[:50]} ({listing.real_days_on_market} gün)",
                    script=script,
                    priority=3,
                )
                session.add(task)
                total_tasks += 1

        session.commit()
        logger.info(f"Günlük {total_tasks} görev oluşturuldu")
        return total_tasks

    except Exception as e:
        session.rollback()
        logger.error(f"Günlük görev üretim hatası: {e}")
        raise
    finally:
        session.close()


@celery_app.task(name="app.workers.tasks.crm_tasks.match_buyers_to_listings")
def match_buyers_to_listings():
    """
    Her saat çalışır.
    Son 1 saatte gelen yeni ilanları müşteri kriterleriyle eşleştirir.
    """
    from app.models.listing import Listing, ListingStatus
    from app.models.customer import Customer
    from app.models.task import Task, TaskType, TaskStatus
    from app.models.tenant import Tenant
    from app.core.security import decrypt_field
    from sqlalchemy import select, and_
    from datetime import timedelta

    session = _get_sync_session()
    try:
        one_hour_ago = datetime.now(timezone.utc) - timedelta(hours=1)
        tenants = session.execute(select(Tenant).where(Tenant.is_active == True)).scalars().all()
        total_matches = 0

        for tenant in tenants:
            new_listings = session.execute(
                select(Listing).where(
                    and_(
                        Listing.tenant_id == tenant.id,
                        Listing.status == ListingStatus.ACTIVE,
                        Listing.first_seen_at >= one_hour_ago,
                    )
                )
            ).scalars().all()

            customers = session.execute(
                select(Customer).where(
                    and_(Customer.tenant_id == tenant.id, Customer.is_active == True)
                )
            ).scalars().all()

            for listing in new_listings:
                for customer in customers:
                    reasons = []
                    if customer.budget_min and customer.budget_max:
                        if customer.budget_min <= listing.price <= customer.budget_max:
                            reasons.append("Bütçeye uyuyor")
                    if customer.preferred_districts and listing.district:
                        if listing.district.lower() in customer.preferred_districts.lower():
                            reasons.append(f"İlçe: {listing.district}")
                    if customer.preferred_rooms and listing.room_count:
                        if listing.room_count in customer.preferred_rooms:
                            reasons.append(f"Oda: {listing.room_count}")

                    if len(reasons) >= 2:
                        customer_name = decrypt_field(customer.full_name_encrypted)
                        task = Task(
                            id=str(uuid.uuid4()),
                            tenant_id=tenant.id,
                            assigned_to_id=customer.assigned_advisor_id,
                            listing_id=listing.id,
                            customer_id=customer.id,
                            task_type=TaskType.BUYER_MATCH,
                            status=TaskStatus.PENDING,
                            title=f"Eşleşme! {customer_name} ← {listing.title[:30]} ({', '.join(reasons)})",
                            priority=2,
                        )
                        session.add(task)
                        total_matches += 1

        session.commit()
        logger.info(f"Alıcı-portföy eşleştirme: {total_matches} eşleşme")
        return total_matches

    except Exception as e:
        session.rollback()
        logger.error(f"Alıcı eşleştirme hatası: {e}")
        raise
    finally:
        session.close()


@celery_app.task(name="app.workers.tasks.crm_tasks.detect_neighbor_price_drop")
def detect_neighbor_price_drop(listing_id: str, neighborhood: str, new_price: float):
    """
    Bir sitede fiyat düştüğünde aynı mahalledeki diğer satıcılar için
    "Komşu Radarı" görevi üret.
    """
    from app.models.listing import Listing, ListingStatus
    from app.models.task import Task, TaskType, TaskStatus
    from sqlalchemy import select, and_

    session = _get_sync_session()
    try:
        # Fiyat düşen ilanı bul
        source = session.execute(select(Listing).where(Listing.id == listing_id)).scalar_one_or_none()
        if not source:
            return

        # Aynı mahalledeki diğer aktif ilanlar
        neighbors = session.execute(
            select(Listing).where(
                and_(
                    Listing.tenant_id == source.tenant_id,
                    Listing.neighborhood == neighborhood,
                    Listing.status == ListingStatus.ACTIVE,
                    Listing.id != listing_id,
                )
            )
        ).scalars().all()

        for neighbor in neighbors:
            script = generate_script("neighbor_radar", {
                "advisor_name": "",
                "listing_neighborhood": neighborhood,
                "neighbor_unit": source.title[:20],
                "price_drop_pct": "5",
                "listing_advantages": "konum ve manzara",
            })
            task = Task(
                id=str(uuid.uuid4()),
                tenant_id=source.tenant_id,
                listing_id=neighbor.id,
                task_type=TaskType.NEIGHBOR_RADAR,
                status=TaskStatus.PENDING,
                title=f"Komşu Radarı: {neighbor.title[:40]} — komşu fiyat kırdı!",
                script=script,
                priority=4,
            )
            session.add(task)

        session.commit()
        logger.info(f"Komşu radar: {neighborhood}, {len(neighbors)} görev oluşturuldu")

    except Exception as e:
        session.rollback()
        logger.error(f"Komşu radar hatası: {e}")
        raise
    finally:
        session.close()


@celery_app.task(name="app.workers.tasks.crm_tasks.check_long_vacant_rentals")
def check_long_vacant_rentals():
    """
    45 günden uzun boş kalan kiralık mülkleri tespit et.
    Ev sahibine "Satıp farklı yatırıma geçelim" teklifi için görev oluştur.
    """
    from app.models.listing import Listing, ListingStatus, ListingType
    from app.models.task import Task, TaskType, TaskStatus
    from app.models.tenant import Tenant
    from sqlalchemy import select, and_

    session = _get_sync_session()
    try:
        tenants = session.execute(select(Tenant).where(Tenant.is_active == True)).scalars().all()
        total = 0

        for tenant in tenants:
            vacant = session.execute(
                select(Listing).where(
                    and_(
                        Listing.tenant_id == tenant.id,
                        Listing.listing_type == ListingType.RENT,
                        Listing.status == ListingStatus.ACTIVE,
                        Listing.days_on_market >= 45,
                    )
                ).order_by(Listing.days_on_market.desc()).limit(20)
            ).scalars().all()

            for listing in vacant:
                task = Task(
                    id=str(uuid.uuid4()),
                    tenant_id=tenant.id,
                    listing_id=listing.id,
                    task_type=TaskType.FOLLOW_UP,
                    status=TaskStatus.PENDING,
                    title=f"Kiralıktan Satışa: {listing.title[:40]} ({listing.days_on_market} gün boş)",
                    script=f"Mülk {listing.days_on_market} gündür kiracısını bulamıyor. Ev sahibine satış + farklı yatırım (faiz, fon) teklifini sun.",
                    priority=5,
                )
                session.add(task)
                total += 1

        session.commit()
        logger.info(f"Kiralıktan satışa: {total} görev oluşturuldu")
        return total

    except Exception as e:
        session.rollback()
        logger.error(f"Kiralıktan satışa hatası: {e}")
        raise
    finally:
        session.close()


@celery_app.task(name="app.workers.tasks.crm_tasks.award_leaderboard_leads")
def award_leaderboard_leads():
    """
    Günlük hedeflerini tutturan danışmanlara en sıcak portföyleri ata.
    """
    from app.models.task import Task, TaskStatus
    from app.models.listing import Listing, ListingStatus
    from app.models.portfolio import Portfolio
    from app.models.user import User, UserRole
    from app.models.tenant import Tenant
    from sqlalchemy import select, and_, func

    DAILY_CALL_TARGET = 15
    DAILY_APPOINTMENT_TARGET = 3

    session = _get_sync_session()
    try:
        today_start = datetime.combine(date.today(), datetime.min.time()).replace(tzinfo=timezone.utc)
        tenants = session.execute(select(Tenant).where(Tenant.is_active == True)).scalars().all()

        for tenant in tenants:
            # Her danışmanın bugün tamamladığı görev sayısı
            advisors = session.execute(
                select(User).where(
                    and_(User.tenant_id == tenant.id, User.role == UserRole.ADVISOR, User.is_active == True)
                )
            ).scalars().all()

            top_performers = []
            for advisor in advisors:
                done_count = session.execute(
                    select(func.count(Task.id)).where(
                        and_(
                            Task.assigned_to_id == advisor.id,
                            Task.status == TaskStatus.DONE,
                            Task.completed_at >= today_start,
                        )
                    )
                ).scalar() or 0

                if done_count >= DAILY_CALL_TARGET:
                    top_performers.append((advisor, done_count))

            if not top_performers:
                continue

            # En yüksek motivasyonlu henüz atanmamış ilanlar
            hot_leads = session.execute(
                select(Listing).where(
                    and_(
                        Listing.tenant_id == tenant.id,
                        Listing.status == ListingStatus.ACTIVE,
                        Listing.motivation_score >= 60,
                    )
                ).order_by(Listing.motivation_score.desc()).limit(len(top_performers))
            ).scalars().all()

            # En çok görev yapana en sıcak lead'i ata
            top_performers.sort(key=lambda x: x[1], reverse=True)
            for (advisor, _), listing in zip(top_performers, hot_leads):
                portfolio = Portfolio(
                    id=str(uuid.uuid4()),
                    tenant_id=tenant.id,
                    advisor_id=advisor.id,
                    listing_id=listing.id,
                    notes="Leaderboard ödülü — günlük hedef tutturuldu",
                    is_exclusive=True,
                )
                session.add(portfolio)
                logger.info(f"Leaderboard ödülü: {advisor.full_name} ← {listing.title[:30]}")

        session.commit()

    except Exception as e:
        session.rollback()
        logger.error(f"Leaderboard ödül hatası: {e}")
        raise
    finally:
        session.close()
