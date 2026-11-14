from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_case_pages_use_root_relative_assets_before_static_rewrite() -> None:
    source = (ROOT / "portal" / "app.py").read_text(encoding="utf-8")
    exporter = (ROOT / "scripts" / "export_static.py").read_text(encoding="utf-8")
    assert 'src="/static/analytics.js"' in source
    assert "url('/static/thumbs/{slug}.jpg')" in source
    assert "src=\"/static/\', \'src=\"static/" in exporter
    assert "url('/static/\", \"url('static/" in exporter


def test_methods_tables_are_horizontally_scrollable() -> None:
    source = (ROOT / "portal" / "science.html").read_text(encoding="utf-8")
    assert ".table-wrap{overflow-x:auto" in source
    assert source.count('<div class="table-wrap">') == 2
    assert source.count("</table></div>") == 2
