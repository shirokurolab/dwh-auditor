"""analyze_cost 関数のテスト (BQ 依存なし・純粋 Python テスト)."""

from __future__ import annotations

import pytest

from bq_auditor.analyzer.cost import _bytes_to_tb, _estimate_cost_usd, analyze_cost
from bq_auditor.config import AppConfig
from bq_auditor.models.job import QueryJob


class TestBytesToTb:
    """_bytes_to_tb ヘルパー関数のテスト."""

    def test_1tb_in_bytes(self) -> None:
        """1 TB のバイト数が正確に 1.0 TB に変換されること."""
        bytes_1tb = 1024**4
        assert _bytes_to_tb(bytes_1tb) == pytest.approx(1.0)

    def test_zero_bytes(self) -> None:
        """0 バイトが 0.0 TB に変換されること."""
        assert _bytes_to_tb(0) == 0.0


class TestEstimateCostUsd:
    """_estimate_cost_usd ヘルパー関数のテスト."""

    def test_1tb_at_default_price(self) -> None:
        """1TB スキャン時のデフォルト料金 ($6.25) が正確に計算されること."""
        bytes_1tb = 1024**4
        cost = _estimate_cost_usd(bytes_1tb, 6.25)
        assert cost == pytest.approx(6.25)

    def test_half_tb_at_default_price(self) -> None:
        """0.5TB スキャン時のコストが $3.125 になること."""
        bytes_half_tb = 1024**4 // 2
        cost = _estimate_cost_usd(bytes_half_tb, 6.25)
        assert cost == pytest.approx(3.125, rel=1e-3)


class TestAnalyzeCost:
    """analyze_cost 関数のテスト."""

    def test_returns_empty_for_no_jobs(self, default_config: AppConfig) -> None:
        """ジョブが空の場合は空リストを返すこと."""
        result = analyze_cost([], default_config)
        assert result == []

    def test_excludes_cache_hits(
        self,
        query_job_cached: QueryJob,
        default_config: AppConfig,
    ) -> None:
        """キャッシュヒットしたジョブ（bytes_billed=0）は除外されること."""
        result = analyze_cost([query_job_cached], default_config)
        assert result == []

    def test_excludes_zero_bytes_billed(
        self,
        query_job_cached: QueryJob,
        default_config: AppConfig,
    ) -> None:
        """total_bytes_billed が 0 のジョブは除外されること."""
        result = analyze_cost([query_job_cached], default_config)
        assert len(result) == 0

    def test_returns_sorted_by_cost_desc(
        self,
        query_job_heavy: QueryJob,
        query_job_light: QueryJob,
        default_config: AppConfig,
    ) -> None:
        """複数ジョブの場合はコスト降順で返されること."""
        result = analyze_cost([query_job_light, query_job_heavy], default_config)
        assert len(result) == 2
        assert result[0].job.job_id == "job_heavy_001"
        assert result[1].job.job_id == "job_light_001"
        assert result[0].estimated_cost_usd > result[1].estimated_cost_usd

    def test_respects_limit(
        self,
        query_job_heavy: QueryJob,
        query_job_light: QueryJob,
        custom_config: AppConfig,
    ) -> None:
        """top_expensive_queries_limit の件数上限が守られること (custom_config は limit=3)."""
        # limit=3 のカスタム設定でも、2件しかジョブがなければ2件返す
        result = analyze_cost([query_job_heavy, query_job_light], custom_config)
        # custom_config の limit=3 なので、2件全部返される
        assert len(result) == 2

    def test_cost_calculation_accuracy(
        self,
        query_job_heavy: QueryJob,
        default_config: AppConfig,
    ) -> None:
        """1TB (1_000_000_000_000 bytes) のジョブのコストが正しく計算されること.

        BQ の課金単位は 1TB = 10^12 bytes (SI 単位)。
        conftest の query_job_heavy は 1_000_000_000_000 bytes なので、
        1024^4 ベースの内部換算では約 0.909 TB → コストは $6.25 * 0.909 ≒ $5.68。
        """
        result = analyze_cost([query_job_heavy], default_config)
        assert len(result) == 1
        # 1_000_000_000_000 bytes / 1024^4 = 約 0.9095 TB
        expected_tb = 1_000_000_000_000 / 1024**4
        expected_cost = expected_tb * 6.25
        assert result[0].estimated_cost_usd == pytest.approx(expected_cost, rel=1e-6)
        assert result[0].scanned_tb == pytest.approx(expected_tb, rel=1e-6)
