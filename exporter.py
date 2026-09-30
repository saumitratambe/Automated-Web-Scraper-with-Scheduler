import csv
import json
import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class Exporter:
    def __init__(self, export_dir: str):
        self.dir = Path(export_dir)
        self.dir.mkdir(parents=True, exist_ok=True)

    def to_csv(self, items: list[dict], source: str = "all") -> str:
        if not items:
            logger.warning("No items to export.")
            return ""

        ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        path = self.dir / f"{source}_{ts}.csv"

        # Flatten data dict into columns prefixed with "data_"
        rows = []
        all_keys: set[str] = set()
        for item in items:
            flat = {
                "id": item.get("id"),
                "source": item.get("source"),
                "url": item.get("url"),
                "scraped_at": item.get("scraped_at"),
            }
            for k, v in (item.get("data") or {}).items():
                flat[f"data_{k}"] = json.dumps(v) if isinstance(v, (list, dict)) else v
            all_keys.update(flat.keys())
            rows.append(flat)

        fieldnames = sorted(all_keys)
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(rows)

        logger.info(f"Exported {len(rows)} rows → {path}")
        return str(path)
