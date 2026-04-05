"""Pydantic モデルのバリデーションテスト."""

from __future__ import annotations

from datetime import datetime, timezone

from bq_auditor.models.job import QueryJob
from bq_auditor.models.result import (
    AuditResult,
)
from bq_auditor.models.table import TableStorage


class TestQueryJob:
    """QueryJob モデルのテスト."""

    def test_create_with_required_fields(self) -> None:
        """必須フィールドのみで QueryJob が作成できること."""
        job = QueryJob(
            job_id="job_001",
            user_email="test@example.com",
            query="SELECT 1",
            creation_time=datetime(2024, 1, 1, tzinfo=timezone.utc),
        )
        assert job.job_id == "job_001"
        assert job.user_email == "test@example.com"
        assert job.total_bytes_billed == 0  # デフォルト値
        assert job.cache_hit is False  # デフォルト値
        assert job.referenced_tables == []  # デフォルト値

    def test_create_with_all_fields(self) -> None:
        """全フィールドを指定して QueryJob が作成できること."""
        job = QueryJob(
            job_id="job_002",
            user_email="analyst@example.com",
            query="SELECT * FROM t",
            creation_time=datetime(2024, 6, 15, 9, 30, tzinfo=timezone.utc),
            total_bytes_billed=1_000_000_000,
            cache_hit=True,
            referenced_tables=["proj.ds.table1", "proj.ds.table2"],
            statement_type="SELECT",
        )
        assert job.total_bytes_billed == 1_000_000_000
        assert job.cache_hit is True
        assert len(job.referenced_tables) == 2

    def test_total_bytes_billed_default_zero(self) -> None:
        """total_bytes_billed のデフォルト値が 0 であること."""
        job = QueryJob(
            job_id="j",
            user_email="u@e.com",
            query="SELECT 1",
            creation_time=datetime(2024, 1, 1, tzinfo=timezone.utc),
        )
        assert job.total_bytes_billed == 0


class TestTableStorage:
    """TableStorage モデルのテスト."""

    def test_full_table_id_computed(self) -> None:
        """full_table_id が project.dataset.table 形式で返されること."""
        table = TableStorage(
            project_id="my-project",
            dataset_id="my_dataset",
            table_id="my_table",
            total_logical_bytes=1_000_000,
        )
        assert table.full_table_id == "my-project.my_dataset.my_table"

    def test_default_bytes_are_zero(self) -> None:
        """バイト系フィールドのデフォルト値が 0 であること."""
        table = TableStorage(
            project_id="p",
            dataset_id="d",
            table_id="t",
        )
        assert table.total_logical_bytes == 0
        assert table.total_physical_bytes == 0
        assert table.active_logical_bytes == 0


class TestAuditResult:
    """AuditResult モデルのテスト."""

    def test_create_empty_result(self) -> None:
        """空の AuditResult が作成できること."""
        result = AuditResult(
            analyzed_days=30,
            project_id="test-project",
            total_jobs_analyzed=100,
            total_tables_analyzed=50,
        )
        assert result.analyzed_days == 30
        assert result.top_expensive_queries == []
        assert result.full_scans == []
        assert result.zombie_tables == []
