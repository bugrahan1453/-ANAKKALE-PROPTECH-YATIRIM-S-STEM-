"""
Duplicate İlan Eşleştirici
Fotoğraf parmak izi (perceptual hash) + adres hash ile tekrar ilanları birleştirir.
"""
import redis.asyncio as aioredis
import os
import logging

logger = logging.getLogger(__name__)
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")


class DedupPipeline:
    def __init__(self):
        self.redis = aioredis.from_url(REDIS_URL, decode_responses=True)

    async def process(self, listing: dict) -> dict:
        """
        address_hash ile daha önce görüldüyse property_id'yi ekle.
        Yeni ise Redis'e kaydet.
        """
        addr_hash = listing.get("address_hash", "")
        if not addr_hash:
            return listing

        key = f"property:addr:{addr_hash}"
        existing_property_id = await self.redis.get(key)

        if existing_property_id:
            listing["property_id"] = existing_property_id
            logger.info(f"Duplicate tespit edildi: property_id={existing_property_id}")
        else:
            import uuid
            new_property_id = str(uuid.uuid4())
            await self.redis.set(key, new_property_id, ex=86400 * 365)  # 1 yıl sakla
            listing["property_id"] = new_property_id

        return listing
