import pytest

from backend import generator


TOPIC = "mit-1-1-velocity-and-distance"


def setup_generation(monkeypatch):
    monkeypatch.setattr(generator.textbook, "exercises_for", lambda *a: [])
    monkeypatch.setattr(generator.rag, "retrieve", lambda *a, **k: [])


def test_seen_curated_exercise_is_excluded(monkeypatch):
    monkeypatch.setattr(generator.textbook, "exercises_for", lambda *a: [{"stem": "Known question"}])
    section = generator._resolve_section(TOPIC)
    assert generator._maybe_curated("single_choice", section, "easy", exclude_stems=["Known question"], force=True) is None


def test_duplicate_model_question_is_retried(monkeypatch):
    setup_generation(monkeypatch)
    responses = iter([
        {"stem": "Known question"},
        {"stem": "Find the slope of $4t$", "options": ["4", "2", "1", "0"], "correct_index": 0},
    ])
    monkeypatch.setattr(generator.llm, "chat_to_json", lambda *a: next(responses))
    result = generator.generate_question("single_choice", TOPIC, exclude_stems=["Known question"])
    assert result.stem == "Find the slope of $4t$"


def test_repeated_model_output_is_not_returned_as_next_question(monkeypatch):
    setup_generation(monkeypatch)
    monkeypatch.setattr(generator.llm, "chat_to_json", lambda *a: {"stem": "Known question"})
    with pytest.raises(ValueError, match="No new question"):
        generator.generate_question("single_choice", TOPIC, exclude_stems=["Known question"])


def test_offline_next_does_not_repeat_fixed_fallback(monkeypatch):
    setup_generation(monkeypatch)
    def offline(*a):
        raise RuntimeError("offline")
    monkeypatch.setattr(generator.llm, "chat_to_json", offline)
    first = generator.generate_question("single_choice", TOPIC)
    with pytest.raises(ValueError, match="No new question"):
        generator.generate_question("single_choice", TOPIC, exclude_stems=[first.stem])
