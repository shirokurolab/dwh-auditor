"""BigQueryExtractor のテスト (pytest-mock で BQ API をモック化)."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest
from pytest_mock import MockerFixture

from bq_auditor.extractor.bigquery import BigQueryExtractor

# ---------------------------------------------------------------------------
# テスト用のダミー Row オブジェクト
# ---------------------------------------------------------------------------


class FakeRow:
    """BigQuery の Row オブジェクトをシミュレートするダミークラス."""

    def __init__(self, data: dict[str, object]) -> None:
        self._data = data

    def __getitem__(self, key: str) -> object:
        return self._data[key]


# ---------------------------------------------------------------------------
# フィクスチャ
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_bq_client(mocker: MockerFixture) -> MagicMock:
    """google.cloud.bigquery.Client の初期化をモック化する."""
    mock_client = MagicMock()
    mocker.patch(
        "bq_auditor.extractor.bigquery.bq.Client",
        return_value=mock_client,
    )
    return mock_client


# ---------------------------------------------------------------------------
# get_job_history のテスト
# ---------------------------------------------------------------------------


class TestGetJobHistory:
    """get_job_history メソッドのテスト."""

    def test_returns_empty_when_no_jobs(self, mock_bq_client: MagicMock) -> None:
        """BQ が 0 件を返す場合は空リストになること."""
        mock_bq_client.query.return_value.result.return_value = []
        extractor = BigQueryExtractor(project_id="test-project", region="region-us")
        jobs = extractor.get_job_history(days=7)
        assert jobs == []
        mock_bq_client.query.assert_called_once()

    def test_returns_parsed_query_jobs(self, mock_bq_client: MagicMock) -> None:
        """BQ の Row が QueryJob モデルに正しく変換されること."""
        fake_rows = [
            FakeRow(
                {
                    "job_id": "job_abc",
                    "user_email": "analyst@example.com",
                    "query": "SELECT * FROM t",
                    "creation_time": datetime(2024, 3, 1, 12, 0, 0, tzinfo=timezone.utc),
                    "total_bytes_billed": 2_000_000_000,
                    "cache_hit": False,
                    "statement_type": "SELECT",
                }
            )
        ]
        mock_bq_client.query.return_value.result.return_value = fake_rows
        extractor = BigQueryExtractor(project_id="test-project", region="region-us")
        jobs = extractor.get_job_history(days=30)

        assert len(jobs) == 1
        assert jobs[0].job_id == "job_abc"
        assert jobs[0].user_email == "analyst@example.com"
        assert jobs[0].total_bytes_billed == 2_000_000_000
        assert jobs[0].cache_hit is False

    def test_handles_naive_datetime(self, mock_bq_client: MagicMock) -> None:
        """tzinfo のない naive datetime が UTC aware に補正されること."""
        naive_dt = datetime(2024, 3, 1, 12, 0, 0)  # tzinfo なし
        fake_rows = [
            FakeRow(
                {
                    "job_id": "job_naive",
                    "user_email": "u@e.com",
                    "query": "SELECT 1",
                    "creation_time": naive_dt,
                    "total_bytes_billed": 0,
                    "cache_hit": True,
                    "statement_type": "SELECT",
                }
            )
        ]
        mock_bq_client.query.return_value.result.return_value = fake_rows
        extractor = BigQueryExtractor(project_id="test-project", region="region-us")
        jobs = extractor.get_job_history(days=30)

        assert jobs[0].creation_time.tzinfo == timezone.utc

    def test_multiple_jobs_returned(self, mock_bq_client: MagicMock) -> None:
        """複数の Row が正しい数の QueryJob に変換されること."""
        dt = datetime(2024, 1, 1, tzinfo=timezone.utc)
        fake_rows = [
            FakeRow(
                {
                    "job_id": f"job_{i}",
                    "user_email": "u@e.com",
                    "query": "SELECT 1",
                    "creation_time": dt,
                    "total_bytes_billed": i * 1_000_000,
                    "cache_hit": False,
                    "statement_type": "SELECT",
                }
            )
            for i in range(5)
        ]
        mock_bq_client.query.return_value.result.return_value = fake_rows
        extractor = BigQueryExtractor(project_id="test-project", region="region-us")
        jobs = extractor.get_job_history(days=30)

        assert len(jobs) == 5
        assert jobs[2].job_id == "job_2"

    def test_sql_contains_days_parameter(self, mock_bq_client: MagicMock) -> None:
        """発行する SQL に days パラメータが正しく埋め込まれること."""
        mock_bq_client.query.return_value.result.return_value = []
        extractor = BigQueryExtractor(project_id="my-project", region="region-us")
        extractor.get_job_history(days=14)

        call_args = mock_bq_client.query.call_args[0][0]
        assert "14" in call_args
        assert "my-project" in call_args


# ---------------------------------------------------------------------------
# get_table_storage のテスト
# ---------------------------------------------------------------------------


class TestGetTableStorage:
    """get_table_storage メソッドのテスト."""

    def test_returns_empty_when_no_tables(self, mock_bq_client: MagicMock) -> None:
        """BQ が 0 件を返す場合は空リストになること."""
        mock_bq_client.query.return_value.result.return_value = []
        extractor = BigQueryExtractor(project_id="test-project", region="region-us")
        tables = extractor.get_table_storage()
        assert tables == []

    def test_returns_parsed_table_storage(self, mock_bq_client: MagicMock) -> None:
        """BQ の Row が TableStorage モデルに正しく変換されること."""
        fake_rows = [
            FakeRow(
                {
                    "project_id": "my-project",
                    "dataset_id": "ds",
                    "table_id": "tbl",
                    "total_logical_bytes": 5_000_000_000,
                    "total_physical_bytes": 4_000_000_000,
                    "active_logical_bytes": 5_000_000_000,
                }
            )
        ]
        mock_bq_client.query.return_value.result.return_value = fake_rows
        extractor = BigQueryExtractor(project_id="my-project", region="region-us")
        tables = extractor.get_table_storage()

        assert len(tables) == 1
        assert tables[0].project_id == "my-project"
        assert tables[0].dataset_id == "ds"
        assert tables[0].table_id == "tbl"
        assert tables[0].total_logical_bytes == 5_000_000_000
        assert tables[0].full_table_id == "my-project.ds.tbl"
