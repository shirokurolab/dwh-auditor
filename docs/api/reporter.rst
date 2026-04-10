####################################################################################################
dwh_auditor.reporter — 監査結果の出力・レポート生成層
####################################################################################################

``dwh_auditor.reporter`` パッケージは、Analyzer が生成した ``AuditResult`` オブジェクトを
ユーザーが参照しやすい形式（ターミナル / Markdown ファイル）に整形して出力します。

----

コンソール出力 (``reporter.console``)
=======================================

`Rich <https://rich.readthedocs.io/>`_ ライブラリを使って、
カラー付きのテーブル形式でターミナルに出力します。

使用例:

.. code-block:: python

   from dwh_auditor.reporter.console import print_to_console
   from dwh_auditor.models.result import AuditResult

   result: AuditResult = ...  # Analyzer から受け取る
   print_to_console(result)

.. automodule:: dwh_auditor.reporter.console
   :members:
   :undoc-members:
   :show-inheritance:

----

Markdown レポート生成 (``reporter.markdown``)
===============================================

``report.md`` を生成します。
CI/CD パイプラインの Artifact として保存したり、
社内 Wiki に自動投稿するのに適した形式です。

使用例:

.. code-block:: python

   from dwh_auditor.reporter.markdown import generate_markdown_report

   generate_markdown_report(result, filepath="audit_report.md")

.. automodule:: dwh_auditor.reporter.markdown
   :members:
   :undoc-members:
   :show-inheritance:
