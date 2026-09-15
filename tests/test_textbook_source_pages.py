"""Regression checks for independent illustrations (whole-page UI removed)."""
import json
from pathlib import Path
from backend import rag


def test_missing_figure_is_reported(tmp_path, monkeypatch):
    monkeypatch.setattr(rag.config, "TEXTBOOK_ASSETS_DIR", tmp_path)
    monkeypatch.setattr(rag, "_figures", lambda: {"fig-1-2": {"path": "parsed/figure.png", "caption": "Fig. 1.2 Constant velocity"}})
    assert rag._figure_payload("fig-1-2", 52)["available"] is False
    (tmp_path / "figure.png").write_bytes(b"fixture")
    assert rag._figure_payload("fig-1-2", 52)["available"] is True


def test_reviewed_associations_do_not_include_unrelated_same_page_figure():
    root = Path(__file__).resolve().parents[1] / "data/textbook/mit-calculus"
    rows = json.loads((root / "verified_content.json").read_text(encoding="utf-8"))
    block = next(row for row in rows if row["id"] == "mit-1-3-rule-constant-acceleration")
    assert block["figure_ids"] == ["fig-1-13"]
    recipes = json.loads((root / "figure_crops.json").read_text(encoding="utf-8"))
    for row in rows:
        for figure_id in row.get("figure_ids", []):
            assert figure_id in recipes
