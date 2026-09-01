"""Build the single MIT Calculus Chroma collection."""
from __future__ import annotations

import argparse
import html
import json
import os
import re
import unicodedata
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable
from uuid import uuid4

import chromadb

from backend import config

os.environ.setdefault("USE_TF", "0")
os.environ.setdefault("TRANSFORMERS_NO_TF", "1")

CONTENT_TYPES = {"concept", "example", "exercise"}
PARSED_TYPES = {"text", "equation", "code"}
SKIPPED_TYPES = {"header", "footer", "page_number", "page_footnote"}
CHUNK_CHARS = 1400
FIGURE_OVERRIDES_FILE = config.TEXTBOOK_DIR / "figure_overrides.json"


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _clean_text(value: str) -> str:
    value = "".join(
        " " if unicodedata.category(char).startswith("C") else char for char in value
    )
    value = value.replace("\u00ad", "").replace("\ufffd", "")
    value = re.sub(r"<sup>(.*?)</sup>", r"^(\1)", value, flags=re.IGNORECASE)
    value = re.sub(r"<sub>(.*?)</sub>", r"_(\1)", value, flags=re.IGNORECASE)
    value = re.sub(r"</?[^>]+>", "", value)
    value = html.unescape(value)
    return re.sub(r"\s+", " ", value).strip()


def _section_map(
    chapters: set[int],
) -> tuple[list[dict[str, Any]], dict[tuple[int, int], dict[str, Any]]]:
    sections: list[dict[str, Any]] = []
    by_page: dict[tuple[int, int], dict[str, Any]] = {}
    for chapter in _read_json(config.TEXTBOOK_TOC_FILE):
        chapter_number = int(chapter["number"])
        if chapter_number not in chapters:
            continue
        for section in chapter["sections"]:
            item = {**section, "chapter": str(chapter_number)}
            sections.append(item)
            for page in range(int(section["pdf_page_start"]), int(section["pdf_page_end"]) + 1):
                by_page[(chapter_number, page)] = item
    return sections, by_page


def _verified_chunks(section_ids: set[str]) -> list[dict[str, Any]]:
    if not config.TEXTBOOK_VERIFIED_CONTENT_FILE.exists():
        return []
    chunks: list[dict[str, Any]] = []
    for item in _read_json(config.TEXTBOOK_VERIFIED_CONTENT_FILE):
        if item["section_id"] not in section_ids:
            continue
        chunks.append({
            "id": item["id"],
            "text": _clean_text(item["text"]),
            "chapter": item["section_id"].split("-")[1],
            "section_id": item["section_id"],
            "title": item["heading"],
            "content_type": item["content_type"],
            "subtype": item.get("subtype", item["content_type"]),
            "formulas": list(item.get("formulas", [])),
            "order": int(item["order"]),
            "pdf_page": int(item["pdf_page"]),
            "requires_figure": bool(item.get("figure_ids")),
            "figure_ids": list(item.get("figure_ids", [])),
        })
    return chunks


def _curated_exercises(section_ids: set[str]) -> list[dict[str, Any]]:
    if not config.TEXTBOOK_EXERCISES_FILE.exists():
        return []
    chunks: list[dict[str, Any]] = []
    for item in _read_json(config.TEXTBOOK_EXERCISES_FILE):
        if item["section_id"] not in section_ids:
            continue
        chunks.append({
            "id": item["id"],
            "text": _clean_text(item["stem"]),
            "chapter": item["section_id"].split("-")[1],
            "section_id": item["section_id"],
            "title": item["section_title"],
            "content_type": "exercise",
            "order": 10_000 + len(chunks),
            "pdf_page": max(1, int(item["printed_page"]) - 50),
            "requires_figure": bool(item.get("requires_figure", False)),
            "figure_ids": list(item.get("figure_ids", [])),
            "difficulty": item["difficulty"],
            "question_type": item["type"],
            "answer_available": bool(item["answer_available"]),
        })
    return chunks


def _figure(
    item: dict[str, Any],
    chapter: int,
    pdf_page: int,
    base_dir: Path,
    figures: dict[str, dict[str, Any]],
) -> str | None:
    relative_path = item.get("img_path")
    if not relative_path:
        return None
    captions = item.get("image_caption") or []
    caption = _clean_text(" ".join(str(value) for value in captions))
    match = re.search(r"\bFig\.\s*(\d+)\.(\d+)", caption, re.IGNORECASE)
    if match:
        figure_id = f"fig-{match.group(1)}-{match.group(2)}"
    else:
        figure_id = f"asset-{chapter}-{Path(relative_path).stem[:16]}"
    figures.setdefault(figure_id, {
        "path": (base_dir / relative_path).relative_to(config.TEXTBOOK_DIR).as_posix(),
        "caption": caption,
        "chapter": chapter,
        "pdf_page": pdf_page,
    })
    return figure_id


def _raw_chunks(
    chapter: int,
    by_page: dict[tuple[int, int], dict[str, Any]],
    verified_sections: set[str],
) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
    chapter_dir = (
        config.TEXTBOOK_DIR
        / "parsed"
        / f"ch{chapter:02d}"
        / f"chapter_{chapter:02d}"
    )
    base_dir = next(
        (chapter_dir / method for method in ("auto", "txt") if (chapter_dir / method).exists()),
        chapter_dir / "auto",
    )
    content_file = base_dir / f"chapter_{chapter:02d}_content_list.json"
    if not content_file.exists():
        # Raw MinerU output is optional: when it is absent the collection is
        # built from verified content and curated exercises only. Existing
        # figure metadata is preserved separately in build_chunks().
        return [], {}

    chunks: list[dict[str, Any]] = []
    figures: dict[str, dict[str, Any]] = {}
    order: Counter[str] = Counter()
    exercise_started: set[str] = set()
    current: dict[str, Any] | None = None
    pending_figures: list[str] = []
    last_section_id: str | None = None

    def flush() -> None:
        nonlocal current
        if not current or not current["text"]:
            current = None
            return
        if current["content_type"] != "exercise" and len(current["text"]) < 30:
            current = None
            return
        order[current["section_id"]] += 1
        current["order"] = order[current["section_id"]]
        current["requires_figure"] = bool(current["figure_ids"])
        suffix = f"{current['content_type']}-{current['order']:03d}"
        current["id"] = f"mit-{current['section_label'].replace('.', '-')}-{suffix}"
        current.pop("section_label")
        chunks.append(current)
        current = None

    for item in _read_json(content_file):
        item_type = item.get("type")
        if item_type in SKIPPED_TYPES:
            continue
        pdf_page = int(item.get("page_idx", 0)) + 1
        section = by_page.get((chapter, pdf_page))
        if not section:
            continue
        section_id = section["id"]
        if last_section_id and last_section_id != section_id:
            flush()
            pending_figures = []
        last_section_id = section_id

        if item_type in {"image", "chart"}:
            figure_id = _figure(item, chapter, pdf_page, base_dir, figures)
            if figure_id:
                if section_id in verified_sections and section_id not in exercise_started:
                    continue
                if current and current["section_id"] == section_id:
                    current["figure_ids"].append(figure_id)
                else:
                    pending_figures.append(figure_id)
            continue
        if item_type not in PARSED_TYPES:
            continue

        text = _clean_text(str(item.get("text", "")))
        if not text:
            continue
        upper = text.upper()
        if upper.endswith("EXERCISES") and section["label"] in text:
            flush()
            pending_figures = []
            exercise_started.add(section_id)
            continue
        if text in {
            f"{section['label']} {section['title']}",
            f"{chapter} Introduction to Calculus",
        }:
            continue
        if item.get("text_level") and re.match(rf"^{chapter}\s+", text):
            continue

        content_type = "exercise" if section_id in exercise_started else "concept"
        if content_type == "concept" and re.match(r"^EXAMPLE(?:\s+\d+)?\b", upper):
            content_type = "example"
        if content_type != "exercise" and section_id in verified_sections:
            continue

        should_flush = (
            current is not None
            and (
                current["section_id"] != section_id
                or current["content_type"] != content_type
                or len(current["text"]) + len(text) + 1 > CHUNK_CHARS
                or bool(item.get("text_level"))
            )
        )
        if should_flush:
            flush()
        if current is None:
            current = {
                "text": "",
                "chapter": str(chapter),
                "section_id": section_id,
                "section_label": section["label"],
                "title": section["title"],
                "content_type": content_type,
                "pdf_page": pdf_page,
                "figure_ids": pending_figures,
            }
            pending_figures = []
            if content_type == "exercise":
                current.update({
                    "difficulty": "unrated",
                    "question_type": "unsupported",
                    "answer_available": False,
                })
        current["text"] = _clean_text(f"{current['text']} {text}")
    flush()
    return chunks, figures


def build_chunks(chapters: Iterable[int]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    chapter_set = set(chapters)
    sections, by_page = _section_map(chapter_set)
    if not sections:
        raise ValueError(f"No TOC sections found for chapters {sorted(chapter_set)}")
    section_ids = {section["id"] for section in sections}
    verified = _verified_chunks(section_ids)
    verified_sections = {chunk["section_id"] for chunk in verified}
    curated_exercises = _curated_exercises(section_ids)
    figures: dict[str, Any] = {}
    # Seed with previously parsed figure metadata so verified-content figure
    # references still resolve even when raw MinerU output is unavailable.
    existing_figures_file = config.TEXTBOOK_DIR / "figures.json"
    if existing_figures_file.exists():
        figures.update(_read_json(existing_figures_file))
    raw_chunks: list[dict[str, Any]] = []
    for chapter in sorted(chapter_set):
        raw, chapter_figures = _raw_chunks(chapter, by_page, verified_sections)
        raw_chunks.extend(raw)
        figures.update(chapter_figures)
    if FIGURE_OVERRIDES_FILE.exists():
        for figure_id, override in _read_json(FIGURE_OVERRIDES_FILE).items():
            if figure_id in figures:
                figures[figure_id].update(override)
    figures_by_page: dict[tuple[int, int], list[str]] = {}
    for figure_id, figure in figures.items():
        key = (int(figure["chapter"]), int(figure["pdf_page"]))
        figures_by_page.setdefault(key, []).append(figure_id)
    for chunk in verified:
        resolved: list[str] = []
        for figure_id in chunk["figure_ids"]:
            match = re.fullmatch(r"page-(\d+)", figure_id)
            key = (int(chunk["chapter"]), int(match.group(1))) if match else None
            resolved.extend(figures_by_page.get(key, []) if key else [figure_id])
        chunk["figure_ids"] = list(dict.fromkeys(resolved))
        chunk["requires_figure"] = bool(chunk["figure_ids"])
    chunks = [*verified, *curated_exercises, *raw_chunks]
    ids = [chunk["id"] for chunk in chunks]
    if len(ids) != len(set(ids)):
        duplicates = [item for item, count in Counter(ids).items() if count > 1]
        raise ValueError(f"Duplicate chunk IDs: {duplicates}")
    invalid = {chunk["content_type"] for chunk in chunks} - CONTENT_TYPES
    if invalid:
        raise ValueError(f"Unsupported content types: {sorted(invalid)}")
    return chunks, figures


def _metadata(chunk: dict[str, Any]) -> dict[str, Any]:
    metadata = {
        "chapter": chunk["chapter"],
        "section_id": chunk["section_id"],
        "title": chunk["title"],
        "content_type": chunk["content_type"],
        "subtype": chunk.get("subtype", chunk["content_type"]),
        "formulas": json.dumps(chunk.get("formulas", []), ensure_ascii=False),
        "order": int(chunk["order"]),
        "pdf_page": int(chunk["pdf_page"]),
        "requires_figure": bool(chunk["requires_figure"]),
        # Chroma metadata values are scalar, so the public list is JSON encoded at rest.
        "figure_ids": json.dumps(chunk["figure_ids"], ensure_ascii=False),
    }
    if chunk["content_type"] == "exercise":
        metadata.update({
            "difficulty": chunk["difficulty"],
            "question_type": chunk["question_type"],
            "answer_available": bool(chunk["answer_available"]),
        })
    return metadata


def ingest(chapters: list[int]) -> dict[str, Any]:
    chunks, figures = build_chunks(chapters)
    config.CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    version = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    build_dir = config.CHROMA_DIR / f"index-{version}-{uuid4().hex[:8]}"
    client = chromadb.PersistentClient(path=str(build_dir))
    collection = client.get_or_create_collection(
        config.CHROMA_COLLECTION,
        metadata={"hnsw:space": "cosine", "source_id": "mit_calculus_f17"},
    )

    from backend.rag import _embedding_model

    model = _embedding_model()
    documents = [chunk["text"] for chunk in chunks]
    embeddings = model.encode(
        documents,
        normalize_embeddings=True,
        show_progress_bar=True,
    ).tolist()
    for start in range(0, len(chunks), 100):
        batch = chunks[start : start + 100]
        collection.add(
            ids=[chunk["id"] for chunk in batch],
            documents=documents[start : start + 100],
            embeddings=embeddings[start : start + 100],
            metadatas=[_metadata(chunk) for chunk in batch],
        )

    figures_file = config.TEXTBOOK_DIR / "figures.json"
    figures_file.write_text(
        json.dumps(figures, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    pointer_tmp = config.CHROMA_POINTER_FILE.with_suffix(".json.tmp")
    pointer_tmp.write_text(
        json.dumps({"path": build_dir.name}, ensure_ascii=False),
        encoding="utf-8",
    )
    os.replace(pointer_tmp, config.CHROMA_POINTER_FILE)
    counts = Counter(chunk["content_type"] for chunk in chunks)
    return {
        "collection": config.CHROMA_COLLECTION,
        "chunks": len(chunks),
        "content_types": dict(sorted(counts.items())),
        "sections": len({chunk["section_id"] for chunk in chunks}),
        "figures": len(figures),
        "path": str(build_dir),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--chapters", type=int, nargs="+", default=[1])
    args = parser.parse_args()
    result = ingest(args.chapters)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
