from __future__ import annotations

import hashlib
import logging
import time
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from html import unescape
from typing import Any

import feedparser

from app.collectors.base import CollectedItem

logger = logging.getLogger("collector")


class RssCollector:
    def __init__(self, max_items_per_source: int = 10, interval_seconds: int = 1) -> None:
        self.max_items_per_source = max_items_per_source
        self.interval_seconds = interval_seconds

    def collect(self, sources: list[dict[str, Any]]) -> list[CollectedItem]:
        results: list[CollectedItem] = []
        for source in sources:
            if not source.get("enabled", True):
                continue
            name = str(source.get("name") or "")
            url = str(source.get("url") or "")
            if not name or not url:
                logger.warning("rss_source_skipped reason=missing_name_or_url name=%s", name)
                continue
            try:
                feed = feedparser.parse(url)
                if getattr(feed, "bozo", False):
                    logger.warning("rss_source_parse_warning name=%s error=%s", name, getattr(feed, "bozo_exception", "unknown"))
                entries = list(feed.entries or [])[: self.max_items_per_source]
                parsed = [self._parse_entry(source, entry) for entry in entries]
                parsed = [item for item in parsed if item is not None]
                results.extend(parsed)
                logger.info("rss_source_done name=%s count=%s", name, len(parsed))
            except Exception as exc:
                logger.exception("rss_source_failed name=%s error=%s", name, exc)
            time.sleep(self.interval_seconds)
        return results

    def _parse_entry(self, source: dict[str, Any], entry: Any) -> CollectedItem | None:
        title = _clean_text(str(getattr(entry, "title", "") or ""))
        link = str(getattr(entry, "link", "") or "")
        if not title or not link:
            return None
        source_name = str(source.get("name") or "RSS")
        external_id = str(getattr(entry, "id", "") or getattr(entry, "guid", "") or link)
        if len(external_id) > 180:
            external_id = hashlib.sha256(external_id.encode("utf-8")).hexdigest()
        author = str(getattr(entry, "author", "") or source_name)
        description = _clean_text(
            str(getattr(entry, "summary", "") or getattr(entry, "description", "") or "")
        )
        published_at = _published_at(entry)
        weight = float(source.get("weight") or 1.0)
        return CollectedItem(
            platform="rss",
            external_id=f"{source_name}:{external_id}",
            title=title,
            author=author,
            url=link,
            published_at=published_at,
            description=description,
            source_weight=weight,
            raw={},
        )


def _published_at(entry: Any) -> datetime | None:
    for attr in ["published", "updated", "created"]:
        value = getattr(entry, attr, None)
        if not value:
            continue
        try:
            parsed = parsedate_to_datetime(str(value))
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            return parsed
        except Exception:
            continue
    return None


def _clean_text(value: str) -> str:
    value = unescape(value)
    return " ".join(value.replace("\n", " ").replace("\r", " ").split())
