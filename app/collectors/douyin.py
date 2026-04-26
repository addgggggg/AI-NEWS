from __future__ import annotations

import logging
import re
import time
from typing import Any

import httpx

from app.collectors.base import CollectedItem

logger = logging.getLogger("collector")


class DouyinCollector:
    def __init__(self, interval_seconds: int = 5) -> None:
        self.interval_seconds = interval_seconds

    def collect(self, accounts: list[dict[str, Any]]) -> list[CollectedItem]:
        results: list[CollectedItem] = []
        headers = {
            "User-Agent": "Mozilla/5.0 AI-News-Agent/0.1",
            "Referer": "https://www.douyin.com/",
        }
        with httpx.Client(timeout=25, headers=headers, follow_redirects=True) as client:
            for account in accounts:
                name = account.get("name", "")
                profile_url = account.get("profile_url", "")
                if not name or not profile_url or "REPLACE_ME" in profile_url:
                    logger.info("douyin_account_skipped name=%s reason=missing_profile_url", name)
                    continue
                try:
                    response = client.get(profile_url)
                    response.raise_for_status()
                    found = self._parse_profile_html(response.text, account)
                    results.extend(found)
                    logger.info("douyin_account_done name=%s count=%s", name, len(found))
                except Exception as exc:
                    logger.exception("douyin_account_failed name=%s error=%s", name, exc)
                time.sleep(self.interval_seconds)
        return results

    def _parse_profile_html(self, html: str, account: dict[str, Any]) -> list[CollectedItem]:
        # Douyin frequently changes rendered data. This parser intentionally only
        # extracts public links when they are visible in the returned HTML.
        name = str(account.get("name") or "")
        weight = float(account.get("weight") or 1.0)
        video_ids = list(dict.fromkeys(re.findall(r"/video/([0-9]+)", html)))
        items: list[CollectedItem] = []
        for video_id in video_ids[:10]:
            items.append(
                CollectedItem(
                    platform="douyin",
                    external_id=video_id,
                    title=f"{name} 发布的新视频",
                    author=name,
                    url=f"https://www.douyin.com/video/{video_id}",
                    source_weight=weight,
                )
            )
        return items
