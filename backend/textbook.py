"""MIT Strang Calculus metadata and structured textbook access."""
from __future__ import annotations

import json
from functools import lru_cache
from typing import Any, Iterator

from . import config


@lru_cache(maxsize=1)
def load_manifest() -> dict[str, Any]:
    return json.loads(config.TEXTBOOK_MANIFEST_FILE.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def load_toc() -> list[dict[str, Any]]:
    return json.loads(config.TEXTBOOK_TOC_FILE.read_text(encoding="utf-8"))


def reset_cache() -> None:
    load_manifest.cache_clear()
    load_toc.cache_clear()
    load_verified_content.cache_clear()
    load_exercises.cache_clear()


def iter_sections(
    toc: list[dict[str, Any]] | None = None,
) -> Iterator[tuple[dict[str, Any], dict[str, Any]]]:
    for chapter in toc or load_toc():
        for section in chapter["sections"]:
            yield chapter, section


def _section_url(section: dict[str, Any]) -> str:
    base = load_manifest()["source_url"]
    return f"{base}#page={section['pdf_page_start']}"


def get_section(section_id: str) -> dict[str, Any] | None:
    for chapter, section in iter_sections():
        if section["id"] != section_id:
            continue
        chapter_title = f"{chapter.get('number', '')} {chapter['title']}".strip()
        label = section.get("label", "")
        display_title = f"{label} {section['title']}".strip()
        return {
            **section,
            "display_title": display_title,
            "chapter_id": chapter["id"],
            "chapter_title": chapter_title,
            "url": _section_url(section),
        }
    return None


def catalog_tree() -> dict[str, Any]:
    manifest = load_manifest()
    enabled = set(manifest.get("enabled_sections", []))
    chapters: list[dict[str, Any]] = []
    for chapter in load_toc():
        sections = [
            {
                "id": section["id"],
                "label": section.get("label", ""),
                "title": f"{section.get('label', '')} {section['title']}".strip(),
                "url": _section_url(section),
            }
            for section in chapter["sections"]
            if not enabled or section["id"] in enabled
        ]
        if sections:
            chapters.append({
                "id": chapter["id"],
                "title": f"{chapter.get('number', '')} {chapter['title']}".strip(),
                "sections": sections,
            })
    return {
        "source": f"{manifest['book']} — {manifest['author']}",
        "attribution": manifest["attribution"],
        "license": manifest["license"],
        "url": manifest["source_url"],
        "default_section_id": manifest["default_section_id"],
        "chapters": chapters,
    }


def known_section_ids() -> set[str]:
    return {section["id"] for _, section in iter_sections()}


def topic_labels() -> list[str]:
    return [
        info["display_title"]
        for _, section in iter_sections()
        if (info := get_section(section["id"])) is not None
    ]


@lru_cache(maxsize=1)
def load_verified_content() -> list[dict[str, Any]]:
    if not config.TEXTBOOK_VERIFIED_CONTENT_FILE.exists():
        return []
    return json.loads(
        config.TEXTBOOK_VERIFIED_CONTENT_FILE.read_text(encoding="utf-8")
    )


@lru_cache(maxsize=1)
def load_exercises() -> list[dict[str, Any]]:
    if not config.TEXTBOOK_EXERCISES_FILE.exists():
        return []
    return json.loads(config.TEXTBOOK_EXERCISES_FILE.read_text(encoding="utf-8"))


def exercises_for(
    section_id: str,
    question_type: str | None = None,
    difficulty: str | None = None,
) -> list[dict[str, Any]]:
    candidates = [
        item
        for item in load_exercises()
        if item["section_id"] == section_id
        and item.get("answer_available", False)
        and not item.get("requires_figure", False)
        and (question_type is None or item["type"] == question_type)
    ]
    if difficulty:
        exact = [item for item in candidates if item["difficulty"] == difficulty]
        if exact:
            return exact
    return candidates
