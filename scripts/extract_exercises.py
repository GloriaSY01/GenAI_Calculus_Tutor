"""Split parsed exercise text into one JSONL record per problem.

Pilot inputs are Study Guide chapter 1 and 18.01SC problem set 1.
Reads MinerU markdown when it exists, and falls back to a plain-text
export with the same stem name.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend import config, exercise_bank, textbook  # noqa: E402

READTHROUGH = re.compile(r"read[\s-]*through|even[\s-]*numbered", re.I)
DRILL_HEAD = re.compile(r"(?im)^#{0,3}\s*Drill Problems\b")
DRILL_ITEM = re.compile(r"(?m)^D(\d+)\s+")
PROBLEM_LINE = re.compile(
    r"(?m)^(?:Problem\s+)?(\d{1,2})(?:\s*[:.])?\s+(?=[A-Za-z(\"'])"
)
PSET_ITEM = re.compile(r"(?m)^(\d+[A-Z]-\d+)\*?\s*(?:,\s*(\d+))?\s*[,.:]?\s*")
REVIEW_STOP = re.compile(
    r"(?m)^(Chapter Review|Graph Problems|Computing Problems?|Review Problems)\b"
)
TEXT_CITE = re.compile(r"(?:Problem|Exercise)\s+(\d+\.\d+)\.(\d+)|(\d+\.\d+)\.(\d+)")
PAGE_MARK = re.compile(r"\n===== PAGE \d+ =====\n")
NOISE = re.compile(
    r"(?im)^(COPYRIGHT .*|MIT OpenCourseWare.*|https://ocw\.mit\.edu.*|"
    r"Resource: Calculus.*|Gilbert Strang.*|For information about citing.*|"
    r"E\. 18\.01 Exercises.*|E\. Solutions to 18\.01 Exercises.*|"
    r"1\. Differentiation.*|\d+)\s*$"
)


def _read_source(stem: str) -> str:
    parsed = config.EXERCISE_PARSED_DIR
    matches = list(parsed.rglob(f"{stem}.md")) if parsed.exists() else []
    mineru = [path for path in matches if {"txt", "auto"} & set(path.parts)]
    chosen = sorted(mineru or matches)
    if chosen:
        return chosen[-1].read_text(encoding="utf-8")
    raise SystemExit(f"no MinerU markdown for {stem}")


def _clean(text: str) -> str:
    text = re.sub(r"</?su[bp]>", "", text, flags=re.I)
    text = PAGE_MARK.sub("\n", text)
    lines = []
    for line in text.splitlines():
        if NOISE.match(line.strip()):
            continue
        lines.append(line.rstrip())
    return re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip()


def _blank(**extra) -> dict:
    row = {
        "exercise_id": "",
        "source": "",
        "source_problem_id": "",
        "stem": "",
        "solution": "",
        "final_answer": "",
        "knowledge_points": [],
        "primary_section_id": "",
        "related_section_ids": [],
        "designed_difficulty": "",
        "difficulty_reason": {},
        "cognitive_task": "",
        "source_form": "",
        "license_ref": "",
        "normalized_stem": "",
        "duplicate_of": "",
        "serve_as_reference": True,
        "section_label": "",
    }
    row.update(extra)
    row["normalized_stem"] = exercise_bank.normalize_stem(row["stem"])
    return row


def _usable_stem(stem: str) -> bool:
    text = re.sub(r"!\[[^\]]*\]\([^)]+\)", " ", stem)
    text = re.sub(r"<[^>]+>", " ", text)
    return len(re.findall(r"[A-Za-z]", text)) >= 20


def _column_smash(stem: str) -> bool:
    lines = [line.strip() for line in stem.splitlines() if line.strip()]
    if len(lines) < 6:
        return False
    return sum(len(line) for line in lines) / len(lines) < 12


def _split_answer(block: str) -> tuple[str, str]:
    match = re.search(
        r"(?i)(?:^|\n)\s*(?:Solution(?:\s+to\s+Problem\s+\d+)?|Answer)\s*:\s*",
        block,
    )
    if not match:
        match = re.search(r"(?i)\bAnswer\s*:\s*", block)
    if not match:
        return block.strip(), ""
    return block[: match.start()].strip(), block[match.end() :].strip()


def _load_stems() -> list[dict]:
    path = config.EXERCISE_STEMS_FILE
    if not path.exists():
        return []
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _curated_index() -> dict[str, str]:
    found = {}
    for item in textbook.load_exercises():
        label = item.get("source_exercise") or ""
        match = re.search(r"(\d+\.\d+)\s+Exercise\s+(\d+)", label)
        if match:
            found[f"{match.group(1)}.{match.group(2)}"] = item["id"]
    return found


def _mark_duplicate(row: dict, stems: list[dict], curated: dict[str, str]) -> None:
    cite = TEXT_CITE.search(row["stem"])
    key = ""
    if cite:
        section = cite.group(1) or cite.group(3)
        number = cite.group(2) or cite.group(4)
        key = f"{section}.{number}"
        if key in curated:
            row["duplicate_of"] = curated[key]
            row["serve_as_reference"] = False
            return
    needle = exercise_bank.normalize_stem(row["stem"])
    if len(needle) < 24:
        return
    for other in stems:
        hay = exercise_bank.normalize_stem(other.get("text") or "")
        if not hay:
            continue
        if needle == hay or (needle in hay and len(hay) <= len(needle) * 3):
            row["duplicate_of"] = other.get("chunk_id") or key or "textbook"
            row["serve_as_reference"] = False
            return


def _norm_title(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def _heading_label(heading: str, sections: list[tuple[str, str]]) -> str | None:
    heading = re.sub(r"\s*\(page\s+\d+\)\s*$", "", heading, flags=re.I).strip("# ").strip()
    known = {label for label, _title in sections}
    numbered = re.match(r"(\d+\.\d+)\b", heading)
    if numbered and numbered.group(1) in known:
        return numbered.group(1)
    norm = _norm_title(heading)
    if len(norm) < 8:
        return None
    for label, title in sections:
        title_norm = _norm_title(title)
        if norm == title_norm or title_norm in norm or norm in title_norm:
            return label
    return None


def _section_spans(text: str) -> list[tuple[str, str]]:
    sections = [
        (section["label"], section["title"])
        for _chapter, section in textbook.iter_sections()
    ]
    hits: list[tuple[int, int, str]] = []
    for match in re.finditer(r"(?m)^#{1,3}\s+(.+)$", text):
        label = _heading_label(match.group(1), sections)
        if label is None:
            continue
        if hits and hits[-1][2] == label:
            continue
        hits.append((match.start(), match.end(), label))
    spans: list[tuple[str, str]] = []
    for index, (_start, end, label) in enumerate(hits):
        nxt = hits[index + 1][0] if index + 1 < len(hits) else len(text)
        spans.append((label, text[end:nxt]))
    return spans


def _model_blocks(section_text: str, label: str) -> tuple[list[tuple[str, str, str]], list[str]]:
    """Keep one increasing run of model problems. Skip textbook reprints."""
    rejects: list[str] = []
    other_section = re.compile(
        rf"(?m)^#{{0,3}}\s*(?!{re.escape(label)}\b)\d+\.\d+\s+[A-Z]"
    )
    stops = [
        match.start()
        for match in (REVIEW_STOP.search(section_text), other_section.search(section_text))
        if match
    ]
    if stops:
        section_text = section_text[: min(stops)]
    matches = list(PROBLEM_LINE.finditer(section_text))
    start_at = next((index for index, match in enumerate(matches) if int(match.group(1)) == 1), None)
    if start_at is None:
        return [], rejects
    answer_key = READTHROUGH.search(section_text, matches[start_at].end())
    blocks: list[tuple[str, str, str]] = []
    previous = 0
    for index, match in enumerate(matches):
        if answer_key and match.start() >= answer_key.start():
            break
        number = int(match.group(1))
        end = matches[index + 1].start() if index + 1 < len(matches) else len(section_text)
        if answer_key and end > answer_key.start():
            end = answer_key.start()
        if number != 1 and not (previous and previous < number <= previous + 2):
            rejects.append(section_text[match.start() : match.start() + 80].replace("\n", " "))
            continue
        if number == 1 and previous:
            rejects.append(section_text[match.start() : match.start() + 80].replace("\n", " "))
            continue
        previous = number
        raw = section_text[match.start() : end]
        stem, solution = _split_answer(raw)
        stem = re.sub(r"^(?:Problem\s+)?\d{1,2}(?:\s*[:.])?\s+", "", stem).strip()
        if len(stem) < 20:
            rejects.append(raw[:80].replace("\n", " "))
            continue
        blocks.append((str(number), stem, solution))
    return blocks, rejects


def extract_study_guide(text: str, chapter: int, license_ref: str, stems, curated) -> tuple[list[dict], list[str]]:
    text = _clean(text)
    rejects: list[str] = []
    drill_at = DRILL_HEAD.search(text)
    drill_text = text[drill_at.end() :] if drill_at else ""
    body = text[: drill_at.start()] if drill_at else text
    rows: list[dict] = []
    for label, section_text in _section_spans(body):
        blocks, section_rejects = _model_blocks(section_text, label)
        rejects.extend(section_rejects)
        for number, stem, solution in blocks:
            row = _blank(
                exercise_id=f"sg-ch{chapter:02d}-{label}-model-{number}",
                source="mit_strang_study_guide",
                source_problem_id=f"guide_ch{chapter:02d}_{label}_model_{number}",
                stem=stem,
                solution=solution,
                source_form="model_problem",
                license_ref=license_ref,
                section_label=label,
            )
            _mark_duplicate(row, stems, curated)
            if _column_smash(row["stem"]):
                row["serve_as_reference"] = False
                rejects.append(row["exercise_id"])
            rows.append(row)
    if drill_text:
        parts = DRILL_ITEM.split(drill_text)
        if parts[0].strip() and (len(parts) < 2 or parts[1] != "1"):
            parts = ["", "1", parts[0], *parts[1:]]
        # split keeps capture groups: [pre, num, body, num, body, ...]
        for number, body_text in zip(parts[1::2], parts[2::2]):
            stem = re.split(r"(?m)^(?:Review Problems|Chapter Review|Graph Problems)\b", body_text)[0]
            stem = re.sub(r"^\d{3,}\s+", "", stem.strip()).strip()
            if len(stem) < 15 or not _usable_stem(stem):
                rejects.append(f"D{number}:{stem[:80]}")
                continue
            row = _blank(
                exercise_id=f"sg-ch{chapter:02d}-drill-D{number}",
                source="mit_strang_study_guide",
                source_problem_id=f"guide_ch{chapter:02d}_drill_D{number}",
                stem=stem,
                source_form="drill",
                license_ref=license_ref,
                section_label="",
            )
            _mark_duplicate(row, stems, curated)
            rows.append(row)
    return rows, rejects


def _pset_blocks(text: str) -> list[tuple[str, str]]:
    text = _clean(text)
    matches = list(PSET_ITEM.finditer(text))
    blocks = []
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        body = text[match.end() : end].strip()
        if len(body) < 15:
            continue
        blocks.append((match.group(1), body))
        sibling = match.group(2)
        if sibling:
            prefix = re.match(r"(\d+[A-Z]-)", match.group(1))
            if prefix:
                blocks.append((prefix.group(1) + sibling, body))
    return blocks


def extract_problem_set(
    problems: str,
    solutions: str,
    pset: str,
    license_ref: str,
    stems,
    curated,
) -> tuple[list[dict], list[str]]:
    problem_blocks = dict(_pset_blocks(problems))
    solution_blocks = dict(_pset_blocks(solutions))
    rejects = []
    rows = []
    for problem_id, stem in problem_blocks.items():
        solution = solution_blocks.get(problem_id, "")
        row = _blank(
            exercise_id=f"sc-{pset}-{problem_id}",
            source="mit_18_01sc",
            source_problem_id=f"{pset}_{problem_id}",
            stem=stem,
            solution=solution,
            source_form="problem_set",
            license_ref=license_ref,
            section_label="",
        )
        _mark_duplicate(row, stems, curated)
        if _column_smash(row["stem"]):
            row["serve_as_reference"] = False
            rejects.append(row["exercise_id"])
        rows.append(row)
    for problem_id in solution_blocks:
        if problem_id not in problem_blocks:
            rejects.append(f"solution without problem: {problem_id}")
    return rows, rejects


def _write(path: Path, rows: list[dict], rejects: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    seen: set[str] = set()
    kept: list[dict] = []
    for row in rows:
        if row["exercise_id"] in seen:
            rejects.append(f"duplicate {row['exercise_id']}")
            continue
        seen.add(row["exercise_id"])
        if not _usable_stem(row["stem"]):
            row["serve_as_reference"] = False
            rejects.append(row["exercise_id"])
        kept.append(row)
    rows = kept
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    reject_path = path.with_suffix(".rejects.txt")
    reject_path.write_text("\n".join(rejects), encoding="utf-8")
    print(json.dumps({
        "output": str(path),
        "rows": len(rows),
        "duplicates": sum(1 for row in rows if row["duplicate_of"]),
        "rejects": len(rejects),
    }, ensure_ascii=False))


def main() -> None:
    sources = {
        item["source_id"]: item
        for item in json.loads(config.EXERCISE_SOURCES_FILE.read_text(encoding="utf-8"))["sources"]
    }
    stems = _load_stems()
    curated = _curated_index()
    guide_license = sources["mit_strang_study_guide"]["license"]
    guide_rows, guide_rejects = extract_study_guide(
        _read_source("guide_ch01"), 1, guide_license, stems, curated
    )
    _write(config.EXERCISE_DRAFT_DIR / "mit_strang_study_guide.jsonl", guide_rows, guide_rejects)
    sc_license = sources["mit_18_01sc"]["license"]
    pset_rows, pset_rejects = extract_problem_set(
        _read_source("MIT18_01SC_pset1prb"),
        _read_source("MIT18_01SC_pset1sol"),
        "pset1",
        sc_license,
        stems,
        curated,
    )
    _write(config.EXERCISE_DRAFT_DIR / "mit_18_01sc.jsonl", pset_rows, pset_rejects)


def batch_remaining() -> None:
    """Extract Study Guide chapters 2-8 and problem sets 2-5.

    Pilot drafts are left untouched.
    """
    sources = {
        item["source_id"]: item
        for item in json.loads(config.EXERCISE_SOURCES_FILE.read_text(encoding="utf-8"))["sources"]
    }
    stems = _load_stems()
    curated = _curated_index()
    guide = sources["mit_strang_study_guide"]
    for chapter in guide["chapters"]:
        if chapter == 1:
            continue
        stem = guide["filename_pattern"].format(nn=f"{chapter:02d}").replace(".pdf", "")
        try:
            text = _read_source(stem)
        except SystemExit:
            print(f"skip missing {stem}")
            continue
        rows, rejects = extract_study_guide(text, chapter, guide["license"], stems, curated)
        _write(config.EXERCISE_DRAFT_DIR / f"guide_ch{chapter:02d}.jsonl", rows, rejects)
    course = sources["mit_18_01sc"]
    raw = config.EXERCISES_DIR / course["save_dir"]
    for pset, files in course["files"].items():
        if pset == "pset1":
            continue
        problem_pdf = raw / course["problems_dir"] / files["problem"]
        solution_pdf = raw / course["solutions_dir"] / files["solution"]
        try:
            problems = _read_source(problem_pdf.stem)
        except SystemExit:
            print(f"skip missing {problem_pdf.name}")
            continue
        try:
            solutions = _read_source(solution_pdf.stem) if solution_pdf.exists() else ""
        except SystemExit:
            solutions = ""
        rows, rejects = extract_problem_set(
            problems, solutions, pset, course["license"], stems, curated
        )
        _write(config.EXERCISE_DRAFT_DIR / f"{pset}.jsonl", rows, rejects)


if __name__ == "__main__":
    if "--batch" in sys.argv:
        batch_remaining()
    else:
        main()
