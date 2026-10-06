from backend.analytics import _compute_practice


def _grade(
    question_id: str,
    *,
    correct: bool,
    assisted: bool = False,
    difficulty: str = "easy",
) -> dict:
    return {
        "event": "practice_grade",
        "question_id": question_id,
        "student_id": "student-1",
        "class_id": "calc1-a",
        "topic": "Derivatives",
        "difficulty": difficulty,
        "correct": correct,
        "ai_assisted": assisted,
        "hint_usage": "ai_assisted" if assisted else "independent",
    }


def test_accuracy_by_ai_use_counts_every_submission_including_retries():
    events = [
        _grade("q-retried-without-ai", correct=False),
        _grade("q-retried-without-ai", correct=True),
        _grade("q-retried-with-ai", correct=False, assisted=True),
        _grade("q-retried-with-ai", correct=True, assisted=True),
        _grade("q-assisted-medium", correct=True, assisted=True, difficulty="medium"),
    ]

    result = _compute_practice(events)

    assert result["n_answers"] == 5
    assert result["correct_rate"] == 0.6
    assert result["independent_solve_rate"] == 0.5
    assert result["ai_assisted_solve_rate"] == 0.667

    easy = next(row for row in result["by_difficulty_completion"]
                if row["difficulty"] == "easy")
    assert easy["attempts"] == 4
    assert easy["independent_submissions"] == 2
    assert easy["independent_correct_count"] == 1
    assert easy["independent_rate"] == 0.5
    assert easy["ai_assisted_submissions"] == 2
    assert easy["ai_assisted_correct_count"] == 1
    assert easy["ai_assisted_rate"] == 0.5


def test_tutor_session_marks_each_matching_submission_as_ai_assisted():
    events = [
        {
            "event": "session_start",
            "problem_id": "q-from-tutor",
            "student_id": "student-1",
            "class_id": "calc1-a",
        },
        _grade("q-from-tutor", correct=False),
        _grade("q-from-tutor", correct=True),
    ]

    result = _compute_practice(events)

    assert result["n_answers"] == 2
    assert result["independent_solve_rate"] == 0.0
    assert result["ai_assisted_solve_rate"] == 0.5
    assert result["practice_completion_modes"] == [
        {"mode": "independent", "count": 0},
        {"mode": "ai_assisted", "count": 2},
    ]
