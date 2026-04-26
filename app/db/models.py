from __future__ import annotations

from pathlib import Path

from app.db.session import transaction


SCHEMA = """
CREATE TABLE IF NOT EXISTS job_runs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  job_date TEXT NOT NULL,
  started_at TEXT NOT NULL,
  finished_at TEXT,
  status TEXT NOT NULL,
  items_collected_count INTEGER DEFAULT 0,
  items_selected_count INTEGER DEFAULT 0,
  delivered INTEGER DEFAULT 0,
  error_message TEXT,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS dedupe_hashes (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  hash_value TEXT NOT NULL UNIQUE,
  platform TEXT,
  first_seen_at TEXT DEFAULT CURRENT_TIMESTAMP,
  expires_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_dedupe_hashes_expires_at
ON dedupe_hashes(expires_at);

CREATE TABLE IF NOT EXISTS health_checks (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  checked_at TEXT DEFAULT CURRENT_TIMESTAMP,
  check_name TEXT NOT NULL,
  status TEXT NOT NULL,
  details TEXT
);
"""


def init_db(db_path: Path) -> None:
    with transaction(db_path) as conn:
        conn.executescript(SCHEMA)
