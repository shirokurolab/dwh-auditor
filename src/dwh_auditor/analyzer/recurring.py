"""定常実行クエリの分析ロジック.

注意: このモジュールは google.cloud.bigquery を一切インポートしてはなりません。
"""

from typing import Any

from dwh_auditor.config import AppConfig
from dwh_auditor.models.result import RecurringCostInsight

_BYTES_PER_TB: float = 1024**4


def analyze_recurring_cost(
    raw_stats: list[dict[str, Any]], config: AppConfig
) -> list[RecurringCostInsight]:
    """定常実行されているクエリのメタデータを RecurringCostInsight のリストにマップ・計算する.

    Args:
        raw_stats: Extractor から抽出した定常クエリの集計辞書
        config: しきい値やコスト単価設定

    Returns:
        RecurringCostInsight のリスト
    """
    tb_usd = config.pricing.tb_scan_usd
    insights: list[RecurringCostInsight] = []

    for stat in raw_stats:
        billed_bytes = stat.get("total_bytes_billed", 0)
        scanned_tb = billed_bytes / _BYTES_PER_TB
        estimated_usd = scanned_tb * tb_usd

        insights.append(
            RecurringCostInsight(
                query_hash=stat["query_hash"],
                query_sample=stat["query_sample"],
                execution_count=stat["execution_count"],
                total_estimated_usd=estimated_usd,
                total_scanned_tb=scanned_tb,
                last_executed_at=stat["last_executed_at"],
            )
        )

    return insights
