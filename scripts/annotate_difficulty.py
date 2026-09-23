"""Annotate designed difficulty from difficulty_rubric.json."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend import config, exercise_bank, llm  # noqa: E402

BATCH = 5
TASKS = {
    "routine_calculation",
    "conceptual_understanding",
    "strategy_selection",
    "error_diagnosis",
    "graphical_interpretation",
    "modelling",
    "multi_step_reasoning",
}
LEVELS = {"easy", "medium", "hard"}
REASON_KEYS = (
    "knowledge_integration",
    "strategy_selection",
    "reasoning_process",
    "transfer_interpretation",
)


def _read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def _annotate(rows: list[dict]) -> dict[str, dict]:
    rubric = exercise_bank.rubric_prompt()
    payload = [
        {
            "exercise_id": row["exercise_id"],
            "stem": row["stem"][:800],
            "solution": (row.get("solution") or "")[:500],
        }
        for row in rows
    ]
    prompt = (
        f"{rubric}\n\n"
        "Assign an initial designed difficulty to each exercise. "
        "This is cognitive difficulty, not a student-accuracy score. "
        "MATH Taxonomy groups are not Easy/Medium/Hard. "
        "Hard must not mainly result from longer arithmetic, bigger numbers, "
        "extra algebra, many sub-parts, or knowledge outside the current section. "
        "difficulty_reason must have exactly these keys: "
        + ", ".join(REASON_KEYS)
        + ". Each value must be a short explanatory phrase such as "
        "'two related ideas' or 'method is given'. Do not use only the words "
        "easy, medium, or hard. cognitive_task must be one of: "
        + ", ".join(sorted(TASKS))
        + ". designed_difficulty must be easy, medium, or hard.\n"
        "Return JSON {\"items\": [{\"exercise_id\", \"designed_difficulty\", "
        "\"difficulty_reason\", \"cognitive_task\"}]}.\n\n"
        + json.dumps(payload, ensure_ascii=False)
    )
    data = llm.chat_to_json(
        [
            {"role": "system", "content": "You output only valid JSON."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.1,
        max_tokens=2200,
    )
    return {item["exercise_id"]: item for item in data.get("items", []) if item.get("exercise_id")}


def _valid(item: dict) -> bool:
    reason = item.get("difficulty_reason") or {}
    phrases = [str(reason.get(key) or "").strip() for key in REASON_KEYS]
    explanatory = all(phrase.lower() not in LEVELS and len(phrase) >= 8 for phrase in phrases)
    return (
        item.get("designed_difficulty") in LEVELS
        and item.get("cognitive_task") in TASKS
        and explanatory
    )


def annotate_rows(rows: list[dict]) -> list[dict]:
    pending = [row for row in rows if row.get("designed_difficulty") not in LEVELS]
    for start in range(0, len(pending), BATCH):
        batch = pending[start : start + BATCH]
        chosen = _annotate(batch)
        for row in batch:
            item = chosen.get(row["exercise_id"]) or {}
            if not _valid(item):
                continue
            row["designed_difficulty"] = item["designed_difficulty"]
            row["difficulty_reason"] = {key: item["difficulty_reason"][key] for key in REASON_KEYS}
            row["cognitive_task"] = item["cognitive_task"]
        print(f"annotated {min(start + BATCH, len(pending))}/{len(pending)}")
    return rows


def _consistency_sample(rows: list[dict]) -> None:
    sample = [row for row in rows if row.get("designed_difficulty") in LEVELS][:3]
    if not sample:
        return
    second = _annotate(sample)
    report = []
    for row in sample:
        again = (second.get(row["exercise_id"]) or {}).get("designed_difficulty")
        report.append({
            "exercise_id": row["exercise_id"],
            "first": row["designed_difficulty"],
            "second": again,
            "same": again == row["designed_difficulty"],
        })
    path = config.EXERCISE_DRAFT_DIR / "difficulty_consistency.json"
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"consistency": report}, ensure_ascii=False))


def main() -> None:
    paths = list(config.EXERCISE_DRAFT_DIR.glob("*.jsonl"))
    if not paths:
        raise SystemExit("no draft jsonl files")
    combined: list[dict] = []
    for path in paths:
        rows = annotate_rows(_read_jsonl(path))
        _write_jsonl(path, rows)
        missing = [row["exercise_id"] for row in rows if row.get("designed_difficulty") not in LEVELS]
        print(json.dumps({"file": path.name, "rows": len(rows), "missing": missing[:10], "missing_count": len(missing)}))
        combined.extend(rows)
    _consistency_sample(combined)


if __name__ == "__main__":
    main()
