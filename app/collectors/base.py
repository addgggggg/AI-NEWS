from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class CollectedItem:
    platform: str
    external_id: str
    title: str
    author: str
    url: str
    published_at: datetime | None = None
    description: str = ""
    metrics: dict[str, int | float] = field(default_factory=dict)
    source_weight: float = 1.0
    raw: dict[str, Any] = field(default_factory=dict)

    def published_iso(self) -> str:
        value = self.published_at or datetime.now(timezone.utc)
        return value.isoformat()
