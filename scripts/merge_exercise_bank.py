"""Merge draft JSONL files into the exercise bank source of truth."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend import config, exercise_bank, textbook  # noqa: E402


def _textbook_pointers() -> list[dict]:
    rows = []
    for item in textbook.load_exercises():
        rows.append({
            "exercise_id": f"textbook-{item['id']}",
            "source": "mit_calculus_textbook",
            "source_problem_id": item["id"],
            "stem": item["stem"],
            "solution": item.get("explanation", ""),
            "final_answer": item.get("final_answer", ""),
            "knowledge_points": [],
            "primary_section_id": item["section_id"],
            "related_section_ids": [],
            "designed_difficulty": item["difficulty"],
            "difficulty_reason": {},
            "cognitive_task": "",
            "source_form": "textbook_exercise",
            "license_ref": "data/textbook/mit-calculus/curated_exercises.json",
            "canonical_ref": item["id"],
            "normalized_stem": exercise_bank.normalize_stem(item["stem"]),
            "duplicate_of": "",
            "serve_as_reference": False,
        })
    return rows


def main() -> None:
    rows: list[dict] = []
    for path in sorted(config.EXERCISE_DRAFT_DIR.glob("*.jsonl")):
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                rows.append(json.loads(line))
    rows.extend(_textbook_pointers())
    kept = []
    rejected = []
    for row in rows:
        if row.get("source_form") == "textbook_exercise":
            kept.append(row)
            continue
        if row.get("designed_difficulty") not in exercise_bank.DIFFICULTIES:
            rejected.append(row.get("exercise_id"))
            continue
        if not row.get("primary_section_id"):
            row["serve_as_reference"] = False
        try:
            exercise_bank.validate_record(row)
        except ValueError as exc:
            rejected.append(f"{row.get('exercise_id')}: {exc}")
            continue
        kept.append(row)
    config.EXERCISE_BANK_FILE.parent.mkdir(parents=True, exist_ok=True)
    with config.EXERCISE_BANK_FILE.open("w", encoding="utf-8") as handle:
        for row in kept:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    exercise_bank.reset_cache()
    loaded = exercise_bank.load()
    print(json.dumps({
        "written": len(kept),
        "loaded": len(loaded),
        "rejected": rejected,
        "references": len(exercise_bank.filter_records()),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
