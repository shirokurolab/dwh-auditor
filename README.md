# 🚀 DWH-Auditor

![PyPI version](https://img.shields.io/badge/pypi-v0.1.0-blue)
![Python Versions](https://img.shields.io/badge/python-3.9%20%7C%203.10%20%7C%203.11-blue)
![License](https://img.shields.io/badge/license-MIT-green)
[![Documentation](https://img.shields.io/badge/docs-GitHub%20Pages-blue)](https://shirokurolab.github.io/dwh-auditor/)

**📚 公式ドキュメント:** [https://shirokurolab.github.io/dwh-auditor/](https://shirokurolab.github.io/dwh-auditor/)

**DWH-Auditor** は、BigQueryのメタデータを分析し、**「クラウド破産」を防ぐためのコスト最適化とデータガバナンス監査**を瞬時に行うオープンソースのCLIツールです。

「誰がどんな重いクエリを投げているのか」「どのテーブルが使われていないのか」を可視化し、具体的なアクション（インサイト）を提示します。

<p align="center">
  <img src="https://raw.githubusercontent.com/shirokurolab/dwh-auditor/main/docs/assets/sample_output.png" alt="DWH-Auditor Console Report Sample">
</p>

## 💡 なぜ DWH-Auditor なのか？

BigQueryは非常に強力ですが、従量課金の性質上、たった一つの非効率なクエリや、放置された不要なテーブルが毎月数万円〜数百万円の無駄なコストを生み出すことがあります。

DWH-Auditorは、複雑な設定なしに `INFORMATION_SCHEMA` を解析し、あなたのデータ基盤の「健康診断」を数秒で完了させます。**実際のテーブルデータには一切アクセスしないため、セキュリティの厳しい環境でも安全に実行できます。**

## ✨ 主な機能

- 💸 **高コストクエリの特定:** 過去N日間の課金バイト数を集計し、コストの元凶となっているクエリTop10をリストアップします。
- 🚨 **フルスキャン（アンチパターン）検知:** パーティション指定漏れなど、非効率なフルスキャンクエリを警告します。
- 🧟 **ゾンビテーブルの発見:** 長期間誰からも参照されていないテーブルを特定し、ストレージコストの削減を促します。
- 📊 **Markdownレポート出力:** CI/CD（GitHub Actions等）に組み込み、チーム全体に日次で監査レポートを共有できます。

## 🛠 クイックスタート

### 1. インストール

```bash
pip install dwh-auditor
```

### 2. 初期設定

```bash
dwh-auditor init
```

カレントディレクトリに config.yaml が生成されます。必要に応じてコスト単価やしきい値を調整してください。

### 3. 監査の実行

```bash
# 例: my-gcp-project の過去30日間を分析
dwh-auditor analyze --project my-gcp-project --days 30 --output console
```

### 4. 🔐 セキュリティについて (Zero Data Access)

DWH-Auditor は、BigQueryのメタデータ（INFORMATION_SCHEMA）のみを読み取ります。ユーザーの実際のテーブルデータ（レコードの中身）を読み取ることは一切ありません。 必要なIAM権限は最小限（roles/bigquery.metadataViewer, roles/bigquery.resourceViewer）で動作します。

### 5. 💼 エンタープライズサポート / データ基盤コンサルティング

DWH-Auditor は、データ基盤の「課題を発見する」ための強力な健康診断ツールです。しかし、発見された重症な課題（複雑なデータモデルの再設計や、大規模なクエリのリファクタリング）を自社リソースだけで解決するのが難しいケースも少なくありません。

もし以下のようなお悩みがございましたら、本ツールの開発者（データエンジニア）による直接の支援・コンサルティングをご提供可能です。

「DWH-Auditorで大量のフルスキャンが検知されたが、既存のBIやETLを壊さずにどうパーティション設計を直せばいいか分からない」

「レガシーなSQL群を、dbtを用いたモダンなデータモデリングに移行したい」

「本ツールを自社のCI/CDパイプラインに組み込み、継続的なデータガバナンス体制を構築したい」

### 6. 👉 ご相談・お問い合わせ:

shirokurolab.oss.tools@gmail.com までお気軽にご連絡ください。初回ヒアリング・コスト削減ポテンシャルの簡易アセスメントは無料で承ります。

### 7. 🤝 貢献について (Contributing)

バグ報告、機能追加のPull Requestは大歓迎です！開発環境のセットアップ方法については CONTRIBUTING.md をご覧ください。

### 8. 📜 ライセンス

## MIT License
