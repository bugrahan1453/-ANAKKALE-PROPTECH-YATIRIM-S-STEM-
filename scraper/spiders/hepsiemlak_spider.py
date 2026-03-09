"""Hepsiemlak Spider — Aynı stealth mimarisi."""
import logging

logger = logging.getLogger(__name__)


class HepsiemlakSpider:
    async def crawl(self) -> list[dict]:
        # Sahibinden spider ile aynı Playwright mimarisini kullanır.
        # Bu dosya iskelet olarak bırakılmıştır.
        logger.info("Hepsiemlak spider çalışıyor...")
        return []
