import pytest

from backend import generator
from backend.schemas import GradeRequest


def test_wrong_answer_remains_hidden():
    generator._REGISTRY["test_q"] = {
        "type": "single_choice",
        "correct_indices": [1],
        "final_answer": "B",
        "explanation": "B follows from the derivative rule.",
        "attempts": 0,
    }
    result = generator.grade(GradeRequest(question_id="test_q", single=0))
    assert result.correct is False
    assert result.correct_answer is None
    assert result.answer_revealed is False
    assert result.attempts == 1


def test_correct_answer_reveals_explanation():
    generator._REGISTRY["test_q"]["attempts"] = 0
    result = generator.grade(GradeRequest(question_id="test_q", single=1))
    assert result.correct is True
    assert result.correct_answer == "B"
    assert result.answer_revealed is True


def test_curated_exercise_is_public_without_answer(monkeypatch):
    exercise = {
        "id": "mit-ex-test",
        "section_id": "mit-1-1-velocity-and-distance",
        "section_title": "1.1 Velocity and Distance",
        "printed_page": 57,
        "type": "single_choice",
        "difficulty": "easy",
        "stem": "Which function has slope 2?",
        "options": ["$2t$", "$t+2$", "$t^2$", "$1/2t$"],
        "correct_indices": [0],
        "final_answer": "$2t$",
        "explanation": "The coefficient of t is the slope.",
        "key_idea": "Read the slope of a line.",
        "solution_steps": ["Identify the coefficient of t."],
        "answer_available": True,
        "requires_figure": False,
    }
    monkeypatch.setattr(generator.config, "TEXTBOOK_EXERCISE_RATIO", 1.0)
    monkeypatch.setattr(
        generator.textbook,
        "exercises_for",
        lambda *args, **kwargs: [exercise],
    )
    monkeypatch.setattr(generator.random, "choice", lambda values: values[0])
    monkeypatch.setattr(generator.random, "random", lambda: 0.0)

    public = generator.generate_question(
        "single_choice",
        "mit-1-1-velocity-and-distance",
        "easy",
    )

    assert public.source == "textbook"
    assert public.section_id == "mit-1-1-velocity-and-distance"
    assert public.topic == "1.1 Velocity and Distance"
    assert public.citations[0].page == 7
    assert "correct_indices" not in public.model_dump()
    problem = generator.to_problem(public.id)
    assert problem is not None
    assert problem.section_id == public.section_id
    assert problem.source == "textbook"


def test_generated_question_uses_section_filtered_rag(monkeypatch):
    captured: dict = {}
    chunk = {
        "id": "concept",
        "source": "Calculus — Gilbert Strang",
        "title": "Velocity and Distance",
        "section": "Velocity and Distance",
        "source_url": "https://example.test#page=2",
        "section_id": "mit-1-1-velocity-and-distance",
        "pdf_page": 2,
        "text": "Velocity is the slope of the distance graph.",
    }
    monkeypatch.setattr(generator.config, "TEXTBOOK_EXERCISE_RATIO", 0.0)
    monkeypatch.setattr(
        generator.textbook,
        "exercises_for",
        lambda *args, **kwargs: [],
    )

    def retrieve(*args, **kwargs):
        captured["retrieve"] = kwargs
        return [chunk]

    def chat_to_json(messages):
        captured["prompt"] = messages[-1]["content"]
        return {
            "stem": "What is the slope of $f(t)=3t$?",
            "options": ["$1$", "$2$", "$3$", "$t$"],
            "correct_index": 2,
            "explanation": "The coefficient is 3.",
            "key_idea": "Slope of a line.",
            "solution_steps": ["Read the coefficient of t."],
        }

    monkeypatch.setattr(generator.rag, "retrieve", retrieve)
    monkeypatch.setattr(generator.llm, "chat_to_json", chat_to_json)

    public = generator.generate_question(
        "single_choice",
        "mit-1-1-velocity-and-distance",
        "medium",
    )

    assert public.source == "generated"
    assert public.section_id == "mit-1-1-velocity-and-distance"
    assert public.citations[0].page == 2
    assert captured["retrieve"]["content_types"] == ("concept", "example")
    assert captured["retrieve"]["include_figure_dependent"] is False
    assert "1.1 Velocity and Distance" in captured["prompt"]
    assert "Velocity is the slope" in captured["prompt"]


def test_unknown_section_is_rejected():
    with pytest.raises(KeyError):
        generator.generate_question("single_choice", "not-a-section", "easy")


def test_generated_question_requests_chinese_output(monkeypatch):
    captured = {}
    monkeypatch.setattr(generator.config, "TEXTBOOK_EXERCISE_RATIO", 0.0)
    monkeypatch.setattr(generator.rag, "retrieve", lambda *args, **kwargs: [])

    def chat_to_json(messages):
        captured["prompt"] = messages[-1]["content"]
        return {
            "stem": "函数 $f(t)=3t$ 的斜率是多少？",
            "options": ["$1$", "$2$", "$3$", "$t$"],
            "correct_index": 2,
            "explanation": "一次函数的斜率是 t 的系数。",
            "key_idea": "读取一次函数的系数。",
            "solution_steps": ["找到 t 的系数。"],
        }

    monkeypatch.setattr(generator.llm, "chat_to_json", chat_to_json)
    public = generator.generate_question(
        "single_choice",
        "mit-1-1-velocity-and-distance",
        "medium",
        language="zh",
    )

    assert "Simplified Chinese" in captured["prompt"]
    assert public.stem.startswith("函数")
    assert public.instructions == "请选择唯一正确答案。"
