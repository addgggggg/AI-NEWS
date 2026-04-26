from __future__ import annotations

import logging
import time
from html import unescape
from datetime import datetime, timezone
from typing import Any

import httpx

from app.collectors.base import CollectedItem

logger = logging.getLogger("collector")


class BilibiliCollector:
    SEARCH_URL = "https://api.bilibili.com/x/web-interface/search/type"
    HOME_URL = "https://www.bilibili.com/"

    def __init__(self, max_results_per_keyword: int = 20, interval_seconds: int = 1) -> None:
        self.max_results_per_keyword = max_results_per_keyword
        self.interval_seconds = interval_seconds

    def collect(self, keywords: list[str]) -> list[CollectedItem]:
        results: list[CollectedItem] = []
        headers = self._headers()
        with httpx.Client(timeout=20, headers=headers, follow_redirects=True) as client:
            self._warmup(client)
            for keyword in keywords:
                try:
                    params = {
                        "search_type": "video",
                        "keyword": keyword,
                        "order": "pubdate",
                        "page": 1,
                    }
                    response = client.get(self.SEARCH_URL, params=params)
                    if response.status_code == 412:
                        logger.warning("bilibili_keyword_blocked keyword=%s status=412", keyword)
                        time.sleep(max(3, self.interval_seconds * 2))
                        continue
                    response.raise_for_status()
                    payload = response.json()
                    items = payload.get("data", {}).get("result", []) or []
                    for item in items[: self.max_results_per_keyword]:
                        parsed = self._parse_item(item)
                        if parsed:
                            results.append(parsed)
                    logger.info("bilibili_keyword_done keyword=%s count=%s", keyword, min(len(items), self.max_results_per_keyword))
                except Exception as exc:
                    logger.exception("bilibili_keyword_failed keyword=%s error=%s", keyword, exc)
                time.sleep(self.interval_seconds)
        return results

    def _warmup(self, client: httpx.Client) -> None:
        try:
            client.get(self.HOME_URL)
        except Exception as exc:
            logger.warning("bilibili_warmup_failed error=%s", exc)

    def _parse_item(self, item: dict[str, Any]) -> CollectedItem | None:
        bvid = str(item.get("bvid") or "")
        aid = str(item.get("aid") or "")
        external_id = bvid or aid
        if not external_id:
            return None
        title = self._clean_html(str(item.get("title") or ""))
        author = str(item.get("author") or "")
        url = item.get("arcurl") or f"https://www.bilibili.com/video/{external_id}"
        published_at = None
        pubdate = item.get("pubdate")
        if isinstance(pubdate, int):
            published_at = datetime.fromtimestamp(pubdate, tz=timezone.utc)
        metrics = {
            "views": self._to_int(item.get("play")),
            "danmaku": self._to_int(item.get("video_review")),
        }
        return CollectedItem(
            platform="bilibili",
            external_id=external_id,
            title=title,
            author=author,
            url=str(url),
            published_at=published_at,
            description=self._clean_html(str(item.get("description") or "")),
            metrics=metrics,
            raw={},
        )

    @staticmethod
    def _clean_html(value: str) -> str:
        cleaned = value.replace("<em class=\"keyword\">", "").replace("</em>", "").strip()
        return unescape(cleaned)

    @staticmethod
    def _to_int(value: Any) -> int:
        try:
            if isinstance(value, str):
                value = value.replace(",", "")
            return int(float(value))
        except Exception:
            return 0

    @staticmethod
    def _headers() -> dict[str, str]:
        return {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Origin": "https://www.bilibili.com",
            "Referer": "https://www.bilibili.com/",
        }
