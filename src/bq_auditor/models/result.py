"""分析結果のデータモデル.

Analyzer 層が Reporter 層に渡す診断結果の型定義です。
"""

from pydantic import BaseModel, Field

from bq_auditor.models.job import QueryJob
from bq_auditor.models.table import TableStorage


class CostInsight(BaseModel):
    """高コストクエリの分析結果."""

    job: QueryJob = Field(description="対象のクエリジョブ")
    estimated_cost_usd: float = Field(description="推定コスト (USD)。pricing.tb_scan_usd × スキャン TB 数で算出。")
    scanned_tb: float = Field(description="スキャンしたデータ量 (TB)")


class FullScanInsight(BaseModel):
    """フルスキャンと判定されたクエリの分析結果."""

    job: QueryJob = Field(description="対象のクエリジョブ")
    scanned_gb: float = Field(description="スキャンしたデータ量 (GB)")


class ZombieTableInsight(BaseModel):
    """使われていないテーブルの分析結果."""

    table: TableStorage = Field(description="対象のテーブル")
    days_unused: int = Field(description="最後に参照されてから経過した日数")
    size_gb: float = Field(description="テーブルの論理ストレージサイズ (GB)")


class AuditResult(BaseModel):
    """Analyzer 層が最終的に出力する総合監査結果レポート."""

    analyzed_days: int = Field(description="分析対象期間 (日数)")
    project_id: str = Field(description="分析対象の GCP プロジェクト ID")
    total_jobs_analyzed: int = Field(description="分析したジョブの総数")
    total_tables_analyzed: int = Field(description="分析したテーブルの総数")
    top_expensive_queries: list[CostInsight] = Field(default_factory=list, description="コストが高いクエリのランキング")
    full_scans: list[FullScanInsight] = Field(default_factory=list, description="フルスキャンと判定されたクエリ一覧")
    zombie_tables: list[ZombieTableInsight] = Field(
        default_factory=list, description="ゾンビテーブルと判定されたテーブル一覧"
    )
