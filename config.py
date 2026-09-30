import os

BASE_DIR = os.path.dirname(__file__)

# --- Scrape targets ---
# type: "bs4" (static) or "selenium" (JS-rendered)
# selectors: CSS selectors; "items" = container, rest = fields per item
SCRAPE_TARGETS = [
    {
        "name": "hacker_news",
        "url": "https://news.ycombinator.com/",
        "type": "bs4",
        "selectors": {
            "items": ".athing",
            "title": ".titleline > a",
            "site": ".sitebit a",
        },
        "interval_minutes": 30,
    },
    {
        "name": "quotes",
        "url": "https://quotes.toscrape.com/",
        "type": "bs4",
        "selectors": {
            "items": ".quote",
            "text": ".text",
            "author": ".author",
            "tags": ".tag",
        },
        "interval_minutes": 60,
    },
]

# --- Storage ---
DB_PATH = os.path.join(BASE_DIR, "data", "scraper.db")
EXPORT_DIR = os.path.join(BASE_DIR, "exports")

# --- Selenium ---
SELENIUM_HEADLESS = True
SELENIUM_TIMEOUT = 15

# --- Scheduler ---
DEFAULT_INTERVAL_MINUTES = 30
MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 5
