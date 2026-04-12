"""Sphinx configuration for dwh-auditor documentation."""

from __future__ import annotations

import os
import sys
from pathlib import Path

# src/ を sys.path に追加して autodoc が dwh_auditor を import できるようにする
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# ---------------------------------------------------------------------------
# Project information
# ---------------------------------------------------------------------------
project = "dwh-auditor"
copyright = "2024, dwh-auditor Contributors"
author = "dwh-auditor Contributors"

# パッケージから動的にバージョンを取得
try:
    from dwh_auditor import __version__ as release
except ImportError:
    release = "0.1.0"

version = release

# ---------------------------------------------------------------------------
# i18n (Internationalization)
# ---------------------------------------------------------------------------
language = "ja"
locale_dirs = ["locale/"]
gettext_compact = False

# ---------------------------------------------------------------------------
# General configuration
# ---------------------------------------------------------------------------
extensions = [
    "sphinx.ext.autodoc",  # docstring から API リファレンスを自動生成
    "sphinx.ext.napoleon",  # Google / NumPy スタイルの docstring をサポート
    "sphinx.ext.viewcode",  # ソースコードへのリンクを追加
    "sphinx.ext.intersphinx",  # 外部ドキュメント (Python 公式等) へのリンク
    "sphinx_copybutton",  # コードブロックにコピーボタンを追加
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

# ---------------------------------------------------------------------------
# Autodoc settings
# ---------------------------------------------------------------------------
autodoc_default_options = {
    "members": True,
    "member-order": "bysource",
    "special-members": "__init__",
    "undoc-members": True,
    "exclude-members": "__weakref__",
}
autodoc_typehints = "description"
autodoc_typehints_format = "short"

# ---------------------------------------------------------------------------
# Napoleon settings (Google-style docstrings)
# ---------------------------------------------------------------------------
napoleon_google_docstring = True
napoleon_numpy_docstring = False
napoleon_include_init_with_doc = True
napoleon_use_admonition_for_examples = True

# ---------------------------------------------------------------------------
# Intersphinx mapping
# ---------------------------------------------------------------------------
intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "pydantic": ("https://docs.pydantic.dev/latest", None),
}

# ---------------------------------------------------------------------------
# HTML output (Furo theme)
# ---------------------------------------------------------------------------
html_theme = "furo"
html_static_path = ["_static"]
html_title = "dwh-auditor"
html_favicon = None

html_theme_options = {
    "sidebar_hide_name": False,
    "navigation_with_keys": True,
    "top_of_page_button": "edit",
    "source_repository": "https://github.com/shirokurolab/dwh-auditor",
    "source_branch": "main",
    "source_directory": "docs/",
    "footer_icons": [
        {
            "name": "GitHub",
            "url": "https://github.com/shirokurolab/dwh-auditor",
            "html": """
                <svg stroke="currentColor" fill="currentColor" stroke-width="0"
                     viewBox="0 0 16 16" height="1em" width="1em">
                  <path fill-rule="evenodd"
                    d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38
                       0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13
                       -.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66
                       .07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15
                       -.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27
                       .68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12
                       .51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48
                       0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0 0 16 8
                       c0-4.42-3.58-8-8-8z"></path>
                </svg>
            """,
            "class": "",
        },
    ],
}

# コードブロックのコピーボタン設定
copybutton_prompt_text = r"\\$ |>>> |\\.\\.\\. "
copybutton_prompt_is_regexp = True

# サイドバーへの言語スイッチャー挿入
html_sidebars = {
    "**": [
        "sidebar/scroll-start.html",
        "sidebar/brand.html",
        "sidebar/language.html",
        "sidebar/search.html",
        "sidebar/navigation.html",
        "sidebar/ethical-ads.html",
        "sidebar/scroll-end.html",
    ]
}

# ---------------------------------------------------------------------------
# Google Analytics 4
# ---------------------------------------------------------------------------
ga_id = os.environ.get("GA_ID")
if ga_id:
    html_js_files = [
        (f"https://www.googletagmanager.com/gtag/js?id={ga_id}", {"async": "async"}),
        (
            None,
            {
                "body": f"""
            window.dataLayer = window.dataLayer || [];
            function gtag(){{dataLayer.push(arguments);}}
            gtag('js', new Date());
            gtag('config', '{ga_id}');
        """
            },
        ),
    ]
