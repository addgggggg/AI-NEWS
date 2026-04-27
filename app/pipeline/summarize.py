from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from datetime import date
from typing import Any

import httpx

from app.collectors.base import CollectedItem

logger = logging.getLogger("summary")


PROMPT = """你是一个 AI 行业新闻编辑，负责把短视频和视频平台信息整理成一份纯文字中文简报。

请根据下面的条目生成一份“纯文字版 AI 新闻简报”。

硬性要求：
1. 只输出纯文本，不使用 Markdown 表格，不使用加粗、标题符号、代码块或复杂排版。
2. 不要逐条搬运标题，要把相同或相近事件合并成一条新闻。
3. 优先保留模型发布、产品更新、公司动态、监管政策、产业融资、技术突破和高质量观点。
4. 过滤纯营销、卖课、标题党、重复搬运、低信息密度内容。
5. 每条重点新闻用 2-4 句话说明：发生了什么、为什么重要、信息是否待确认。
6. 不要编造条目中没有的信息；无法确认时写“待确认”。
7. 每条新闻末尾保留 1-2 个来源链接。
8. 控制篇幅，整份简报建议 800-1500 字。

输出格式必须如下：

AI 新闻简报（YYYY-MM-DD）

一、今日重点
1. 标题
   摘要：……
   重要性：……
   来源：……

二、产品与模型动态
1. ……

三、国内 AI 动态
1. ……

四、海外 AI 动态
1. ……

五、值得关注的视频
1. ……

六、继续关注
1. ……
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
    lines = [f"AI 新闻简报（{today}）", "", "一、今日重点"]
    if not items:
        lines.append("1. 今日未采集到足够 AI 相关新闻。")
    else:
        for index, item in enumerate(items[:8], start=1):
            lines.append(f"{index}. {item.title}")
            lines.append(f"   摘要：来自 {item.platform} 的相关内容，作者为 {item.author or '未知'}。")
            lines.append("   重要性：模型服务不可用，当前为降级摘要，未进行深度合并分析。")
            lines.append(f"   来源：{item.url}")
    lines.extend(["", "二、产品与模型动态", "1. 待模型总结。", "", "三、国内 AI 动态", "1. 待模型总结。", "", "四、海外 AI 动态", "1. 待模型总结。", "", "五、值得关注的视频"])
    for index, item in enumerate(items[:8], start=1):
        lines.append(f"{index}. {item.title}。来源：{item.url}")
    lines.extend(["", "六、继续关注", "1. 建议检查 LLM 配置，以获得完整的事件合并和行业分析。"])
    return "\n".join(lines)
