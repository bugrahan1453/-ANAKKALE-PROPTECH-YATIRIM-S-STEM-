"""Celery uygulama tanımı — Scraping, AI, bildirim görevleri."""
from celery import Celery
from celery.schedules import crontab
from app.core.config import settings

celery_app = Celery(
    "proptech",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        "app.workers.tasks.scrape_tasks",
        "app.workers.tasks.ai_tasks",
        "app.workers.tasks.notification_tasks",
        "app.workers.tasks.crm_tasks",
    ],
)

celery_app.conf.beat_schedule = {
    # Her 30 dakikada scraper çalıştır
    "scrape-listings": {
        "task": "app.workers.tasks.scrape_tasks.run_full_scrape",
        "schedule": crontab(minute=f"*/{settings.SCRAPE_INTERVAL_MINUTES}"),
    },
    # Sabah 08:00'de günlük görevleri oluştur
    "generate-daily-tasks": {
        "task": "app.workers.tasks.crm_tasks.generate_daily_tasks",
        "schedule": crontab(hour=8, minute=0),
    },
    # Her saat başı alıcı-portföy eşleştirme
    "match-buyers-to-listings": {
        "task": "app.workers.tasks.crm_tasks.match_buyers_to_listings",
        "schedule": crontab(minute=0),
    },
    # Gece DOM sayacını güncelle
    "update-dom-counters": {
        "task": "app.workers.tasks.ai_tasks.update_dom_counters",
        "schedule": crontab(hour=0, minute=30),
    },
}

celery_app.conf.task_routes = {
    "app.workers.tasks.scrape_tasks.*": {"queue": "scraping"},
    "app.workers.tasks.ai_tasks.*": {"queue": "ai"},
    "app.workers.tasks.notification_tasks.*": {"queue": "notifications"},
    "app.workers.tasks.crm_tasks.*": {"queue": "crm"},
}
