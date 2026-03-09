"""Scraping Görevleri — Koordinasyon ve tetikleme."""
from app.workers.celery_app import celery_app
import httpx
import logging

logger = logging.getLogger(__name__)


@celery_app.task(name="app.workers.tasks.scrape_tasks.run_full_scrape")
def run_full_scrape():
    """Tüm scraper spiders'ı tetikle."""
    from app.core.config import settings
    try:
        with httpx.Client(timeout=30) as client:
            client.post(f"{settings.SCRAPER_URL}/scrape/trigger", json={"sources": ["all"]})
        logger.info("Scrape tetiklendi")
    except Exception as e:
        logger.error(f"Scrape tetiklenemedi: {e}")
        raise


@celery_app.task(name="app.workers.tasks.scrape_tasks.process_new_listing")
def process_new_listing(listing_data: dict):
    """
    Yeni ilan geldiğinde:
    1. Duplicate kontrolü (fotoğraf hash + adres hash)
    2. Hayalet ilan kontrolü (daha önce görüldü mü?)
    3. Yeniden yükleme tespiti
    4. AI skorlama kuyruğuna gönder
    """
    from app.workers.tasks.ai_tasks import score_motivation, analyze_photos
    listing_id = listing_data.get("id")
    description = listing_data.get("description", "")
    photos = listing_data.get("photo_urls", [])

    score_motivation.delay(listing_id, description)
    if photos:
        analyze_photos.delay(listing_id, photos)

    logger.info(f"Yeni ilan işleme kuyruğa alındı: {listing_id}")
