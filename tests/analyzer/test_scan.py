"""detect_full_scans 関数のテスト (BQ 依存なし・純粋 Python テスト)."""

from __future__ import annotations

from datetime import datetime

import pytest

from dwh_auditor.analyzer.scan import _is_full_scan, detect_full_scans
from dwh_auditor.config import AppConfig
from dwh_auditor.models.job import QueryJob


class TestIsFullScan:
    """_is_full_scan ヘルパー関数のテスト."""

    def test_query_without_where_is_full_scan(self) -> None:
        """WHERE 句がないクエリはフルスキャンと判定されること."""
        assert _is_full_scan("SELECT * FROM `project.dataset.table`") is True

    def test_query_with_partition_filter_is_not_full_scan(self) -> None:
        """パーティションフィルタがある場合はフルスキャンでないこと."""
        query = "SELECT * FROM t WHERE _PARTITIONTIME = '2024-01-01'"
        assert _is_full_scan(query) is False

    def test_query_with_date_filter_is_not_full_scan(self) -> None:
        """日付フィルタがある場合はフルスキャンでないこと."""
        query = "SELECT * FROM t WHERE created_at >= '2024-01-01'"
        assert _is_full_scan(query) is False

    def test_query_with_where_but_no_partition_is_full_scan(self) -> None:
        """WHERE 句はあるがパーティション・日付指定がない場合はフルスキャン扱い."""
        query = "SELECT * FROM t WHERE user_id = 1"
        assert _is_full_scan(query) is True

    def test_case_insensitive_where(self) -> None:
        """WHERE は大文字小文字を問わず検知されること."""
        query = "select * from t where _partitiontime = '2024-01-01'"
        assert _is_full_scan(query) is False


class TestDetectFullScans:
    """detect_full_scans 関数のテスト."""

    def test_returns_empty_for_no_jobs(self, default_config: AppConfig) -> None:
        """ジョブが空の場合は空リストを返すこと."""
        result = detect_full_scans([], default_config)
        assert result == []

    def test_detects_full_scan_job(
        self,
        query_job_full_scan: QueryJob,
        default_config: AppConfig,
    ) -> None:
        """WHERE 句なし・しきい値超えのジョブがフルスキャンとして検知されること."""
        result = detect_full_scans([query_job_full_scan], default_config)
        assert len(result) == 1
        assert result[0].job.job_id == "job_full_scan_001"
        assert result[0].scanned_gb == pytest.approx(5_000_000_000 / 1024**3, rel=1e-3)

    def test_excludes_small_scans_below_threshold(
        self,
        default_config: AppConfig,
        sample_timestamp: datetime,
    ) -> None:
        """ignore_full_scan_under_gb 以下のスキャンは除外されること (デフォルト 1GB)."""
        tiny_job = QueryJob(
            job_id="tiny_job",
            user_email="dev@example.com",
            query="SELECT * FROM t",  # WHERE なし → is_full_scan = True
            creation_time=sample_timestamp,
            total_bytes_billed=500_000_000,  # 0.5 GB < 1 GB (threshold)
            cache_hit=False,
        )
        result = detect_full_scans([tiny_job], default_config)
        assert result == []

    def test_excludes_cache_hit_jobs(
        self,
        query_job_cached: QueryJob,
        default_config: AppConfig,
    ) -> None:
        """キャッシュヒットしたジョブは除外されること."""
        result = detect_full_scans([query_job_cached], default_config)
        assert result == []

    def test_partitioned_query_not_detected(
        self,
        query_job_light: QueryJob,
        default_config: AppConfig,
    ) -> None:
        """パーティション指定のあるクエリは検知されないこと."""
        result = detect_full_scans([query_job_light], default_config)
        assert result == []

    def test_sorted_by_scanned_gb_desc(
        self,
        default_config: AppConfig,
        sample_timestamp: datetime,
    ) -> None:
        """複数件の場合は scanned_gb 降順で返されること."""
        job_big = QueryJob(
            job_id="big",
            user_email="u@e.com",
            query="SELECT * FROM t",
            creation_time=sample_timestamp,
            total_bytes_billed=10_000_000_000,  # 10 GB
            cache_hit=False,
        )
        job_small = QueryJob(
            job_id="small",
            user_email="u@e.com",
            query="SELECT * FROM t",
            creation_time=sample_timestamp,
            total_bytes_billed=2_000_000_000,  # 2 GB
            cache_hit=False,
        )
        result = detect_full_scans([job_small, job_big], default_config)
        assert result[0].job.job_id == "big"
        assert result[1].job.job_id == "small"
