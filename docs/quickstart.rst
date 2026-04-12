###########################################################
クイックスタート — dwh-auditor のインストールと初回監査実行
###########################################################

このページでは、**dwh-auditor** のインストールから BigQuery の初回監査実行までを
5 分以内に完了することを目標に解説します。


前提条件
========

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - 要件
     - 詳細
   * - Python バージョン
     - 3.9 以上
   * - GCP 認証
     - ``gcloud auth application-default login`` または ``GOOGLE_APPLICATION_CREDENTIALS``
   * - IAM 権限
     - ``roles/bigquery.metadataViewer`` / ``roles/bigquery.resourceViewer``


インストール
============

pip でのインストール
--------------------

.. code-block:: bash

   pip install dwh-auditor

インストール確認:

.. code-block:: bash

   dwh-auditor --help


uv を使ったインストール（推奨）
--------------------------------

`uv <https://docs.astral.sh/uv/>`_ を使うと、依存関係の解決が高速で再現性も高まります。

.. code-block:: bash

   uv add dwh-auditor


ソースからのインストール（開発者向け）
---------------------------------------

.. code-block:: bash

   git clone https://github.com/shirokurolab/dwh-auditor.git
   cd dwh-auditor

   # 仮想環境の作成と依存インストール
   uv venv && uv pip install -e ".[dev]"


GCP 認証の設定
==============

Application Default Credentials（推奨）
-----------------------------------------

ローカル開発では、Google Cloud SDK の ADC を使うのが最もシンプルです。

.. code-block:: bash

   gcloud auth application-default login

サービスアカウントキーを使う場合（CI/CD 環境向け）
---------------------------------------------------

.. code-block:: bash

   export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account.json"

.. warning::

   サービスアカウントキー（JSON ファイル）は **Git リポジトリに絶対コミットしないでください。**
   CI/CD 環境では GitHub Actions の Secrets またはWorkload Identity Federation を使用してください。


設定ファイルの生成（init コマンド）
====================================

監査を実行する前に、設定ファイルのテンプレートを生成します。

.. code-block:: bash

   dwh-auditor init

カレントディレクトリに ``config.yaml`` が生成されます。
内容はコスト単価やしきい値のカスタマイズに使います。
詳細は :doc:`configuration` を参照してください。


監査の実行（analyze コマンド）
================================

基本的な使い方
--------------

.. code-block:: bash

   # my-gcp-project の過去 30 日間をコンソール出力で分析
   dwh-auditor analyze --project my-gcp-project --days 30

東京リージョンを指定する場合
-----------------------------

.. code-block:: bash

   dwh-auditor analyze \
     --project my-gcp-project \
     --region region-asia-northeast1 \
     --days 30

Markdown レポートを生成する場合
--------------------------------

.. code-block:: bash

   dwh-auditor analyze \
     --project my-gcp-project \
     --days 30 \
     --output markdown \
     --report-path audit_report.md

.. tip::

   ``--output markdown`` を指定すると GitHub Actions の Artifact として保存し、チームに共有するのに便利です。

JSON を出力する場合
-------------------

.. code-block:: bash

   dwh-auditor analyze \
     --project my-gcp-project \
     --output json > result.json

複数のコンピューティングプロジェクトをまたいで分析する場合
-----------------------------------------------------------

ストレージ（データ用プロジェクト）とコンピューティング（クエリ実行用プロジェクト）が分かれている場合、
クエリが実行されるプロジェクトのリストをカンマ区切りで渡します。

.. code-block:: bash

   dwh-auditor analyze \
     --project my-storage-project \
     --job-projects my-compute-prj1,my-compute-prj2 \
     --days 30


コマンドリファレンス
====================

analyze コマンドのオプション一覧
---------------------------------

.. code-block:: text

   Usage: dwh-auditor analyze [OPTIONS]

   Options:
     -p, --project TEXT       分析対象の GCP プロジェクト ID  [required]
     -jp, --job-projects TEXT クエリが実行されるプロジェクトのカンマ区切りリスト
     -r, --region TEXT        BigQuery のリージョン           [default: region-us]
     -d, --days INTEGER       過去何日分を分析するか          [default: 30]
     -c, --config TEXT        設定ファイルのパス              [default: config.yaml]
     -o, --output TEXT        出力形式: console, markdown または json [default: console]
         --report-path TEXT   Markdown レポートの出力先       [default: report.md]
     --help                   ヘルプを表示


次のステップ
============

* :doc:`configuration` — ``config.yaml`` のしきい値やコスト単価をカスタマイズする
* :doc:`architecture` — dwh-auditor の内部設計と 3 層アーキテクチャを理解する
* :doc:`api/index` — Python API として組み込む方法を確認する
