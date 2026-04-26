from __future__ import annotations

from datetime import datetime, timezone

from app.collectors.base import CollectedItem


def rank_items(items: list[CollectedItem], keywords: list[str]) -> list[CollectedItem]:
    return sorted(items, key=lambda item: score_item(item, keywords), reverse=True)


def score_item(item: CollectedItem, keywords: list[str]) -> float:
    text = f"{item.title} {item.description}".lower()
    relevance = sum(1 for keyword in keywords if keyword.lower() in text)
    views = float(item.metrics.get("views", 0) or 0)
    engagement = min(1.0, views / 100000.0)
    freshness = 0.5
    if item.published_at:
        age_hours = max(0.0, (datetime.now(timezone.utc) - item.published_at).total_seconds() / 3600)
        freshness = max(0.0, 1.0 - age_hours / 72.0)
    return relevance * 0.35 + freshness * 0.20 + engagement * 0.25 + item.source_weight * 0.10
