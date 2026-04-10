"""ゾンビテーブル（使われていないテーブル）の検知ロジック.

注意: このモジュールは google.cloud.bigquery を一切インポートしてはなりません。
純粋な Python ロジックのみで構成し、単体テストがミリ秒単位で完了するようにします。
"""

from datetime import datetime, timezone

from dwh_auditor.config import AppConfig
from dwh_auditor.models.job import QueryJob
from dwh_auditor.models.result import ZombieTableInsight
from dwh_auditor.models.table import TableStorage

_BYTES_PER_GB: float = 1024**3


def _bytes_to_gb(bytes_value: int) -> float:
    """バイト数を GB に変換する."""
    return bytes_value / _BYTES_PER_GB


def _collect_referenced_table_ids(jobs: list[QueryJob]) -> set[str]:
    """全ジョブで参照されたテーブルの完全修飾名セットを返す.

    referenced_tables フィールドが空の場合は、クエリ文字列から
    バッグストップ的に FROM 句のテーブルを推定はしません (精度を優先)。

    Args:
        jobs: QueryJob のリスト

    Returns:
        参照されたテーブル ID のセット ("project.dataset.table" 形式)
    """
    referenced: set[str] = set()
    for job in jobs:
        for table_id in job.referenced_tables:
            referenced.add(table_id)
    return referenced


def detect_zombie_tables(
    tables: list[TableStorage],
    jobs: list[QueryJob],
    config: AppConfig,
) -> list[ZombieTableInsight]:
    """ゾンビテーブルを検知する.

    zombie_table_days 以上、一度も SELECT で参照されていないテーブルを
    ゾンビとして報告します。

    Args:
        tables: TableStorage のリスト (Extractor から受け取る)
        jobs: QueryJob のリスト (同上。参照テーブルの特定に使用)
        config: AppConfig オブジェクト

    Returns:
        ZombieTableInsight のリスト (ストレージサイズ降順)
    """
    zombie_days = config.thresholds.zombie_table_days
    referenced_ids = _collect_referenced_table_ids(jobs)
    now = datetime.now(tz=timezone.utc)

    insights: list[ZombieTableInsight] = []
    for table in tables:
        if table.full_table_id not in referenced_ids:
            insights.append(
                ZombieTableInsight(
                    table=table,
                    days_unused=zombie_days,
                    size_gb=_bytes_to_gb(table.total_logical_bytes),
                )
            )

    # ストレージが大きいテーブルを優先的に報告
    insights.sort(key=lambda x: x.size_gb, reverse=True)
    _ = now  # future: last_modified_time を使った精密な経過日数計算のために保持
    return insights
