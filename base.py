import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class ScrapedItem:
    source: str
    url: str
    data: dict[str, Any]
    scraped_at: datetime = field(default_factory=datetime.utcnow)


class BaseScraper(ABC):
    def __init__(self, name: str, url: str):
        self.name = name
        self.url = url
        self.logger = logging.getLogger(f"{__name__}.{name}")

    @abstractmethod
    def scrape(self) -> list[ScrapedItem]:
        pass

    def _make_item(self, data: dict) -> ScrapedItem:
        return ScrapedItem(source=self.name, url=self.url, data=data)
