"""フルスキャン（非効率クエリ）の検知ロジック.

注意: このモジュールは google.cloud.bigquery を一切インポートしてはなりません。
純粋な Python ロジックのみで構成し、単体テストがミリ秒単位で完了するようにします。
"""

import re

from dwh_auditor.config import AppConfig
from dwh_auditor.models.job import QueryJob
from dwh_auditor.models.result import FullScanInsight
from dwh_auditor.models.table import TableStorage

# 1 GB をバイトに変換する定数
_BYTES_PER_GB: float = 1024**3

# パーティション絞り込みに使われる典型的なパターン (フォールバック用)
_PARTITION_FILTER_PATTERN = re.compile(
    r"WHERE\s.*(partition|_PARTITIONTIME|_PARTITIONDATE|\d{4}-\d{2}-\d{2})",
    re.IGNORECASE | re.DOTALL,
)


def _bytes_to_gb(bytes_value: int) -> float:
    """バイト数を GB に変換する."""
    return bytes_value / _BYTES_PER_GB


def _is_full_scan_fallback(query: str) -> bool:
    """クエリがフルスキャンを行っている可能性があるか、文字列で簡易判定する.フォールバック用."""
    query_upper = query.upper()
    if "WHERE" not in query_upper:
        return True
    return not bool(_PARTITION_FILTER_PATTERN.search(query))


def detect_full_scans(
    jobs: list[QueryJob], tables: list[TableStorage], config: AppConfig
) -> list[FullScanInsight]:
    """フルスキャンの可能性があるクエリを検知する.

    バイト比率バリデーション方式:
    クエリの課金バイト数が参照テーブルの物理サイズの 90% 以上ならフルスキャンとみなす。

    Args:
        jobs: Extractor から抽出したパース対象のジョブ
        tables: テーブルサイズ情報をルックアップするためのリスト
        config: しきい値

    Returns:
        FullScanInsight のリスト
    """
    ignore_threshold_bytes = config.thresholds.ignore_full_scan_under_gb * _BYTES_PER_GB
    ratio_threshold = config.thresholds.full_scan_ratio_threshold

    table_size_map = {t.full_table_id: t.total_logical_bytes for t in tables}

    insights: list[FullScanInsight] = []
    for job in jobs:
        if job.total_bytes_billed <= ignore_threshold_bytes:
            continue
        if job.cache_hit:
            continue

        total_referenced_size = 0
        cannot_calculate_size = False
        
        if not job.referenced_tables:
            cannot_calculate_size = True
        else:
            for ref in job.referenced_tables:
                if ref not in table_size_map or table_size_map[ref] <= 0:
                    cannot_calculate_size = True
                    break
                total_referenced_size += table_size_map[ref]

        is_full_scan = False
        if cannot_calculate_size or total_referenced_size == 0:
            is_full_scan = _is_full_scan_fallback(job.query)
        else:
            ratio = job.total_bytes_billed / total_referenced_size
            if ratio >= ratio_threshold:
                is_full_scan = True

        if is_full_scan:
            insights.append(
                FullScanInsight(
                    job=job,
                    scanned_gb=_bytes_to_gb(job.total_bytes_billed),
                )
            )

    insights.sort(key=lambda x: x.scanned_gb, reverse=True)
    return insights
