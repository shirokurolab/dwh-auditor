"""テスト共通フィクスチャ."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from dwh_auditor.config import AppConfig, PricingConfig, ThresholdsConfig
from dwh_auditor.models.job import QueryJob
from dwh_auditor.models.table import TableStorage


@pytest.fixture
def sample_timestamp() -> datetime:
    """テスト用のタイムスタンプ (UTC)."""
    return datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc)


@pytest.fixture
def default_config() -> AppConfig:
    """デフォルト設定の AppConfig フィクスチャ."""
    return AppConfig()


@pytest.fixture
def custom_config() -> AppConfig:
    """カスタム設定の AppConfig フィクスチャ."""
    return AppConfig(
        pricing=PricingConfig(tb_scan_usd=6.25),
        thresholds=ThresholdsConfig(
            ignore_full_scan_under_gb=1.0,
            top_expensive_queries_limit=3,
            zombie_table_days=90,
        ),
    )


@pytest.fixture
def query_job_heavy(sample_timestamp: datetime) -> QueryJob:
    """重いクエリジョブ (1TB 課金) のフィクスチャ."""
    return QueryJob(
        job_id="job_heavy_001",
        user_email="analyst@example.com",
        query="SELECT * FROM `project.dataset.large_table`",
        creation_time=sample_timestamp,
        total_bytes_billed=1_000_000_000_000,  # 1 TB
        cache_hit=False,
        referenced_tables=["project.dataset.large_table"],
    )


@pytest.fixture
def query_job_light(sample_timestamp: datetime) -> QueryJob:
    """軽いクエリジョブ (100MB 課金) のフィクスチャ."""
    return QueryJob(
        job_id="job_light_001",
        user_email="engineer@example.com",
        query=("SELECT id, name FROM `project.dataset.small_table` WHERE _PARTITIONTIME = '2024-01-01'"),
        creation_time=sample_timestamp,
        total_bytes_billed=100_000_000,  # 100 MB
        cache_hit=False,
        referenced_tables=["project.dataset.small_table"],
    )


@pytest.fixture
def query_job_cached(sample_timestamp: datetime) -> QueryJob:
    """キャッシュヒットしたクエリジョブのフィクスチャ."""
    return QueryJob(
        job_id="job_cached_001",
        user_email="user@example.com",
        query="SELECT COUNT(*) FROM `project.dataset.table`",
        creation_time=sample_timestamp,
        total_bytes_billed=0,
        cache_hit=True,
        referenced_tables=["project.dataset.table"],
    )


@pytest.fixture
def query_job_full_scan(sample_timestamp: datetime) -> QueryJob:
    """フルスキャンクエリ (WHERE 句なし、5GB 課金) のフィクスチャ."""
    return QueryJob(
        job_id="job_full_scan_001",
        user_email="rookie@example.com",
        query="SELECT * FROM `project.dataset.big_table`",
        creation_time=sample_timestamp,
        total_bytes_billed=5_000_000_000,  # 5 GB
        cache_hit=False,
        referenced_tables=[],
    )


@pytest.fixture
def table_active() -> TableStorage:
    """アクティブなテーブルのフィクスチャ."""
    return TableStorage(
        project_id="project",
        dataset_id="dataset",
        table_id="large_table",
        total_logical_bytes=500_000_000_000,  # 500 GB
        total_physical_bytes=300_000_000_000,
        active_logical_bytes=500_000_000_000,
    )


@pytest.fixture
def table_zombie() -> TableStorage:
    """ゾンビテーブルのフィクスチャ (参照されていないテーブル)."""
    return TableStorage(
        project_id="project",
        dataset_id="dataset",
        table_id="unused_old_table",
        total_logical_bytes=10_000_000_000,  # 10 GB
        total_physical_bytes=8_000_000_000,
        active_logical_bytes=10_000_000_000,
    )
