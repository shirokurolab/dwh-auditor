####################################################################################################
dwh_auditor.models — DWH 監査用内部データモデル (Pydantic)
####################################################################################################

``dwh_auditor.models`` パッケージは、各層（Extractor → Analyzer → Reporter）が
データを受け渡す際の「型契約」を定義します。
``dict`` 型を直接受け渡すのではなく Pydantic モデルを使うことで、
静的型チェックとランタイムバリデーションの両方を実現します。

----

クエリジョブモデル (``models.job``)
=====================================

.. automodule:: dwh_auditor.models.job
   :members:
   :undoc-members:
   :show-inheritance:

----

テーブルストレージモデル (``models.table``)
============================================

.. automodule:: dwh_auditor.models.table
   :members:
   :undoc-members:
   :show-inheritance:

----

分析結果モデル (``models.result``)
====================================

.. automodule:: dwh_auditor.models.result
   :members:
   :undoc-members:
   :show-inheritance:
