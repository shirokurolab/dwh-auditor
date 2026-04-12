# 🚀 DWH-Auditor

[English](README.md) | [日本語](README.ja.md)

![PyPI version](https://img.shields.io/badge/pypi-v0.2.3-blue)
![Python Versions](https://img.shields.io/badge/python-3.9%20%7C%203.10%20%7C%203.11%20%7C%203.12-blue)
![License](https://img.shields.io/badge/license-MIT-green)
[![Documentation](https://img.shields.io/badge/docs-GitHub%20Pages-blue)](https://shirokurolab.github.io/dwh-auditor/)

**📚 Official Documentation:** [https://shirokurolab.github.io/dwh-auditor/](https://shirokurolab.github.io/dwh-auditor/)

**DWH-Auditor** is an open-source CLI tool that parses BigQuery metadata to instantly perform **cost optimization and data governance auditing to prevent runaway cloud costs**.

By visualizing exactly _who_ is executing heavy queries and _which_ tables are completely unused, it uncovers hidden financial waste and provides actionable insights.

<p align="center">
  <img src="https://raw.githubusercontent.com/shirokurolab/dwh-auditor/main/docs/assets/sample_output_v0.2.3.png" alt="DWH-Auditor Console Report Sample">
</p>

## 💡 Why DWH-Auditor?

While BigQuery is extremely powerful, its pay-as-you-go pricing model means that a single inefficient query or an abandoned, massive table can stealthily generate thousands of dollars in wasted costs every month.

DWH-Auditor analyzes your `INFORMATION_SCHEMA` seamlessly without any complex configurations, delivering a "health check" for your data infrastructure in seconds. **Because it never accesses your actual table data, it can be safely executed even in strict, highly secure enterprise environments.**

## ✨ Key Features

- 💸 **Identifying High-Cost Queries:** Aggregates billed bytes over the past N days and surfaces the Top 10 most expensive ad-hoc queries.
- 🔄 **Recurring Execution Alerts:** Detects dashboards or batch processes that are running expensive queries on a recurring schedule.
- 🚨 **Detecting Full Table Scans (Anti-patterns):** Warns you about inefficient queries, such as full table scans caused by missing partition filters.
- 🧟 **Identifying Zombie Tables:** Locates storage-heavy tables that haven't been queried for a long time, enabling swift storage cost reductions.
- 📊 **Multi-Format Reporting:** Integrates effortlessly into your CI/CD pipelines (e.g. GitHub Actions) to share daily audit reports in Markdown or JSON to your team.

## 🛠 Quickstart

### 1. Installation

```bash
pip install dwh-auditor
```

### 2. Initialization

```bash
dwh-auditor init
```

A `config.yaml` file will be generated in the current directory. Adjust the cost rates and warning thresholds as necessary to fit your environment.

### 3. Execution

```bash
# Example: Analyze the past 30 days for my-gcp-project
dwh-auditor analyze --project my-gcp-project --days 30 --output console
```

### 4. 🔐 Security (Zero Data Access)

DWH-Auditor strictly reads metadata (`INFORMATION_SCHEMA`) from BigQuery and **never** reads actual table records. It operates flawlessly under the principle of least privilege, requiring only `roles/bigquery.metadataViewer` and `roles/bigquery.resourceViewer`.

### 5. 💼 Enterprise Support & Data Infrastructure Consulting

DWH-Auditor is a powerful diagnostic tool for uncovering issues in your data platform. However, resolving severe structural issues—such as redesigning complex data models or refactoring massive query pipelines—can often be challenging to handle with internal resources alone.

If you are facing these challenges, the developer behind this tool (Data Engineer) offers direct support and professional consulting:

- "DWH-Auditor detected massive full table scans, but we don't know how to redesign partitions without breaking existing BI/ETL workflows."
- "We want to migrate a collection of legacy SQL scripts to modern data modeling using dbt."
- "We need to integrate this tool into our CI/CD pipeline to establish continuous data governance."

### 6. 👉 Contact Us

Feel free to reach out at shirokurolab.oss.tools@gmail.com. Initial consultations and high-level cost reduction assessments are provided completely free of charge.

### 7. 🤝 Contributing

We heartily welcome bug reports and Pull Requests! If you want to contribute, please check `CONTRIBUTING.md` for instructions on setting up your development environment.

### 8. 📜 License

## MIT License
