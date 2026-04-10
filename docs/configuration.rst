####################################################################################################
設定ファイル (config.yaml) — コスト単価・しきい値の DWH 監査設定
####################################################################################################

dwh-auditor の各診断ルールは、プロジェクト固有の基準に合わせて
``config.yaml`` でカスタマイズできます。
「何を異常とみなすか」はビジネス要件によって異なるため、
すべての値をユーザーが上書きできる設計になっています。


設定ファイルの生成
==================

.. code-block:: bash

   dwh-auditor init

カレントディレクトリに ``config.yaml`` が生成されます。
既にファイルが存在する場合は上書きされません。

.. note::

   ``config.yaml`` は Git リポジトリに含めても問題ありません。
   ただし、機密情報（サービスアカウントキーなど）は **絶対に含めないでください。**


設定ファイルの全スキーマ
=========================

.. code-block:: yaml

   # dwh-auditor config.yaml

   pricing:
     # 1TB スキャンあたりのオンデマンド料金（USD）
     # BigQuery オンデマンド料金のデフォルト値: $6.25/TB
     tb_scan_usd: 6.25

   thresholds:
     # フルスキャン検知の除外ライン（GB）
     # この値以下のスキャンは警告から除外されます
     # 小規模なマスターテーブルのスキャンで警告疲れを防ぐための設定
     ignore_full_scan_under_gb: 1.0

     # 高コストクエリの報告件数上限
     top_expensive_queries_limit: 10

     # ゾンビテーブルとみなすまでの未参照日数
     zombie_table_days: 90

   # （将来の拡張用）dbt 連携設定
   dbt:
     enabled: false
     job_label_key: "dbt_model"


各設定値の詳細
==============

pricing セクション
------------------

``pricing.tb_scan_usd``
~~~~~~~~~~~~~~~~~~~~~~~

1TB スキャンあたりのオンデマンド料金（USD）です。
コスト推定の計算式は以下の通りです。

.. code-block:: text

   推定コスト (USD) = スキャン TB 数 × tb_scan_usd

.. list-table::
   :header-rows: 1

   * - キー
     - デフォルト値
     - 説明
   * - ``tb_scan_usd``
     - ``6.25``
     - BigQuery オンデマンドの標準料金に対応

.. tip::

   Editions（Flex Slots / Standard / Enterprise）を利用している場合、
   スロット時間課金モデルになります。
   この場合は ``tb_scan_usd: 0.0`` に設定し、コスト分析を参考値として使用してください。


thresholds セクション
---------------------

``thresholds.ignore_full_scan_under_gb``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

この GB 数以下のスキャンは **フルスキャン警告から除外** されます。

.. list-table::
   :header-rows: 1

   * - キー
     - デフォルト値
     - 推奨用途
   * - ``ignore_full_scan_under_gb``
     - ``1.0``
     - 小規模マスターテーブル（都道府県テーブルなど）のスキャンを無視する

``thresholds.top_expensive_queries_limit``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

高コストクエリの報告件数の上限です。

.. list-table::
   :header-rows: 1

   * - キー
     - デフォルト値
     - 説明
   * - ``top_expensive_queries_limit``
     - ``10``
     - コンソール・レポートに表示するクエリの最大件数

``thresholds.zombie_table_days``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

この日数以上、一度も ``SELECT`` で参照されていないテーブルを
**ゾンビテーブル** として报告します。

.. list-table::
   :header-rows: 1

   * - キー
     - デフォルト値
     - 説明
   * - ``zombie_table_days``
     - ``90``
     - 過去 90 日間の JOBS ビューにテーブルが現れなければゾンビ判定


dbt セクション（将来の拡張用）
-------------------------------

dbt が発行するクエリを BigQuery のジョブラベルで識別し、
dbt モデルごとのコスト集計を行う設定です。
現バージョンでは ``enabled: false`` のままにしてください。

.. list-table::
   :header-rows: 1
   :widths: 30 15 55

   * - キー
     - デフォルト値
     - 説明
   * - ``dbt.enabled``
     - ``false``
     - dbt 連携を有効にするか
   * - ``dbt.job_label_key``
     - ``"dbt_model"``
     - dbt モデルを識別するラベルキー名


Pydantic スキーマ
=================

設定ファイルは Python 側で Pydantic モデル :class:`dwh_auditor.config.AppConfig` に
パースされるため、不正な値（負の料金、0 件のしきい値など）は
起動時にバリデーションエラーとして検出されます。

.. code-block:: python

   from dwh_auditor.config import load_config

   config = load_config("config.yaml")
   print(config.pricing.tb_scan_usd)   # 6.25
   print(config.thresholds.zombie_table_days)  # 90

詳細は :doc:`api/config` を参照してください。
