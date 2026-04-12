####################################################################################################
dwh_auditor.analyzer — DWH コスト分析・セキュリティ診断ロジック
####################################################################################################

``dwh_auditor.analyzer`` パッケージは、Extractor から受け取った Pydantic モデルと
``config.yaml`` のしきい値を突き合わせ、診断を行う **純粋な Python ロジック** です。

.. note::

   このパッケージは ``google.cloud.bigquery`` を **一切インポートしません。**
   外部 API 通信が存在しないため、ユニットテストはミリ秒単位で完了します。
   ダミーの ``QueryJob`` / ``TableStorage`` オブジェクトを渡すだけでテストできます。

----

コスト分析 (``analyzer.cost``)
================================

.. automodule:: dwh_auditor.analyzer.cost
   :members:
   :undoc-members:
   :show-inheritance:

----

定常コスト分析 (``analyzer.recurring``)
=========================================

.. automodule:: dwh_auditor.analyzer.recurring
   :members:
   :undoc-members:
   :show-inheritance:

----

フルスキャン検知 (``analyzer.scan``)
======================================

.. automodule:: dwh_auditor.analyzer.scan
   :members:
   :undoc-members:
   :show-inheritance:

----

ゾンビテーブル検知 (``analyzer.zombie``)
=========================================

.. automodule:: dwh_auditor.analyzer.zombie
   :members:
   :undoc-members:
   :show-inheritance:

----

分析ランナー (``analyzer.runner``)
====================================

.. automodule:: dwh_auditor.analyzer.runner
   :members:
   :undoc-members:
   :show-inheritance:
