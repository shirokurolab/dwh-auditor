"""テーブルプロファイリング・およびゾンビ（未使用）判定ロジック.

注意: このモジュールは google.cloud.bigquery を一切インポートしてはなりません。
純粋な Python ロジックのみで構成し、単体テストがミリ秒単位で完了するようにします。
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from dwh_auditor.config import AppConfig
from dwh_auditor.models.result import TableUsageProfile
from dwh_auditor.models.table import TableStorage

_BYTES_PER_GB: float = 1024**3


def _bytes_to_gb(bytes_value: int) -> float:
    """バイト数を GB に変換する."""
    return bytes_value / _BYTES_PER_GB


def analyze_table_usage(
    tables: list[TableStorage],
    usage_stats: dict[str, dict[str, Any]],
    config: AppConfig,
    now: Optional[datetime] = None,
) -> list[TableUsageProfile]:
    """各テーブルのプロファイル（利用状況とゾンビ判定結果）を返す.

    Extractor から受け取った軽量な usage_stats と tables を結合します。

    Args:
        tables: TableStorage のリスト (Extractor から受け取る)
        usage_stats: "project.dataset.table" をキーとする統計辞書 (Extractor から受け取る)
        config: AppConfig オブジェクト
        now: 基準となる現在日時 (テスト用)

    Returns:
        TableUsageProfile のリスト (ストレージサイズ降順)
    """
    zombie_days = config.thresholds.zombie_table_days
    if now is None:
        now = datetime.now(tz=timezone.utc)

    profiles: list[TableUsageProfile] = []
    for table in tables:
        stat = usage_stats.get(table.full_table_id, {})
        last_accessed_at = stat.get("last_accessed_at")
        access_count = stat.get("access_count", 0)
        top_users = stat.get("top_users", [])

        # 判定ロジック:
        # 一度も取得期間内でアクセスされていない、または最終アクセスが閾値より昔ならゾンビ
        is_zombie = False
        if last_accessed_at is None:
            is_zombie = True
        else:
            diff_days = (now - last_accessed_at).days
            if diff_days >= zombie_days:
                is_zombie = True

        if is_zombie:
            profiles.append(
                TableUsageProfile(
                    table=table,
                    is_zombie=True,
                    last_accessed_at=last_accessed_at,
                    top_users=top_users,
                    access_count_30d=access_count,
                    size_gb=_bytes_to_gb(table.total_logical_bytes),
                )
            )

    # ストレージが大きい順にソートし、多すぎる場合は上位 100 件程度に制限する
    profiles.sort(key=lambda x: x.size_gb, reverse=True)
    return profiles[:100]
