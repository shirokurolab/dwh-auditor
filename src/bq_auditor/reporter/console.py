"""コンソール出力層 (Rich を使ったリッチな CLI 出力)."""

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from bq_auditor.models.result import AuditResult

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
    _print_cost_table(result)
    _print_full_scan_table(result)
    _print_zombie_table(result)
    _print_footer()


def _print_header(result: AuditResult) -> None:
    """監査サマリーのヘッダーパネルを表示する."""
    summary = (
        f"[bold]プロジェクト:[/bold] {result.project_id}\n"
        f"[bold]分析期間:[/bold] 過去 {result.analyzed_days} 日間\n"
        f"[bold]分析ジョブ数:[/bold] {result.total_jobs_analyzed:,} 件\n"
        f"[bold]分析テーブル数:[/bold] {result.total_tables_analyzed:,} 件\n\n"
        f"[bold yellow]⚠  高コストクエリ:[/bold yellow] {len(result.top_expensive_queries)} 件\n"
        f"[bold red]🚨 フルスキャン:[/bold red] {len(result.full_scans)} 件\n"
        f"[bold magenta]🧟 ゾンビテーブル:[/bold magenta] {len(result.zombie_tables)} 件"
    )
    _console.print(
        Panel(
            summary,
            title="[bold cyan]🚀 BQ-Auditor 監査レポート[/bold cyan]",
            border_style="cyan",
        )
    )


def _print_cost_table(result: AuditResult) -> None:
    """高コストクエリのテーブルを表示する."""
    if not result.top_expensive_queries:
        _console.print("[green]✅ 高コストクエリは検出されませんでした。[/green]\n")
        return

    table = Table(
        title="💸 高コストクエリ Top",
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
        title="🚨 フルスキャン検知",
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


def _print_zombie_table(result: AuditResult) -> None:
    """ゾンビテーブル検知結果のテーブルを表示する."""
    if not result.zombie_tables:
        _console.print("[green]✅ ゾンビテーブルは検出されませんでした。[/green]\n")
        return

    table = Table(
        title="🧟 ゾンビテーブル",
        box=box.ROUNDED,
        border_style="magenta",
        show_lines=True,
    )
    table.add_column("テーブル (完全修飾名)", style="cyan", min_width=30)
    table.add_column("未使用日数", justify="right", style="magenta")
    table.add_column("サイズ (GB)", justify="right", style="dim")

    for insight in result.zombie_tables:
        table.add_row(
            insight.table.full_table_id,
            f"{insight.days_unused} 日以上",
            f"{insight.size_gb:.2f}",
        )

    _console.print(table)
    _console.print()


def _print_footer() -> None:
    """フッターのビジネス導線を表示する."""
    footer = Text()
    footer.append(
        "💼 これらの課題を解決するための専門的なサポートが必要ですか?\n",
        style="bold",
    )
    footer.append(
        "データモデルの再設計や dbt 移行支援については、お気軽にご相談ください。\n",
    )
    footer.append(
        "👉 https://github.com/your-org/bq-auditor",
        style="bold blue underline",
    )
    _console.print(Panel(footer, border_style="dim", title="[dim]Enterprise Support[/dim]"))
