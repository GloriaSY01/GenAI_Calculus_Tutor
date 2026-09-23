import json

import pytest

from backend import exercise_bank


def test_too_close_detects_copied_stem():
    original = "Find the equation of the line through (0, 3) with slope 5."
    copied = "Find the equation of the line through (0, 3) with slope 5. Show your steps."
    assert exercise_bank.too_close(copied, [original]) is True
    assert exercise_bank.too_close("A different question about circular motion.", [original]) is False


def test_bank_rejects_bad_difficulty(tmp_path, monkeypatch):
    path = tmp_path / "exercise_bank.jsonl"
    path.write_text(json.dumps({
        "exercise_id": "bad-1",
        "source": "mit_18_01sc",
        "source_problem_id": "pset1_1A-1",
        "stem": "Sketch y = x^2.",
        "designed_difficulty": "extreme",
    }) + "\n", encoding="utf-8")
    monkeypatch.setattr(exercise_bank.config, "EXERCISE_BANK_FILE", path)
    exercise_bank.reset_cache()
    with pytest.raises(ValueError, match="Invalid difficulty"):
        exercise_bank.load()


def test_filter_skips_duplicates_and_other_sections(tmp_path, monkeypatch):
    rows = [
        {
            "exercise_id": "keep",
            "source": "mit_strang_study_guide",
            "source_problem_id": "guide_ch01_1.1_model_1",
            "stem": "Find the velocity on 0 < t < 2.",
            "designed_difficulty": "easy",
            "primary_section_id": "mit-1-1-velocity-and-distance",
            "serve_as_reference": True,
        },
        {
            "exercise_id": "dup",
            "source": "mit_strang_study_guide",
            "source_problem_id": "guide_ch01_1.1_model_2",
            "stem": "This reprints a textbook exercise.",
            "designed_difficulty": "easy",
            "primary_section_id": "mit-1-1-velocity-and-distance",
            "duplicate_of": "mit-ex-1-1-23",
            "serve_as_reference": False,
        },
    ]
    path = tmp_path / "exercise_bank.jsonl"
    path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
    monkeypatch.setattr(exercise_bank.config, "EXERCISE_BANK_FILE", path)
    exercise_bank.reset_cache()
    found = exercise_bank.filter_records(
        section_id="mit-1-1-velocity-and-distance",
        difficulty="easy",
    )
    assert [row["exercise_id"] for row in found] == ["keep"]


def test_generator_rejects_a_copied_reference(monkeypatch):
    from backend import generator

    reference = {
        "exercise_id": "sg-ch01-1.1-model-1",
        "stem": "Find the equation of the line through (0, 3) with slope 5.",
        "designed_difficulty": "easy",
        "difficulty_reason": {"knowledge_integration": "one idea"},
        "primary_section_id": "mit-1-1-velocity-and-distance",
    }
    monkeypatch.setattr(generator.config, "TEXTBOOK_EXERCISE_RATIO", 0.0)
    monkeypatch.setattr(generator.textbook, "exercises_for", lambda *args, **kwargs: [])
    monkeypatch.setattr(generator.rag, "retrieve", lambda *args, **kwargs: [])
    monkeypatch.setattr(
        generator.exercise_bank,
        "retrieve_references",
        lambda *args, **kwargs: [reference],
    )
    monkeypatch.setattr(generator.exercise_bank, "textbook_copy_stems", lambda section_id: ())
    monkeypatch.setattr(
        generator.llm,
        "chat_to_json",
        lambda *args, **kwargs: {
            "stem": reference["stem"],
            "options": ["a", "b", "c", "d"],
            "correct_index": 0,
        },
    )
    with pytest.raises(ValueError, match="previously seen"):
        generator.generate_question(
            "single_choice",
            "mit-1-1-velocity-and-distance",
            "easy",
        )
