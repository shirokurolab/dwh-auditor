"""BigQuery メタデータ抽出層.

警告: このモジュールのみ google.cloud.bigquery をインポートできます。
他のモジュール (analyzer/, reporter/, main.py) からは直接インポートしてはなりません。
"""

from __future__ import annotations

from datetime import datetime, timezone

import google.cloud.bigquery as bq

from bq_auditor.models.job import QueryJob
from bq_auditor.models.table import TableStorage

# INFORMATION_SCHEMA.JOBS から取得する SQL テンプレート
_JOBS_QUERY_TEMPLATE = """
SELECT
    job_id,
    user_email,
    query,
    creation_time,
    IFNULL(total_bytes_billed, 0)   AS total_bytes_billed,
    IFNULL(cache_hit, FALSE)         AS cache_hit,
    IFNULL(statement_type, 'SELECT') AS statement_type
FROM
    `{project}`.`{region}`.INFORMATION_SCHEMA.JOBS
WHERE
    creation_time >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL {days} DAY)
    AND job_type = 'QUERY'
    AND state = 'DONE'
    AND error_result IS NULL
ORDER BY
    total_bytes_billed DESC
"""

# INFORMATION_SCHEMA.TABLE_STORAGE から取得する SQL テンプレート
_TABLE_STORAGE_QUERY_TEMPLATE = """
SELECT
    table_catalog  AS project_id,
    table_schema   AS dataset_id,
    table_name     AS table_id,
    IFNULL(total_logical_bytes, 0)   AS total_logical_bytes,
    IFNULL(total_physical_bytes, 0)  AS total_physical_bytes,
    IFNULL(active_logical_bytes, 0)  AS active_logical_bytes
FROM
    `{project}`.`{region}`.INFORMATION_SCHEMA.TABLE_STORAGE
WHERE
    deleted = FALSE
"""


class BigQueryExtractor:
    """BigQuery の INFORMATION_SCHEMA からメタデータを抽出するクラス.

    このクラスは BQ ライブラリとの唯一の接点です。
    テスト時は google.cloud.bigquery.Client をモックして差し替えます。
    """

    def __init__(self, project_id: str, region: str) -> None:
        """初期化.

        Args:
            project_id: 分析対象の GCP プロジェクト ID
            region: BigQuery のリージョン (例: "region-us", "region-asia-northeast1")
        """
        self._project_id = project_id
        self._region = region
        self._client: bq.Client = bq.Client(project=project_id)

    def get_job_history(self, days: int = 30) -> list[QueryJob]:
        """INFORMATION_SCHEMA.JOBS からクエリジョブ履歴を取得する.

        Args:
            days: 過去何日分のジョブ履歴を取得するか (デフォルト 30 日)

        Returns:
            QueryJob のリスト (total_bytes_billed の降順)
        """
        sql = _JOBS_QUERY_TEMPLATE.format(
            project=self._project_id,
            region=self._region,
            days=days,
        )
        rows = self._client.query(sql).result()
        jobs: list[QueryJob] = []
        for row in rows:
            creation_time: datetime = row["creation_time"]
            # BQ SDK が返す datetime は UTC aware のため、そのまま利用
            if creation_time.tzinfo is None:
                creation_time = creation_time.replace(tzinfo=timezone.utc)
            jobs.append(
                QueryJob(
                    job_id=str(row["job_id"]),
                    user_email=str(row["user_email"]),
                    query=str(row["query"]),
                    creation_time=creation_time,
                    total_bytes_billed=int(row["total_bytes_billed"]),
                    cache_hit=bool(row["cache_hit"]),
                    statement_type=str(row["statement_type"]),
                )
            )
        return jobs

    def get_table_storage(self) -> list[TableStorage]:
        """INFORMATION_SCHEMA.TABLE_STORAGE からテーブルストレージ情報を取得する.

        Returns:
            TableStorage のリスト
        """
        sql = _TABLE_STORAGE_QUERY_TEMPLATE.format(
            project=self._project_id,
            region=self._region,
        )
        rows = self._client.query(sql).result()
        tables: list[TableStorage] = []
        for row in rows:
            tables.append(
                TableStorage(
                    project_id=str(row["project_id"]),
                    dataset_id=str(row["dataset_id"]),
                    table_id=str(row["table_id"]),
                    total_logical_bytes=int(row["total_logical_bytes"]),
                    total_physical_bytes=int(row["total_physical_bytes"]),
                    active_logical_bytes=int(row["active_logical_bytes"]),
                )
            )
        return tables
