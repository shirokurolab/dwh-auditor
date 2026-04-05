"""設定ファイル (config.yaml) の読み込みとパース."""

from __future__ import annotations

import yaml
from pydantic import BaseModel, Field


class PricingConfig(BaseModel):
    """コスト計算の単価設定."""

    tb_scan_usd: float = Field(
        default=6.25,
        description="1TB スキャンあたりのオンデマンド料金 (USD)",
        gt=0,
    )


class ThresholdsConfig(BaseModel):
    """警告しきい値の設定."""

    ignore_full_scan_under_gb: float = Field(
        default=1.0,
        description="この GB 数以下のフルスキャンは無視する",
        ge=0,
    )
    top_expensive_queries_limit: int = Field(
        default=10,
        description="高コストクエリの報告件数上限",
        gt=0,
    )
    zombie_table_days: int = Field(
        default=90,
        description="ゾンビテーブルとみなすまでの未参照日数",
        gt=0,
    )


class DbtConfig(BaseModel):
    """dbt 連携設定 (将来拡張用)."""

    enabled: bool = Field(default=False, description="dbt 連携を有効にするか")
    job_label_key: str = Field(
        default="dbt_model",
        description="dbt モデルを識別する BigQuery ジョブラベルのキー名",
    )


class AppConfig(BaseModel):
    """設定ファイル全体のスキーマ."""

    pricing: PricingConfig = Field(default_factory=PricingConfig)
    thresholds: ThresholdsConfig = Field(default_factory=ThresholdsConfig)
    dbt: DbtConfig = Field(default_factory=DbtConfig)


def load_config(path: str) -> AppConfig:
    """YAML 設定ファイルを読み込み AppConfig に変換して返す.

    Args:
        path: 設定ファイルのパス (例: "config.yaml")

    Returns:
        パース済みの AppConfig オブジェクト

    Raises:
        FileNotFoundError: 指定されたパスにファイルが存在しない場合
        yaml.YAMLError: YAML のパースに失敗した場合
        pydantic.ValidationError: 設定値がスキーマに合致しない場合
    """
    with open(path, encoding="utf-8") as f:
        raw: dict[str, object] = yaml.safe_load(f) or {}
    return AppConfig.model_validate(raw)
