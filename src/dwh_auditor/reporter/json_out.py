"""JSON フォーマットの出力層."""

from dwh_auditor.models.result import AuditResult


def generate_json_report(result: AuditResult) -> str:
    """AuditResult を JSON 文字列に変換する.

    CI/CD ツール等での利用を想定し、標準出力にそのまま渡せる形式で出力する。
    """
    return result.model_dump_json(indent=2)
