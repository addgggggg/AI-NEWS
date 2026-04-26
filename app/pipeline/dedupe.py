from __future__ import annotations

import hashlib
import re
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

from app.collectors.base import CollectedItem
from app.db.session import transaction


def normalize_title(title: str) -> str:
    return re.sub(r"\s+", "", title).lower()


def item_hashes(item: CollectedItem) -> list[str]:
    candidates = [
        f"{item.platform}:external:{item.external_id}",
        f"{item.platform}:url:{item.url}",
        f"title:{normalize_title(item.title)}",
        f"title_author:{normalize_title(item.title)}:{item.author.lower()}",
    ]
    return [hashlib.sha256(value.encode("utf-8")).hexdigest() for value in candidates if value]


def filter_new_items(db_path: Path, items: list[CollectedItem], retention_days: int = 7) -> list[CollectedItem]:
    now = datetime.now(timezone.utc)
    expires_at = (now + timedelta(days=retention_days)).isoformat()
    output: list[CollectedItem] = []
    with transaction(db_path) as conn:
        for item in items:
            hashes = item_hashes(item)
            if _exists_any(conn, hashes):
                continue
            output.append(item)
            for value in hashes:
                conn.execute(
                    "INSERT OR IGNORE INTO dedupe_hashes(hash_value, platform, expires_at) VALUES (?, ?, ?)",
                    (value, item.platform, expires_at),
                )
    return output


def _exists_any(conn: sqlite3.Connection, hashes: list[str]) -> bool:
    for value in hashes:
        row = conn.execute("SELECT 1 FROM dedupe_hashes WHERE hash_value = ? LIMIT 1", (value,)).fetchone()
        if row:
            return True
    return False
