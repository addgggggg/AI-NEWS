from __future__ import annotations

import logging
import re
import time
from typing import Any

import httpx

from app.collectors.base import CollectedItem

logger = logging.getLogger("collector")


class DouyinCollector:
    def __init__(
        self,
        interval_seconds: int = 5,
        render_with_browser: bool = False,
        browser_headless: bool = True,
        browser_wait_seconds: int = 8,
    ) -> None:
        self.interval_seconds = interval_seconds
        self.render_with_browser = render_with_browser
        self.browser_headless = browser_headless
        self.browser_wait_seconds = browser_wait_seconds

    def collect(self, accounts: list[dict[str, Any]]) -> list[CollectedItem]:
        if self.render_with_browser:
            return self._collect_with_browser(accounts)
        return self._collect_with_http(accounts)

    def _collect_with_http(self, accounts: list[dict[str, Any]]) -> list[CollectedItem]:
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
                if "/user/" not in profile_url:
                    logger.warning(
                        "douyin_account_skipped name=%s reason=profile_url_must_be_user_homepage url=%s",
                        name,
                        profile_url,
                    )
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

    def _collect_with_browser(self, accounts: list[dict[str, Any]]) -> list[CollectedItem]:
        results: list[CollectedItem] = []
        try:
            from playwright.sync_api import sync_playwright
        except Exception as exc:
            logger.error("douyin_browser_unavailable error=%s", exc)
            return self._collect_with_http(accounts)

        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=self.browser_headless)
            context = browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/124.0.0.0 Safari/537.36"
                ),
                locale="zh-CN",
                viewport={"width": 1365, "height": 900},
            )
            page = context.new_page()
            for account in accounts:
                name = account.get("name", "")
                profile_url = account.get("profile_url", "")
                if not name or not profile_url or "REPLACE_ME" in profile_url:
                    logger.info("douyin_account_skipped name=%s reason=missing_profile_url", name)
                    continue
                if "/user/" not in profile_url:
                    logger.warning(
                        "douyin_account_skipped name=%s reason=profile_url_must_be_user_homepage url=%s",
                        name,
                        profile_url,
                    )
                    continue
                try:
                    page.goto(profile_url, wait_until="domcontentloaded", timeout=30000)
                    page.wait_for_timeout(self.browser_wait_seconds * 1000)
                    if "验证码" in page.title():
                        logger.warning("douyin_account_blocked_by_captcha name=%s", name)
                        continue
                    html = page.content()
                    found = self._parse_profile_html(html, account)
                    if not found:
                        found = self._parse_links_from_browser(page, account)
                    results.extend(found)
                    logger.info("douyin_account_done name=%s count=%s mode=browser", name, len(found))
                except Exception as exc:
                    logger.exception("douyin_account_failed name=%s mode=browser error=%s", name, exc)
                time.sleep(self.interval_seconds)
            context.close()
            browser.close()
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

    def _parse_links_from_browser(self, page: Any, account: dict[str, Any]) -> list[CollectedItem]:
        name = str(account.get("name") or "")
        weight = float(account.get("weight") or 1.0)
        hrefs = page.eval_on_selector_all("a[href]", "nodes => nodes.map(node => node.href)")
        video_ids: list[str] = []
        for href in hrefs:
            match = re.search(r"/video/([0-9]+)", str(href))
            if match:
                video_ids.append(match.group(1))
        items: list[CollectedItem] = []
        for video_id in list(dict.fromkeys(video_ids))[:10]:
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
