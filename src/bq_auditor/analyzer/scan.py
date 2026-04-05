"""フルスキャン（非効率クエリ）の検知ロジック.

注意: このモジュールは google.cloud.bigquery を一切インポートしてはなりません。
純粋な Python ロジックのみで構成し、単体テストがミリ秒単位で完了するようにします。
"""

import re

from bq_auditor.config import AppConfig
from bq_auditor.models.job import QueryJob
from bq_auditor.models.result import FullScanInsight

# 1 GB をバイトに変換する定数
_BYTES_PER_GB: float = 1024**3

# パーティション絞り込みに使われる典型的なパターン
# WHERE 句に日付フィルタ or _PARTITIONTIME / _PARTITIONDATE が含まれているか
_PARTITION_FILTER_PATTERN = re.compile(
    r"WHERE\s.*(partition|_PARTITIONTIME|_PARTITIONDATE|\d{4}-\d{2}-\d{2})",
    re.IGNORECASE | re.DOTALL,
)


def _bytes_to_gb(bytes_value: int) -> float:
    """バイト数を GB に変換する."""
    return bytes_value / _BYTES_PER_GB


def _is_full_scan(query: str) -> bool:
    """クエリがフルスキャンを行っている可能性があるか判定する.

    簡易判定ルール:
    - WHERE 句が存在しない、または
    - WHERE 句にパーティション指定パターンが含まれていない

    Args:
        query: SQL クエリ文字列

    Returns:
        フルスキャンの可能性がある場合 True
    """
    query_upper = query.upper()
    if "WHERE" not in query_upper:
        return True
    # パーティションフィルタや日付フィルタが見当たらない場合もフルスキャン扱い
    return not bool(_PARTITION_FILTER_PATTERN.search(query))


def detect_full_scans(jobs: list[QueryJob], config: AppConfig) -> list[FullScanInsight]:
    """フルスキャンの可能性があるクエリを検知する.

    ignore_full_scan_under_gb 以下のスキャンは警告から除外します
    (小規模マスターテーブルのスキャンで警告疲れを防ぐため)。

    Args:
        jobs: QueryJob のリスト
        config: AppConfig オブジェクト

    Returns:
        FullScanInsight のリスト (スキャン GB 降順)
    """
    ignore_threshold_bytes = config.thresholds.ignore_full_scan_under_gb * _BYTES_PER_GB

    insights: list[FullScanInsight] = []
    for job in jobs:
        if job.total_bytes_billed <= ignore_threshold_bytes:
            continue
        if job.cache_hit:
            continue
        if _is_full_scan(job.query):
            insights.append(
                FullScanInsight(
                    job=job,
                    scanned_gb=_bytes_to_gb(job.total_bytes_billed),
                )
            )

    insights.sort(key=lambda x: x.scanned_gb, reverse=True)
    return insights
