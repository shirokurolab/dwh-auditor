################################
コントリビュートガイド
################################

dwh-auditor はオープンソースプロジェクトです。
バグ報告、機能改善の提案、Pull Request を歓迎します。


開発環境のセットアップ
======================

.. code-block:: bash

   git clone https://github.com/shirokurolab/dwh-auditor.git
   cd dwh-auditor

   # 仮想環境の作成（uv 推奨）
   uv venv
   uv pip install -e ".[dev]"

   # テストの実行
   uv run pytest tests/ -v

   # Lint & フォーマットチェック
   uv run ruff check .
   uv run ruff format --check .

   # 型チェック
   uv run mypy src/dwh_auditor


コントリビュートの流れ
=======================

1. Issue の確認または作成
2. ``feature/<機能名>`` または ``fix/<バグ名>`` ブランチを切る
3. コードを実装（TDD: テストを先に書く）
4. ``ruff`` / ``mypy`` を通過させる
5. Pull Request を作成


開発ルール
==========

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - ルール
     - 詳細
   * - TDD
     - テストを先に書く（Red → Green → Refactor）
   * - 型ヒント必須
     - 全関数・メソッドに型ヒントを付与し ``mypy --strict`` を通過させる
   * - Lint ゼロ警告
     - ``ruff check`` / ``ruff format`` で警告ゼロを維持する
   * - Extractor の隔離
     - ``google.cloud.bigquery`` は ``extractor/bigquery.py`` のみでインポートする

詳しくは `CONTRIBUTING.md <https://github.com/shirokurolab/dwh-auditor/blob/main/CONTRIBUTING.md>`_ を参照してください。


ライセンス
==========

MIT License — 詳細は `LICENSE <https://github.com/shirokurolab/dwh-auditor/blob/main/LICENSE>`_ を参照してください。
