"""BigQuery テーブルストレージのデータモデル."""

from pydantic import BaseModel, Field, computed_field


class TableStorage(BaseModel):
    """BigQuery テーブルごとのストレージ情報を表すモデル.

    Extractor 層が BQ の INFORMATION_SCHEMA.TABLE_STORAGE から取得し、
    Analyzer 層（ゾンビテーブル検知）に渡す際のデータ契約として機能します。
    """

    project_id: str = Field(description="GCP プロジェクト ID")
    dataset_id: str = Field(description="BigQuery データセット ID")
    table_id: str = Field(description="BigQuery テーブル ID")
    total_logical_bytes: int = Field(default=0, description="テーブルの論理的なストレージサイズ (バイト)")
    total_physical_bytes: int = Field(default=0, description="テーブルの物理的なストレージサイズ (バイト、圧縮後)")
    active_logical_bytes: int = Field(default=0, description="アクティブストレージの論理サイズ (バイト)")

    @computed_field  # type: ignore[prop-decorator]
    @property
    def full_table_id(self) -> str:
        """プロジェクト・データセット・テーブル名を結合した完全修飾名."""
        return f"{self.project_id}.{self.dataset_id}.{self.table_id}"
