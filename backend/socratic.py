"""The Socratic tutoring agent.

Core idea (research hook): in the "explain" condition the tutor uses an
*explain-to-unlock* policy -- it will not advance to the next hint until the
student has given a reasoning explanation of acceptable quality. The "control"
condition gives progressive hints without requiring an explanation. Comparing
the two is the planned experiment.
"""
import logging
import re
from typing import Dict, List, Optional, Tuple

from . import guardrail, llm, rag, textbook
from .schemas import Condition, Language, Problem, TutorTurn

log = logging.getLogger(__name__)

_ASSESSMENT_ORDER = ["none", "weak", "partial", "adequate", "strong"]
_VALID_ACTIONS = {"probe", "hint", "correct", "affirm", "advance", "complete", "blocked"}
_FIELD_KEYS = ("ASSESSMENT", "ACTION", "ASKS_EXPLANATION", "SOLVED", "MASTERY_GAIN", "MESSAGE")

_SHARED_RULES = """\
You are a Socratic Calculus 1 tutor. Your job is to help the student reach the
answer THEMSELVES through guided questioning.

Hard rules (never break these):
- NEVER reveal the final answer or a complete worked solution.
- Give at most ONE small step or ONE guiding question per reply.
- Use the private reference solution only to decide what to ask next; never
  paste it.
- Be warm, encouraging and concise (2-4 sentences).
- Write all mathematics in LaTeX using $...$ for inline and $$...$$ for block
  math, so it renders correctly.
- If the student is clearly stuck after several attempts, you may give a more
  concrete hint, but still stop short of the final answer.
"""

_EXPLAIN_POLICY = """\
EXPLAIN-TO-UNLOCK POLICY (this session):
Before giving the next hint, require the student to explain the reasoning behind
their current step ("why" / "how"). Evaluate the quality of their explanation:
- If it is "adequate" or "strong": affirm it briefly and give the next small
  nudge (action = "advance").
- If it is "weak" or "partial": ask a focused follow-up "why/how" question to
  push them to justify their reasoning (action = "probe"); do NOT advance yet.
- If they state a step with no reasoning: ask them to explain why first
  (action = "probe", asks_for_explanation = true).
"""

_CONTROL_POLICY = """\
HINT POLICY (this session):
Give progressive Socratic hints to move the student forward one step at a time.
You do NOT require the student to justify their reasoning before advancing; if
they state a correct next step, move on with action = "hint" (or "correct" for
an error, "affirm" when they get a step right). Do not gate progress on
explanations.
Important: still fill in ASSESSMENT and MASTERY_GAIN honestly based on whatever
reasoning the student happened to show, so the two study conditions are measured
the same way. Just don't *demand* an explanation.
"""

_OUTPUT_SPEC = """\
Respond in EXACTLY this format (plain text, NOT JSON). Output the metadata
lines first, then MESSAGE last:
ASSESSMENT: <none|weak|partial|adequate|strong>
ACTION: <probe|hint|correct|affirm|advance|complete>
ASKS_EXPLANATION: <yes|no>
SOLVED: <yes|no>
MASTERY_GAIN: <yes|no>
MESSAGE: <your reply to the student here; use $...$ and $$...$$ for math>

Field meanings:
- ASSESSMENT: quality of the student's reasoning in their latest message.
- ACTION: "advance" only after adequate/strong reasoning; "probe" to ask them
  to justify; "hint"/"correct"/"affirm" for normal guidance.
- SOLVED: "yes" ONLY if the student has stated the correct final answer
  themselves.
- MASTERY_GAIN: "yes" if this turn shows genuine reasoning progress worth
  crediting.
The MESSAGE is the only thing the student sees; everything after "MESSAGE:"
(including line breaks) is part of it.
"""


def _system_prompt(problem: Optional[Problem], condition: Condition,
                   hint_level: int, textbook_context: str = "",
                   language: Language = "en") -> str:
    policy = _EXPLAIN_POLICY if condition == "explain" else _CONTROL_POLICY
    language_rule = (
        "Write only the MESSAGE value in Simplified Chinese. Keep the metadata "
        "field names and enum values in English exactly as specified."
        if language == "zh"
        else "Write the MESSAGE value in English."
    )
    grounding = ""
    if textbook_context:
        grounding = (
            "\nTEXTBOOK CONTEXT:\n"
            "Use this context to ground definitions and teaching hints. Cite it as "
            "[1], [2], etc. Never claim a source that is not listed.\n"
            f"{textbook_context}\n"
        )

    if problem is None:
        # Free chat: no fixed problem, the student can ask about anything.
        return (
            f"{_SHARED_RULES}\n{policy}\n"
            "There is NO fixed problem in this session. The student may ask "
            "about any Calculus 1 topic (limits, derivatives, integrals, etc.). "
            "Work out the correct solution yourself, but never just hand over "
            "the final answer -- guide the student to it.\n\n"
            f"{grounding}\n{language_rule}\n"
            f"Current hint level used so far: {hint_level}.\n\n"
            f"{_OUTPUT_SPEC}"
        )

    reference = (
        f"PRIVATE REFERENCE (do not reveal):\n"
        f"- Final answer: {problem.final_answer}\n"
        f"- Key idea: {problem.key_idea}\n"
        f"- Solution steps:\n  "
        + "\n  ".join(f"{i+1}. {s}" for i, s in enumerate(problem.solution_steps))
    )
    return (
        f"{_SHARED_RULES}\n{policy}\n"
        f"PROBLEM (shown to student): {problem.statement}\n\n"
        f"{reference}\n{grounding}\n{language_rule}\n"
        f"Current hint level used so far: {hint_level} "
        f"(higher means the student has needed more help).\n\n"
        f"{_OUTPUT_SPEC}"
    )


def opening_message(
    problem: Optional[Problem],
    condition: Condition,
    language: Language = "en",
) -> str:
    if language == "zh":
        if problem is None:
            msg = (
                "你好！我是你的微积分导师。你可以询问微积分 1 中的极限、导数或积分，"
                "我会引导你自己推理，而不是直接给出答案。"
            )
            if condition == "explain":
                return msg + " 你正在学习什么？目前有什么想法？"
            return msg + " 你希望我帮助你理解什么？"
        base = (
            f"我们一起分析这道 **{problem.topic}** 题。我不会直接给出答案，"
            f"而会帮助你自己找到解法。\n\n{problem.statement}\n\n"
        )
        if condition == "explain":
            return base + "首先你想从哪里入手？为什么认为这个方法合适？"
        return base + "你的第一步会怎么做？"
    if problem is None:
        msg = (
            "Hi! I'm your calculus tutor. Ask me anything about Calculus 1 — "
            "limits, derivatives, integrals — and I'll help you reason it out "
            "yourself rather than just handing over the answer."
        )
        if condition == "explain":
            return msg + " What are you working on, and what's your thinking so far?"
        return msg + " What would you like help with?"

    base = (
        f"Let's work through this **{problem.topic}** problem together. "
        f"I won't just give you the answer — I'll help you get there yourself.\n\n"
        f"{problem.statement}\n\n"
    )
    if condition == "explain":
        return base + (
            "To start: what is your first idea for tackling this, and **why** "
            "do you think it's a good approach?"
        )
    return base + "What's your first step? Tell me what you'd try."


def process_turn(
    problem: Optional[Problem],
    condition: Condition,
    history: List[Dict[str, str]],
    hint_level: int,
    mastery: int,
    student_text: str,
    current_topic: str | None = None,
    engagement_flag: str | None = None,
    language: Language = "en",
) -> TutorTurn:
    # 1. Input guardrail.
    flagged = guardrail.check_input(student_text)
    if flagged:
        return TutorTurn(
            tutor_message=guardrail.deflection_message(flagged, language),
            reasoning_assessment="none",
            action="blocked",
            asks_for_explanation=True,
            hint_level=hint_level,
            mastery=mastery,
            is_solved=False,
        )

    # 2. Retrieve textbook grounding. Missing indexes degrade safely.
    retrieved: list[dict] = []
    section_id = (
        problem.section_id
        if problem and problem.section_id in textbook.known_section_ids()
        else current_topic if current_topic in textbook.known_section_ids() else None
    )
    section = textbook.get_section(section_id) if section_id else None
    topic = (
        section["display_title"]
        if section
        else problem.topic if problem else current_topic
    )
    problem_context = problem.statement if problem else ""
    retrieval_query = "\n".join(
        part
        for part in (
            f"Section: {topic}" if topic else "",
            f"Current problem: {problem_context}" if problem_context else "",
            f"Student message: {student_text}",
        )
        if part
    )
    try:
        retrieved = rag.retrieve(
            retrieval_query,
            topic=topic,
            section_id=section_id,
            content_types=("concept", "example"),
        )
    except (rag.RAGUnavailable, OSError, ValueError):
        retrieved = []
    textbook_context = rag.format_context(retrieved)

    # 3. Build the conversation for the LLM.
    messages: List[Dict[str, str]] = [
        {
            "role": "system",
            "content": _system_prompt(
                problem,
                condition,
                hint_level,
                textbook_context=textbook_context,
                language=language,
            ),
        }
    ]
    messages.extend(history)
    messages.append({"role": "user", "content": student_text})

    # 4. Call the model and parse the line-based structured reply.
    try:
        raw = llm.chat(messages, retries=2)
        fields, message = _parse_response(raw)
    except Exception as exc:  # noqa: BLE001 - surface a safe fallback
        # Logged because this turn still gets recorded like a normal one; a
        # silent stream of these quietly skews the analytics.
        log.warning("Tutor turn fell back after LLM failure: %s", exc)
        return TutorTurn(
            tutor_message=(
                "抱歉，我刚才没能组织好回复。请再描述一下你目前对这一步的想法。"
                if language == "zh"
                else (
                    "Sorry, I had trouble forming a response. Could you restate "
                    "your current thinking on this step?"
                )
            ),
            reasoning_assessment="none",
            action="probe",
            asks_for_explanation=True,
            hint_level=hint_level,
            mastery=mastery,
            is_solved=False,
        )

    assessment = fields.get("ASSESSMENT", "none").lower()
    if assessment not in _ASSESSMENT_ORDER:
        assessment = "none"
    action = fields.get("ACTION", "hint").lower()
    if action not in _VALID_ACTIONS:
        action = "hint"
    is_solved = _as_bool(fields.get("SOLVED"))
    asks_for_explanation = _as_bool(fields.get("ASKS_EXPLANATION"))
    mastery_gain = _as_bool(fields.get("MASTERY_GAIN"))
    if not message:
        message = (
            "我们继续：你的下一步是什么？为什么？"
            if language == "zh"
            else "Let's keep going — what's your next step, and why?"
        )

    # 5. Enforce the experimental policy server-side.
    if (
        condition == "explain"
        and assessment not in ("adequate", "strong")
        and action in ("advance", "complete")
    ):
        action = "probe"
        is_solved = False
        asks_for_explanation = True
        mastery_gain = False
        message = (
            "在进入下一步前，请解释为什么你当前的步骤成立。"
            "是哪条微积分规则或表达式特征支持它？"
            if language == "zh"
            else (
                "Before we move to the next step, explain why your current step is "
                "valid. Which calculus rule or feature of the expression supports it?"
            )
        )

    # Low-evidence behavior triggers verification rather than an accusation.
    if engagement_flag and (mastery_gain or is_solved):
        action = "probe"
        is_solved = False
        mastery_gain = False
        asks_for_explanation = True
        message = (
            "在更新进度前，请用自己的话验证这一步：为什么你选择的规则适用于这里？"
            if language == "zh"
            else (
                "Before I update your progress, verify this step in your own words: "
                "why does the rule you chose apply here?"
            )
        )

    # 6. Output-side guardrail: rewrite once without exposing private references.
    safety_event = None
    if problem:
        safety_event = guardrail.check_output(
            message, problem.final_answer, problem.solution_steps
        )
        if safety_event:
            try:
                message = llm.chat([
                    {
                        "role": "system",
                        "content": (
                            "Rewrite the tutor reply as one Socratic question. Remove "
                            "all final answers and worked solutions. Keep at most one "
                            "small hint and do not add new mathematical facts. "
                            + (
                                "Write the result in Simplified Chinese."
                                if language == "zh"
                                else "Write the result in English."
                            )
                        ),
                    },
                    {"role": "user", "content": message},
                ], temperature=0.1, max_tokens=180, retries=1)
            except Exception:
                message = ""
            if not message or guardrail.check_output(
                message, problem.final_answer, problem.solution_steps
            ):
                message = (
                    "最终结果留给你自己发现。你会对当前表达式使用哪条规则？为什么？"
                    if language == "zh"
                    else (
                        "Let's keep the final result for you to discover. What rule "
                        "would you apply to the current expression, and why?"
                    )
                )

    # 7. Update bookkeeping.
    new_hint_level = hint_level
    if action in ("hint", "advance", "correct"):
        new_hint_level = hint_level + 1

    new_mastery = mastery
    if mastery_gain or is_solved:
        new_mastery = min(100, mastery + (25 if is_solved else 10))

    return TutorTurn(
        tutor_message=message,
        reasoning_assessment=assessment,
        action=action,
        asks_for_explanation=asks_for_explanation,
        hint_level=new_hint_level,
        mastery=new_mastery,
        is_solved=is_solved,
        citations=rag.citations(retrieved),
        engagement_flag=engagement_flag,
        safety_event=safety_event,
    )


def _as_bool(value: str | None) -> bool:
    if value is None:
        return False
    return value.strip().lower() in ("yes", "true", "1", "y")


def _parse_response(text: str) -> Tuple[Dict[str, str], str]:
    """Parse the line-based 'HEADER: value ... MESSAGE: free text' format.

    Returns (fields, message). Everything after the MESSAGE: marker (including
    subsequent lines) is treated as the student-facing message, which keeps
    LaTeX backslashes intact (the reason we avoid JSON here).
    """
    fields: Dict[str, str] = {}
    message_lines: List[str] = []
    in_message = False
    header_re = re.compile(
        r"^\s*(" + "|".join(_FIELD_KEYS) + r")\s*:\s*(.*)$", re.IGNORECASE
    )

    for line in text.splitlines():
        if in_message:
            message_lines.append(line)
            continue
        m = header_re.match(line)
        if m:
            key = m.group(1).upper()
            val = m.group(2)
            if key == "MESSAGE":
                in_message = True
                if val.strip():
                    message_lines.append(val)
            else:
                fields[key] = val.strip()
        # Lines before any recognized header are ignored.

    message = "\n".join(message_lines).strip()
    # Fallback: if the model ignored the format entirely, treat the whole
    # reply as the message so the student still gets something useful.
    if not message and not fields:
        message = text.strip()
    return fields, message
