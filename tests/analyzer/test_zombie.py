"""detect_zombie_tables 関数のテスト (BQ 依存なし・純粋 Python テスト)."""

from __future__ import annotations

from bq_auditor.analyzer.zombie import detect_zombie_tables
from bq_auditor.config import AppConfig
from bq_auditor.models.job import QueryJob
from bq_auditor.models.table import TableStorage


class TestDetectZombieTables:
    """detect_zombie_tables 関数のテスト."""

    def test_returns_empty_for_no_tables(
        self,
        default_config: AppConfig,
    ) -> None:
        """テーブルが空の場合は空リストを返すこと."""
        result = detect_zombie_tables([], [], default_config)
        assert result == []

    def test_detects_unreferenced_table(
        self,
        table_zombie: TableStorage,
        query_job_heavy: QueryJob,
        default_config: AppConfig,
    ) -> None:
        """ジョブで参照されていないテーブルがゾンビとして検知されること."""
        # query_job_heavy は "project.dataset.large_table" を参照
        # table_zombie は "project.dataset.unused_old_table" → 参照されていない
        result = detect_zombie_tables([table_zombie], [query_job_heavy], default_config)
        assert len(result) == 1
        assert result[0].table.table_id == "unused_old_table"

    def test_does_not_flag_referenced_table(
        self,
        table_active: TableStorage,
        query_job_heavy: QueryJob,
        default_config: AppConfig,
    ) -> None:
        """ジョブで参照されているテーブルはゾンビとして検知されないこと."""
        # query_job_heavy は "project.dataset.large_table" を参照
        # table_active は "project.dataset.large_table" → 参照されている
        result = detect_zombie_tables([table_active], [query_job_heavy], default_config)
        assert result == []

    def test_returns_empty_when_all_tables_referenced(
        self,
        table_active: TableStorage,
        table_zombie: TableStorage,
        query_job_heavy: QueryJob,
        default_config: AppConfig,
    ) -> None:
        """全テーブルが参照されている場合は空リストを返すこと."""
        # referenced_tables を動的に上書き
        job_referencing_both = query_job_heavy.model_copy(
            update={
                "referenced_tables": [
                    table_active.full_table_id,
                    table_zombie.full_table_id,
                ]
            }
        )
        result = detect_zombie_tables([table_active, table_zombie], [job_referencing_both], default_config)
        assert result == []

    def test_sorted_by_size_desc(
        self,
        table_active: TableStorage,
        table_zombie: TableStorage,
        default_config: AppConfig,
    ) -> None:
        """ゾンビリストはストレージサイズ降順で返されること."""
        # 両テーブルともジョブで参照しない → どちらもゾンビ
        result = detect_zombie_tables([table_active, table_zombie], [], default_config)
        assert len(result) == 2
        # table_active: 500GB > table_zombie: 10GB
        assert result[0].table.table_id == "large_table"
        assert result[1].table.table_id == "unused_old_table"

    def test_days_unused_is_config_value(
        self,
        table_zombie: TableStorage,
        default_config: AppConfig,
    ) -> None:
        """days_unused が config の zombie_table_days と一致すること."""
        result = detect_zombie_tables([table_zombie], [], default_config)
        assert len(result) == 1
        assert result[0].days_unused == default_config.thresholds.zombie_table_days

    def test_size_gb_conversion(
        self,
        table_zombie: TableStorage,
        default_config: AppConfig,
    ) -> None:
        """size_gb が total_logical_bytes の GB 換算値と一致すること."""
        result = detect_zombie_tables([table_zombie], [], default_config)
        expected_gb = 10_000_000_000 / 1024**3
        assert result[0].size_gb == pytest.approx(expected_gb, rel=1e-3)


import pytest  # noqa: E402 (テストファイル末尾に配置しています)
