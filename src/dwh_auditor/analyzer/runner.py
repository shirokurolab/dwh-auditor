"""分析ランナー: 各 Analyzer を呼び出して AuditResult に集約する.

注意: このモジュールは google.cloud.bigquery を一切インポートしてはなりません。
"""

from typing import Any

from dwh_auditor.analyzer.cost import analyze_cost
from dwh_auditor.analyzer.recurring import analyze_recurring_cost
from dwh_auditor.analyzer.scan import detect_full_scans
from dwh_auditor.analyzer.zombie import analyze_table_usage
from dwh_auditor.config import AppConfig
from dwh_auditor.models.job import QueryJob
from dwh_auditor.models.result import AuditResult
from dwh_auditor.models.table import TableStorage


def run_analysis(
    top_cost_jobs: list[QueryJob],
    heavy_scan_jobs: list[QueryJob],
    recurring_stats: list[dict[str, Any]],
    table_usages: dict[str, dict[str, Any]],
    tables: list[TableStorage],
    config: AppConfig,
    analyzed_days: int,
    project_id: str,
) -> AuditResult:
    """全 Analyzer を実行し、総合監査結果を返す.

    Args:
        top_cost_jobs: 高コストランキング用のジョブ抽出結果
        heavy_scan_jobs: フルスキャン検知用のジョブ抽出結果
        recurring_stats: 定常実行クエリの抽出結果 (dict)
        table_usages: テーブルごとの利用統計 (dict)
        tables: テーブルストレージ情報
        config: AppConfig オブジェクト
        analyzed_days: 分析対象期間 (日数)
        project_id: 分析対象の自 GCP プロジェクト ID

    Returns:
        AuditResult オブジェクト
    """
    top_expensive = analyze_cost(top_cost_jobs, config)
    recurring_expensive = analyze_recurring_cost(recurring_stats, config)
    full_scans = detect_full_scans(heavy_scan_jobs, tables, config)
    profiles = analyze_table_usage(tables, table_usages, config)

    # Note: total_jobs_analyzed は厳密な全ジョブ数とはならなくなったが、概算または 0 とするか
    # ユーザーに対する報告の分かりやすさのため、足切り前の情報を出せないのでひとまず 0 とするか、
    # 各抽出結果の合計とする。ここでは便宜上、top + heavy + recurringとする。
    total_analyzed = len(top_cost_jobs) + len(heavy_scan_jobs) + len(recurring_stats)

    return AuditResult(
        analyzed_days=analyzed_days,
        project_id=project_id,
        total_jobs_analyzed=total_analyzed,
        total_tables_analyzed=len(tables),
        top_expensive_queries=top_expensive,
        recurring_expensive_queries=recurring_expensive,
        full_scans=full_scans,
        table_profiles=profiles,
    )
