import logging
from datetime import datetime

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

logger = logging.getLogger(__name__)


class ScraperScheduler:
    def __init__(self, db, exporter, auto_export: bool = False):
        self.db = db
        self.exporter = exporter
        self.auto_export = auto_export
        self.scheduler = BackgroundScheduler(timezone="UTC")

    # ------------------------------------------------------------------
    def add_job(self, scraper, interval_minutes: int):
        job_id = f"scrape_{scraper.name}"

        def run():
            started = datetime.utcnow()
            logger.info(f"[{scraper.name}] job started")
            self.db.log_job(scraper.name, "running", started_at=started)
            try:
                items = scraper.scrape()
                count = self.db.save_items(items)
                self.db.log_job(scraper.name, "success", items_count=count, started_at=started)
                logger.info(f"[{scraper.name}] done — {count} items")

                if self.auto_export and count:
                    rows = self.db.get_items(source=scraper.name, limit=count)
                    path = self.exporter.to_csv(rows, source=scraper.name)
                    logger.info(f"[{scraper.name}] exported → {path}")

            except Exception as exc:
                logger.exception(f"[{scraper.name}] job error")
                self.db.log_job(scraper.name, "error", error=str(exc), started_at=started)

        self.scheduler.add_job(
            run,
            trigger=IntervalTrigger(minutes=interval_minutes),
            id=job_id,
            replace_existing=True,
            next_run_time=datetime.utcnow(),  # fire immediately on start
        )
        logger.info(f"Scheduled [{scraper.name}] every {interval_minutes} min")

    # ------------------------------------------------------------------
    def start(self):
        self.scheduler.start()
        logger.info("Scheduler started")

    def stop(self):
        self.scheduler.shutdown(wait=False)
        logger.info("Scheduler stopped")

    def list_jobs(self) -> list[dict]:
        return [
            {"id": j.id, "next_run": str(j.next_run_time), "trigger": str(j.trigger)}
            for j in self.scheduler.get_jobs()
        ]
