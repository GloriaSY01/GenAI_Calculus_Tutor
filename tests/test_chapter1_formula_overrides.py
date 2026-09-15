import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_every_chapter_one_formula_has_a_latex_override():
    textbook = ROOT / "data/textbook/mit-calculus"
    rows = json.loads((textbook / "verified_content.json").read_text(encoding="utf-8"))
    overrides = json.loads((textbook / "formula_overrides.json").read_text(encoding="utf-8"))
    chapter_one = [row for row in rows if row["section_id"].startswith("mit-1-")]
    assert len(overrides) == len(chapter_one)
    for row in chapter_one:
        formulas = overrides[row["id"]]
        assert len(formulas) == len(row["formulas"])
        assert all(value.startswith("\\displaystyle ") for value in formulas)
        assert all("\\" in value for value in formulas)
