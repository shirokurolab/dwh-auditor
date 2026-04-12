"""分析結果のデータモデル.

Analyzer 層が Reporter 層に渡す診断結果の型定義です。
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from dwh_auditor.models.job import QueryJob
from dwh_auditor.models.table import TableStorage


class CostInsight(BaseModel):
    """高コストクエリの分析結果."""

    job: QueryJob = Field(description="対象のクエリジョブ")
    estimated_cost_usd: float = Field(description="推定コスト (USD)。pricing.tb_scan_usd × スキャン TB 数で算出。")
    scanned_tb: float = Field(description="スキャンしたデータ量 (TB)")


class FullScanInsight(BaseModel):
    """フルスキャンと判定されたクエリの分析結果."""

    job: QueryJob = Field(description="対象のクエリジョブ")
    scanned_gb: float = Field(description="スキャンしたデータ量 (GB)")


class TableUsageProfile(BaseModel):
    """テーブルの利用状況プロファイルとゾンビ判定結果."""

    table: TableStorage = Field(description="対象のテーブル")
    is_zombie: bool = Field(description="設定された日数以上未使用（ゾンビ）であるか")
    last_accessed_at: Optional[datetime] = Field(default=None, description="最後に参照された日時")  # noqa: UP045
    top_users: list[str] = Field(default_factory=list, description="頻繁にアクセスしているユーザー群")
    access_count_30d: int = Field(default=0, description="指定期間内のアクセス回数")
    size_gb: float = Field(description="テーブルの論理ストレージサイズ (GB)")


class RecurringCostInsight(BaseModel):
    """バッチやBI等から定常的に実行されている高コストクエリの分析結果."""

    query_hash: str = Field(description="BigQuery が発行したクエリハッシュ")
    query_sample: str = Field(description="代表的なクエリテキスト")
    execution_count: int = Field(description="期間中の実行回数")
    total_estimated_usd: float = Field(description="期間中の総推定コスト (USD)")
    total_scanned_tb: float = Field(description="総スキャン量 (TB)")
    last_executed_at: datetime = Field(description="最終実行日時")


class AuditResult(BaseModel):
    """Analyzer 層が最終的に出力する総合監査結果レポート."""

    analyzed_days: int = Field(description="分析対象期間 (日数)")
    project_id: str = Field(description="分析対象の GCP プロジェクト ID")
    total_jobs_analyzed: int = Field(description="分析したジョブの総数")
    total_tables_analyzed: int = Field(description="分析したテーブルの総数")
    top_expensive_queries: list[CostInsight] = Field(
        default_factory=list, description="コストが高いアドホッククエリのランキング"
    )
    recurring_expensive_queries: list[RecurringCostInsight] = Field(
        default_factory=list, description="定常実行の高コストクエリ"
    )
    full_scans: list[FullScanInsight] = Field(default_factory=list, description="フルスキャンと判定されたクエリ一覧")
    table_profiles: list[TableUsageProfile] = Field(
        default_factory=list, description="各テーブルの利用状況およびゾンビ判定結果"
    )
