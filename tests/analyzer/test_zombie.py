"""analyze_table_usage 関数のテスト."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from dwh_auditor.analyzer.zombie import analyze_table_usage
from dwh_auditor.config import AppConfig
from dwh_auditor.models.table import TableStorage


class TestAnalyzeTableUsage:
    def test_returns_empty_for_no_tables(self, default_config: AppConfig) -> None:
        result = analyze_table_usage([], {}, default_config)
        assert result == []

    def test_detects_only_zombie_tables(self, default_config: AppConfig) -> None:
        now = datetime(2024, 6, 1, tzinfo=timezone.utc)

        table_zombie = TableStorage(project_id="test", dataset_id="ds", table_id="old_t", total_logical_bytes=100)
        table_active = TableStorage(project_id="test", dataset_id="ds", table_id="active_t", total_logical_bytes=200)

        # 100日前
        old_time = now - timedelta(days=100)
        # 昨日
        recent_time = now - timedelta(days=1)

        usage_stats = {
            table_zombie.full_table_id: {
                "last_accessed_at": old_time,
                "access_count": 1,
                "top_users": ["u1@example.com"],
            },
            table_active.full_table_id: {
                "last_accessed_at": recent_time,
                "access_count": 50,
                "top_users": ["u2@example.com"],
            },
        }

        default_config.thresholds.zombie_table_days = 90

        result = analyze_table_usage([table_zombie, table_active], usage_stats, default_config, now=now)

        # アクティブなテーブルは除外され、ゾンビテーブル1件のみが返ること
        assert len(result) == 1

        zombie_res = result[0]
        assert zombie_res.table.table_id == "old_t"
        assert zombie_res.is_zombie is True
        assert zombie_res.access_count_30d == 1
        assert zombie_res.top_users == ["u1@example.com"]
