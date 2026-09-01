"""AI-powered calculus content generation (project section 2.1).

Generates four question types via the LLM:
  - single_choice    (one correct option)
  - multiple_choice  (one or more correct options)
  - fill_blank       (one or more blanks)
  - drag_order       (order the solution steps -- drag-and-drop process exercise)

Generated questions are kept in an in-memory registry so they can be graded
server-side and handed to the Socratic tutor (2.2) by id. Answers are never
sent to the client; grading happens here.
"""
import random
import re
import time
import uuid
from typing import Any, Dict, List, Tuple

from . import config, llm, rag, textbook
from .schemas import (
    GeneratedQuestionPublic,
    GradeRequest,
    GradeResponse,
    Language,
    Problem,
    QuestionType,
)

_REGISTRY: Dict[str, Dict[str, Any]] = {}

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
    record: Dict[str, Any] = {
        "id": qid,
        "type": qtype,
        "topic": topic,
        "section_id": section_id,
        "difficulty": difficulty,
        "stem": data.get("stem", "").strip(),
        "explanation": data.get("explanation", "").strip(),
        "key_idea": data.get("key_idea", "").strip(),
        "solution_steps": data.get("solution_steps", []) or [],
        "source": source,
        "citations": citations,
        "language": language,
        "created_at": time.time(),
        "attempts": 0,
    }

    if qtype == "single_choice":
        record["options"] = list(data["options"])
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
        record["options"] = list(data["options"])
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
) -> GeneratedQuestionPublic | None:
    candidates = textbook.exercises_for(section["id"], qtype, difficulty)
    if not candidates or random.random() >= config.TEXTBOOK_EXERCISE_RATIO:
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
    _REGISTRY[qid] = record
    return _public(record)


def generate_question(
    qtype: QuestionType,
    topic: str,
    difficulty: str = "medium",
    *,
    language: Language = "en",
) -> GeneratedQuestionPublic:
    section = _resolve_section(topic)
    curated = _maybe_curated(qtype, section, difficulty, language)
    if curated:
        return curated

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
    prompt += _SPECS[qtype]
    citations = rag.citations(retrieved) or [_citation(section)]
    source = "generated"
    try:
        data = llm.chat_to_json([
            {"role": "system", "content": "You output only valid JSON."},
            {"role": "user", "content": prompt},
        ])
    except Exception:
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
    _REGISTRY[qid] = record
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
        correct = chosen == set(q["correct_indices"])
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
