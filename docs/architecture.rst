############################################################
アーキテクチャ設計 — DWH 監査の 3 層分離アーキテクチャ
############################################################

dwh-auditor は **「関心の分離 (Separation of Concerns)」** を厳格に適用した
3 層アーキテクチャで設計されています。
この設計により、BigQuery 固有のコードを一か所に集約し、
将来 Snowflake や Redshift などの DWH に拡張する際も
最小限の変更で対応できます。


全体の処理フロー
================

.. code-block:: text

   ┌─────────────────────────────────────────────┐
   │  CLI (main.py / Typer)                      │
   │  dwh-auditor analyze --project ... --days 30  │
   └────────────────────┬────────────────────────┘
                        │
              ┌─────────▼──────────┐
              │  Extractor Tier       │  ← google.cloud.bigquery EXCLUSIVELY here
              │  extractor/         │
              │  bigquery.py        │
              └─────────┬──────────┘
                        │ [QueryJob, TableStorage]
              ┌─────────▼──────────┐
              │  Analyzer Tier        │  ← Pure Python, zero external API dependencies
              │  analyzer/          │
              │  cost.py / scan.py  │
              │  zombie.py          │
              └─────────┬──────────┘
                        │ [AuditResult]
              ┌─────────▼──────────┐
              │  Reporter Tier        │
              │  reporter/          │
              │  console.py         │  ← Rich terminal output
              │  markdown.py        │  ← Generates report.md
              └────────────────────┘


各層の責務
==========

Extractor Tier (``src/dwh_auditor/extractor/``)
-----------------------------------------------

**BigQuery との唯一の接点** です。
``INFORMATION_SCHEMA`` へのクエリ発行と、その結果を
Pydantic モデルへの変換のみを担います。

.. note::

   ``google.cloud.bigquery`` ライブラリの import は
   **``extractor/bigquery.py`` のみ** に許可されています。
   他のモジュールからは絶対にインポートしてはなりません。

取得するデータソース:

.. list-table::
   :header-rows: 1
   :widths: 40 60

   * - INFORMATION_SCHEMA ビュー
     - 取得内容
   * - ``INFORMATION_SCHEMA.JOBS``
     - 過去 N 日間のクエリ実行履歴
   * - ``INFORMATION_SCHEMA.TABLE_STORAGE``
     - テーブルごとのストレージ使用量

提供する関数インターフェース:

.. code-block:: python

   extractor = BigQueryExtractor(project_id="my-project", region="region-us")
   jobs: list[QueryJob] = extractor.get_job_history(days=30)
   tables: list[TableStorage] = extractor.get_table_storage()


Analyzer Tier (``src/dwh_auditor/analyzer/``)
---------------------------------------------

Extractor から受け取った Pydantic モデルと、``config.yaml`` のしきい値を
突き合わせて診断を行う **純粋な Python ロジック** です。

外部 API 通信を一切含まないため、単体テストが **ミリ秒単位** で完了します。

.. list-table::
   :header-rows: 1
   :widths: 25 75

   * - モジュール
     - 診断ロジック
   * - ``analyzer/cost.py``
     - 高コストクエリの検知（スキャンバイト数 → USD 変換、Top-N ランキング）
   * - ``analyzer/scan.py``
     - フルスキャン検知（WHERE 句・パーティションフィルタの有無を正規表現で判定）
   * - ``analyzer/zombie.py``
     - ゾンビテーブル検知（ジョブ履歴の参照テーブルと突き合わせ）
   * - ``analyzer/runner.py``
     - 上記 3 つを呼び出して ``AuditResult`` に集約


Reporter Tier (``src/dwh_auditor/reporter/``)
---------------------------------------------

``AuditResult`` を受け取り、ユーザーに見せる形式に整形します。

.. list-table::
   :header-rows: 1
   :widths: 25 75

   * - モジュール
     - 出力先
   * - ``reporter/console.py``
     - `Rich <https://rich.readthedocs.io/>`_ ライブラリによるターミナルへのカラー出力
   * - ``reporter/markdown.py``
     - ``report.md`` の生成（CI/CD の Artifact として保存可能）


内部データモデル
================

各層の間のデータ受け渡しには Pydantic モデルを使用しています。
``dict`` をそのまま受け渡すのではなく、型定義を持たせることで
バグを防ぎ、エディタの補完を効かせます。

.. code-block:: text

   Extractor → Analyzer:
     - QueryJob           (1 BQ job history record)
     - TableStorage       (1 table storage info record)

   Analyzer → Reporter:
     - CostInsight        (High-cost query analysis result)
     - FullScanInsight    (Full scan detection result)
     - ZombieTableInsight (Zombie table detection result)
     - AuditResult        (Aggregated result of the above)

詳細は :doc:`api/models` を参照してください。


テスト戦略 — なぜ高速テストが可能なのか
========================================

3 層分離の最大のメリットは **テストの書きやすさ** です。

Testing the Analyzer Tier
-------------------------

Pydantic モデルにダミーデータを入れて関数を呼ぶだけです。
BigQuery のモックは **一切不要** で、46 テストが **0.35 秒以内** に完了します。

.. code-block:: python

   # Analyzer can be tested without connecting to BQ
   jobs = [QueryJob(job_id="j1", user_email="u@e.com", ...)]
   result = analyze_cost(jobs, config=AppConfig())
   assert len(result) == 1

Testing the Extractor Tier
--------------------------

``pytest-mock`` で ``google.cloud.bigquery.Client`` をパッチするだけです。

.. code-block:: python

   def test_get_job_history(mocker):
       mock_client = mocker.patch("dwh_auditor.extractor.bigquery.bq.Client")
       mock_client.return_value.query.return_value.result.return_value = [...]

       extractor = BigQueryExtractor(project_id="p", region="region-us")
       jobs = extractor.get_job_history(days=30)
       assert len(jobs) == 1


拡張性 — 他 DWH への対応
===========================

Extractor Tierを差し替えるだけで、他のデータウェアハウスに対応できます。

.. code-block:: text

   extractor/
   ├── bigquery.py    ← Current implementation
   ├── snowflake.py   ← Future extension example
   └── redshift.py    ← Future extension example

Analyzer Tierと Reporter Tierは **変更不要** です。
