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

   # Create virtual environment and install dependencies
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

   # Analyze my-gcp-project for the past 30 days and output to console
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

   ``--output markdown`` を指定すると ``report.md``（または ``--report-path`` で指定したファイル）が
   生成されます。GitHub Actions の Artifact として保存し、チームに共有するのに便利です。


コマンドリファレンス
====================

analyze コマンドのオプション一覧
---------------------------------

.. code-block:: text

   Usage: dwh-auditor analyze [OPTIONS]

   Options:
     -p, --project TEXT       Target GCP project ID           [required]
     -r, --region TEXT        BigQuery Region                 [default: region-us]
     -d, --days INTEGER       Number of past days to analyze  [default: 30]
     -c, --config TEXT        Configuration file path         [default: config.yaml]
     -o, --output TEXT        Output format: console/markdown [default: console]
         --report-path TEXT   Markdown report output path     [default: report.md]
     --help                   Show this message and exit.


次のステップ
============

* :doc:`configuration` — ``config.yaml`` のしきい値やコスト単価をカスタマイズする
* :doc:`architecture` — dwh-auditor の内部設計と 3 層アーキテクチャを理解する
* :doc:`api/index` — Python API として組み込む方法を確認する
