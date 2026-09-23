"""Map draft exercises onto the 51 textbook sections.

Study Guide rows that already carry a section label map directly.
18.01SC rows, and any Study Guide row without a label, go through
MiniLM top-5 candidates and an LLM choice.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend import config, llm, rag, textbook  # noqa: E402

BATCH = 4


def _read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def _cards() -> list[dict]:
    blurbs: dict[str, str] = {}
    for item in textbook.load_verified_content():
        if item.get("content_type") == "concept" and item.get("section_id") not in blurbs:
            blurbs[item["section_id"]] = (item.get("text") or "")[:400]
    cards = []
    for chapter, section in textbook.iter_sections():
        cards.append({
            "id": section["id"],
            "label": section["label"],
            "title": section["title"],
            "chapter": chapter["title"],
            "summary": blurbs.get(section["id"], ""),
        })
    return cards


def _by_label(cards: list[dict]) -> dict[str, dict]:
    return {card["label"]: card for card in cards}


def _scope_cards(row: dict, cards: list[dict]) -> list[dict]:
    """Study Guide chapter N stays inside that chapter when the label is missing."""
    if row.get("source") != "mit_strang_study_guide":
        return cards
    match = re.search(r"ch(\d+)", row.get("exercise_id") or "")
    if not match:
        return cards
    prefix = f"{int(match.group(1))}."
    scoped = [card for card in cards if card["label"].startswith(prefix)]
    return scoped or cards


def _candidate_map(rows: list[dict], cards: list[dict]) -> dict[str, list[dict]]:
    if not rows:
        return {}
    model = rag._embedding_model()
    found: dict[str, list[dict]] = {}
    groups: dict[tuple[str, ...], list[dict]] = {}
    scopes = {row["exercise_id"]: _scope_cards(row, cards) for row in rows}
    for row in rows:
        key = tuple(card["id"] for card in scopes[row["exercise_id"]])
        groups.setdefault(key, []).append(row)
    for key, group in groups.items():
        pool = scopes[group[0]["exercise_id"]]
        card_text = [
            f"{card['label']} {card['title']}. {card['chapter']}. {card['summary']}"
            for card in pool
        ]
        card_vecs = model.encode(card_text, normalize_embeddings=True, show_progress_bar=False)
        stem_vecs = model.encode(
            [row["stem"][:1000] for row in group],
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        scores = stem_vecs @ card_vecs.T
        for index, row in enumerate(group):
            order = scores[index].argsort()[::-1][:5]
            found[row["exercise_id"]] = [pool[int(pos)] for pos in order]
    return found


def _choose(batch: list[dict], candidates: dict[str, list[dict]]) -> dict[str, dict]:
    payload = []
    for row in batch:
        options = [
            {"id": card["id"], "label": card["label"], "title": card["title"]}
            for card in candidates[row["exercise_id"]]
        ]
        payload.append({
            "exercise_id": row["exercise_id"],
            "stem": row["stem"][:900],
            "candidates": options,
        })
    prompt = (
        "Map each calculus exercise to the current textbook sections. "
        "Choose primary_section_id only from that item's candidates. "
        "related_section_ids may include other candidate ids, or be empty. "
        "knowledge_points is a short list of calculus ideas in the exercise. "
        "If no candidate fits, use an empty primary_section_id. "
        "Return JSON {\"items\": [{\"exercise_id\", \"primary_section_id\", "
        "\"related_section_ids\", \"knowledge_points\"}]}.\n\n"
        + json.dumps(payload, ensure_ascii=False)
    )
    data = llm.chat_to_json(
        [
            {"role": "system", "content": "You output only valid JSON."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.1,
        max_tokens=1800,
    )
    return {item["exercise_id"]: item for item in data.get("items", []) if item.get("exercise_id")}


def _apply_direct(row: dict, cards_by_label: dict[str, dict]) -> bool:
    label = (row.get("section_label") or "").strip()
    card = cards_by_label.get(label)
    if not card:
        return False
    row["primary_section_id"] = card["id"]
    row["related_section_ids"] = row.get("related_section_ids") or []
    return True


def map_rows(rows: list[dict]) -> list[dict]:
    cards = _cards()
    labels = _by_label(cards)
    pending = []
    for row in rows:
        if row.get("primary_section_id"):
            continue
        if _apply_direct(row, labels):
            continue
        pending.append(row)
    candidates = _candidate_map(pending, cards)
    allowed = {card["id"] for card in cards}
    for start in range(0, len(pending), BATCH):
        batch = pending[start : start + BATCH]
        chosen = _choose(batch, candidates)
        for row in batch:
            item = chosen.get(row["exercise_id"]) or {}
            primary = item.get("primary_section_id") or ""
            if primary not in allowed:
                primary = ""
            related = [
                section_id
                for section_id in (item.get("related_section_ids") or [])
                if section_id in allowed and section_id != primary
            ]
            row["primary_section_id"] = primary
            row["related_section_ids"] = related
            row["knowledge_points"] = item.get("knowledge_points") or []
            if row.get("duplicate_of"):
                row["serve_as_reference"] = False
            else:
                row["serve_as_reference"] = bool(primary)
        print(f"mapped {min(start + BATCH, len(pending))}/{len(pending)}")
    return rows


def main() -> None:
    paths = list(config.EXERCISE_DRAFT_DIR.glob("*.jsonl"))
    if not paths:
        raise SystemExit("no draft jsonl files")
    for path in paths:
        rows = map_rows(_read_jsonl(path))
        _write_jsonl(path, rows)
        mapped = sum(1 for row in rows if row.get("primary_section_id"))
        print(json.dumps({"file": path.name, "rows": len(rows), "mapped": mapped}))


if __name__ == "__main__":
    main()
