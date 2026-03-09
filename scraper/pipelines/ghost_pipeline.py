"""
Hayalet İlan Hafızası + Yeniden Yükleme Tespiti
Silinen ilanların DOM ve son fiyatını Redis'te sonsuza dek saklar.
"""
import redis.asyncio as aioredis
import os
import json
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")


class GhostListingPipeline:
    def __init__(self):
        self.redis = aioredis.from_url(REDIS_URL, decode_responses=True)

    async def process(self, listing: dict) -> dict:
        source_key = f"listing:{listing['source_site']}:{listing['source_id']}"
        existing_raw = await self.redis.get(source_key)

        if existing_raw:
            existing = json.loads(existing_raw)
            # Yeniden yükleme tespiti
            real_dom = existing.get("real_dom", 0) + existing.get("dom", 0)
            listing["real_days_on_market"] = real_dom
            listing["is_repost"] = True
            logger.info(f"Yeniden yükleme tespit edildi: {listing['source_id']}, Gerçek DOM: {real_dom}")
        else:
            listing["real_days_on_market"] = 0
            listing["is_repost"] = False

        # Güncel durumu kaydet
        await self.redis.set(
            source_key,
            json.dumps({
                "price": listing["price"],
                "dom": listing.get("days_on_market", 0),
                "real_dom": listing.get("real_days_on_market", 0),
                "last_seen": datetime.now(timezone.utc).isoformat(),
            }),
            # Sonsuz saklama için ex=None (Redis'te kalıcı)
        )
        return listing

    async def mark_deleted(self, source_site: str, source_id: str, last_price: float):
        """İlan silindiğinde son fiyatı 'hayalet' olarak işaretle."""
        ghost_key = f"ghost:{source_site}:{source_id}"
        await self.redis.set(
            ghost_key,
            json.dumps({"last_price": last_price, "deleted_at": datetime.now(timezone.utc).isoformat()}),
        )
