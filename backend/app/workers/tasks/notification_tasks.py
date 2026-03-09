"""Bildirim görevleri — SMS, WhatsApp, e-posta."""
from app.workers.celery_app import celery_app
from app.core.config import settings
import httpx
import logging

logger = logging.getLogger(__name__)


@celery_app.task(name="app.workers.tasks.notification_tasks.send_broker_sms")
def send_broker_sms(message: str):
    """Broker'a (Sadece broker) kritik uyarı SMS gönder."""
    try:
        from twilio.rest import Client
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        client.messages.create(
            body=message,
            from_=settings.TWILIO_PHONE_NUMBER,
            to=settings.BROKER_PHONE_NUMBER,
        )
        logger.info("Broker SMS gönderildi")
    except Exception as e:
        logger.error(f"SMS gönderilemedi: {e}")
        raise


@celery_app.task(name="app.workers.tasks.notification_tasks.send_whatsapp_alert")
def send_whatsapp_alert(message: str, phone: str):
    """WhatsApp Business API ile mesaj gönder."""
    try:
        from twilio.rest import Client
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        client.messages.create(
            body=message,
            from_=f"whatsapp:{settings.TWILIO_PHONE_NUMBER}",
            to=f"whatsapp:{phone}",
        )
    except Exception as e:
        logger.error(f"WhatsApp gönderilemedi: {e}")
        raise


@celery_app.task(name="app.workers.tasks.notification_tasks.bloody_market_alert")
def bloody_market_alert(listing_id: str, listing_title: str, price: float, guaranteed_value: float):
    """Kanlı piyasa radarı — Garantili değerin %20 altı."""
    ratio = (guaranteed_value - price) / guaranteed_value * 100
    message = (
        f"🔴 KANLI PİYASA RADARI\n"
        f"İlan: {listing_title}\n"
        f"Fiyat: {price:,.0f} TL\n"
        f"Garantili Değer: {guaranteed_value:,.0f} TL\n"
        f"İskonto: %{ratio:.1f}\n"
        f"Hemen harekete geç!"
    )
    send_broker_sms.delay(message)
    send_whatsapp_alert.delay(message, settings.BROKER_PHONE_NUMBER)
