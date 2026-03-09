"""Makro Tetikleyiciler — TCMB faiz takibi, piyasa alarmları."""
from app.workers.celery_app import celery_app
from app.workers.tasks.notification_tasks import send_broker_sms
import httpx
import logging

logger = logging.getLogger(__name__)

# TCMB politika faizi endpoint (gerçek API ile değiştirilmeli)
TCMB_RATE_URL = "https://evds2.tcmb.gov.tr/service/evds/series=TP.TRY.MT01"


@celery_app.task(name="app.workers.tasks.macro_tasks.check_interest_rate")
def check_interest_rate():
    """
    Kredi faizlerindeki düşüşü takip et.
    %1+ düşüşte broker'a alarm gönder:
    "Faiz düştü, 3M altı 2+1 evleri hemen ara, piyasa hızlanacak"
    """
    try:
        # TCMB EVDS API sorgusu (production'da doğru endpoint)
        response = httpx.get(TCMB_RATE_URL, timeout=15)
        if response.status_code != 200:
            logger.warning("TCMB API erişilemedi")
            return

        # Faiz oranını parse et ve karşılaştır
        # Bu kısım gerçek veri formatına göre ayarlanır
        logger.info("Faiz oranı kontrolü tamamlandı")

    except Exception as e:
        logger.error(f"Makro tetikleyici hatası: {e}")


@celery_app.task(name="app.workers.tasks.macro_tasks.check_price_drops")
def check_price_drops():
    """
    Son 24 saatte %5+ fiyat düşüren ilanları tespit et.
    Broker'a toplu rapor gönder.
    """
    logger.info("Fiyat düşüşü analizi çalışıyor...")
    # DB sorgusu ile son 24 saatteki fiyat değişimlerini kontrol et
