"""AI-powered calculus content generation (project section 2.1).

Generates four question types via the LLM:
  - single_choice    (one correct option)
  - multiple_choice  (one or more correct options)
  - fill_blank       (one or more blanks)
  - drag_order       (order the solution steps -- drag-and-drop process exercise)

Generated questions are kept in a server-side registry so they can be graded
and handed to the Socratic tutor (2.2) by id. The registry is persisted across
server restarts. Answers are never sent to the client; grading happens here.
"""
from __future__ import annotations

import random
import json
import re
import threading
import time
import uuid
from typing import Any, Dict, List, Tuple

from . import config, exercise_bank, llm, rag, textbook
from .math_quality import (
    choice_key,
    normalize_math_notation,
    validate_choice_question,
    validate_question_data,
)
from .schemas import (
    GeneratedQuestionPublic,
    GradeRequest,
    GradeResponse,
    Language,
    Problem,
    QuestionType,
)

_REGISTRY_LOCK = threading.RLock()


def _load_registry() -> Dict[str, Dict[str, Any]]:
    path = config.GENERATED_QUESTIONS_FILE
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    if not isinstance(data, dict):
        return {}
    registry: Dict[str, Dict[str, Any]] = {}
    for qid, record in data.items():
        if not isinstance(record, dict) or record.get("id") != qid:
            continue
        try:
            if record.get("type") in {"single_choice", "multiple_choice"}:
                validate_choice_question(record, record["type"])
        except (KeyError, TypeError, ValueError):
            # Old generated records may predate duplicate-option validation.
            # Never restore a question that current quality rules reject.
            continue
        registry[str(qid)] = record
    return registry


_REGISTRY: Dict[str, Dict[str, Any]] = _load_registry()


def _register(record: Dict[str, Any]) -> None:
    """Store private grading data atomically so browser-saved questions remain valid."""
    path = config.GENERATED_QUESTIONS_FILE
    with _REGISTRY_LOCK:
        _REGISTRY[record["id"]] = record
        # Keep recent questions only; this is a local grading cache, not analytics.
        recent = sorted(
            _REGISTRY.items(),
            key=lambda pair: float(pair[1].get("created_at", 0)),
        )[-2000:]
        payload = dict(recent)
        path.parent.mkdir(parents=True, exist_ok=True)
        temp = path.with_suffix(path.suffix + ".tmp")
        temp.write_text(
            json.dumps(payload, ensure_ascii=False, separators=(",", ":")),
            encoding="utf-8",
        )
        temp.replace(path)

_BASE = (
    "You are an expert Calculus 1 question author. Create ONE {difficulty} "
    "question on the topic \"{topic}\".\n"
    "MATH NOTATION RULES (critical, because the output must be valid JSON): "
    "write math inside $...$ using SIMPLE, backslash-free notation only:\n"
    "  - exponents with ^   e.g. $x^2$, $e^x$\n"
    "  - fractions with /    e.g. $(x+1)/(x-1)$\n"
    "  - roots with sqrt()   e.g. $sqrt(x)$\n"
    "  - multiplication with *, and words like lim, integral, d/dx\n"
    "  - subscripts with _    e.g. $lim_{{x->3}}$\n"
    "DO NOT use any backslash LaTeX commands (no \\frac, \\sqrt, \\lim, \\int, "
    "etc.). Backslashes will break the JSON.\n"
    "Solve it yourself carefully so the correct answer is genuinely correct. "
    "Every answer option must be mathematically and semantically distinct. "
    "Do not include equivalent duplicates such as $6x$ and $6x+0$. "
    "Output ONLY a single JSON object, no prose around it.\n\n"
)

_SPECS: Dict[QuestionType, str] = {
    "single_choice": (
        'JSON shape:\n'
        '{\n'
        '  "stem": "the question",\n'
        '  "options": ["opt A", "opt B", "opt C", "opt D"],\n'
        '  "correct_index": 0,\n'
        '  "explanation": "why the correct option is right",\n'
        '  "key_idea": "one-line concept",\n'
        '  "solution_steps": ["step 1", "step 2", "..."]\n'
        '}\n'
        'Exactly 4 options, exactly one correct.'
    ),
    "multiple_choice": (
        'JSON shape:\n'
        '{\n'
        '  "stem": "the question (state that more than one may be correct)",\n'
        '  "options": ["opt A", "opt B", "opt C", "opt D", "opt E"],\n'
        '  "correct_indices": [0, 2],\n'
        '  "explanation": "why those options are right",\n'
        '  "key_idea": "one-line concept",\n'
        '  "solution_steps": ["step 1", "step 2", "..."]\n'
        '}\n'
        '4-5 options, two or three correct.'
        ' The correct options must express genuinely different facts, not '
        'equivalent rewrites of one answer. Do not use a single elementary '
        'derivative question as multiple choice when it has only one distinct answer.'
    ),
    "fill_blank": (
        'Use the placeholder ___ (three underscores) in the stem for each blank.\n'
        'JSON shape:\n'
        '{\n'
        '  "stem": "... ___ ... ___ ...",\n'
        '  "blanks": [\n'
        '    {"answer": "primary answer", "alternatives": ["equivalent form"]}\n'
        '  ],\n'
        '  "explanation": "brief explanation",\n'
        '  "key_idea": "one-line concept",\n'
        '  "solution_steps": ["step 1", "step 2", "..."]\n'
        '}\n'
        'The number of blanks in "blanks" must match the number of ___ markers.'
    ),
    "drag_order": (
        'Create a "put the solution steps in order" exercise.\n'
        'JSON shape:\n'
        '{\n'
        '  "stem": "Arrange the steps in the correct order to solve: <problem>",\n'
        '  "steps": ["first step", "second step", "third step", "fourth step"],\n'
        '  "final_answer": "the final result",\n'
        '  "explanation": "brief explanation",\n'
        '  "key_idea": "one-line concept"\n'
        '}\n'
        'List "steps" in the CORRECT order (4-6 steps). Each step must be a '
        'distinct, self-contained sentence.'
    ),
}


def _validate_choice_options(data: dict[str, Any]) -> None:
    qtype = "multiple_choice" if "correct_indices" in data else "single_choice"
    validate_choice_question(data, qtype)


def _review_generated_question(
    data: dict[str, Any], qtype: QuestionType, topic: str
) -> None:
    if not config.QUESTION_REVIEW_ENABLED:
        return
    review = llm.chat_json(
        [
            {
                "role": "system",
                "content": (
                    "You are an independent Calculus 1 assessment reviewer. "
                    "Recalculate the problem from scratch. Check that the stem is "
                    "unambiguous, every option is distinct, the declared answer is "
                    "exactly correct, the explanation is consistent, and mathematical "
                    "notation uses symbols such as sin(x) and cos(x). For multiple "
                    "choice, require at least two genuinely different correct facts. "
                    "Return JSON only: {\"valid\": true|false, \"issues\": [\"...\"]}."
                ),
            },
            {
                "role": "user",
                "content": json.dumps(
                    {"topic": topic, "type": qtype, "question": data},
                    ensure_ascii=False,
                ),
            },
        ],
        temperature=0,
        max_tokens=700,
    )
    if review.get("valid") is not True:
        issues = review.get("issues") or ["independent review failed"]
        raise ValueError("Question review rejected content: " + "; ".join(map(str, issues)))


def _deterministic_derivative_fallback(
    qtype: QuestionType,
    section: dict[str, Any],
    language: Language,
    exclude_stems: list[str] | None,
) -> dict[str, Any] | None:
    """Create a small, exact derivative exercise when model generation is exhausted.

    The coefficients are varied, while the answer is computed directly from the
    power rule. This path is intentionally limited to derivative sections where
    the template can be verified deterministically.
    """
    if "derivative" not in section["display_title"].lower():
        return None
    excluded = {_norm(stem) for stem in (exclude_stems or [])}
    for _ in range(24):
        a = random.randint(2, 9)
        n = random.randint(2, 5)
        b = random.choice([value for value in range(-8, 9) if value])
        c = random.randint(-9, 9)
        lead = a * n
        power = n - 1
        function = f"{a}x^{n} {'+' if b > 0 else '-'} {abs(b)}x {'+' if c >= 0 else '-'} {abs(c)}"
        derivative = f"{lead}x^{power} {'+' if b > 0 else '-'} {abs(b)}"
        if power == 1:
            derivative = derivative.replace("x^1", "x")
        if language == "zh":
            stem = f"函数 $f(x) = {function}$ 的导数是什么？"
            explanation = (
                f"使用幂函数求导法则：$d/dx({a}x^{n})={lead}x^{power}$，"
                f"$d/dx({b}x)={b}$，常数项的导数为 0，因此 $f'(x)={derivative}$。"
            ).replace("x^1", "x")
            key_idea = "逐项使用幂函数求导法则，常数项的导数为 0。"
            solution_steps = [
                f"用幂函数求导法则计算 ${a}x^{n}$ 的导数。",
                f"分别计算 ${b}x$ 与常数项的导数。",
                f"合并各项，得到 $f'(x)={derivative}$。",
            ]
        else:
            stem = f"What is the derivative of $f(x) = {function}$?"
            explanation = (
                f"Apply the power rule term by term: $d/dx({a}x^{n})={lead}x^{power}$, "
                f"$d/dx({b}x)={b}$, and the constant differentiates to 0. Thus $f'(x)={derivative}$."
            ).replace("x^1", "x")
            key_idea = "Apply the power rule term by term; constants differentiate to zero."
            solution_steps = [
                f"Differentiate ${a}x^{n}$ with the power rule.",
                f"Differentiate ${b}x$ and the constant term.",
                f"Combine the terms to obtain $f'(x)={derivative}$.",
            ]
        if _norm(stem) in excluded:
            continue
        common = {
            "stem": stem,
            "explanation": explanation,
            "key_idea": key_idea,
            "solution_steps": solution_steps,
        }
        if qtype == "single_choice":
            return {
                **common,
                "options": [
                    derivative,
                    f"{a}x^{power} {'+' if b > 0 else '-'} {abs(b)}",
                    f"{lead}x^{n} {'+' if b > 0 else '-'} {abs(b)}",
                    f"{lead}x^{power}",
                ],
                "correct_index": 0,
            }
        if qtype == "multiple_choice":
            multi_stem = (
                f"关于函数 $f(x) = {function}$，请选择所有正确说法。"
                if language == "zh"
                else f"Select every correct statement about $f(x) = {function}$."
            )
            if _norm(multi_stem) in excluded:
                continue
            return {
                **common,
                "stem": multi_stem,
                "options": [
                    f"$f'(x)={derivative}$",
                    f"$f'(0)={b}$",
                    "The constant term has derivative 0." if language == "en" else "常数项的导数为 0。",
                    f"$f'(x)={a}x^{power}$",
                    "The derivative is a constant function." if language == "en" else "导函数是常数函数。",
                ],
                "correct_indices": [0, 1, 2],
            }
        if qtype == "fill_blank":
            return {
                **common,
                "stem": (
                    f"若 $f(x) = {function}$，则 $f'(x)=$ ___。"
                    if language == "zh"
                    else f"If $f(x) = {function}$, then $f'(x)=$ ___."
                ),
                "blanks": [{"answer": derivative, "alternatives": [f"{derivative}+0"]}],
            }
        return {
            **common,
            "stem": (
                f"请按正确顺序排列求 $f(x)={function}$ 导数的步骤。"
                if language == "zh"
                else f"Arrange the steps for differentiating $f(x)={function}$."
            ),
            "steps": common["solution_steps"] + [
                f"写出最终答案：$f'(x)={derivative}$。"
                if language == "zh"
                else f"State the final answer: $f'(x)={derivative}$."
            ],
            "final_answer": derivative,
        }
    return None


def _resolve_section(topic: str) -> dict[str, Any]:
    section = textbook.get_section(topic)
    if section:
        return section
    needle = topic.strip().lower()
    for _, candidate in textbook.iter_sections():
        info = textbook.get_section(candidate["id"])
        if info and needle in {
            info["title"].lower(),
            info["display_title"].lower(),
        }:
            return info
    raise KeyError(topic)


def _citation(section: dict[str, Any], pdf_page: int | None = None) -> dict[str, Any]:
    manifest = textbook.load_manifest()
    page = pdf_page or int(section["pdf_page_start"])
    return {
        "number": 1,
        "source": f"{manifest['book']} — {manifest['author']}",
        "title": section["display_title"],
        "section": section["display_title"],
        "url": f"{manifest['source_url'].split('#', 1)[0]}#page={page}",
        "page": page,
    }


def _build_record(
    *,
    qid: str,
    qtype: QuestionType,
    topic: str,
    section_id: str,
    difficulty: str,
    data: dict[str, Any],
    source: str,
    citations: list[dict[str, Any]],
    language: Language = "en",
) -> Dict[str, Any]:
    validate_question_data(data, qtype)
    record: Dict[str, Any] = {
        "id": qid,
        "type": qtype,
        "topic": topic,
        "section_id": section_id,
        "difficulty": difficulty,
        "stem": normalize_math_notation(data.get("stem", "").strip()),
        "explanation": normalize_math_notation(data.get("explanation", "").strip()),
        "key_idea": normalize_math_notation(data.get("key_idea", "").strip()),
        "solution_steps": [
            normalize_math_notation(step)
            for step in (data.get("solution_steps", []) or [])
        ],
        "source": source,
        "citations": citations,
        "language": language,
        "created_at": time.time(),
        "attempts": 0,
    }

    if qtype == "single_choice":
        record["options"] = [normalize_math_notation(option) for option in data["options"]]
        indices = data.get("correct_indices")
        record["correct_indices"] = (
            [int(index) for index in indices]
            if indices is not None
            else [int(data["correct_index"])]
        )
        record["final_answer"] = data.get(
            "final_answer", record["options"][record["correct_indices"][0]]
        )
        record["instructions"] = (
            "请选择唯一正确答案。" if language == "zh"
            else "Select the one correct answer."
        )
    elif qtype == "multiple_choice":
        record["options"] = [normalize_math_notation(option) for option in data["options"]]
        record["correct_indices"] = [int(i) for i in data["correct_indices"]]
        record["final_answer"] = data.get(
            "final_answer",
            ", ".join(record["options"][i] for i in record["correct_indices"]),
        )
        record["instructions"] = (
            "请选择所有正确答案（可能不止一个）。" if language == "zh"
            else "Select ALL correct answers (more than one may apply)."
        )
    elif qtype == "fill_blank":
        if "blank_answers" in data:
            record["blank_answers"] = [list(values) for values in data["blank_answers"]]
        else:
            blanks = data["blanks"]
            record["blank_answers"] = [
                [blank.get("answer", "")]
                + list(blank.get("alternatives", []) or [])
                for blank in blanks
            ]
        record["final_answer"] = data.get(
            "final_answer",
            "; ".join(values[0] for values in record["blank_answers"]),
        )
        record["instructions"] = (
            "请填写每个空格。" if language == "zh" else "Fill in each blank."
        )
    else:  # drag_order
        raw_steps = data.get("steps_correct") or data["steps"]
        steps = [step.strip() for step in raw_steps if step.strip()]
        record["steps_correct"] = steps
        record["final_answer"] = data.get("final_answer", "").strip()
        shuffled = steps[:]
        if len(shuffled) > 1:
            while shuffled == steps:
                random.shuffle(shuffled)
        record["steps_shuffled"] = shuffled
        record["instructions"] = (
            "请将步骤按正确顺序排列。" if language == "zh"
            else "Put the steps in the correct order."
        )
    return record


def _public(record: Dict[str, Any]) -> GeneratedQuestionPublic:
    kwargs: dict[str, Any] = {
        "id": record["id"],
        "type": record["type"],
        "topic": record["topic"],
        "section_id": record["section_id"],
        "difficulty": record["difficulty"],
        "stem": record["stem"],
        "instructions": record["instructions"],
        "source": record["source"],
        "citations": record["citations"],
        "language": record.get("language", "en"),
    }
    if record["type"] in {"single_choice", "multiple_choice"}:
        kwargs["options"] = record["options"]
    elif record["type"] == "fill_blank":
        kwargs["n_blanks"] = len(record["blank_answers"])
    else:
        kwargs["steps"] = record["steps_shuffled"]
    return GeneratedQuestionPublic(**kwargs)


def _maybe_curated(
    qtype: QuestionType,
    section: dict[str, Any],
    difficulty: str,
    language: Language = "en",
    exclude_stems: list[str] | None = None,
    force: bool = False,
) -> GeneratedQuestionPublic | None:
    candidates = textbook.exercises_for(section["id"], qtype, difficulty)
    excluded = {_norm(stem) for stem in (exclude_stems or [])}
    candidates = [item for item in candidates if _norm(item["stem"]) not in excluded]
    if not candidates or (not force and random.random() >= config.TEXTBOOK_EXERCISE_RATIO):
        return None
    item = random.choice(candidates)
    pdf_page = (
        int(section["pdf_page_start"])
        + int(item["printed_page"])
        - int(section["printed_page_start"])
    )
    qid = f"tb_{item['id']}_{uuid.uuid4().hex[:6]}"
    record = _build_record(
        qid=qid,
        qtype=qtype,
        topic=section["display_title"],
        section_id=section["id"],
        difficulty=item["difficulty"],
        data=item,
        source="textbook",
        citations=[_citation(section, pdf_page)],
        language=language,
    )
    record["reference_ids"] = []
    record["difficulty_reason"] = {}
    _register(record)
    return _public(record)


def generate_question(
    qtype: QuestionType,
    topic: str,
    difficulty: str = "medium",
    *,
    language: Language = "en",
    exclude_stems: list[str] | None = None,
) -> GeneratedQuestionPublic:
    section = _resolve_section(topic)
    excluded = {_norm(stem) for stem in (exclude_stems or [])}
    curated = _maybe_curated(qtype, section, difficulty, language, exclude_stems)
    if curated:
        return curated

    # Introductory derivative drills have exact symbolic templates. Serving
    # those directly avoids two network model calls while retaining strict,
    # deterministic answer validation.
    if difficulty == "easy":
        fast_data = _deterministic_derivative_fallback(
            qtype, section, language, exclude_stems
        )
        if fast_data is not None:
            qid = "rule_" + uuid.uuid4().hex[:10]
            record = _build_record(
                qid=qid,
                qtype=qtype,
                topic=section["display_title"],
                section_id=section["id"],
                difficulty=difficulty,
                data=fast_data,
                source="generated",
                citations=[_citation(section)],
                language=language,
            )
            record["reference_ids"] = []
            record["difficulty_reason"] = {
                "knowledge_integration": "single_rule",
                "strategy_selection": "direct",
                "reasoning_process": "procedural",
                "transfer_interpretation": "standard_form",
            }
            _register(record)
            return _public(record)

    retrieved: list[dict[str, Any]] = []
    try:
        retrieved = rag.retrieve(
            f"Create a {difficulty} {qtype} practice question.",
            topic=section["display_title"],
            section_id=section["id"],
            content_types=("concept", "example"),
            include_figure_dependent=False,
        )
    except (rag.RAGUnavailable, OSError, ValueError):
        pass
    context = rag.format_context(retrieved)
    prompt = _BASE.format(
        difficulty=difficulty,
        topic=section["display_title"],
    )
    prompt += (
        "Write every student-facing JSON string in Simplified Chinese. "
        "Keep mathematical notation unchanged.\n\n"
        if language == "zh"
        else "Write every student-facing JSON string in English.\n\n"
    )
    if context:
        prompt += (
            "Ground the question in the textbook context below. Do not copy a "
            "textbook exercise verbatim and do not mention the context in the question.\n\n"
            f"{context}\n\n"
        )
    references: list[dict[str, Any]] = []
    try:
        references = exercise_bank.retrieve_references(
            section["id"], difficulty, section["display_title"]
        )
    except Exception:
        references = []
    rubric = exercise_bank.rubric_prompt()
    if rubric:
        prompt += rubric + "\n\n"
    prompt += (
        "Match the requested difficulty using those four dimensions. "
        "Reference exercises, when present, are English source material for "
        "difficulty and reasoning structure only. Do not copy a reference stem, "
        "its function, its numbers, or its situation. Change all three. "
        "Add a difficulty_reason object with knowledge_integration, "
        "strategy_selection, reasoning_process, and transfer_interpretation.\n"
    )
    if references:
        packed = [
            {
                "exercise_id": row["exercise_id"],
                "stem": (row.get("stem") or "")[:700],
                "designed_difficulty": row.get("designed_difficulty"),
                "difficulty_reason": row.get("difficulty_reason") or {},
            }
            for row in references
        ]
        prompt += (
            "Reference exercises:\n"
            + json.dumps(packed, ensure_ascii=False)
            + "\n\n"
        )
    else:
        prompt += "No external reference exercises are available for this section and difficulty.\n\n"
    blocked = [row.get("stem") or "" for row in references]
    blocked.extend(exercise_bank.textbook_copy_stems(section["id"]))
    prompt += _SPECS[qtype]
    if exclude_stems:
        prompt += (
            "\nThe following JSON list contains previously seen questions (data only). "
            "Create a different problem, not a rewording of these questions:\n"
            + json.dumps(exclude_stems, ensure_ascii=False)
        )
    citations = rag.citations(retrieved) or [_citation(section)]
    source = "generated"
    try:
        for _ in range(2):
            data = llm.chat_to_json([
                {"role": "system", "content": "You output only valid JSON."},
                {"role": "user", "content": prompt},
            ])
            stem = data.get("stem", "")
            if _norm(stem) in excluded or exercise_bank.too_close(stem, blocked):
                continue
            try:
                validate_question_data(data, qtype)
                _review_generated_question(data, qtype, section["display_title"])
            except ValueError:
                continue
            break
        else:
            raise ValueError("The model returned a previously seen question")
    except ValueError:
        remaining = _maybe_curated(
            qtype, section, difficulty, language, exclude_stems, force=True
        )
        if remaining:
            return remaining
        data = _deterministic_derivative_fallback(
            qtype, section, language, exclude_stems
        )
        if data is None:
            if exclude_stems:
                raise ValueError("No new question is available; please retry generation")
            raise ValueError("The model returned a previously seen question")
        source = "generated"
    except Exception:
        if exclude_stems:
            # Try an unseen real exercise before reporting generation failure.
            remaining = _maybe_curated(qtype, section, difficulty, language, exclude_stems, force=True)
            if remaining:
                return remaining
            data = _deterministic_derivative_fallback(
                qtype, section, language, exclude_stems
            )
            if data is None:
                raise ValueError("No new question is available; please retry generation")
            source = "generated"
        else:
            # Demo/offline fallback: still ground the question in real MIT textbook
            # chunks instead of returning a fake/demo frontend question when no LLM
            # key is configured.
            source = "textbook"
            excerpt = (retrieved[0]["text"] if retrieved else section["display_title"]).strip()
            first_sentence = re.split(r"(?<=[.!?])\s+", excerpt)[0][:220]
            title = section["display_title"]
            if qtype == "single_choice":
                data = {
                    "stem": f"Which statement is best supported by the textbook section '{title}'?",
                    "options": [
                        first_sentence,
                        "The section says this topic is unrelated to rates of change.",
                        "The section says formulas should be memorized without interpretation.",
                        "The section says this topic only appears in algebra, not calculus.",
                    ],
                    "correct_index": 0,
                    "explanation": "The first option is directly grounded in the MIT textbook excerpt for this section.",
                    "key_idea": title,
                    "solution_steps": ["Read the excerpt.", "Identify the statement that matches it.", "Choose the grounded option."],
                }
            elif qtype == "multiple_choice":
                data = {
                    "stem": f"Select the statements that match the textbook discussion of '{title}'.",
                    "options": [
                        first_sentence,
                        f"This question is about {title}.",
                        "The topic is unrelated to Calculus 1.",
                        "The textbook source should be ignored.",
                    ],
                    "correct_indices": [0, 1],
                    "explanation": "The correct statements are grounded in the section title and excerpt.",
                    "key_idea": title,
                    "solution_steps": ["Match each option against the excerpt.", "Select only supported claims."],
                }
            elif qtype == "fill_blank":
                data = {
                    "stem": f"This MIT textbook section is about ___ .",
                    "blanks": [{"answer": title, "alternatives": [section["title"]]}],
                    "explanation": "The blank is the section topic shown in the textbook citation.",
                    "key_idea": title,
                    "solution_steps": ["Use the section title as the topic."],
                }
            else:
                data = {
                    "stem": f"Arrange the steps for studying the textbook section '{title}'.",
                    "steps": [
                        "Read the textbook excerpt carefully.",
                        "Identify the main calculus idea.",
                        "Connect the idea to the section title.",
                        "Use the idea to answer the question.",
                    ],
                    "final_answer": title,
                    "explanation": "The order follows a normal reading-to-application workflow grounded in the section.",
                    "key_idea": title,
                }
    qid = "gen_" + uuid.uuid4().hex[:10]
    record = _build_record(
        qid=qid,
        qtype=qtype,
        topic=section["display_title"],
        section_id=section["id"],
        difficulty=difficulty,
        data=data,
        source=source,
        citations=citations,
        language=language,
    )
    record["reference_ids"] = [row["exercise_id"] for row in references]
    record["difficulty_reason"] = data.get("difficulty_reason") or {}
    _register(record)
    return _public(record)


def get(qid: str) -> Dict[str, Any] | None:
    return _REGISTRY.get(qid)


# --------------------------------------------------------------------------- #
# Grading
# --------------------------------------------------------------------------- #
def _norm(s: str) -> str:
    return s.strip().lower().replace(" ", "").replace("$", "")


def grade(req: GradeRequest) -> GradeResponse:
    q = _REGISTRY.get(req.question_id)
    if q is None:
        raise KeyError(req.question_id)

    qtype = q["type"]
    correct = False
    q["attempts"] = int(q.get("attempts", 0)) + 1

    if qtype == "single_choice":
        correct = req.single is not None and req.single in q["correct_indices"]
    elif qtype == "multiple_choice":
        chosen = set(req.multiple or [])
        options = q.get("options") or []
        valid = all(isinstance(index, int) and 0 <= index < len(options) for index in chosen)
        chosen_answers = {choice_key(options[index]) for index in chosen if valid}
        correct_answers = {
            choice_key(options[index])
            for index in q["correct_indices"]
            if 0 <= index < len(options)
        }
        correct = valid and bool(chosen_answers) and chosen_answers == correct_answers
    elif qtype == "fill_blank":
        answers = req.blanks or []
        accepted = q["blank_answers"]
        correct = len(answers) == len(accepted) and all(
            _norm(a) in {_norm(x) for x in acc}
            for a, acc in zip(answers, accepted)
        )
    elif qtype == "drag_order":
        order = req.order or []
        correct = [_norm(s) for s in order] == [_norm(s) for s in q["steps_correct"]]

    if correct:
        prefix = "回答正确！" if q.get("language") == "zh" else "Correct!"
        feedback = f"{prefix} {q.get('explanation') or ''}"
    else:
        feedback = (
            "还不完全正确。请重新检查第一个不确定步骤所使用的规则，"
            "或者打开 Tutor 获取引导提示。"
            if q.get("language") == "zh"
            else (
                "Not quite. Recheck the rule used in your first uncertain step, "
                "or open the tutor for a guided hint."
            )
        )
    return GradeResponse(
        correct=correct, feedback=feedback.strip(),
        correct_answer=q.get("final_answer") if correct else None,
        attempts=q["attempts"],
        answer_revealed=correct,
    )


# --------------------------------------------------------------------------- #
# Bridge to the Socratic tutor (2.2)
# --------------------------------------------------------------------------- #
def to_problem(qid: str) -> Problem | None:
    q = _REGISTRY.get(qid)
    if q is None:
        return None

    statement = q["stem"]
    if q.get("options"):
        letters = "ABCDEFGH"
        opts = "\n".join(f"- {letters[i]}. {o}" for i, o in enumerate(q["options"]))
        label = "选项" if q.get("language") == "zh" else "Options"
        statement = f"{statement}\n\n{label}:\n{opts}"
    elif q.get("steps_shuffled"):
        steps = "\n".join(f"- {s}" for s in q["steps_shuffled"])
        label = "待排序步骤" if q.get("language") == "zh" else "Steps to order"
        statement = f"{statement}\n\n{label}:\n{steps}"

    solution_steps = q.get("solution_steps") or q.get("steps_correct") or []
    return Problem(
        id=qid,
        topic=q["topic"],
        section_id=q.get("section_id"),
        difficulty=q["difficulty"],
        tags=[q["type"]],
        statement=statement,
        source=q.get("source", "generated"),
        citations=q.get("citations", []),
        final_answer=q.get("final_answer", ""),
        key_idea=q.get("key_idea", ""),
        solution_steps=solution_steps,
    )
