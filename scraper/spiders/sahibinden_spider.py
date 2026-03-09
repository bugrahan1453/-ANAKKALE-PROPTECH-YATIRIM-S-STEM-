"""
Sahibinden.com Spider — Stealth Playwright + Proxy Rotasyonu
Anti-bot: User-Agent rotasyonu, rastgele bekleme, residential proxy
"""
import asyncio
import random
import hashlib
import os
import logging
from playwright.async_api import async_playwright

logger = logging.getLogger(__name__)

PROXY_API_KEY = os.getenv("PROXY_API_KEY", "")
SEARCH_URL = (
    "https://www.sahibinden.com/satilik-daire/canakkale"
    "?pagingSize=50&category_id=28"
)


class SahibindenSpider:
    async def crawl(self) -> list[dict]:
        listings = []
        async with async_playwright() as pw:
            # Stealth tarayıcı
            browser = await pw.chromium.launch(
                headless=True,
                args=[
                    "--no-sandbox",
                    "--disable-blink-features=AutomationControlled",
                    "--disable-dev-shm-usage",
                ],
                proxy=self._get_proxy() if PROXY_API_KEY else None,
            )
            ctx = await browser.new_context(
                user_agent=self._random_ua(),
                viewport={"width": 1366, "height": 768},
                locale="tr-TR",
            )
            # Bot tespitini engelle
            await ctx.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            """)

            page = await ctx.new_page()
            await page.goto(SEARCH_URL, wait_until="networkidle", timeout=30_000)
            await asyncio.sleep(random.uniform(2, 4))

            items = await page.query_selector_all(".searchResultsItem")
            for item in items[:50]:
                try:
                    listing = await self._parse_item(item)
                    if listing:
                        listings.append(listing)
                except Exception as e:
                    logger.warning(f"İlan parse hatası: {e}")

            await browser.close()
        logger.info(f"Sahibinden: {len(listings)} ilan çekildi")
        return listings

    async def _parse_item(self, item) -> dict | None:
        title_el = await item.query_selector(".classifiedTitle")
        price_el = await item.query_selector(".price")
        loc_el = await item.query_selector(".searchResultsLocationValue")
        link_el = await item.query_selector("a.classifiedTitle")

        if not title_el or not price_el:
            return None

        title = (await title_el.inner_text()).strip()
        price_raw = (await price_el.inner_text()).strip().replace(".", "").replace(" TL", "").replace(",", "")
        location = (await loc_el.inner_text()).strip() if loc_el else ""
        href = await link_el.get_attribute("href") if link_el else ""
        source_url = f"https://www.sahibinden.com{href}" if href else ""
        source_id = href.split("/")[-1].split("?")[0] if href else ""

        try:
            price = float(price_raw)
        except ValueError:
            return None

        # Sahibinden = FSBO (bireysel mi?) — Başlıkta "sahibinden" geçiyor mu?
        is_fsbo = "sahibinden" in title.lower() or "sahibi" in title.lower()

        return {
            "source_site": "sahibinden",
            "source_id": source_id,
            "source_url": source_url,
            "title": title,
            "price": price,
            "currency": "TRY",
            "location_raw": location,
            "is_fsbo": is_fsbo,
            "address_hash": hashlib.md5(location.encode()).hexdigest(),
        }

    def _get_proxy(self) -> dict:
        return {
            "server": f"http://proxy.provider.io:8080",
            "username": "user",
            "password": PROXY_API_KEY,
        }

    def _random_ua(self) -> str:
        agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/123.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/122.0.0.0 Safari/537.36",
        ]
        return random.choice(agents)
