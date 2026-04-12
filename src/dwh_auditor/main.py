"""DWH-Auditor CLI エントリーポイント.

コマンド:
  dwh-auditor init     - カレントディレクトリに config.yaml を生成
  dwh-auditor analyze  - BigQuery の監査を実行してレポートを出力
"""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Annotated

import typer

from dwh_auditor.analyzer.runner import run_analysis
from dwh_auditor.config import load_config
from dwh_auditor.extractor.bigquery import BigQueryExtractor
from dwh_auditor.reporter.console import print_to_console
from dwh_auditor.reporter.json_out import generate_json_report
from dwh_auditor.reporter.markdown import generate_markdown_report

app = typer.Typer(
    name="dwh-auditor",
    help="🚀 DWH-Auditor: BigQuery のコスト最適化とガバナンス監査のための CLI ツール",
    add_completion=False,
    pretty_exceptions_show_locals=False,
)

# config_template.yaml のパス (パッケージルートからの相対パスを解決)
_TEMPLATE_PATH = Path(__file__).parent.parent.parent / "config_template.yaml"


@app.command()
def init(
    output: Annotated[
        str,
        typer.Option(
            "--output",
            "-o",
            help="生成する設定ファイルのパス (デフォルト: config.yaml)",
        ),
    ] = "config.yaml",
) -> None:
    """カレントディレクトリにデフォルトの config.yaml を生成します.

    既に config.yaml が存在する場合は上書きしません。
    """
    dest = Path(output)
    if dest.exists():
        typer.echo(
            f"⚠️  {output} は既に存在します。上書きする場合は手動で削除してください。",
            err=True,
        )
        raise typer.Exit(code=1)

    if not _TEMPLATE_PATH.exists():
        typer.echo(
            f"❌ テンプレートファイルが見つかりません: {_TEMPLATE_PATH}",
            err=True,
        )
        raise typer.Exit(code=1)

    shutil.copy(_TEMPLATE_PATH, dest)
    typer.echo(f"✅ {output} を生成しました。環境に合わせてしきい値などを調整してください。")


@app.command()
def analyze(
    project: Annotated[
        str,
        typer.Option("--project", "-p", help="分析対象(テーブルが存在する)の GCP プロジェクト ID"),
    ],
    job_projects: Annotated[
        str,
        typer.Option(
            "--job-projects",
            "-jp",
            help="クエリが実行されるプロジェクトのカンマ区切りリスト (未指定の場合は project と同じ)",
        ),
    ] = "",
    region: Annotated[
        str,
        typer.Option(
            "--region",
            "-r",
            help="BigQuery のリージョン (例: region-us, region-asia-northeast1)",
        ),
    ] = "region-us",
    days: Annotated[
        int,
        typer.Option("--days", "-d", help="過去何日分のジョブ履歴を分析するか"),
    ] = 30,
    config_path: Annotated[
        str,
        typer.Option("--config", "-c", help="設定ファイルのパス"),
    ] = "config.yaml",
    output: Annotated[
        str,
        typer.Option(
            "--output",
            "-o",
            help="出力形式: 'console', 'markdown', 'json'",
        ),
    ] = "console",
    report_path: Annotated[
        str,
        typer.Option("--report-path", help="Markdown レポートの出力先パス"),
    ] = "report.md",
) -> None:
    """BigQuery のメタデータを分析し、コスト削減のインサイトを抽出します."""
    is_json = output == "json"

    if not is_json:
        typer.echo(f"🔍 プロジェクト '{project}' ({region}) の過去 {days} 日間の監査を開始します...")

    # 1. 設定ファイルの読み込み
    config_file = Path(config_path)
    if not config_file.exists():
        if not is_json:
            typer.echo(
                f"⚠️  設定ファイル '{config_path}' が見つかりません。"
                " デフォルト設定で実行します。\n"
                "   `dwh-auditor init` でデフォルト設定ファイルを生成できます。",
                err=True,
            )
        from dwh_auditor.config import AppConfig

        config = AppConfig()
    else:
        try:
            config = load_config(config_path)
        except Exception as e:
            typer.echo(f"❌ 設定ファイルの読み込みに失敗しました: {e}", err=True)
            raise typer.Exit(code=1) from e

    # job_projects のパース
    jp_list = [p.strip() for p in job_projects.split(",")] if job_projects else [project]

    if not is_json:
        typer.echo(f"📡 BigQuery からメタデータを取得中... (Job Projects: {', '.join(jp_list)})")

    # 2. Extractor: BQ からデータ取得
    try:
        extractor = BigQueryExtractor(target_project_id=project, job_project_ids=jp_list, region=region)
        # 用途別に最適化されたクエリを発行する
        top_cost_jobs = extractor.get_top_cost_jobs(days=days, limit=config.thresholds.top_expensive_queries_limit)
        heavy_scan_jobs = extractor.get_heavy_scan_jobs(
            days=days, min_scanned_bytes=int(config.thresholds.ignore_full_scan_under_gb * (1024**3))
        )
        recurring_stats = extractor.get_recurring_cost_jobs(days=days)
        table_usages = extractor.get_table_usage_stats(days=days)
        tables = extractor.get_table_storage()
    except Exception as e:
        typer.echo(f"❌ BigQuery へのアクセスに失敗しました: {e}", err=True)
        raise typer.Exit(code=1) from e

    if not is_json:
        typer.echo("🔬 分析中...")

    # 3. Analyzer: 診断の実行
    result = run_analysis(
        top_cost_jobs=top_cost_jobs,
        heavy_scan_jobs=heavy_scan_jobs,
        recurring_stats=recurring_stats,
        table_usages=table_usages,
        tables=tables,
        config=config,
        analyzed_days=days,
        project_id=project,
    )

    # 4. Reporter: 結果の出力
    if output == "markdown":
        generate_markdown_report(result, filepath=report_path)
        typer.echo(f"📄 Markdown レポートを生成しました: {report_path}")
    elif output == "json":
        # jsonの場合は標準出力にjson文字だけを出力する
        print(generate_json_report(result))
    else:
        print_to_console(result)


def main() -> None:
    """CLIのエントリーポイント。直接実行時に使用。"""
    app()


if __name__ == "__main__":
    main()
