#!/usr/bin/env python3
"""
Automated Web Scraper with Scheduler

Commands:
  run       — scrape all targets once
  schedule  — run scheduler (continuous, Ctrl-C to stop)
  export    — dump all DB data to CSV files
  history   — print recent job history
"""
import argparse
import logging
import signal
import sys
import time
from datetime import datetime

import config
from scraper import BS4Scraper, SeleniumScraper
from storage import Database, Exporter
from scheduler import ScraperScheduler

# ── logging ───────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("scraper.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)


# ── helpers ───────────────────────────────────────────────────────────
def _build_scraper(target: dict):
    name = target["name"]
    url = target["url"]
    selectors = target.get("selectors", {})
    if target.get("type") == "selenium":
        return SeleniumScraper(
            name=name,
            url=url,
            selectors=selectors,
            headless=config.SELENIUM_HEADLESS,
            timeout=config.SELENIUM_TIMEOUT,
        )
    return BS4Scraper(name=name, url=url, selectors=selectors)


# ── commands ──────────────────────────────────────────────────────────
def cmd_run(db: Database, exporter: Exporter):
    print(f"Running {len(config.SCRAPE_TARGETS)} scraper(s)...\n")
    for target in config.SCRAPE_TARGETS:
        scraper = _build_scraper(target)
        started = datetime.utcnow()
        print(f"  ↓  {target['name']}  {target['url']}")
        db.log_job(target["name"], "running", started_at=started)
        items = scraper.scrape()
        count = db.save_items(items)
        db.log_job(target["name"], "success", items_count=count, started_at=started)
        print(f"     saved {count} items\n")


def cmd_schedule(db: Database, exporter: Exporter):
    scheduler = ScraperScheduler(db=db, exporter=exporter, auto_export=False)
    for target in config.SCRAPE_TARGETS:
        scraper = _build_scraper(target)
        interval = target.get("interval_minutes", config.DEFAULT_INTERVAL_MINUTES)
        scheduler.add_job(scraper, interval_minutes=interval)

    scheduler.start()
    print("Scheduler running (Ctrl-C to stop)\n")
    for job in scheduler.list_jobs():
        print(f"  {job['id']:35s}  next: {job['next_run']}")
    print()

    def _shutdown(sig, frame):
        print("\nShutting down...")
        scheduler.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)
    while True:
        time.sleep(1)


def cmd_export(db: Database, exporter: Exporter):
    for target in config.SCRAPE_TARGETS:
        items = db.get_items(source=target["name"], limit=100_000)
        if items:
            path = exporter.to_csv(items, source=target["name"])
            print(f"  {target['name']}: {len(items)} rows → {path}")
        else:
            print(f"  {target['name']}: no data")


def cmd_history(db: Database, exporter: Exporter):
    jobs = db.get_job_history(limit=30)
    if not jobs:
        print("No job history.")
        return
    hdr = f"{'Source':<25} {'Status':<10} {'Items':>6}  {'Started':<26} Error"
    print(hdr)
    print("-" * len(hdr))
    for j in jobs:
        print(
            f"{j['source']:<25} {j['status']:<10} {j['items_count']:>6}  "
            f"{j['started_at']:<26} {j.get('error') or ''}"
        )


# ── main ──────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="Web Scraper with Scheduler",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "command",
        choices=["run", "schedule", "export", "history"],
    )
    args = parser.parse_args()

    db = Database(config.DB_PATH)
    exporter = Exporter(config.EXPORT_DIR)

    {
        "run": cmd_run,
        "schedule": cmd_schedule,
        "export": cmd_export,
        "history": cmd_history,
    }[args.command](db, exporter)


if __name__ == "__main__":
    main()
