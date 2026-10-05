"""Deterministic math-notation cleanup and checks for student-facing content."""
from __future__ import annotations

import re
from typing import Any

from sympy import Symbol, diff, simplify
from sympy.parsing.sympy_parser import (
    convert_xor,
    implicit_multiplication_application,
    parse_expr,
    standard_transformations,
)

_FUNCTION_NAMES = {
    "反正弦": "asin",
    "反余弦": "acos",
    "反正切": "atan",
    "正弦": "sin",
    "余弦": "cos",
    "正切": "tan",
    "余切": "cot",
    "正割": "sec",
    "余割": "csc",
}

_FUNCTION_CALL = re.compile(
    r"(?<![A-Za-z])(?:asin|acos|atan|sin|cos|tan|cot|sec|csc|ln|log|exp|sqrt)"
    r"\s*\([^()\n]*\)",
    re.IGNORECASE,
)

MATH_SPAN = re.compile(
    r"\$\$[\s\S]*?\$\$|\$(?:\\.|[^$])*?\$|\\\[[\s\S]*?\\\]|\\\([\s\S]*?\\\)"
)
MATH_OR_FUNCTION = re.compile(MATH_SPAN.pattern + "|" + _FUNCTION_CALL.pattern, re.IGNORECASE)


def normalize_math_notation(value: str) -> str:
    """Keep formula notation symbolic even inside Chinese presentation text."""
    text = str(value)
    for chinese, symbol in _FUNCTION_NAMES.items():
        text = re.sub(
            rf"{chinese}\s*([\(（])\s*([^\)）]+?)\s*([\)）])",
            lambda match: f"{symbol}({match.group(2)})",
            text,
        )
    return text


def choice_key(value: str) -> str:
    """Return a conservative key for detecting obviously equivalent options."""
    text = normalize_math_notation(value).strip().lower()
    text = text.replace(" ", "").replace("$", "").replace("−", "-").replace("·", "*")
    text = text.replace("\\left", "").replace("\\right", "")
    previous = None
    while text != previous:
        previous = text
        text = re.sub(r"\+0(?=$|[\)\]\},;])", "", text)
        text = re.sub(r"(?<=[=(\[{,;])0\+", "", text)
    return text


def derivative_correct_indices(stem: str, options: list[str]) -> set[int] | None:
    """Recalculate straightforward derivative MCQs with SymPy when parseable."""
    lowered = stem.lower()
    if "derivative" not in lowered and "导数" not in stem:
        return None
    formulas = [match.group(0).strip("$ ") for match in MATH_SPAN.finditer(stem)]
    if not formulas:
        calls = _FUNCTION_CALL.findall(normalize_math_notation(stem))
        formulas = calls[:1]
    if not formulas:
        return None

    try:
        target = _parse_expression(formulas[0])
        symbols = sorted(target.free_symbols, key=lambda item: item.name)
        if len(symbols) != 1:
            return None
        expected = diff(target, symbols[0])
        correct: set[int] = set()
        for index, option in enumerate(options):
            candidate = _parse_expression(option)
            if simplify(candidate - expected) == 0:
                correct.add(index)
        return correct
    except Exception:
        return None


def validate_choice_question(data: dict[str, Any], qtype: str) -> None:
    options = [str(option) for option in data.get("options") or []]
    if len(options) < 3:
        raise ValueError("Choice questions require at least three options")

    indices = data.get("correct_indices")
    if indices is None and "correct_index" in data:
        indices = [data["correct_index"]]
    if not isinstance(indices, list) or not indices:
        raise ValueError("Choice question has no correct answer")
    try:
        correct = {int(index) for index in indices}
    except (TypeError, ValueError) as exc:
        raise ValueError("Choice question has invalid correct indices") from exc
    if any(index < 0 or index >= len(options) for index in correct):
        raise ValueError("Choice question correct index is out of range")
    if qtype == "single_choice" and len(correct) != 1:
        raise ValueError("Single-choice question must have exactly one correct answer")
    if qtype == "multiple_choice" and len(correct) < 2:
        raise ValueError("Multiple-choice question needs at least two distinct correct answers")

    seen: dict[str, int] = {}
    for index, option in enumerate(options):
        key = choice_key(option)
        if key in seen:
            raise ValueError(f"Equivalent answer options at indices {seen[key]} and {index}")
        seen[key] = index

    recalculated = derivative_correct_indices(str(data.get("stem") or ""), options)
    if recalculated is not None and recalculated != correct:
        raise ValueError(
            "Declared derivative answers do not match symbolic calculation: "
            f"declared={sorted(correct)}, calculated={sorted(recalculated)}"
        )


def validate_question_data(data: dict[str, Any], qtype: str) -> None:
    """Reject incomplete or internally inconsistent generated question data."""
    if not str(data.get("stem") or "").strip():
        raise ValueError("Question stem is empty")
    if not str(data.get("explanation") or "").strip():
        raise ValueError("Question explanation is empty")
    if not str(data.get("key_idea") or "").strip():
        raise ValueError("Question key idea is empty")

    if qtype in {"single_choice", "multiple_choice"}:
        validate_choice_question(data, qtype)
        return

    if qtype == "fill_blank":
        answers = data.get("blank_answers")
        if answers is None:
            answers = [
                [blank.get("answer", "")] + list(blank.get("alternatives", []) or [])
                for blank in (data.get("blanks") or [])
            ]
        markers = str(data["stem"]).count("___")
        if not answers or markers != len(answers):
            raise ValueError("Fill-blank markers and answers do not match")
        if any(not values or not str(values[0]).strip() for values in answers):
            raise ValueError("Fill-blank question has an empty primary answer")
        return

    if qtype == "drag_order":
        steps = data.get("steps_correct") or data.get("steps") or []
        normalized = [choice_key(str(step)) for step in steps if str(step).strip()]
        if not 3 <= len(normalized) <= 8:
            raise ValueError("Step-order question requires 3-8 steps")
        if len(normalized) != len(set(normalized)):
            raise ValueError("Step-order question contains duplicate steps")
        if not str(data.get("final_answer") or "").strip():
            raise ValueError("Step-order question has no final answer")


def _parse_expression(value: str):
    text = normalize_math_notation(value).strip().strip("$")
    text = text.replace("−", "-").replace("·", "*")
    if "=" in text:
        text = text.rsplit("=", 1)[1]
    text = re.sub(r"^[A-Za-z]\s*'\s*\([^)]*\)\s*", "", text)
    transformations = standard_transformations + (convert_xor, implicit_multiplication_application)
    x, t, u, y = (Symbol(name) for name in ("x", "t", "u", "y"))
    return parse_expr(
        text,
        local_dict={"x": x, "t": t, "u": u, "y": y},
        transformations=transformations,
        evaluate=True,
    )
