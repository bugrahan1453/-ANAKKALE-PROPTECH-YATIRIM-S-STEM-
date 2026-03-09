"""
Scraper Servisi — Anti-bot Headless Tarayıcı ile İlan Çekimi
Playwright + Residential Proxy rotasyonu
"""
from fastapi import FastAPI, BackgroundTasks
from spiders.sahibinden_spider import SahibindenSpider
from spiders.hepsiemlak_spider import HepsiemlakSpider
from pipelines.dedup_pipeline import DedupPipeline
from pipelines.ghost_pipeline import GhostListingPipeline
import logging

logger = logging.getLogger(__name__)
app = FastAPI(title="PropTech Scraper")

dedup = DedupPipeline()
ghost = GhostListingPipeline()


@app.post("/scrape/trigger")
async def trigger_scrape(payload: dict, background_tasks: BackgroundTasks):
    sources = payload.get("sources", ["all"])
    background_tasks.add_task(run_scrape, sources)
    return {"status": "triggered", "sources": sources}


async def run_scrape(sources: list[str]):
    spiders = []
    if "all" in sources or "sahibinden" in sources:
        spiders.append(SahibindenSpider())
    if "all" in sources or "hepsiemlak" in sources:
        spiders.append(HepsiemlakSpider())

    for spider in spiders:
        try:
            listings = await spider.crawl()
            for listing in listings:
                # 1. Duplicate kontrolü
                canonical = await dedup.process(listing)
                # 2. Hayalet/yeniden yükleme kontrolü
                await ghost.process(canonical)
                # 3. Backend'e gönder
                await _push_to_backend(canonical)
        except Exception as e:
            logger.error(f"Spider {spider.__class__.__name__} hatası: {e}")


async def _push_to_backend(listing: dict):
    import httpx
    import os
    backend_url = os.getenv("BACKEND_URL", "http://backend:8000")
    try:
        async with httpx.AsyncClient() as client:
            await client.post(f"{backend_url}/api/v1/internal/listings/ingest", json=listing)
    except Exception as e:
        logger.error(f"Backend'e gönderim hatası: {e}")


@app.get("/health")
def health():
    return {"status": "ok", "service": "scraper"}
