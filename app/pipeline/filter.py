from __future__ import annotations

from app.collectors.base import CollectedItem


def filter_ai_related(items: list[CollectedItem], keywords: list[str]) -> list[CollectedItem]:
    lowered = [keyword.lower() for keyword in keywords]
    output: list[CollectedItem] = []
    for item in items:
        text = f"{item.title} {item.description}".lower()
        if any(keyword.lower() in text for keyword in lowered):
            output.append(item)
    return output
