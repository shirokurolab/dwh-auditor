"""BigQuery クエリジョブのデータモデル."""

from datetime import datetime

from pydantic import BaseModel, Field


class QueryJob(BaseModel):
    """BigQuery のクエリジョブ履歴を表すモデル.

    Extractor 層が BQ の INFORMATION_SCHEMA.JOBS から取得し、
    Analyzer 層に渡す際のデータ契約として機能します。
    """

    job_id: str = Field(description="BigQuery ジョブの一意識別子")
    user_email: str = Field(description="クエリを発行したユーザーまたは SA のメールアドレス")
    query: str = Field(description="実行された SQL クエリ文字列")
    creation_time: datetime = Field(description="ジョブの作成日時 (UTC)")
    total_bytes_billed: int = Field(default=0, description="課金対象となったバイト数 (キャッシュヒット時は 0)")
    cache_hit: bool = Field(default=False, description="クエリキャッシュがヒットしたか")
    referenced_tables: list[str] = Field(
        default_factory=list,
        description="クエリで参照されたテーブルの完全修飾名リスト (project.dataset.table 形式)",
    )
    statement_type: str = Field(default="SELECT", description="SQL ステートメントの種類 (SELECT, INSERT 等)")
