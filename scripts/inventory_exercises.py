"""Inventory textbook examples, curated exercises, and live Chroma stems.

Writes data/exercises/textbook_stems.jsonl for duplicate checks. Does not
rebuild the textbook index.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend import config, rag, textbook  # noqa: E402


def _row(**fields) -> dict:
    return fields


def main() -> None:
    rows: list[dict] = []
    verified = textbook.load_verified_content()
    example_count = 0
    for item in verified:
        if item.get("content_type") != "example":
            continue
        example_count += 1
        rows.append(_row(
            origin="verified_content",
            chunk_id=item.get("id"),
            section_id=item.get("section_id"),
            content_type="example",
            text=(item.get("text") or "")[:2000],
        ))

    curated = textbook.load_exercises()
    for item in curated:
        rows.append(_row(
            origin="curated_exercise",
            chunk_id=item.get("id"),
            section_id=item.get("section_id"),
            content_type="exercise",
            difficulty=item.get("difficulty"),
            question_type=item.get("type"),
            text=item.get("stem") or "",
        ))

    chroma_exercise = 0
    chroma_unrated = 0
    chroma_example = 0
    try:
        collection = rag._collection()
        batch = collection.get(include=["documents", "metadatas"])
        for doc, meta in zip(batch.get("documents") or [], batch.get("metadatas") or []):
            meta = meta or {}
            kind = meta.get("content_type")
            if kind == "example":
                chroma_example += 1
            if kind != "exercise":
                continue
            chroma_exercise += 1
            if meta.get("difficulty") in (None, "", "unrated"):
                chroma_unrated += 1
            rows.append(_row(
                origin="chroma_exercise",
                chunk_id=meta.get("chunk_id"),
                section_id=meta.get("section_id"),
                content_type="exercise",
                difficulty=meta.get("difficulty") or "unrated",
                text=(doc or "")[:2000],
            ))
    except Exception as exc:
        print(f"chroma inventory skipped: {exc}")

    config.EXERCISES_DIR.mkdir(parents=True, exist_ok=True)
    path = config.EXERCISE_STEMS_FILE
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")

    print(json.dumps({
        "verified_examples": example_count,
        "curated_exercises": len(curated),
        "chroma_examples": chroma_example,
        "chroma_exercises": chroma_exercise,
        "chroma_unrated_exercises": chroma_unrated,
        "stem_rows": len(rows),
        "output": str(path),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
