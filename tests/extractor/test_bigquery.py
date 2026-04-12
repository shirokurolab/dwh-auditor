"""BigQueryExtractor のテスト (モック使用)."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

from dwh_auditor.extractor.bigquery import BigQueryExtractor


@pytest.fixture
def mock_bq_client(mocker: MagicMock) -> MagicMock:
    """google.cloud.bigquery.Client をモック化する."""
    mock_client = mocker.patch("dwh_auditor.extractor.bigquery.bq.Client")
    return mock_client.return_value


class TestBigQueryExtractor:
    def test_init_sets_target_and_job_projects(self, mock_bq_client: MagicMock) -> None:
        extractor = BigQueryExtractor(
            target_project_id="target-prj", job_project_ids=["jp1", "jp2"], region="region-us"
        )
        assert extractor._target_project_id == "target-prj"
        assert extractor._job_project_ids == ["jp1", "jp2"]
        assert extractor._region == "region-us"

    def test_init_defaults_job_project_to_target_if_empty(self, mock_bq_client: MagicMock) -> None:
        extractor = BigQueryExtractor(target_project_id="target-prj", job_project_ids=[], region="region-us")
        assert extractor._job_project_ids == ["target-prj"]

    def test_get_top_cost_jobs(self, mock_bq_client: MagicMock) -> None:
        extractor = BigQueryExtractor(target_project_id="target-prj", job_project_ids=["jp1"], region="region-us")

        mock_query_job = MagicMock()
        mock_query_job.result.return_value = []
        mock_bq_client.query.return_value = mock_query_job

        extractor.get_top_cost_jobs(days=30, limit=10)

        mock_bq_client.query.assert_called_once()
        sql: str = mock_bq_client.query.call_args[0][0]
        assert "jp1" in sql
        assert "LIMIT 10" in sql

    def test_get_heavy_scan_jobs(self, mock_bq_client: MagicMock) -> None:
        extractor = BigQueryExtractor(target_project_id="target-prj", job_project_ids=["jp1"], region="region-us")

        mock_query_job = MagicMock()
        mock_query_job.result.return_value = []
        mock_bq_client.query.return_value = mock_query_job

        extractor.get_heavy_scan_jobs(days=30, min_scanned_bytes=2000)

        mock_bq_client.query.assert_called_once()
        sql: str = mock_bq_client.query.call_args[0][0]
        assert "jp1" in sql
        assert "2000" in sql
        assert "LIMIT 1000" in sql

    def test_get_recurring_cost_jobs(self, mock_bq_client: MagicMock) -> None:
        extractor = BigQueryExtractor(target_project_id="target-prj", job_project_ids=["jp1"], region="region-us")

        mock_query_job = MagicMock()
        mock_query_job.result.return_value = [
            {
                "query_hash": "hash_x",
                "query_sample": "SELECT 1",
                "execution_count": 50,
                "total_bytes_billed": 100000,
                "last_executed_at": datetime(2024, 1, 1, tzinfo=timezone.utc),
            }
        ]
        mock_bq_client.query.return_value = mock_query_job

        stats = extractor.get_recurring_cost_jobs(days=30, min_executions=5)

        assert len(stats) == 1
        assert stats[0]["query_hash"] == "hash_x"
        mock_bq_client.query.assert_called_once()
        sql: str = mock_bq_client.query.call_args[0][0]
        assert "HAVING execution_count >= 5" in sql

    def test_get_table_usage_stats(self, mock_bq_client: MagicMock) -> None:
        extractor = BigQueryExtractor(target_project_id="target-prj", job_project_ids=["jp1"], region="region-us")

        mock_query_job = MagicMock()
        mock_query_job.result.return_value = [
            {
                "table_id": "target-prj.ds.t",
                "last_accessed_at": datetime(2024, 1, 1, tzinfo=timezone.utc),
                "access_count": 5,
                "top_users": ["u@e.com"],
            }
        ]
        mock_bq_client.query.return_value = mock_query_job

        usages = extractor.get_table_usage_stats(days=30)

        assert len(usages) == 1
        assert "target-prj.ds.t" in usages
        assert usages["target-prj.ds.t"]["access_count"] == 5
        mock_bq_client.query.assert_called_once()

    def test_get_table_storage(self, mock_bq_client: MagicMock) -> None:
        extractor = BigQueryExtractor(target_project_id="target-prj", job_project_ids=[], region="region-us")

        mock_query_job = MagicMock()
        mock_query_job.result.return_value = [
            {
                "project_id": "target-prj",
                "dataset_id": "ds",
                "table_id": "test_table",
                "total_logical_bytes": 100,
                "total_physical_bytes": 50,
                "active_logical_bytes": 100,
            }
        ]
        mock_bq_client.query.return_value = mock_query_job

        tables = extractor.get_table_storage()

        assert len(tables) == 1
        assert tables[0].table_id == "test_table"
        assert tables[0].total_logical_bytes == 100
