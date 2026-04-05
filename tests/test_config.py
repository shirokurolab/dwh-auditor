"""config.py のテスト."""

from __future__ import annotations

import pytest

from bq_auditor.config import AppConfig, load_config


class TestLoadConfig:
    """load_config 関数のテスト."""

    def test_load_valid_config(self, tmp_path: pytest.fixture) -> None:  # type: ignore[name-defined]
        """正常な YAML ファイルを読み込めること."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text(
            """
pricing:
  tb_scan_usd: 5.0
thresholds:
  ignore_full_scan_under_gb: 2.0
  top_expensive_queries_limit: 5
  zombie_table_days: 60
dbt:
  enabled: false
  job_label_key: dbt_model
""",
            encoding="utf-8",
        )
        config = load_config(str(config_file))
        assert config.pricing.tb_scan_usd == 5.0
        assert config.thresholds.ignore_full_scan_under_gb == 2.0
        assert config.thresholds.top_expensive_queries_limit == 5
        assert config.thresholds.zombie_table_days == 60
        assert config.dbt.enabled is False

    def test_load_partial_config_uses_defaults(self, tmp_path: pytest.fixture) -> None:  # type: ignore[name-defined]
        """一部のフィールドが省略されている場合はデフォルト値が使われること."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text(
            """
pricing:
  tb_scan_usd: 7.0
""",
            encoding="utf-8",
        )
        config = load_config(str(config_file))
        assert config.pricing.tb_scan_usd == 7.0
        # 省略されたフィールドはデフォルト値
        assert config.thresholds.zombie_table_days == 90
        assert config.thresholds.top_expensive_queries_limit == 10

    def test_load_empty_yaml_uses_defaults(self, tmp_path: pytest.fixture) -> None:  # type: ignore[name-defined]
        """空の YAML ファイルの場合はすべてデフォルト値が使われること."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("", encoding="utf-8")
        config = load_config(str(config_file))
        assert config == AppConfig()

    def test_file_not_found_raises_error(self) -> None:
        """存在しないファイルパスを渡した場合に FileNotFoundError が発生すること."""
        with pytest.raises(FileNotFoundError):
            load_config("/nonexistent/path/config.yaml")


class TestAppConfig:
    """AppConfig デフォルト値のテスト."""

    def test_default_values(self) -> None:
        """デフォルト値が仕様通りであること."""
        config = AppConfig()
        assert config.pricing.tb_scan_usd == 6.25
        assert config.thresholds.ignore_full_scan_under_gb == 1.0
        assert config.thresholds.top_expensive_queries_limit == 10
        assert config.thresholds.zombie_table_days == 90
        assert config.dbt.enabled is False
