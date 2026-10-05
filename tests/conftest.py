import pytest

from backend import config


@pytest.fixture(autouse=True)
def isolate_generated_questions(monkeypatch, tmp_path):
    monkeypatch.setattr(config, "QUESTION_REVIEW_ENABLED", False)
    monkeypatch.setattr(config, "TUTOR_REVIEW_ENABLED", False)
    monkeypatch.setattr(config, "GENERATED_QUESTIONS_FILE", tmp_path / "generated_questions.json")
