"""Generate MIT Calculus TOC entries from MinerU heading metadata."""
from __future__ import annotations

import argparse
import json
import re
import unicodedata
from collections import Counter
from pathlib import Path
from typing import Any

from backend import config

TITLE_OVERRIDES = {
    (2, "2.1"): "The Derivative of a Function",
    (3, "3.6"): "Iterations x(n+1) = F(x(n))",
    (6, "6.2"): "The Exponential e^x",
}


def _content_file(chapter: int) -> Path:
    root = (
        config.TEXTBOOK_DIR
        / "parsed"
        / f"ch{chapter:02d}"
        / f"chapter_{chapter:02d}"
    )
    for method in ("auto", "txt"):
        path = root / method / f"chapter_{chapter:02d}_content_list.json"
        if path.exists():
            return path
    raise FileNotFoundError(f"No MinerU content list found below {root}")


def _clean(value: str) -> str:
    value = "".join(char if char >= " " else " " for char in value)
    return re.sub(r"\s+", " ", value).strip()


def _slug(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", normalized.lower()).strip("-")


def _printed_pages(items: list[dict[str, Any]]) -> dict[int, int]:
    pages: dict[int, int] = {}
    for item in items:
        if item.get("type") != "page_number":
            continue
        text = _clean(str(item.get("text", "")))
        if text.isdigit():
            pages.setdefault(int(item.get("page_idx", 0)) + 1, int(text))
    return pages


def chapter_toc(chapter: int) -> dict[str, Any]:
    items = json.loads(_content_file(chapter).read_text(encoding="utf-8"))
    pattern = re.compile(rf"^{chapter}\.(\d+)\s+(.+)$")
    headings: dict[str, tuple[str, int]] = {}
    chapter_title = ""
    for item in items:
        text = _clean(str(item.get("text", "")))
        match = pattern.match(text)
        if match and item.get("text_level") in {1, 2}:
            label = f"{chapter}.{match.group(1)}"
            title = match.group(2).strip()
            if "EXERCISES" not in title.upper():
                headings.setdefault(label, (title, int(item.get("page_idx", 0)) + 1))
        elif item.get("text_level") == 1 and text and not chapter_title:
            chapter_title = text
    if not headings:
        raise ValueError(f"No section headings found for Chapter {chapter}")

    page_count = max(int(item.get("page_idx", 0)) for item in items) + 1
    printed = _printed_pages(items)
    printed_offset = Counter(
        printed_page - pdf_page for pdf_page, printed_page in printed.items()
    ).most_common(1)[0][0]
    ordered = sorted(
        headings.items(),
        key=lambda pair: tuple(int(part) for part in pair[0].split(".")),
    )
    sections: list[dict[str, Any]] = []
    for index, (label, (title, start)) in enumerate(ordered):
        end = ordered[index + 1][1][1] - 1 if index + 1 < len(ordered) else page_count
        printed_start = printed.get(start)
        printed_end = printed.get(end)
        title = TITLE_OVERRIDES.get((chapter, label), title)
        section = {
            "id": f"mit-{label.replace('.', '-')}-{_slug(title)}",
            "label": label,
            "title": title,
            "pdf_page_start": start,
            "pdf_page_end": end,
        }
        section["printed_page_start"] = printed_start or start + printed_offset
        section["printed_page_end"] = printed_end or end + printed_offset
        sections.append(section)
    chapter_title = re.sub(
        rf"^CHAPTER\s+{chapter}\s*", "", chapter_title, flags=re.IGNORECASE
    ).strip()
    return {
        "id": f"mit-ch{chapter}",
        "number": str(chapter),
        "title": chapter_title or f"Chapter {chapter}",
        "sections": sections,
    }


def build_toc() -> list[dict[str, Any]]:
    current = json.loads(config.TEXTBOOK_TOC_FILE.read_text(encoding="utf-8"))
    chapter_one = next(chapter for chapter in current if chapter["number"] == "1")
    return [chapter_one, *(chapter_toc(chapter) for chapter in range(2, 9))]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    toc = build_toc()
    payload = json.dumps(toc, ensure_ascii=False, indent=2)
    if args.write:
        config.TEXTBOOK_TOC_FILE.write_text(payload + "\n", encoding="utf-8")
    print(payload)


if __name__ == "__main__":
    main()
