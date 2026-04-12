"""BigQuery メタデータ抽出層.

警告: このモジュールのみ google.cloud.bigquery をインポートできます。
他のモジュール (analyzer/, reporter/, main.py) からは直接インポートしてはなりません。
"""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from typing import Any, Callable, Optional, TypeVar, cast

import google.cloud.bigquery as bq
from google.api_core.exceptions import Forbidden
from rich.console import Console

from dwh_auditor.models.job import QueryJob
from dwh_auditor.models.table import TableStorage

# -------------------------------------------------------------------------
# SQL テンプレート
# -------------------------------------------------------------------------

_TOP_COST_SQL_BODY = """
SELECT
    job_id,
    user_email,
    query,
    creation_time,
    IFNULL(total_bytes_billed, 0)   AS total_bytes_billed,
    IFNULL(cache_hit, FALSE)         AS cache_hit,
    IFNULL(statement_type, 'SELECT') AS statement_type,
    TO_JSON_STRING(referenced_tables) AS referenced_tables_json
FROM `{project}`.`{region}`.INFORMATION_SCHEMA.JOBS
WHERE creation_time >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL {days} DAY)
  AND job_type = 'QUERY' AND state = 'DONE' AND error_result IS NULL
"""

_HEAVY_SCAN_SQL_BODY = """
SELECT
    job_id,
    user_email,
    query,
    creation_time,
    IFNULL(total_bytes_billed, 0)   AS total_bytes_billed,
    IFNULL(cache_hit, FALSE)         AS cache_hit,
    IFNULL(statement_type, 'SELECT') AS statement_type,
    TO_JSON_STRING(referenced_tables) AS referenced_tables_json
FROM `{project}`.`{region}`.INFORMATION_SCHEMA.JOBS
WHERE creation_time >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL {days} DAY)
  AND job_type = 'QUERY' AND state = 'DONE' AND error_result IS NULL
  AND cache_hit = FALSE
  AND total_bytes_billed >= {min_bytes}
"""

_RECURRING_SQL_BODY = """
SELECT
    query_info.query_hashes.normalized_literals AS query_hash,
    ANY_VALUE(query) AS query_sample,
    COUNT(1) AS execution_count,
    SUM(total_bytes_billed) AS total_bytes_billed,
    MAX(creation_time) AS last_executed_at
FROM `{project}`.`{region}`.INFORMATION_SCHEMA.JOBS
WHERE creation_time >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL {days} DAY)
  AND job_type = 'QUERY' AND state = 'DONE' AND error_result IS NULL
  AND cache_hit = FALSE AND total_bytes_billed > 0
GROUP BY 1
HAVING execution_count >= {min_executions}
"""

_TABLE_USAGE_SQL_BODY = """
SELECT
    ref_table.project_id || '.' || ref_table.dataset_id || '.' || ref_table.table_id AS table_id,
    MAX(creation_time) AS last_accessed_at,
    COUNT(1) AS access_count,
    ARRAY_AGG(DISTINCT user_email IGNORE NULLS LIMIT 5) AS top_users
FROM `{project}`.`{region}`.INFORMATION_SCHEMA.JOBS,
UNNEST(referenced_tables) AS ref_table
WHERE creation_time >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL {days} DAY)
  AND job_type = 'QUERY' AND state = 'DONE' AND error_result IS NULL
GROUP BY 1
"""

_TABLE_STORAGE_SQL = """
SELECT
    table_catalog  AS project_id,
    table_schema   AS dataset_id,
    table_name     AS table_id,
    IFNULL(total_logical_bytes, 0)   AS total_logical_bytes,
    IFNULL(total_physical_bytes, 0)  AS total_physical_bytes,
    IFNULL(active_logical_bytes, 0)  AS active_logical_bytes
FROM `{project}`.`{region}`.INFORMATION_SCHEMA.TABLE_STORAGE
WHERE deleted = FALSE
"""


def _parse_referenced_tables(json_str: Optional[str]) -> list[str]:
    """JSON 文字列からテーブルIDの完全修飾名のリストを構築する."""
    import json

    if not json_str:
        return []
    try:
        tables = json.loads(json_str)
        refs = []
        for t in tables:
            pid = t.get("project_id", "")
            did = t.get("dataset_id", "")
            tid = t.get("table_id", "")
            if pid and did and tid:
                refs.append(f"{pid}.{did}.{tid}")
        return refs
    except Exception:
        return []


def _build_union_query(projects: list[str], region: str, body_template: str, **kwargs: Any) -> str:  # noqa: ANN401
    """複数プロジェクトに対する UNION ALL クエリを構築する."""
    parts = []
    for p in projects:
        parts.append(body_template.format(project=p, region=region, **kwargs))
    return "\nUNION ALL\n".join(parts)


F = TypeVar("F", bound=Callable[..., Any])


def _handle_bq_error(func: F) -> F:
    """BQ 実行時のエラー、特に IAM 権限不足をキャッチして分かりやすいエラーを提示するデコレータ."""

    def wrapper(*args: Any, **kwargs: Any) -> Any:  # noqa: ANN401
        try:
            return func(*args, **kwargs)
        except Forbidden as e:
            c = Console()
            c.print("\n[bold red]✖ BigQuery へのアクセス権限が拒否されました (403 Forbidden)[/bold red]")
            c.print("以下の原因が考えられます：")
            c.print("1. 実行しているアカウントに [cyan]roles/bigquery.metadataViewer[/cyan] 等の権限が不足している")
            c.print("2. 指定されたプロジェクトが存在しない、または API が有効化されていない")
            c.print(f"\n[red]詳細エラー:[/red] {e.message}")
            sys.exit(1)

    return cast(F, wrapper)


class BigQueryExtractor:
    """BigQuery メタデータ抽出クラス (v0.2.0 API 準拠)."""

    def __init__(self, target_project_id: str, job_project_ids: list[str], region: str) -> None:
        self._target_project_id = target_project_id
        self._job_project_ids = job_project_ids if job_project_ids else [target_project_id]
        self._region = region
        self._client: bq.Client = bq.Client(project=target_project_id)

    @_handle_bq_error
    def get_top_cost_jobs(self, days: int, limit: int) -> list[QueryJob]:
        """高コストクエリを抽出する (LIMIT によって API 通信量を劇的に抑える)."""
        sql = _build_union_query(self._job_project_ids, self._region, _TOP_COST_SQL_BODY, days=days)
        sql += f"\nORDER BY total_bytes_billed DESC LIMIT {limit}"
        return self._fetch_jobs_by_sql(sql)

    @_handle_bq_error
    def get_heavy_scan_jobs(self, days: int, min_scanned_bytes: int) -> list[QueryJob]:
        """フルスキャン判定用に、一定容量以上をスキャンしたジョブのみ抽出する."""
        sql = _build_union_query(
            self._job_project_ids, self._region, _HEAVY_SCAN_SQL_BODY, days=days, min_bytes=min_scanned_bytes
        )
        # 上限は念の為1000件などに絞る。非常に大規模環境でOOMを防ぐため
        sql += "\nORDER BY total_bytes_billed DESC LIMIT 1000"
        return self._fetch_jobs_by_sql(sql)

    def _fetch_jobs_by_sql(self, sql: str) -> list[QueryJob]:
        rows = self._client.query(sql).result()
        jobs: list[QueryJob] = []
        for row in rows:
            c_time: datetime = row["creation_time"]
            if c_time.tzinfo is None:
                c_time = c_time.replace(tzinfo=timezone.utc)
            jobs.append(
                QueryJob(
                    job_id=str(row["job_id"]),
                    user_email=str(row["user_email"]),
                    query=str(row["query"]),
                    creation_time=c_time,
                    total_bytes_billed=int(row["total_bytes_billed"]),
                    cache_hit=bool(row["cache_hit"]),
                    statement_type=str(row["statement_type"]),
                    referenced_tables=_parse_referenced_tables(row.get("referenced_tables_json")),
                )
            )
        return jobs

    @_handle_bq_error
    def get_recurring_cost_jobs(self, days: int, min_executions: int = 5, limit: int = 50) -> list[dict[str, Any]]:
        """定常実行クエリのメタデータを抽出する."""
        sql = _build_union_query(
            self._job_project_ids, self._region, _RECURRING_SQL_BODY, days=days, min_executions=min_executions
        )
        sql += f"\nORDER BY total_bytes_billed DESC LIMIT {limit}"
        rows = self._client.query(sql).result()
        results = []
        for row in rows:
            c_time: datetime = row["last_executed_at"]
            if c_time.tzinfo is None:
                c_time = c_time.replace(tzinfo=timezone.utc)
            results.append(
                {
                    "query_hash": str(row["query_hash"]),
                    "query_sample": str(row["query_sample"]),
                    "execution_count": int(row["execution_count"]),
                    "total_bytes_billed": int(row["total_bytes_billed"]),
                    "last_executed_at": c_time,
                }
            )
        return results

    @_handle_bq_error
    def get_table_usage_stats(self, days: int) -> dict[str, dict[str, Any]]:
        """参照テーブル一覧と利用統計を抽出する. (UNNESTを利用)"""
        sql = _build_union_query(self._job_project_ids, self._region, _TABLE_USAGE_SQL_BODY, days=days)
        rows = self._client.query(sql).result()
        stats_map = {}
        for row in rows:
            c_time: datetime = row["last_accessed_at"]
            if c_time.tzinfo is None:
                c_time = c_time.replace(tzinfo=timezone.utc)
            stats_map[str(row["table_id"])] = {
                "last_accessed_at": c_time,
                "access_count": int(row["access_count"]),
                "top_users": list(row["top_users"]),
            }
        return stats_map

    @_handle_bq_error
    def get_table_storage(self) -> list[TableStorage]:
        """INFORMATION_SCHEMA.TABLE_STORAGE からテーブルストレージ情報を抽出する."""
        sql = _TABLE_STORAGE_SQL.format(
            project=self._target_project_id,
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
