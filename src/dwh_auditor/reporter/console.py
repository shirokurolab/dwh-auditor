"""コンソール出力層 (Rich を使ったリッチな CLI 出力)."""

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from dwh_auditor.models.result import AuditResult

_console = Console()

_BYTES_PER_GB: float = 1024**3


def _format_cost(usd: float) -> str:
    """USD コストをフォーマットする."""
    return f"${usd:.4f}"


def _truncate(text: str, max_len: int = 60) -> str:
    """テキストを指定文字数で切り詰める."""
    return text[:max_len] + "..." if len(text) > max_len else text


def print_to_console(result: AuditResult) -> None:
    """AuditResult をターミナルにリッチ表示する.

    Args:
        result: Analyzer から受け取った監査結果
    """
    _print_header(result)
    _print_recurring_cost_table(result)
    _print_cost_table(result)
    _print_full_scan_table(result)
    _print_table_profile_table(result)


def _print_header(result: AuditResult) -> None:
    """監査サマリーのヘッダーパネルを表示する."""
    zombie_count = len(result.table_profiles)
    
    summary = (
        f"[bold]プロジェクト:[/bold] {result.project_id}\n"
        f"[bold]分析期間:[/bold] 過去 {result.analyzed_days} 日間\n"
        f"[bold]分析ジョブ数(取得済):[/bold] {result.total_jobs_analyzed:,} 件\n"
        f"[bold]分析テーブル数:[/bold] {result.total_tables_analyzed:,} 件\n\n"
        f"[bold yellow]⚠  定常実行の高コストクエリ:[/bold yellow] {len(result.recurring_expensive_queries)} 件\n"
        f"[bold yellow]⚠  アドホック高コストクエリ:[/bold yellow] {len(result.top_expensive_queries)} 件\n"
        f"[bold red]🚨 フルスキャン:[/bold red] {len(result.full_scans)} 件\n"
        f"[bold magenta]🧟 ゾンビテーブル:[/bold magenta] {zombie_count} 件"
    )
    _console.print(
        Panel(
            summary,
            title="[bold cyan]🚀 DWH-Auditor 監査レポート[/bold cyan]",
            border_style="cyan",
        )
    )

def _print_recurring_cost_table(result: AuditResult) -> None:
    """定常実行されている高コストクエリを表示する."""
    if not result.recurring_expensive_queries:
        _console.print("[green]✅ 定常実行の赤字クエリは検出されませんでした。[/green]\n")
        return

    table = Table(
        title="🚨 定常実行アラート: 最もコストを消費している定期システムジョブ Top",
        box=box.ROUNDED,
        border_style="red",
        show_lines=True,
    )
    table.add_column("順位", style="bold", justify="right", width=4)
    table.add_column("実行回数", style="cyan", justify="right")
    table.add_column("合計コスト (USD)", justify="right", style="bold red")
    table.add_column("スキャン (TB)", justify="right", style="yellow")
    table.add_column("クエリ (先頭)", style="dim", min_width=30)
    table.add_column("最終実行日時", style="dim", min_width=20)

    for i, insight in enumerate(result.recurring_expensive_queries, 1):
        dt_str = insight.last_executed_at.strftime("%Y-%m-%d %H:%M:%S UTC")
        table.add_row(
            str(i),
            f"{insight.execution_count} 回",
            _format_cost(insight.total_estimated_usd),
            f"{insight.total_scanned_tb:.4f}",
            _truncate(insight.query_sample),
            dt_str,
        )

    _console.print(table)
    _console.print()

def _print_cost_table(result: AuditResult) -> None:
    """高コストクエリのテーブルを表示する."""
    if not result.top_expensive_queries:
        _console.print("[green]✅ (アドホック)高コストクエリは検出されませんでした。[/green]\n")
        return

    table = Table(
        title="💸 アドホック高コストクエリ Top",
        box=box.ROUNDED,
        border_style="yellow",
        show_lines=True,
    )
    table.add_column("順位", style="bold", justify="right", width=4)
    table.add_column("ユーザー", style="cyan", min_width=20)
    table.add_column("スキャン (TB)", justify="right", style="yellow")
    table.add_column("推定コスト (USD)", justify="right", style="bold yellow")
    table.add_column("クエリ (先頭)", style="dim", min_width=30)

    for i, insight in enumerate(result.top_expensive_queries, 1):
        table.add_row(
            str(i),
            insight.job.user_email,
            f"{insight.scanned_tb:.4f}",
            _format_cost(insight.estimated_cost_usd),
            _truncate(insight.job.query),
        )

    _console.print(table)
    _console.print()


def _print_full_scan_table(result: AuditResult) -> None:
    """フルスキャン検知結果のテーブルを表示する."""
    if not result.full_scans:
        _console.print("[green]✅ フルスキャンは検出されませんでした。[/green]\n")
        return

    table = Table(
        title="🚨 フルスキャン検知 (テーブルサイズ超過)",
        box=box.ROUNDED,
        border_style="red",
        show_lines=True,
    )
    table.add_column("ユーザー", style="cyan", min_width=20)
    table.add_column("スキャン (GB)", justify="right", style="red")
    table.add_column("クエリ (先頭)", style="dim", min_width=40)

    for insight in result.full_scans:
        table.add_row(
            insight.job.user_email,
            f"{insight.scanned_gb:.2f}",
            _truncate(insight.job.query),
        )

    _console.print(table)
    _console.print()


def _print_table_profile_table(result: AuditResult) -> None:
    """テーブル利用状況・ゾンビテーブル検知のテーブルを表示する."""
    if not result.table_profiles:
        _console.print("[green]✅ ゾンビテーブルは検出されませんでした。[/green]\n")
        return

    table = Table(
        title="🧟 ゾンビテーブル (未使用/低利用) Top 100",
        box=box.ROUNDED,
        border_style="magenta",
        show_lines=True,
    )
    table.add_column("ステータス", style="bold", justify="center")
    table.add_column("テーブル (完全修飾名)", style="cyan", min_width=30)
    table.add_column("サイズ (GB)", justify="right", style="dim")
    table.add_column("利用回数(期間内)", justify="right", style="green")
    table.add_column("トップユーザー", style="blue")
    table.add_column("最終アクセス", style="dim")

    for profile in result.table_profiles:
        dt_str = profile.last_accessed_at.strftime("%Y-%m-%d") if profile.last_accessed_at else "---"
        users_str = ", ".join(profile.top_users) if profile.top_users else "---"

        table.add_row(
            "🧟 ゾンビ",
            profile.table.full_table_id,
            f"{profile.size_gb:.2f}",
            str(profile.access_count_30d),
            _truncate(users_str, 20),
            dt_str,
        )

    _console.print(table)
    _console.print()
