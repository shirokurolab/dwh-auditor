# 開発への貢献 (Contributing)

## 開発環境のセットアップ

本プロジェクトはパッケージマネージャーとして [uv](https://github.com/astral-sh/uv) を利用しています。

### 1. uv のインストール

まだ `uv` をインストールしていない場合は、以下のコマンドでインストールします。

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

_(Mac/Linuxの場合。Windows等は[公式ドキュメント](https://docs.astral.sh/uv/getting-started/installation/)をご参照ください)_

### 2. リポジトリのクローンと依存関係のインストール

```bash
git clone https://github.com/shirokurolab/dwh-auditor.git
cd dwh-auditor
uv sync --all-extras  # dev や docs などの追加パッケージも含めて .venv にインストールされます
```

### 3. ローカルでの実行

`uv run` コマンドを使用することで、作成された仮想環境上でCLIを実行できます。

```bash
# 設定ファイルの生成
uv run dwh-auditor init

# 実際の監査コマンドの実行例
uv run dwh-auditor analyze --project your-gcp-project-id --output console
```

### 4. 開発ツールの実行

フォーマット、Lint、型チェック、テストの実行方法は以下の通りです（`--all-extras` でインストール済みである必要があります）。

```bash
# フォーマット (Ruff)
uv run ruff format .
uv run ruff check --fix .

# 型チェック (Mypy)
uv run mypy src tests

# テスト (Pytest)
uv run pytest
```

---

## 開発フロー

### 1. 提案 (Proposal)

アクション: GitHubの Issues を作成する。

内容: バグ報告や新機能のアイデア（例：「Snowflake対応を追加したい」「新しいアンチパターン検知を追加したい」）を起票します。

ルール: いきなりコードを書き始めず、まずはIssueで「なぜその機能が必要か（Why）」を共有します。

### 2. 議論 (Discussion)

アクション: Issueのコメント欄でのディスカッション。

内容: メンテナと提案者で、仕様やアプローチについて議論します。

ルール: 複雑な機能の場合は、ここで内部データモデル（Pydantic）の変更点などをすり合わせ、「よし、この方針でいこう（Approved）」と合意形成を行います。

### 3. 実装 (Implementation)

アクション: リポジトリをForkし、ブランチを切ってコードを書く。

内容: uv を使ってローカル環境を構築し、実装を行います。

ルール:

コードフォーマットとLintは ruff check と ruff format をクリアすること。

型チェックは mypy をクリアすること。

新規ロジックには必ず pytest でテストコードを追加すること。

### 4. レビュー (Review)

アクション: GitHubで Pull Request (PR) を作成する。

内容: CI（GitHub Actions）が自動で走り、ruff, mypy, pytest が実行されます。CIがグリーン（成功）になったら、メンテナがコードレビューを行います。

ルール: レビューは「コードの綺麗さ」だけでなく、「アーキテクチャの原則（抽出層と分析層が混ざっていないか等）」を守れているかを確認します。

### 5. マージ (Merge)

アクション: メンテナがPRを main ブランチにマージする。

内容: マージ後、タグ付け（例: v0.2.4）を行うことで、GitHub Actions経由でPyPIへ自動リリースされ、世界中のユーザーが pip install (または uv pip install) できるようになります。
