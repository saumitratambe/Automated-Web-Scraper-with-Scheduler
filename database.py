import json
import logging
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

from scraper.base import ScrapedItem

logger = logging.getLogger(__name__)

DDL = """
CREATE TABLE IF NOT EXISTS scraped_data (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    source      TEXT    NOT NULL,
    url         TEXT    NOT NULL,
    data        TEXT    NOT NULL,
    scraped_at  TEXT    NOT NULL,
    created_at  TEXT    DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_sd_source     ON scraped_data(source);
CREATE INDEX IF NOT EXISTS idx_sd_scraped_at ON scraped_data(scraped_at);

CREATE TABLE IF NOT EXISTS scrape_jobs (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    source      TEXT    NOT NULL,
    status      TEXT    NOT NULL,
    items_count INTEGER DEFAULT 0,
    error       TEXT,
    started_at  TEXT    NOT NULL,
    finished_at TEXT
);
"""


class Database:
    def __init__(self, db_path: str):
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init()

    @contextmanager
    def _conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _init(self):
        with self._conn() as c:
            c.executescript(DDL)
        logger.info(f"DB ready: {self.db_path}")

    # ------------------------------------------------------------------
    def save_items(self, items: list[ScrapedItem]) -> int:
        if not items:
            return 0
        with self._conn() as c:
            c.executemany(
                "INSERT INTO scraped_data (source, url, data, scraped_at) VALUES (?,?,?,?)",
                [
                    (i.source, i.url, json.dumps(i.data), i.scraped_at.isoformat())
                    for i in items
                ],
            )
        return len(items)

    def log_job(
        self,
        source: str,
        status: str,
        items_count: int = 0,
        error: str | None = None,
        started_at: datetime | None = None,
        finished_at: datetime | None = None,
    ):
        now = datetime.utcnow()
        fin = finished_at.isoformat() if finished_at else (now.isoformat() if status != "running" else None)
        with self._conn() as c:
            c.execute(
                "INSERT INTO scrape_jobs (source,status,items_count,error,started_at,finished_at)"
                " VALUES (?,?,?,?,?,?)",
                (source, status, items_count, error, (started_at or now).isoformat(), fin),
            )

    def get_items(self, source: str | None = None, limit: int = 500) -> list[dict]:
        with self._conn() as c:
            if source:
                rows = c.execute(
                    "SELECT * FROM scraped_data WHERE source=? ORDER BY scraped_at DESC LIMIT ?",
                    (source, limit),
                ).fetchall()
            else:
                rows = c.execute(
                    "SELECT * FROM scraped_data ORDER BY scraped_at DESC LIMIT ?",
                    (limit,),
                ).fetchall()
        out = []
        for row in rows:
            d = dict(row)
            d["data"] = json.loads(d["data"])
            out.append(d)
        return out

    def get_job_history(self, limit: int = 50) -> list[dict]:
        with self._conn() as c:
            rows = c.execute(
                "SELECT * FROM scrape_jobs ORDER BY started_at DESC LIMIT ?", (limit,)
            ).fetchall()
        return [dict(r) for r in rows]

    def count(self, source: str | None = None) -> int:
        with self._conn() as c:
            if source:
                return c.execute(
                    "SELECT COUNT(*) FROM scraped_data WHERE source=?", (source,)
                ).fetchone()[0]
            return c.execute("SELECT COUNT(*) FROM scraped_data").fetchone()[0]
