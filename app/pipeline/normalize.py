from __future__ import annotations

from app.collectors.base import CollectedItem


def normalize_items(items: list[CollectedItem]) -> list[CollectedItem]:
    output: list[CollectedItem] = []
    for item in items:
        item.title = item.title.strip()
        item.author = item.author.strip()
        item.url = item.url.strip()
        item.description = item.description.strip()
        if item.title and item.url:
            output.append(item)
    return output
