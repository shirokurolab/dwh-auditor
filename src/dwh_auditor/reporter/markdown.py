"""Markdown レポート生成層."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from dwh_auditor.models.result import AuditResult

_BYTES_PER_GB: float = 1024**3


def _format_cost(usd: float) -> str:
    """USD コストをフォーマットする."""
    return f"${usd:.4f}"


def _truncate(text: str, max_len: int = 80) -> str:
    """テキストを指定文字数で切り詰める."""
    return text[:max_len] + "..." if len(text) > max_len else text


def generate_markdown_report(result: AuditResult, filepath: str = "report.md") -> None:
    """AuditResult を Markdown 形式のレポートファイルとして出力する.

    CI/CD の Artifact として保存したり、社内 Wiki に貼り付けることを想定しています。
    末尾にビジネス導線を含みます。

    Args:
        result: Analyzer から受け取った監査結果
        filepath: 出力先ファイルパス (デフォルト: "report.md")
    """
    lines: list[str] = []
    generated_at = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    zombie_count = len(result.table_profiles)

    # ヘッダー
    lines += [
        "# 🚀 DWH-Auditor 監査レポート",
        "",
        f"> **生成日時:** {generated_at}  ",
        f"> **プロジェクト:** `{result.project_id}`  ",
        f"> **分析期間:** 過去 {result.analyzed_days} 日間  ",
        f"> **ジョブ数 (分析対象抽出):** {result.total_jobs_analyzed:,} 件  ",
        f"> **テーブル数:** {result.total_tables_analyzed:,} 件  ",
        "",
        "---",
        "",
    ]

    # サマリー
    lines += [
        "## 📊 サマリー",
        "",
        "| 指標 | 件数 |",
        "|------|------|",
        f"| 🚨 定常実行アラート | {len(result.recurring_expensive_queries)} 件 |",
        f"| 💸 アドホック高コストクエリ | {len(result.top_expensive_queries)} 件 |",
        f"| 🚨 フルスキャン検知 | {len(result.full_scans)} 件 |",
        f"| 🧟 ゾンビテーブル | {zombie_count} 件 |",
        "",
        "---",
        "",
    ]

    # 定常高コストクエリ
    lines += [
        "## 🚨 定常実行アラート (Recurring Jobs)",
        "",
        "> **インサイト:** バッチや dbt、ダッシュボードツールから定期的に発行されている赤字クエリの合算被害額です。",
        "",
    ]
    if result.recurring_expensive_queries:
        lines += [
            "| 順位 | 実行回数 | 合計コスト (USD) | スキャン (TB) | 最終実行日時 | クエリ |",
            "|------|--------|---------------|-------------|------------|-------|",
        ]
        for i, rec_insight in enumerate(result.recurring_expensive_queries, 1):
            dt_str = rec_insight.last_executed_at.strftime("%Y-%m-%d %H:%M UTC")
            query_snippet = _truncate(rec_insight.query_sample.replace("\n", " "), 50)
            lines.append(
                f"| {i} "
                f"| {rec_insight.execution_count} 回 "
                f"| **{_format_cost(rec_insight.total_estimated_usd)}** "
                f"| {rec_insight.total_scanned_tb:.4f} "
                f"| {dt_str} "
                f"| `{query_snippet}` |"
            )
    else:
        lines.append("✅ 定常実行の赤字クエリは検出されませんでした。")
    lines += ["", "---", ""]

    # 高コストクエリ
    lines += [
        "## 💸 アドホック高コストクエリ Top",
        "",
    ]
    if result.top_expensive_queries:
        lines += [
            "| 順位 | ユーザー | スキャン (TB) | 推定コスト (USD) | クエリ |",
            "|------|---------|-------------|---------------|-------|",
        ]
        for i, cost_insight in enumerate(result.top_expensive_queries, 1):
            query_snippet = _truncate(cost_insight.job.query.replace("\n", " "), 60)
            lines.append(
                f"| {i} "
                f"| `{cost_insight.job.user_email}` "
                f"| {cost_insight.scanned_tb:.4f} "
                f"| {_format_cost(cost_insight.estimated_cost_usd)} "
                f"| `{query_snippet}` |"
            )
    else:
        lines.append("✅ アドホックの高コストクエリは検出されませんでした。")
    lines += ["", "---", ""]

    # フルスキャン
    lines += [
        "## 🚨 フルスキャン検知",
        "",
        "> **インサイト:** パーティションテーブルの設計、またはクエリのフィルタリング見直しが必要です。",
        "",
    ]
    if result.full_scans:
        lines += [
            "| ユーザー | スキャン (GB) | クエリ |",
            "|---------|------------|-------|",
        ]
        for fs_insight in result.full_scans:
            query_snippet = _truncate(fs_insight.job.query.replace("\n", " "), 60)
            lines.append(f"| `{fs_insight.job.user_email}` | {fs_insight.scanned_gb:.2f} | `{query_snippet}` |")
    else:
        lines.append("✅ フルスキャンは検出されませんでした。")
    lines += ["", "---", ""]

    # ゾンビテーブル・利用状況
    lines += [
        "## 🧟 ゾンビテーブル (未使用/低利用) Top 100",
        "",
        "> **インサイト:** 誰からも使われていない（ゾンビ）テーブルは削除を検討してください。"
        "アクセスがある場合でも利用回数が少ない場合は整理対象となります。",
        "",
    ]
    if result.table_profiles:
        lines += [
            "| ステータス | テーブル | サイズ (GB) | アクセス回数 | トップユーザー | 最終アクセス |",
            "|-----------|---------|-----------|------------|--------------|------------|",
        ]
        for profile in result.table_profiles:
            dt_str = profile.last_accessed_at.strftime("%Y-%m-%d") if profile.last_accessed_at else "---"
            users_str = ", ".join(profile.top_users) if profile.top_users else "---"

            lines.append(
                f"| 🧟 ゾンビ "
                f"| `{profile.table.full_table_id}` "
                f"| {profile.size_gb:.2f} "
                f"| {profile.access_count_30d} "
                f"| `{users_str}` "
                f"| {dt_str} |"
            )
    else:
        lines.append("✅ 期間中のゾンビテーブルは見つかりませんでした。")
    lines += ["", "---", ""]

    lines += [
        "_Generated by [DWH-Auditor](https://github.com/shirokurolab/dwh-auditor)"
        " — Zero Data Access, Maximum Insight._",
    ]

    output_path = Path(filepath)
    output_path.write_text("\n".join(lines), encoding="utf-8")
