"""BQ-Auditor CLI エントリーポイント.

コマンド:
  bq-auditor init     - カレントディレクトリに config.yaml を生成
  bq-auditor analyze  - BigQuery の監査を実行してレポートを出力
"""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Annotated

import typer

from bq_auditor.analyzer.runner import run_analysis
from bq_auditor.config import load_config
from bq_auditor.extractor.bigquery import BigQueryExtractor
from bq_auditor.reporter.console import print_to_console
from bq_auditor.reporter.markdown import generate_markdown_report

app = typer.Typer(
    name="bq-auditor",
    help="🚀 BQ-Auditor: BigQuery のコスト最適化とガバナンス監査のための CLI ツール",
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

    # パッケージインストール後は config_template.yaml が同梱されていない場合があるため
    # importlib.resources で取得する方法も将来的に検討する
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
        typer.Option("--project", "-p", help="分析対象の GCP プロジェクト ID"),
    ],
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
            help="出力形式: 'console' または 'markdown'",
        ),
    ] = "console",
    report_path: Annotated[
        str,
        typer.Option("--report-path", help="Markdown レポートの出力先パス"),
    ] = "report.md",
) -> None:
    """BigQuery のメタデータを分析し、コスト削減のインサイトを抽出します.

    使用例:
        bq-auditor analyze --project my-gcp-project --days 30 --output console
        bq-auditor analyze --project my-gcp-project --region region-asia-northeast1 --output markdown
    """
    typer.echo(f"🔍 プロジェクト '{project}' ({region}) の過去 {days} 日間の監査を開始します...")

    # 1. 設定ファイルの読み込み
    config_file = Path(config_path)
    if not config_file.exists():
        typer.echo(
            f"⚠️  設定ファイル '{config_path}' が見つかりません。"
            " デフォルト設定で実行します。\n"
            "   `bq-auditor init` でデフォルト設定ファイルを生成できます。",
            err=True,
        )
        from bq_auditor.config import AppConfig

        config = AppConfig()
    else:
        try:
            config = load_config(config_path)
        except Exception as e:
            typer.echo(f"❌ 設定ファイルの読み込みに失敗しました: {e}", err=True)
            raise typer.Exit(code=1) from e

    # 2. Extractor: BQ からデータ取得
    typer.echo("📡 BigQuery からメタデータを取得中...")
    try:
        extractor = BigQueryExtractor(project_id=project, region=region)
        jobs = extractor.get_job_history(days=days)
        tables = extractor.get_table_storage()
    except Exception as e:
        typer.echo(f"❌ BigQuery へのアクセスに失敗しました: {e}", err=True)
        typer.echo(
            "  認証情報を確認してください: "
            "GOOGLE_APPLICATION_CREDENTIALS または `gcloud auth application-default login`",
            err=True,
        )
        raise typer.Exit(code=1) from e

    typer.echo(f"✅ 取得完了: ジョブ {len(jobs):,} 件 / テーブル {len(tables):,} 件")

    # 3. Analyzer: 診断の実行
    typer.echo("🔬 分析中...")
    result = run_analysis(
        jobs=jobs,
        tables=tables,
        config=config,
        analyzed_days=days,
        project_id=project,
    )

    # 4. Reporter: 結果の出力
    if output == "markdown":
        generate_markdown_report(result, filepath=report_path)
        typer.echo(f"📄 Markdown レポートを生成しました: {report_path}")
    else:
        print_to_console(result)


def main() -> None:
    """CLIのエントリーポイント。直接実行時に使用。"""
    app()


if __name__ == "__main__":
    main()
