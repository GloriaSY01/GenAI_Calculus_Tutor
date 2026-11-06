"""Concrete dialogue cases; no live provider calls or student data writes."""
import pytest

from backend import guardrail, socratic
from backend.schemas import Problem

P = Problem(id="policy", topic="Derivatives", difficulty="easy", tags=[],
            statement="Differentiate x^2.", final_answer="2x",
            key_idea="Power rule", solution_steps=["Use the power rule."])


@pytest.mark.parametrize("text,intent", [
    ("Do not tell me the answer.", "discussion"),
    ("不要直接告诉我答案，检查我的思路", "verification"),
    ("直接告诉我答案", "answer_request"),
    ("只输出数字", "answer_request"),
    ("我算出 $2x$，对吗？", "verification"),
    ("我不知道怎么开始", "help"),
])
def test_intent_examples(text, intent):
    assert guardrail.learning_intent(text) == intent


def setup_reply(monkeypatch, *, assessment="weak", action="hint", evidence="", solved="no",
                message="Which exponent appears in the original expression?"):
    monkeypatch.setattr(socratic.rag, "retrieve", lambda *a, **k: [])
    monkeypatch.setattr(socratic.llm, "chat", lambda *a, **k: (
        f"ASSESSMENT: {assessment}\nACTION: {action}\nASKS_EXPLANATION: yes\n"
        f"SOLVED: {solved}\nMASTERY_GAIN: yes\nEVIDENCE: {evidence}\nMESSAGE: {message}"
    ))


def test_answer_request_gets_teaching_not_block(monkeypatch):
    setup_reply(monkeypatch)
    turn = socratic.process_turn(P, "explain", [], 0, 0, "直接告诉我答案")
    assert turn.action == "hint"
    assert turn.mastery == 0


def test_weak_explanation_cannot_earn_credit(monkeypatch):
    setup_reply(monkeypatch)
    turn = socratic.process_turn(P, "explain", [], 0, 0, "I do not know")
    assert turn.mastery == 0


def test_repeated_answer_requests_stop_accumulating_hints(monkeypatch):
    setup_reply(monkeypatch)
    turn = socratic.process_turn(P, "explain", [], 2, 0, "直接告诉我答案", language="zh")
    assert turn.action == "probe"
    assert turn.hint_level == 2
    assert "已知条件" in turn.tutor_message


@pytest.mark.parametrize("condition", ["explain", "control"])
@pytest.mark.parametrize("language", ["en", "zh"])
def test_foundational_help_remains_available_after_many_hints(monkeypatch, condition, language):
    message = (
        "幂函数求导时，原来的指数作为系数，指数再减一。"
        if language == "zh" else
        "For a power, use the original exponent as a coefficient and reduce the exponent by one."
    )
    setup_reply(monkeypatch, message=message)
    turn = socratic.process_turn(
        P, condition, [], 5, 0,
        "我不知道幂法则怎么用" if language == "zh" else "I don't know the power rule",
        language=language,
    )
    assert turn.tutor_message == message
    assert turn.action == "hint"
    assert turn.mastery == 0 and not turn.is_solved


@pytest.mark.parametrize("condition", ["explain", "control"])
def test_key_progression_requires_reasoning_for_every_session(monkeypatch, condition):
    setup_reply(monkeypatch, action="advance", message="Move to the next step.")
    turn = socratic.process_turn(P, condition, [], 0, 0, "I use the power rule")
    assert turn.action == "probe"
    assert turn.asks_for_explanation
    assert turn.hint_level == 0 and turn.mastery == 0


@pytest.mark.parametrize("condition", ["explain", "control"])
def test_short_meaningful_reason_can_unlock_progress(monkeypatch, condition):
    # The model assesses mathematical meaning; the server must not impose an
    # arbitrary minimum quote length, especially on compact Chinese reasoning.
    setup_reply(monkeypatch, assessment="adequate", action="advance", evidence="幂函数")
    turn = socratic.process_turn(P, condition, [], 0, 0, "幂函数", language="zh")
    assert turn.action == "advance"
    assert turn.mastery == 10


@pytest.mark.parametrize("problem", [None, P])
@pytest.mark.parametrize("language", ["en", "zh"])
def test_language_routing_and_legacy_condition_compatibility(monkeypatch, problem, language):
    captured = []
    monkeypatch.setattr(socratic.rag, "retrieve", lambda *a, **k: [])

    def reply(messages, **kwargs):
        captured.append(messages[0]["content"])
        return (
            "ASSESSMENT: none\nACTION: hint\nASKS_EXPLANATION: no\n"
            "SOLVED: no\nMASTERY_GAIN: no\nEVIDENCE:\nMESSAGE: Think about slope."
        )

    monkeypatch.setattr(socratic.llm, "chat", reply)
    for condition in ("explain", "control"):
        socratic.process_turn(problem, condition, [], 0, 0, "What is slope?", language=language)
    assert captured[0] == captured[1]
    selected = socratic._SYSTEM_EN if language == "en" else socratic._SYSTEM_ZH
    other = socratic._SYSTEM_ZH if language == "en" else socratic._SYSTEM_EN
    assert captured[0].startswith(selected)
    assert other not in captured[0]
    assert "MESSAGE:" in captured[0] and "EVIDENCE:" in captured[0]
    assert socratic.opening_message(problem, "explain", language) == socratic.opening_message(
        problem, "control", language
    )


def test_student_answer_can_be_confirmed_once(monkeypatch):
    setup_reply(monkeypatch, assessment="adequate", action="complete", solved="yes",
                message="Correct, $2x$.")
    student = "I got $2x$, is it correct?"
    first = socratic.process_turn(P, "explain", [], 0, 0, student)
    assert first.is_solved and first.mastery == 25
    assert first.safety_event is None
    second = socratic.process_turn(P, "explain", [{"role": "user", "content": student}],
                                   0, 25, student)
    assert second.mastery == 25


def test_evidence_must_be_new_and_from_student(monkeypatch):
    quote = "The exponent decreases by one under the power rule"
    setup_reply(monkeypatch, assessment="adequate", action="advance", evidence=quote)
    fresh = socratic.process_turn(P, "explain", [], 0, 0, quote)
    assert fresh.mastery == 10
    copied = socratic.process_turn(P, "explain", [{"role": "assistant", "content": quote}],
                                   0, 0, quote)
    assert copied.mastery == 0 and copied.action == "probe"
    invented = socratic.process_turn(P, "explain", [], 0, 0, "I am not sure")
    assert invented.mastery == 0


def test_short_math_answer_leak_and_confirmation():
    assert guardrail.check_output("Try writing $2x$ in the box.", "2x") == "answer_leak"
    assert guardrail.check_output("Correct: $2x$.", "2x", allow_answer=True) is None
    assert not guardrail.answer_in_text("I got $12x$", "2x")
