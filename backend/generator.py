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
import uuid
from typing import Any, Dict, List, Tuple

from . import llm
from .schemas import (
    GeneratedQuestionPublic,
    GradeRequest,
    GradeResponse,
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


def generate_question(qtype: QuestionType, topic: str,
                      difficulty: str = "medium") -> GeneratedQuestionPublic:
    prompt = _BASE.format(difficulty=difficulty, topic=topic) + _SPECS[qtype]
    data = llm.chat_to_json([
        {"role": "system", "content": "You output only valid JSON."},
        {"role": "user", "content": prompt},
    ])

    qid = "gen_" + uuid.uuid4().hex[:10]
    record: Dict[str, Any] = {
        "id": qid, "type": qtype, "topic": topic, "difficulty": difficulty,
        "stem": data.get("stem", "").strip(),
        "explanation": data.get("explanation", "").strip(),
        "key_idea": data.get("key_idea", "").strip(),
        "solution_steps": data.get("solution_steps", []) or [],
    }

    if qtype == "single_choice":
        record["options"] = data["options"]
        record["correct_indices"] = [int(data["correct_index"])]
        record["final_answer"] = data["options"][int(data["correct_index"])]
        instructions = "Select the one correct answer."
        public = GeneratedQuestionPublic(
            id=qid, type=qtype, topic=topic, difficulty=difficulty,
            stem=record["stem"], options=record["options"], instructions=instructions,
        )

    elif qtype == "multiple_choice":
        record["options"] = data["options"]
        record["correct_indices"] = [int(i) for i in data["correct_indices"]]
        record["final_answer"] = ", ".join(
            record["options"][i] for i in record["correct_indices"]
        )
        instructions = "Select ALL correct answers (more than one may apply)."
        public = GeneratedQuestionPublic(
            id=qid, type=qtype, topic=topic, difficulty=difficulty,
            stem=record["stem"], options=record["options"], instructions=instructions,
        )

    elif qtype == "fill_blank":
        blanks = data["blanks"]
        record["blank_answers"] = [
            [b.get("answer", "")] + list(b.get("alternatives", []) or [])
            for b in blanks
        ]
        record["final_answer"] = "; ".join(b.get("answer", "") for b in blanks)
        instructions = "Fill in each blank."
        public = GeneratedQuestionPublic(
            id=qid, type=qtype, topic=topic, difficulty=difficulty,
            stem=record["stem"], n_blanks=len(blanks), instructions=instructions,
        )

    else:  # drag_order
        steps = [s.strip() for s in data["steps"] if s.strip()]
        record["steps_correct"] = steps
        record["final_answer"] = data.get("final_answer", "").strip()
        shuffled = steps[:]
        if len(shuffled) > 1:
            while shuffled == steps:
                random.shuffle(shuffled)
        record["steps_shuffled"] = shuffled
        instructions = "Put the steps in the correct order."
        public = GeneratedQuestionPublic(
            id=qid, type=qtype, topic=topic, difficulty=difficulty,
            stem=record["stem"], steps=shuffled, instructions=instructions,
        )

    _REGISTRY[qid] = record
    return public


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

    prefix = "Correct! " if correct else "Not quite. "
    feedback = prefix + (q.get("explanation") or "")
    return GradeResponse(
        correct=correct, feedback=feedback.strip(),
        correct_answer=q.get("final_answer", ""),
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
        statement = f"{statement}\n\nOptions:\n{opts}"
    elif q.get("steps_shuffled"):
        steps = "\n".join(f"- {s}" for s in q["steps_shuffled"])
        statement = f"{statement}\n\nSteps to order:\n{steps}"

    solution_steps = q.get("solution_steps") or q.get("steps_correct") or []
    return Problem(
        id=qid,
        topic=q["topic"],
        difficulty=q["difficulty"],
        tags=[q["type"]],
        statement=statement,
        final_answer=q.get("final_answer", ""),
        key_idea=q.get("key_idea", ""),
        solution_steps=solution_steps,
    )
