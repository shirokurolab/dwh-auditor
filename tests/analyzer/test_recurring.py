"""analyze_recurring_cost 関数のテスト."""

from __future__ import annotations

from datetime import datetime, timezone

from dwh_auditor.analyzer.recurring import analyze_recurring_cost
from dwh_auditor.config import AppConfig


class TestAnalyzeRecurringCost:
    """定常実行クエリのコスト集計のテスト."""

    def test_returns_empty_for_no_stats(self, default_config: AppConfig) -> None:
        """データが空の場合は空リストを返すこと."""
        result = analyze_recurring_cost([], default_config)
        assert result == []

    def test_calculates_cost_and_returns_insights(self, default_config: AppConfig) -> None:
        """指定された stats から RecurringCostInsight を正しく生成すること."""
        raw_stats = [
            {
                "query_hash": "hash_1",
                "query_sample": "SELECT * FROM t",
                "execution_count": 100,
                "total_bytes_billed": 100 * (1024**4),  # 100 TB
                "last_executed_at": datetime(2024, 1, 1, tzinfo=timezone.utc),
            },
            {
                "query_hash": "hash_2",
                "query_sample": "SELECT * FROM u",
                "execution_count": 10,
                "total_bytes_billed": 0.5 * (1024**4),  # 0.5 TB
                "last_executed_at": datetime(2024, 1, 2, tzinfo=timezone.utc),
            },
        ]

        # config のコスト単価設定を 1TB = $5 に固定
        default_config.pricing.tb_scan_usd = 5.0

        insights = analyze_recurring_cost(raw_stats, default_config)

        assert len(insights) == 2

        insight1 = next(i for i in insights if i.query_hash == "hash_1")
        assert insight1.total_scanned_tb == 100.0
        assert insight1.total_estimated_usd == 500.0  # 100 TB * $5
        assert insight1.execution_count == 100

        insight2 = next(i for i in insights if i.query_hash == "hash_2")
        assert insight2.total_scanned_tb == 0.5
        assert insight2.total_estimated_usd == 2.5  # 0.5 TB * $5
