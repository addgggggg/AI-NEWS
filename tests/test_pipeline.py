from __future__ import annotations

import sqlite3
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from app.collectors.base import CollectedItem
from app.db.models import init_db
from app.pipeline.dedupe import filter_new_items
from app.pipeline.filter import filter_ai_related
from app.pipeline.normalize import normalize_items
from app.pipeline.rank import rank_items
from run import has_successful_delivery


class PipelineTest(unittest.TestCase):
    def test_normalize_filters_empty_url(self) -> None:
        items = [
            CollectedItem(platform="x", external_id="1", title=" title ", author=" a ", url=" "),
            CollectedItem(platform="x", external_id="2", title=" AI ", author=" a ", url=" https://example.com "),
        ]
        output = normalize_items(items)
        self.assertEqual(len(output), 1)
        self.assertEqual(output[0].title, "AI")

    def test_filter_ai_related(self) -> None:
        items = [
            CollectedItem(platform="x", external_id="1", title="AI news", author="a", url="https://a.test"),
            CollectedItem(platform="x", external_id="2", title="food", author="a", url="https://b.test"),
        ]
        output = filter_ai_related(items, ["AI"])
        self.assertEqual([item.external_id for item in output], ["1"])

    def test_dedupe_keeps_hash_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "test.db"
            init_db(db_path)
            item = CollectedItem(platform="x", external_id="1", title="AI news", author="a", url="https://a.test")
            self.assertEqual(len(filter_new_items(db_path, [item], retention_days=7)), 1)
            self.assertEqual(len(filter_new_items(db_path, [item], retention_days=7)), 0)
            conn = sqlite3.connect(db_path)
            rows = conn.execute("SELECT hash_value FROM dedupe_hashes").fetchall()
            conn.close()
            self.assertGreaterEqual(len(rows), 1)
            self.assertNotIn("AI news", rows[0][0])

    def test_rank_orders_relevant_fresh_items(self) -> None:
        old = CollectedItem(
            platform="x",
            external_id="old",
            title="misc",
            author="a",
            url="https://old.test",
            published_at=datetime(2020, 1, 1, tzinfo=timezone.utc),
        )
        fresh = CollectedItem(
            platform="x",
            external_id="fresh",
            title="OpenAI 大模型",
            author="a",
            url="https://fresh.test",
            published_at=datetime.now(timezone.utc),
        )
        ranked = rank_items([old, fresh], ["OpenAI", "大模型"])
        self.assertEqual(ranked[0].external_id, "fresh")

    def test_has_successful_delivery(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "test.db"
            init_db(db_path)
            conn = sqlite3.connect(db_path)
            conn.execute(
                """
                INSERT INTO job_runs(job_date, started_at, status, delivered)
                VALUES (?, ?, ?, ?)
                """,
                ("2026-04-27", "2026-04-27T00:00:00+08:00", "success", 1),
            )
            conn.commit()
            conn.close()
            self.assertTrue(has_successful_delivery(db_path, "2026-04-27"))
            self.assertFalse(has_successful_delivery(db_path, "2026-04-28"))


if __name__ == "__main__":
    unittest.main()
