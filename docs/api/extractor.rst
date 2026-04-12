#######################################################
dwh_auditor.extractor — BigQuery メタデータ抽出層
#######################################################

``dwh_auditor.extractor`` パッケージは、BigQuery の ``INFORMATION_SCHEMA`` から
メタデータを取得して Pydantic モデルに変換する **唯一の層** です。

.. warning::

   ``google.cloud.bigquery`` ライブラリの直接 import は
   このパッケージの ``bigquery.py`` のみに限定されています。
   Analyzer・Reporter・CLI からは **絶対にインポートしないでください。**
   この制約により、テスト時は ``BigQueryExtractor`` だけをモック化すれば
   他の全層をモックなしでテストできます。

テスト方法:

.. code-block:: python

   def test_get_job_history(mocker):
       # Only mock google.cloud.bigquery.Client
       mock_client = mocker.patch("dwh_auditor.extractor.bigquery.bq.Client")
       mock_client.return_value.query.return_value.result.return_value = [
           {"job_id": "j1", "user_email": "u@e.com", ...}
       ]
       extractor = BigQueryExtractor(project_id="my-project", region="region-us")
       jobs = extractor.get_job_history(days=30)
       assert len(jobs) == 1

----

.. automodule:: dwh_auditor.extractor.bigquery
   :members:
   :undoc-members:
   :show-inheritance:
