"""generate_json_report 関数のテスト."""

from __future__ import annotations

import json

from dwh_auditor.models.result import AuditResult
from dwh_auditor.reporter.json_out import generate_json_report


def test_generate_json_report() -> None:
    """AuditResult が JSON 形式の文字列としてダンプされること."""
    result = AuditResult(
        analyzed_days=30,
        project_id="test-prj",
        total_jobs_analyzed=100,
        total_tables_analyzed=50,
        top_expensive_queries=[],
        recurring_expensive_queries=[],
        full_scans=[],
        table_profiles=[],
    )

    json_str = generate_json_report(result)

    # JSON としてパースできること
    parsed = json.loads(json_str)

    assert parsed["project_id"] == "test-prj"
    assert parsed["analyzed_days"] == 30
    assert parsed["total_jobs_analyzed"] == 100
    assert parsed["total_tables_analyzed"] == 50
    assert parsed["top_expensive_queries"] == []
