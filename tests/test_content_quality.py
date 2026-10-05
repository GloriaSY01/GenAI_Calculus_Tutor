import json

import pytest

from backend import config
from backend.math_quality import validate_choice_question, validate_question_data


def test_all_curated_questions_pass_quality_gate():
    exercises = json.loads(config.TEXTBOOK_EXERCISES_FILE.read_text(encoding="utf-8"))
    for exercise in exercises:
        validate_question_data(exercise, exercise["type"])


def test_rejects_fake_multiple_choice_with_one_real_answer():
    with pytest.raises(ValueError, match="at least two"):
        validate_choice_question(
            {
                "stem": "Which expressions are derivatives of $sin(x)$?",
                "options": ["cos(x)", "-cos(x)", "sin(x)", "-sin(x)", "0"],
                "correct_indices": [0],
            },
            "multiple_choice",
        )


def test_rejects_incorrect_declared_derivative_answer():
    with pytest.raises(ValueError, match="symbolic calculation"):
        validate_choice_question(
            {
                "stem": "What is the derivative of $sin(x)$?",
                "options": ["cos(x)", "-cos(x)", "sin(x)", "0"],
                "correct_index": 1,
            },
            "single_choice",
        )


def test_rejects_fill_blank_with_missing_answer():
    with pytest.raises(ValueError, match="markers and answers"):
        validate_question_data(
            {
                "stem": "The derivative is ___ and the value is ___ .",
                "blanks": [{"answer": "2x"}],
                "explanation": "Use the power rule.",
                "key_idea": "Power rule",
            },
            "fill_blank",
        )


def test_rejects_duplicate_ordering_steps():
    with pytest.raises(ValueError, match="duplicate steps"):
        validate_question_data(
            {
                "stem": "Order the steps.",
                "steps": ["Differentiate.", "Differentiate.", "Simplify."],
                "final_answer": "2x",
                "explanation": "Differentiate and simplify.",
                "key_idea": "Power rule",
            },
            "drag_order",
        )
