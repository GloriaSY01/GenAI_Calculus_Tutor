"""Load the external exercise bank and retrieve reference items."""
from __future__ import annotations

import json
from functools import lru_cache
from typing import Any, Iterable

from . import config

SOURCE_FORMS = {
    "model_problem",
    "drill",
    "worked_example",
    "problem_set",
    "textbook_exercise",
}
COGNITIVE_TASKS = {
    "routine_calculation",
    "conceptual_understanding",
    "strategy_selection",
    "error_diagnosis",
    "graphical_interpretation",
    "modelling",
    "multi_step_reasoning",
}
DIFFICULTIES = {"easy", "medium", "hard"}
REQUIRED = (
    "exercise_id",
    "source",
    "source_problem_id",
    "stem",
    "designed_difficulty",
)


def normalize_stem(text: str) -> str:
    return "".join(ch.lower() for ch in (text or "") if ch.isalnum())


def too_close(stem: str, others: Iterable[str]) -> bool:
    needle = normalize_stem(stem)
    if not needle:
        return False
    for other in others:
        hay = normalize_stem(other)
        if not hay:
            continue
        if needle == hay:
            return True
        shorter, longer = (needle, hay) if len(needle) <= len(hay) else (hay, needle)
        if len(shorter) >= 24 and shorter in longer:
            return True
    return False


def load_rubric() -> dict[str, Any]:
    path = config.EXERCISE_RUBRIC_FILE
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def rubric_prompt() -> str:
    rubric = load_rubric()
    if not rubric:
        return ""
    lines = [
        "Designed difficulty uses these four dimensions. "
        "MATH Taxonomy groups are not a difficulty scale.",
    ]
    for name, levels in (rubric.get("dimensions") or {}).items():
        lines.append(f"{name}:")
        for level in ("easy", "medium", "hard"):
            if level in levels:
                lines.append(f"  {level}: {levels[level]}")
    banned = rubric.get("hard_must_not") or []
    if banned:
        lines.append("Hard difficulty must not mainly result from: " + "; ".join(banned) + ".")
    return "\n".join(lines)


def validate_record(row: dict[str, Any]) -> None:
    missing = [key for key in REQUIRED if not row.get(key)]
    if missing:
        raise ValueError(f"Exercise {row.get('exercise_id')} missing {missing}")
    if row["designed_difficulty"] not in DIFFICULTIES:
        raise ValueError(f"Invalid difficulty on {row['exercise_id']}")
    form = row.get("source_form")
    if form and form not in SOURCE_FORMS:
        raise ValueError(f"Invalid source_form on {row['exercise_id']}")
    task = row.get("cognitive_task")
    if task and task not in COGNITIVE_TASKS:
        raise ValueError(f"Invalid cognitive_task on {row['exercise_id']}")


@lru_cache(maxsize=1)
def load() -> list[dict[str, Any]]:
    path = config.EXERCISE_BANK_FILE
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    pairs: set[tuple[str, str]] = set()
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        row = json.loads(line)
        validate_record(row)
        key = row["exercise_id"]
        pair = (row["source"], row["source_problem_id"])
        if key in seen or pair in pairs:
            raise ValueError(f"Duplicate exercise at line {line_no}: {key}")
        seen.add(key)
        pairs.add(pair)
        rows.append(row)
    return rows


def reset_cache() -> None:
    load.cache_clear()
    textbook_copy_stems.cache_clear()


def get(exercise_id: str) -> dict[str, Any] | None:
    for row in load():
        if row["exercise_id"] == exercise_id:
            return row
    return None


def filter_records(
    *,
    section_id: str | None = None,
    difficulty: str | None = None,
    serve_as_reference: bool = True,
) -> list[dict[str, Any]]:
    rows = []
    for row in load():
        if serve_as_reference and row.get("serve_as_reference") is False:
            continue
        if row.get("duplicate_of"):
            continue
        if section_id and row.get("primary_section_id") != section_id:
            continue
        if difficulty and row.get("designed_difficulty") != difficulty:
            continue
        rows.append(row)
    return rows


def reference_stems(section_id: str | None = None) -> list[str]:
    return [row["stem"] for row in filter_records(section_id=section_id, serve_as_reference=True)]


def normalized_stems(section_id: str | None = None) -> list[str]:
    return [normalize_stem(stem) for stem in reference_stems(section_id)]


@lru_cache(maxsize=8)
def textbook_copy_stems(section_id: str) -> tuple[str, ...]:
    """Curated and raw textbook exercise text used only for copy checks."""
    path = config.EXERCISE_STEMS_FILE
    if not path.exists():
        return ()
    stems: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if row.get("section_id") != section_id:
            continue
        if row.get("content_type") != "exercise":
            continue
        text = row.get("text") or ""
        if text:
            stems.append(text)
    return tuple(stems)


def _client():
    import chromadb

    config.EXERCISE_CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    return chromadb.PersistentClient(path=str(config.EXERCISE_CHROMA_DIR))


def retrieve_references(
    section_id: str,
    difficulty: str,
    query: str,
    k: int | None = None,
) -> list[dict[str, Any]]:
    """Metadata-filter first, then optional semantic ranking inside the slice."""
    pool = filter_records(section_id=section_id, difficulty=difficulty)
    limit = k or config.EXERCISE_REFERENCE_K
    if not pool:
        return []
    if len(pool) <= limit:
        return pool[:limit]
    try:
        from .rag import _embedding_model

        collection = _client().get_collection(config.EXERCISE_CHROMA_COLLECTION)
        if collection.count() == 0:
            return pool[:limit]
        vector = _embedding_model().encode(
            [query], normalize_embeddings=True, show_progress_bar=False
        )[0]
        result = collection.query(
            query_embeddings=[vector.tolist()],
            n_results=min(limit, collection.count()),
            where={
                "$and": [
                    {"primary_section_id": section_id},
                    {"difficulty": difficulty},
                ]
            },
            include=["metadatas"],
        )
        ids = [
            (meta or {}).get("exercise_id")
            for meta in (result.get("metadatas") or [[]])[0]
        ]
        found = [get(eid) for eid in ids if eid]
        return [row for row in found if row][:limit]
    except Exception:
        return pool[:limit]
