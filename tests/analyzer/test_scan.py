"""detect_full_scans 関数のテスト."""

from __future__ import annotations
from datetime import datetime

import pytest

from dwh_auditor.analyzer.scan import _is_full_scan_fallback, detect_full_scans
from dwh_auditor.config import AppConfig
from dwh_auditor.models.job import QueryJob
from dwh_auditor.models.table import TableStorage


class TestIsFullScanFallback:
    def test_query_without_where_is_full_scan(self) -> None:
        assert _is_full_scan_fallback("SELECT * FROM `project.dataset.table`") is True

    def test_query_with_partition_filter_is_not_full_scan(self) -> None:
        query = "SELECT * FROM t WHERE _PARTITIONTIME = '2024-01-01'"
        assert _is_full_scan_fallback(query) is False


class TestDetectFullScans:
    def test_returns_empty_for_no_jobs(self, default_config: AppConfig) -> None:
        result = detect_full_scans([], [], default_config)
        assert result == []

    def test_detects_full_scan_job(self, default_config: AppConfig, sample_timestamp: datetime) -> None:
        table = TableStorage(
            project_id="test_project",
            dataset_id="test_dataset",
            table_id="test_table",
            total_logical_bytes=1000,
        )
        job = QueryJob(
            job_id="job1",
            user_email="test@example.com",
            query="SELECT * FROM test_project.test_dataset.test_table",
            creation_time=sample_timestamp,
            total_bytes_billed=950, # 95% ratio -> > 90% threshold
            referenced_tables=[table.full_table_id]
        )
        
        # force threshold to 0.90 for test
        default_config.thresholds.full_scan_ratio_threshold = 0.90
        # drop ignore limits to 0 for test so small scans trigger it
        default_config.thresholds.ignore_full_scan_under_gb = 0.0
        
        result = detect_full_scans([job], [table], default_config)
        assert len(result) == 1
        assert result[0].job.job_id == "job1"

    def test_does_not_flag_partitioned_query(self, default_config: AppConfig, sample_timestamp: datetime) -> None:
        table = TableStorage(
            project_id="test_project",
            dataset_id="test_dataset",
            table_id="test_table",
            total_logical_bytes=1000,
        )
        job = QueryJob(
            job_id="job2",
            user_email="test@example.com",
            query="SELECT * FROM test_project.test_dataset.test_table WHERE ds='2024-01-01'",
            creation_time=sample_timestamp,
            total_bytes_billed=100, # 10% ratio -> not a full scan
            referenced_tables=[table.full_table_id]
        )
        default_config.thresholds.full_scan_ratio_threshold = 0.90
        default_config.thresholds.ignore_full_scan_under_gb = 0.0
        
        result = detect_full_scans([job], [table], default_config)
        assert len(result) == 0
