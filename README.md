# Automated Web Scraper with Scheduler

Static + dynamic scraping, SQLite storage, scheduled runs, CSV export.

## Stack

| Layer      | Library                             |
|------------|-------------------------------------|
| Static     | `requests` + `BeautifulSoup` + `lxml` |
| Dynamic    | `Selenium` + `webdriver-manager`    |
| Storage    | SQLite (via `sqlite3`)              |
| Scheduler  | `APScheduler` (BackgroundScheduler) |
| Export     | stdlib `csv`                        |

---

## Setup

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Selenium targets also need **Google Chrome** installed.  
`webdriver-manager` downloads the matching ChromeDriver automatically.

---

## Usage

```bash
# Scrape all targets once, save to DB
python main.py run

# Start continuous scheduler (fires immediately, then on interval)
python main.py schedule

# Export all DB data to CSV files in ./exports/
python main.py export

# Print recent job history
python main.py history
```

---

## Adding a Scrape Target

Edit `config.py`:

```python
SCRAPE_TARGETS = [
    {
        "name":             "my_site",          # unique ID, used in filenames & DB
        "url":              "https://example.com",
        "type":             "bs4",              # "bs4" or "selenium"
        "selectors": {
            "items":  ".product-card",          # container (one per row)
            "title":  "h2.name",               # field selectors inside container
            "price":  ".price",
            "rating": ".stars",
        },
        "interval_minutes": 30,                 # scheduler interval
    },
]
```

Omit `"items"` to scrape the whole page as a single raw-text item.

---

## Project Layout

```
main.py            CLI (run / schedule / export / history)
config.py          Targets, paths, timeouts
requirements.txt

scraper/
  base.py          BaseScraper, ScrapedItem dataclass
  bs4_scraper.py   Requests + BeautifulSoup (static HTML)
  selenium_scraper.py  Chrome WebDriver (JS-rendered pages)

storage/
  database.py      SQLite — scraped_data + scrape_jobs tables
  exporter.py      Flatten & export rows to timestamped CSV

scheduler/
  job_scheduler.py APScheduler wrapper — add/start/stop jobs

data/              SQLite DB (auto-created)
exports/           CSV files (auto-created)
scraper.log        Log file (auto-created)
```

---

## Database Schema

**scraped_data** — one row per scraped item  
**scrape_jobs** — audit log (start time, status, item count, errors)

Query directly:
```bash
sqlite3 data/scraper.db "SELECT source, count(*) FROM scraped_data GROUP BY source;"
```
