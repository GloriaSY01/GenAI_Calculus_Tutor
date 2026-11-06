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
            "SOLVED: no\nMASTERY_GAIN: yes\n"
            "EVIDENCE: differentiating x squared brings down the exponent\n"
            "MESSAGE: The final answer is 2x."
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


def test_tutor_repairs_translated_function_notation(monkeypatch):
    _mock_retrieval(monkeypatch)
    monkeypatch.setattr(
        socratic.llm,
        "chat",
        lambda *args, **kwargs: (
            "ASSESSMENT: partial\nACTION: hint\nASKS_EXPLANATION: no\n"
            "SOLVED: no\nMASTERY_GAIN: no\nMESSAGE: 你记得正弦(x)的导数规则吗？"
        ),
    )

    turn = socratic.process_turn(
        None, "control", [], 0, 0, "我不确定", language="zh"
    )

    assert "sin(x)" in turn.tutor_message
    assert "正弦(x)" not in turn.tutor_message


def test_tutor_factual_review_fails_closed(monkeypatch):
    _mock_retrieval(monkeypatch)
    monkeypatch.setattr(socratic.config, "TUTOR_REVIEW_ENABLED", True)
    monkeypatch.setattr(
        socratic.llm,
        "chat",
        lambda *args, **kwargs: (
            "ASSESSMENT: partial\nACTION: hint\nASKS_EXPLANATION: no\n"
            "SOLVED: no\nMASTERY_GAIN: no\nMESSAGE: Use the product rule."
        ),
    )
    monkeypatch.setattr(
        socratic.llm,
        "chat_json",
        lambda *args, **kwargs: {"valid": False, "issues": ["wrong rule"]},
    )

    turn = socratic.process_turn(
        PROBLEM, "control", [], 0, 0, "I am unsure."
    )

    assert turn.action == "probe"
    assert turn.safety_event == "factual_review"
    assert "does not mean your answer is wrong" in turn.tutor_message


def test_review_repairs_and_rechecks_before_display(monkeypatch):
    _mock_retrieval(monkeypatch)
    monkeypatch.setattr(socratic.config, "TUTOR_REVIEW_ENABLED", True)
    replies = iter([
        "ASSESSMENT: none\nACTION: hint\nASKS_EXPLANATION: no\n"
        "SOLVED: no\nMASTERY_GAIN: no\nEVIDENCE:\nMESSAGE: Use the product rule.",
        "The derivative gives the slope of the original function's graph.",
    ])
    monkeypatch.setattr(socratic.llm, "chat", lambda *a, **k: next(replies))
    reviews = []

    def review(messages, **kwargs):
        reviews.append(messages)
        return {"valid": len(reviews) == 2, "issues": ["wrong rule"] if len(reviews) == 1 else []}

    monkeypatch.setattr(socratic.llm, "chat_json", review)
    turn = socratic.process_turn(PROBLEM, "explain", [], 0, 0, "Is it the slope of the derivative?")
    assert len(reviews) == 2
    assert "original function" in turn.tutor_message
    assert turn.mastery == 0 and not turn.is_solved


def test_repair_answer_leak_never_reaches_student(monkeypatch):
    _mock_retrieval(monkeypatch)
    monkeypatch.setattr(socratic.config, "TUTOR_REVIEW_ENABLED", True)
    replies = iter([
        "ASSESSMENT: none\nACTION: hint\nASKS_EXPLANATION: no\n"
        "SOLVED: no\nMASTERY_GAIN: no\nEVIDENCE:\nMESSAGE: Use the product rule.",
        "The final answer is $2x$.",
    ])
    monkeypatch.setattr(socratic.llm, "chat", lambda *a, **k: next(replies))
    monkeypatch.setattr(socratic.llm, "chat_json", lambda *a, **k: {"valid": False, "issues": ["wrong rule"]})
    turn = socratic.process_turn(PROBLEM, "explain", [], 0, 0, "I am stuck")
    assert "2x" not in turn.tutor_message
    assert turn.safety_event == "factual_review"
    assert turn.mastery == 0


def test_missing_protocol_is_retried_with_same_conversation(monkeypatch):
    _mock_retrieval(monkeypatch)
    calls = []

    def reply(messages, **kwargs):
        calls.append(messages)
        if len(calls) == 1:
            return "A plain reply without metadata."
        return (
            "ASSESSMENT: none\nACTION: hint\nASKS_EXPLANATION: no\n"
            "SOLVED: no\nMASTERY_GAIN: no\nEVIDENCE:\nMESSAGE: A derivative measures local change."
        )

    monkeypatch.setattr(socratic.llm, "chat", reply)
    turn = socratic.process_turn(None, "explain", [], 0, 0, "What is a derivative?")
    assert len(calls) == 2
    assert calls[0][-1] == calls[1][-1]
    assert sum(m['role'] == 'system' for m in calls[0]) == 1
    assert turn.tutor_message == "A derivative measures local change."
