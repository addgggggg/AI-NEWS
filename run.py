from __future__ import annotations

import argparse
import logging
import time
from datetime import date, datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import httpx

from app.cleanup import cleanup as cleanup_task
from app.collectors.bilibili import BilibiliCollector
from app.collectors.douyin import DouyinCollector
from app.config import load_douyin_accounts, load_settings
from app.db.models import init_db
from app.db.session import transaction
from app.delivery.feishu import send_text
from app.healthcheck import persist_healthcheck, run_healthcheck
from app.logging_config import setup_logging
from app.pipeline.dedupe import filter_new_items
from app.pipeline.filter import filter_ai_related
from app.pipeline.normalize import normalize_items
from app.pipeline.rank import rank_items
from app.pipeline.summarize import LLMConfig, summarize
from app.scheduler import start_scheduler


def main() -> None:
    parser = argparse.ArgumentParser(description="AI News Agent")
    parser.add_argument("command", choices=["init-db", "once", "auto", "schedule", "healthcheck", "cleanup", "dry-run"])
    parser.add_argument("--collector", choices=["bilibili", "douyin"])
    parser.add_argument("--summary", action="store_true")
    parser.add_argument("--delivery", action="store_true")
    args = parser.parse_args()

    settings = load_settings()
    setup_logging(settings.root_dir)
    db_path = settings.path(settings.get("storage", "sqlite_path", default="./ai_news.db"))

    if args.command == "init-db":
        init_db(db_path)
        print(f"SQLite initialized: {db_path}")
        return
    if args.command == "healthcheck":
        init_db(db_path)
        results = run_healthcheck(settings)
        persist_healthcheck(db_path, results)
        for name, status, details in results:
            print(f"{status.upper():5} {name}: {details}")
        return
    if args.command == "cleanup":
        init_db(db_path)
        run_cleanup(settings, db_path)
        return
    if args.command == "dry-run":
        init_db(db_path)
        run_dry_run(settings, args)
        return
    if args.command == "once":
        init_db(db_path)
        run_once(settings, db_path)
        return
    if args.command == "auto":
        init_db(db_path)
        run_auto(settings, db_path)
        return
    if args.command == "schedule":
        init_db(db_path)
        start_scheduler(settings, lambda: run_once(settings, db_path))


def run_once(settings, db_path: Path) -> None:
    logger = logging.getLogger("app")
    started_at = datetime.now(timezone.utc)
    job_id = create_job_run(db_path, started_at, today_for_settings(settings))
    report_path: Path | None = None
    delivered = False
    selected_count = 0
    collected_count = 0
    try:
        items = normalize_items(collect_all(settings))
        collected_count = len(items)
        keywords = settings.get("keywords", default=[])
        filtered = filter_ai_related(items, keywords)
        new_items = filter_new_items(db_path, filtered, settings.get("dedupe", "retention_days", default=7))
        ranked = rank_items(new_items, keywords)
        max_items = settings.get("summary", "max_items", default=40)
        selected = ranked[:max_items]
        selected_count = len(selected)
        if not selected:
            raise RuntimeError("No AI news items selected; report not sent.")
        report = summarize(selected, llm_config=get_llm_config(settings))
        report_path = write_report(settings, report)
        delivered = send_text(report, settings.get("delivery", "feishu", "webhook_env", default="FEISHU_WEBHOOK"))
        if not delivered:
            raise RuntimeError("Feishu delivery failed.")
        if settings.get("storage", "delete_after_success", default=True) and report_path:
            remove_report_dir(report_path.parent)
        finish_job_run(db_path, job_id, "success", collected_count, selected_count, delivered=True)
        logger.info("job_done status=success collected=%s selected=%s", collected_count, selected_count)
    except Exception as exc:
        logger.exception("job_failed error=%s", exc)
        finish_job_run(db_path, job_id, "failed", collected_count, selected_count, delivered=delivered, error=str(exc))
    finally:
        if settings.get("cleanup", "run_after_job", default=True):
            run_cleanup(settings, db_path)


def run_auto(settings, db_path: Path) -> None:
    logger = logging.getLogger("app")
    interval_seconds = settings.get("auto_run", "check_interval_seconds", default=1800)
    start_delay_seconds = settings.get("auto_run", "start_delay_seconds", default=0)
    logger.info("auto_run_started interval_seconds=%s start_delay_seconds=%s", interval_seconds, start_delay_seconds)
    if start_delay_seconds:
        time.sleep(start_delay_seconds)
    while True:
        try:
            today = today_for_settings(settings)
            if has_successful_delivery(db_path, today):
                logger.info("auto_run_skip reason=already_delivered today=%s", today)
            elif internet_available(settings):
                logger.info("auto_run_trigger today=%s", today)
                run_once(settings, db_path)
            else:
                logger.info("auto_run_wait reason=network_unavailable today=%s", today)
        except KeyboardInterrupt:
            logger.info("auto_run_stopped")
            raise
        except Exception as exc:
            logger.exception("auto_run_loop_error error=%s", exc)
        time.sleep(interval_seconds)


def today_for_settings(settings) -> str:
    timezone_name = settings.get("schedule", "timezone", default="Asia/Shanghai")
    return datetime.now(ZoneInfo(timezone_name)).date().isoformat()


def has_successful_delivery(db_path: Path, job_date: str) -> bool:
    with transaction(db_path) as conn:
        row = conn.execute(
            """
            SELECT 1
            FROM job_runs
            WHERE job_date = ? AND status = 'success' AND delivered = 1
            LIMIT 1
            """,
            (job_date,),
        ).fetchone()
    return row is not None


def internet_available(settings) -> bool:
    urls = settings.get("auto_run", "network_check_urls", default=["https://www.bilibili.com", "https://open.feishu.cn"])
    timeout_seconds = settings.get("auto_run", "network_check_timeout_seconds", default=8)
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        )
    }
    for url in urls:
        try:
            response = httpx.get(url, headers=headers, timeout=timeout_seconds, follow_redirects=True)
            if response.status_code < 500:
                return True
        except Exception:
            continue
    return False


def collect_all(settings) -> list:
    items = []
    keywords = settings.get("keywords", default=[])
    if settings.get("bilibili", "enabled", default=True):
        collector = BilibiliCollector(
            max_results_per_keyword=settings.get("bilibili", "max_results_per_keyword", default=20),
            interval_seconds=settings.get("bilibili", "request_interval_seconds", default=1),
        )
        items.extend(collector.collect(keywords))
    if settings.get("douyin", "enabled", default=True):
        collector = DouyinCollector(
            interval_seconds=settings.get("douyin", "request_interval_seconds", default=5),
            render_with_browser=settings.get("douyin", "render_with_browser", default=False),
            browser_headless=settings.get("douyin", "browser_headless", default=True),
            browser_wait_seconds=settings.get("douyin", "browser_wait_seconds", default=8),
        )
        items.extend(collector.collect(load_douyin_accounts(settings)))
    return items


def run_dry_run(settings, args) -> None:
    if args.collector == "bilibili":
        items = BilibiliCollector(max_results_per_keyword=3).collect(settings.get("keywords", default=[])[:2])
        print(f"Bilibili dry-run items: {len(items)}")
    elif args.collector == "douyin":
        items = DouyinCollector(
            interval_seconds=1,
            render_with_browser=settings.get("douyin", "render_with_browser", default=False),
            browser_headless=settings.get("douyin", "browser_headless", default=True),
            browser_wait_seconds=settings.get("douyin", "browser_wait_seconds", default=8),
        ).collect(load_douyin_accounts(settings))
        print(f"Douyin dry-run items: {len(items)}")
    elif args.summary:
        report = summarize([], llm_config=get_llm_config(settings))
        print(report)
    elif args.delivery:
        ok = send_text("AI News Agent 测试消息", settings.get("delivery", "feishu", "webhook_env", default="FEISHU_WEBHOOK"))
        print(f"Feishu delivery dry-run: {ok}")
    else:
        print("Specify --collector bilibili|douyin, --summary, or --delivery.")


def run_cleanup(settings, db_path: Path) -> None:
    cleanup_task(
        db_path=db_path,
        temp_report_dir=settings.path(settings.get("storage", "temp_report_dir", default="./tmp/reports")),
        keep_failed_hours=settings.get("storage", "keep_failed_tmp_hours", default=24),
        log_dir=settings.root_dir / "logs",
        log_retention_days=settings.get("cleanup", "log_retention_days", default=14),
    )


def get_llm_config(settings) -> LLMConfig:
    import os

    provider = settings.get("summary", "provider", default="openai_compatible")
    model_env = settings.get("summary", "model_env", default="LLM_MODEL")
    api_key_env = settings.get("summary", "api_key_env", default="LLM_API_KEY")
    base_url_env = settings.get("summary", "base_url_env", default="LLM_BASE_URL")
    return LLMConfig(
        provider=provider,
        model=os.getenv(model_env) or settings.get("summary", "model", default=""),
        api_key=os.getenv(api_key_env) or settings.get("summary", "api_key", default=""),
        base_url=os.getenv(base_url_env) or settings.get("summary", "base_url", default=""),
        timeout_seconds=settings.get("summary", "timeout_seconds", default=60),
    )


def write_report(settings, report: str) -> Path:
    report_dir = settings.path(settings.get("storage", "temp_report_dir", default="./tmp/reports")) / date.today().isoformat()
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / "daily_report.md"
    report_path.write_text(report, encoding="utf-8")
    return report_path


def remove_report_dir(path: Path) -> None:
    for child in path.iterdir():
        if child.is_dir():
            remove_report_dir(child)
        else:
            child.unlink(missing_ok=True)
    path.rmdir()


def create_job_run(db_path: Path, started_at: datetime, job_date: str) -> int:
    with transaction(db_path) as conn:
        cursor = conn.execute(
            "INSERT INTO job_runs(job_date, started_at, status) VALUES (?, ?, ?)",
            (job_date, started_at.isoformat(), "running"),
        )
        return int(cursor.lastrowid)


def finish_job_run(
    db_path: Path,
    job_id: int,
    status: str,
    collected_count: int,
    selected_count: int,
    delivered: bool,
    error: str | None = None,
) -> None:
    with transaction(db_path) as conn:
        conn.execute(
            """
            UPDATE job_runs
            SET finished_at = ?, status = ?, items_collected_count = ?,
                items_selected_count = ?, delivered = ?, error_message = ?
            WHERE id = ?
            """,
            (
                datetime.now(timezone.utc).isoformat(),
                status,
                collected_count,
                selected_count,
                1 if delivered else 0,
                error,
                job_id,
            ),
        )


if __name__ == "__main__":
    main()
