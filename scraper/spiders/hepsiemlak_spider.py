"""
Hepsiemlak Spider — Stealth Playwright + Proxy Rotasyonu
"""
import asyncio
import random
import hashlib
import os
import logging
from playwright.async_api import async_playwright

logger = logging.getLogger(__name__)

PROXY_API_KEY = os.getenv("PROXY_API_KEY", "")
BASE_URL = "https://www.hepsiemlak.com"
SEARCH_URL = f"{BASE_URL}/canakkale-satilik"


class HepsiemlakSpider:
    async def crawl(self, pages: int = 3) -> list[dict]:
        listings = []
        async with async_playwright() as pw:
            browser = await pw.chromium.launch(
                headless=True,
                args=["--no-sandbox", "--disable-blink-features=AutomationControlled"],
                proxy=self._get_proxy() if PROXY_API_KEY else None,
            )
            ctx = await browser.new_context(
                user_agent=self._random_ua(),
                viewport={"width": 1366, "height": 768},
                locale="tr-TR",
            )
            # Webdriver tespitini gizle
            await ctx.add_init_script(
                "Object.defineProperty(navigator, 'webdriver', { get: () => undefined });"
            )

            page = await ctx.new_page()
            try:
                for page_num in range(1, pages + 1):
                    url = f"{SEARCH_URL}?page={page_num}"
                    await page.goto(url, wait_until="networkidle", timeout=30_000)
                    await asyncio.sleep(random.uniform(2, 5))

                    items = await page.query_selector_all(
                        ".listing-item, .list-view-item, [class*='card-'], [data-id]"
                    )
                    for item in items:
                        try:
                            listing = await self._parse_item(item)
                            if listing:
                                listings.append(listing)
                        except Exception as e:
                            logger.warning(f"Hepsiemlak parse hatası: {e}")

                    # Son sayfaya geldiyse dur
                    if len(items) == 0:
                        break

            except Exception as e:
                logger.error(f"Hepsiemlak sayfa yükleme hatası: {e}")
            finally:
                await browser.close()

        logger.info(f"Hepsiemlak: {len(listings)} ilan çekildi")
        return listings

    async def _parse_item(self, item) -> dict | None:
        title_el = await item.query_selector("a.card-link, .listing-title, h3 a, a[href*='/canakkale']")
        price_el = await item.query_selector(".list-view-price, .price, [class*='price']")
        loc_el = await item.query_selector(".list-view-location, .location, [class*='location']")

        if not title_el or not price_el:
            return None

        title = (await title_el.inner_text()).strip()
        href = await title_el.get_attribute("href") or ""
        source_url = f"{BASE_URL}{href}" if href and not href.startswith("http") else href
        source_id = href.rstrip("/").split("/")[-1].split("?")[0] if href else ""

        price_raw = (await price_el.inner_text()).strip()
        price_clean = price_raw.replace(".", "").replace(",", "").replace("TL", "").replace(" ", "").replace("₺", "")
        try:
            price = float(price_clean)
        except ValueError:
            return None

        location = ""
        if loc_el:
            location = (await loc_el.inner_text()).strip()

        parts = [p.strip() for p in location.split("/")]
        district = parts[-2] if len(parts) >= 2 else ""
        neighborhood = parts[-1] if len(parts) >= 1 else ""

        # Alan m2
        area_m2 = None
        area_el = await item.query_selector("[class*='squareMeter'], [class*='area'], [class*='square']")
        if area_el:
            area_text = (await area_el.inner_text()).strip()
            try:
                area_m2 = float(area_text.replace("m²", "").replace("m2", "").strip())
            except ValueError:
                pass

        # Oda sayısı
        room_count = None
        room_el = await item.query_selector("[class*='room'], [class*='Room'], .houseRoomCount")
        if room_el:
            room_text = (await room_el.inner_text()).strip()
            if "+" in room_text or room_text.replace(" ", "").isalnum():
                room_count = room_text

        # Fotoğraflar
        img_els = await item.query_selector_all("img[src*='hepsiemlak'], img[data-src]")
        photos = []
        for img in img_els[:5]:
            src = await img.get_attribute("src") or await img.get_attribute("data-src") or ""
            if src and src.startswith("http"):
                photos.append(src)

        is_fsbo = "sahibinden" in title.lower() or "sahibinden" in location.lower()

        return {
            "source_site": "hepsiemlak",
            "source_id": source_id,
            "source_url": source_url,
            "title": title,
            "price": price,
            "currency": "TRY",
            "district": district,
            "neighborhood": neighborhood,
            "location_raw": location,
            "area_m2": area_m2,
            "room_count": room_count,
            "photos": photos,
            "is_fsbo": is_fsbo,
            "address_hash": hashlib.md5(location.encode("utf-8")).hexdigest(),
        }

    def _get_proxy(self) -> dict:
        return {
            "server": "http://proxy.provider.io:8080",
            "username": "user",
            "password": PROXY_API_KEY,
        }

    def _random_ua(self) -> str:
        agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0",
        ]
        return random.choice(agents)
