from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from datetime import date
from typing import Any

import httpx

from app.collectors.base import CollectedItem

logger = logging.getLogger("summary")


PROMPT = """你是一个 AI 行业新闻分析师。

请根据下面的视频和新闻条目，生成一份中文 AI 新闻日报。

要求：
1. 不要逐条复述，要合并相同事件。
2. 优先关注模型发布、产品更新、公司动态、监管政策、产业融资、技术突破。
3. 过滤营销、带货、重复搬运和低信息密度内容。
4. 每条重点新闻说明为什么重要。
5. 保留来源链接。
6. 如果信息不足，要标注“待确认”。

输出结构：
- 今日重点
- 产品与模型动态
- 国内 AI 动态
- 海外 AI 动态
- 热门视频
- 值得继续关注
"""


@dataclass(frozen=True)
class LLMConfig:
    provider: str = "openai_compatible"
    model: str = ""
    api_key: str = ""
    base_url: str = ""
    timeout_seconds: int = 60


def summarize(items: list[CollectedItem], llm_config: LLMConfig) -> str:
    if not items:
        return _fallback_summary(items)
    if not llm_config.api_key and llm_config.provider != "none":
        logger.warning("llm_api_key_missing provider=%s using_fallback_summary=true", llm_config.provider)
        return _fallback_summary(items)

    try:
        if llm_config.provider in {"openai", "openai_compatible"}:
            return _summarize_openai_compatible(items, llm_config)
        if llm_config.provider == "ollama":
            return _summarize_ollama(items, llm_config)
        if llm_config.provider == "none":
            return _fallback_summary(items)
        logger.error("unsupported_llm_provider provider=%s", llm_config.provider)
    except Exception as exc:
        logger.exception("llm_summary_failed provider=%s error=%s", llm_config.provider, exc)
    return _fallback_summary(items)


def _summarize_openai_compatible(items: list[CollectedItem], config: LLMConfig) -> str:
    if not config.model:
        raise RuntimeError("LLM model is not configured.")
    if config.base_url:
        base_url = config.base_url.rstrip("/")
    elif config.provider == "openai":
        base_url = "https://api.openai.com/v1"
    else:
        raise RuntimeError("LLM base_url is not configured for openai_compatible provider.")
    url = f"{base_url}/chat/completions"
    payload = {
        "model": config.model,
        "messages": [
            {"role": "system", "content": PROMPT},
            {"role": "user", "content": f"条目：\n{_format_items(items)}"},
        ],
        "temperature": 0.2,
    }
    headers = {
        "Authorization": f"Bearer {config.api_key}",
        "Content-Type": "application/json",
    }
    with httpx.Client(timeout=config.timeout_seconds) as client:
        response = client.post(url, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()
    text = _extract_chat_completion_text(data)
    if not text:
        raise RuntimeError("LLM response did not include message content.")
    return text


def _summarize_ollama(items: list[CollectedItem], config: LLMConfig) -> str:
    if not config.model:
        raise RuntimeError("Ollama model is not configured.")
    base_url = config.base_url.rstrip("/") if config.base_url else "http://localhost:11434"
    url = f"{base_url}/api/chat"
    payload = {
        "model": config.model,
        "messages": [
            {"role": "system", "content": PROMPT},
            {"role": "user", "content": f"条目：\n{_format_items(items)}"},
        ],
        "stream": False,
        "options": {"temperature": 0.2},
    }
    with httpx.Client(timeout=config.timeout_seconds) as client:
        response = client.post(url, json=payload)
        response.raise_for_status()
        data = response.json()
    text = data.get("message", {}).get("content")
    if not text:
        raise RuntimeError("Ollama response did not include message content.")
    return str(text)


def _extract_chat_completion_text(data: dict[str, Any]) -> str:
    choices = data.get("choices") or []
    if not choices:
        return ""
    message = choices[0].get("message") or {}
    content = message.get("content")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for part in content:
            if isinstance(part, dict) and "text" in part:
                parts.append(str(part["text"]))
        return "\n".join(parts)
    return ""


def _format_items(items: list[CollectedItem]) -> str:
    lines = []
    for index, item in enumerate(items, start=1):
        lines.append(
            f"{index}. [{item.platform}] {item.title} | 作者：{item.author} | 链接：{item.url} | 简介：{item.description[:160]}"
        )
    return "\n".join(lines)


def _fallback_summary(items: list[CollectedItem]) -> str:
    today = date.today().isoformat()
    lines = [f"# AI 新闻日报 - {today}", "", "## 今日重点"]
    if not items:
        lines.append("- 今日未采集到足够 AI 相关新闻。")
    else:
        for item in items[:10]:
            lines.append(f"- [{item.platform}] {item.title} - {item.author}：{item.url}")
    lines.extend(["", "## 产品与模型动态", "- 待模型总结。", "", "## 热门视频"])
    for item in items[:10]:
        lines.append(f"- {item.title}：{item.url}")
    return "\n".join(lines)
