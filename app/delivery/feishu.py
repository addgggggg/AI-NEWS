from __future__ import annotations

import logging
import os

import httpx

logger = logging.getLogger("delivery")


def send_text(markdown: str, webhook_env: str = "FEISHU_WEBHOOK") -> bool:
    webhook = os.getenv(webhook_env)
    if not webhook:
        logger.error("feishu_webhook_missing env=%s", webhook_env)
        return False
    payload = {
        "msg_type": "text",
        "content": {"text": markdown[:18000]},
    }
    try:
        response = httpx.post(webhook, json=payload, timeout=20)
        response.raise_for_status()
        data = response.json()
        ok = data.get("code") in (0, None) or data.get("StatusCode") in (0, None)
        logger.info("feishu_delivery_done ok=%s", ok)
        return bool(ok)
    except Exception as exc:
        logger.exception("feishu_delivery_failed error=%s", exc)
        return False
