"""分析ランナー: 各 Analyzer を呼び出して AuditResult に集約する.

注意: このモジュールは google.cloud.bigquery を一切インポートしてはなりません。
"""

from dwh_auditor.analyzer.cost import analyze_cost
from dwh_auditor.analyzer.scan import detect_full_scans
from dwh_auditor.analyzer.zombie import detect_zombie_tables
from dwh_auditor.config import AppConfig
from dwh_auditor.models.job import QueryJob
from dwh_auditor.models.result import AuditResult
from dwh_auditor.models.table import TableStorage


def run_analysis(
    jobs: list[QueryJob],
    tables: list[TableStorage],
    config: AppConfig,
    analyzed_days: int,
    project_id: str,
) -> AuditResult:
    """全 Analyzer を実行し、総合監査結果を返す.

    Args:
        jobs: Extractor から受け取った QueryJob リスト
        tables: Extractor から受け取った TableStorage リスト
        config: AppConfig オブジェクト
        analyzed_days: 分析対象期間 (日数)
        project_id: 分析対象の GCP プロジェクト ID

    Returns:
        AuditResult オブジェクト
    """
    top_expensive = analyze_cost(jobs, config)
    full_scans = detect_full_scans(jobs, config)
    zombies = detect_zombie_tables(tables, jobs, config)

    return AuditResult(
        analyzed_days=analyzed_days,
        project_id=project_id,
        total_jobs_analyzed=len(jobs),
        total_tables_analyzed=len(tables),
        top_expensive_queries=top_expensive,
        full_scans=full_scans,
        zombie_tables=zombies,
    )
