from __future__ import annotations

from apscheduler.schedulers.blocking import BlockingScheduler

from app.config import Settings


def start_scheduler(settings: Settings, job_func) -> None:
    timezone = settings.get("schedule", "timezone", default="Asia/Shanghai")
    run_at = settings.get("schedule", "daily_run_at", default="08:30")
    hour, minute = [int(part) for part in run_at.split(":", 1)]
    scheduler = BlockingScheduler(timezone=timezone)
    scheduler.add_job(job_func, "cron", hour=hour, minute=minute)
    scheduler.start()
