"""高コストクエリの分析ロジック.

注意: このモジュールは google.cloud.bigquery を一切インポートしてはなりません。
純粋な Python ロジックのみで構成し、単体テストがミリ秒単位で完了するようにします。
"""

from bq_auditor.config import AppConfig
from bq_auditor.models.job import QueryJob
from bq_auditor.models.result import CostInsight

# 1 TB をバイトに変換する定数
_BYTES_PER_TB: float = 1024**4


def _bytes_to_tb(bytes_value: int) -> float:
    """バイト数を TB に変換する."""
    return bytes_value / _BYTES_PER_TB


def _estimate_cost_usd(total_bytes_billed: int, tb_price_usd: float) -> float:
    """スキャンバイト数からコスト (USD) を推定する.

    Args:
        total_bytes_billed: 課金対象バイト数
        tb_price_usd: 1TB あたりのオンデマンド料金 (USD)

    Returns:
        推定コスト (USD)
    """
    return _bytes_to_tb(total_bytes_billed) * tb_price_usd


def analyze_cost(jobs: list[QueryJob], config: AppConfig) -> list[CostInsight]:
    """クエリジョブを解析し、高コストクエリのランキングを返す.

    キャッシュヒットしたジョブは課金ゼロなので除外します。

    Args:
        jobs: QueryJob のリスト (Extractor から受け取る)
        config: AppConfig オブジェクト

    Returns:
        CostInsight のリスト (コスト降順、上位 N 件)
    """
    tb_price = config.pricing.tb_scan_usd
    limit = config.thresholds.top_expensive_queries_limit

    insights: list[CostInsight] = []
    for job in jobs:
        if job.total_bytes_billed <= 0:
            continue
        cost_usd = _estimate_cost_usd(job.total_bytes_billed, tb_price)
        scanned_tb = _bytes_to_tb(job.total_bytes_billed)
        insights.append(
            CostInsight(
                job=job,
                estimated_cost_usd=cost_usd,
                scanned_tb=scanned_tb,
            )
        )

    insights.sort(key=lambda x: x.estimated_cost_usd, reverse=True)
    return insights[:limit]
