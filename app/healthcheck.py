from __future__ import annotations

import os
from pathlib import Path

from app.config import Settings, load_douyin_accounts
from app.db.models import init_db


def run_healthcheck(settings: Settings) -> list[tuple[str, str, str]]:
    results: list[tuple[str, str, str]] = []
    results.append(("config", "ok" if settings.config_path.exists() else "fail", str(settings.config_path)))
    results.append((".env", "ok" if (settings.root_dir / ".env").exists() else "warn", ".env is optional but needed for secrets"))

    db_path = settings.path(settings.get("storage", "sqlite_path", default="./ai_news.db"))
    try:
        init_db(db_path)
        results.append(("database", "ok", str(db_path)))
    except Exception as exc:
        results.append(("database", "fail", str(exc)))

    for key in ["tmp", "logs"]:
        path = settings.root_dir / key
        try:
            path.mkdir(parents=True, exist_ok=True)
            probe = path / ".write_probe"
            probe.write_text("ok", encoding="utf-8")
            probe.unlink(missing_ok=True)
            results.append((key, "ok", str(path)))
        except Exception as exc:
            results.append((key, "fail", str(exc)))

    keywords = settings.get("keywords", default=[])
    results.append(("keywords", "ok" if keywords else "fail", f"count={len(keywords)}"))

    accounts = load_douyin_accounts(settings)
    results.append(("douyin_accounts", "ok" if accounts else "warn", f"enabled_count={len(accounts)}"))

    webhook_env = settings.get("delivery", "feishu", "webhook_env", default="FEISHU_WEBHOOK")
    results.append(("feishu_webhook", "ok" if os.getenv(webhook_env) else "warn", f"env={webhook_env}"))

    provider = settings.get("summary", "provider", default="openai_compatible")
    api_key_env = settings.get("summary", "api_key_env", default="LLM_API_KEY")
    model_env = settings.get("summary", "model_env", default="LLM_MODEL")
    base_url_env = settings.get("summary", "base_url_env", default="LLM_BASE_URL")
    if provider == "ollama":
        results.append(("llm_api_key", "ok", "ollama does not require api key by default"))
    elif provider == "none":
        results.append(("llm_api_key", "ok", "summary provider disabled; fallback summary will be used"))
    else:
        results.append(("llm_api_key", "ok" if os.getenv(api_key_env) else "warn", f"env={api_key_env}"))
    results.append(("llm_model", "ok" if os.getenv(model_env) or settings.get("summary", "model") or provider == "none" else "warn", f"env={model_env}"))
    if provider == "openai":
        detail = f"env={base_url_env}; default=https://api.openai.com/v1 when empty"
        results.append(("llm_base_url", "ok", detail))
    elif provider == "openai_compatible":
        results.append(("llm_base_url", "ok" if os.getenv(base_url_env) or settings.get("summary", "base_url") else "warn", f"env={base_url_env}"))
    else:
        results.append(("llm_base_url", "ok" if os.getenv(base_url_env) or settings.get("summary", "base_url") or provider == "none" else "warn", f"env={base_url_env}"))
    return results


def persist_healthcheck(db_path: Path, results: list[tuple[str, str, str]]) -> None:
    from app.db.session import transaction

    with transaction(db_path) as conn:
        for name, status, details in results:
            conn.execute(
                "INSERT INTO health_checks(check_name, status, details) VALUES (?, ?, ?)",
                (name, status, details),
            )
