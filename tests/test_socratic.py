from backend import rag, socratic
from backend.schemas import Problem


PROBLEM = Problem(
    id="p1",
    topic="Derivatives",
    difficulty="easy",
    tags=["power-rule"],
    statement="Differentiate x^2.",
    final_answer="2x",
    key_idea="Power rule",
    solution_steps=["Use the power rule and reduce the exponent by one."],
)


def _mock_retrieval(monkeypatch):
    monkeypatch.setattr(rag, "retrieve", lambda *args, **kwargs: [])


def test_explain_policy_is_enforced_server_side(monkeypatch):
    _mock_retrieval(monkeypatch)
    monkeypatch.setattr(
        socratic.llm,
        "chat",
        lambda *args, **kwargs: (
            "ASSESSMENT: weak\nACTION: advance\nASKS_EXPLANATION: no\n"
            "SOLVED: no\nMASTERY_GAIN: yes\nMESSAGE: Move to the next step."
        ),
    )
    turn = socratic.process_turn(
        PROBLEM, "explain", [], 0, 0, "I use the power rule."
    )
    assert turn.action == "probe"
    assert turn.asks_for_explanation is True
    assert turn.mastery == 0


def test_output_answer_leak_falls_back_to_question(monkeypatch):
    _mock_retrieval(monkeypatch)
    replies = iter([
        (
            "ASSESSMENT: adequate\nACTION: advance\nASKS_EXPLANATION: no\n"
            "SOLVED: no\nMASTERY_GAIN: yes\nMESSAGE: The final answer is 2x."
        ),
        "The answer is 2x.",
    ])
    monkeypatch.setattr(socratic.llm, "chat", lambda *args, **kwargs: next(replies))
    turn = socratic.process_turn(
        PROBLEM,
        "explain",
        [],
        0,
        0,
        "Because differentiating x squared brings down the exponent.",
    )
    assert turn.safety_event == "answer_leak"
    assert "final result for you to discover" in turn.tutor_message
    assert "2x" not in turn.tutor_message


def test_mit_section_id_filters_tutor_retrieval(monkeypatch):
    captured = {}

    def retrieve(query, **kwargs):
        captured["query"] = query
        captured.update(kwargs)
        return []

    monkeypatch.setattr(rag, "retrieve", retrieve)
    monkeypatch.setattr(
        socratic.llm,
        "chat",
        lambda *args, **kwargs: (
            "ASSESSMENT: partial\nACTION: hint\nASKS_EXPLANATION: no\n"
            "SOLVED: no\nMASTERY_GAIN: no\nMESSAGE: What does slope represent?"
        ),
    )

    socratic.process_turn(
        None,
        "control",
        [],
        0,
        0,
        "How are velocity and distance connected?",
        current_topic="mit-1-1-velocity-and-distance",
    )

    assert captured["section_id"] == "mit-1-1-velocity-and-distance"
    assert captured["content_types"] == ("concept", "example")
    assert "Section: 1.1 Velocity and Distance" in captured["query"]


def test_chinese_tutor_language_is_enforced(monkeypatch):
    captured = {}
    _mock_retrieval(monkeypatch)

    def chat(messages, **kwargs):
        captured["system"] = messages[0]["content"]
        return (
            "ASSESSMENT: partial\nACTION: hint\nASKS_EXPLANATION: no\n"
            "SOLVED: no\nMASTERY_GAIN: no\nMESSAGE: 斜率表示距离变化的快慢。"
        )

    monkeypatch.setattr(socratic.llm, "chat", chat)
    opening = socratic.opening_message(None, "explain", "zh")
    turn = socratic.process_turn(
        None,
        "control",
        [],
        0,
        0,
        "速度和距离有什么关系？",
        language="zh",
    )

    assert opening.startswith("你好")
    assert "Simplified Chinese" in captured["system"]
    assert turn.tutor_message.startswith("斜率")
