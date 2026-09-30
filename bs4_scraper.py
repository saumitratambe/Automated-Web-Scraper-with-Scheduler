import logging
from typing import Any

import requests
from bs4 import BeautifulSoup

from .base import BaseScraper, ScrapedItem

logger = logging.getLogger(__name__)

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}


class BS4Scraper(BaseScraper):
    def __init__(self, name: str, url: str, selectors: dict[str, str | None]):
        super().__init__(name, url)
        self.selectors = selectors

    def scrape(self) -> list[ScrapedItem]:
        try:
            resp = requests.get(self.url, headers=_HEADERS, timeout=10)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "lxml")
            return self._parse(soup)
        except Exception as exc:
            self.logger.error(f"Scrape failed [{self.url}]: {exc}")
            return []

    def _parse(self, soup: BeautifulSoup) -> list[ScrapedItem]:
        container_sel = self.selectors.get("items")
        if not container_sel:
            # No container — grab full page text as single item
            return [self._make_item({"raw_text": soup.get_text(" ", strip=True)[:1000]})]

        items: list[ScrapedItem] = []
        for el in soup.select(container_sel):
            data: dict[str, Any] = {}
            for key, sel in self.selectors.items():
                if key == "items" or sel is None:
                    continue
                found = el.select(sel)
                if len(found) == 1:
                    data[key] = found[0].get_text(strip=True)
                elif found:
                    data[key] = [f.get_text(strip=True) for f in found]
                else:
                    data[key] = None
            if any(v for v in data.values()):
                items.append(self._make_item(data))
        return items
