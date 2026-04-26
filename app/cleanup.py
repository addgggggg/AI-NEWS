from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path

from app.db.session import transaction

logger = logging.getLogger("app")


def cleanup(db_path: Path, temp_report_dir: Path, keep_failed_hours: int, log_dir: Path, log_retention_days: int) -> None:
    now = datetime.now(timezone.utc)
    deleted_dirs = 0
    if temp_report_dir.exists():
        cutoff = now - timedelta(hours=keep_failed_hours)
        for child in temp_report_dir.iterdir():
            if child.is_dir():
                modified = datetime.fromtimestamp(child.stat().st_mtime, tz=timezone.utc)
                if modified < cutoff:
                    _remove_tree(child)
                    deleted_dirs += 1
    with transaction(db_path) as conn:
        deleted_hashes = conn.execute("DELETE FROM dedupe_hashes WHERE expires_at < ?", (now.isoformat(),)).rowcount
    deleted_logs = _delete_old_logs(log_dir, now - timedelta(days=log_retention_days))
    logger.info("cleanup_done deleted_report_dirs=%s deleted_hashes=%s deleted_logs=%s", deleted_dirs, deleted_hashes, deleted_logs)


def _remove_tree(path: Path) -> None:
    for child in path.iterdir():
        if child.is_dir():
            _remove_tree(child)
        else:
            child.unlink(missing_ok=True)
    path.rmdir()


def _delete_old_logs(log_dir: Path, cutoff: datetime) -> int:
    if not log_dir.exists():
        return 0
    count = 0
    for item in log_dir.glob("*.log*"):
        modified = datetime.fromtimestamp(item.stat().st_mtime, tz=timezone.utc)
        if modified < cutoff:
            item.unlink(missing_ok=True)
            count += 1
    return count
