"""CRM Görevleri — Günlük görev üretimi, alıcı-portföy eşleştirme."""
from app.workers.celery_app import celery_app
import logging

logger = logging.getLogger(__name__)


@celery_app.task(name="app.workers.tasks.crm_tasks.generate_daily_tasks")
def generate_daily_tasks():
    """
    Her sabah 08:00'de çalışır.
    - Motivasyon skoru yüksek sahibinden ilanları bulur → Soğuk arama görevi
    - 90+ gün DOM → Takip görevi
    - Komşu fiyat kırması → Komşu radar görevi
    """
    logger.info("Günlük görevler oluşturuluyor...")
    # Gerçek uygulama: DB sorguları + Task oluşturma


@celery_app.task(name="app.workers.tasks.crm_tasks.match_buyers_to_listings")
def match_buyers_to_listings():
    """
    Her saat çalışır.
    Yeni ilanları müşteri kriterleriyle eşleştirir,
    danışmana "Bu ev tam Mehmet Bey'in kriterlerine uyuyor" bildirimi oluşturur.
    """
    logger.info("Alıcı-portföy eşleştirme başladı...")


@celery_app.task(name="app.workers.tasks.crm_tasks.detect_neighbor_price_drop")
def detect_neighbor_price_drop(listing_id: str, neighborhood: str, new_price: float):
    """
    Bir sitede fiyat düştüğünde aynı mahalledeki diğer satıcılar için
    "Komşu Radarı" görevi üret.
    """
    logger.info(f"Komşu radar: {neighborhood} mahallesi, yeni fiyat {new_price}")


@celery_app.task(name="app.workers.tasks.crm_tasks.check_long_vacant_rentals")
def check_long_vacant_rentals():
    """
    45 günden uzun boş kalan kiralık mülkleri tespit et.
    Ev sahibine "Satıp farklı yatırıma geçelim" teklifi için liste oluştur.
    """
    logger.info("Uzun süreli boş kiralıklar kontrol ediliyor...")


@celery_app.task(name="app.workers.tasks.crm_tasks.award_leaderboard_leads")
def award_leaderboard_leads():
    """
    Günlük hedeflerini tutturan danışmanlara sıcak portföyler ata.
    Kurtlar Vadisi oyunlaştırması.
    """
    logger.info("Leaderboard ödülleri dağıtılıyor...")
