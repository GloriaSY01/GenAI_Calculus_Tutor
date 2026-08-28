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

from . import guardrail, llm
from .schemas import Condition, Problem, TutorTurn

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
                   hint_level: int) -> str:
    policy = _EXPLAIN_POLICY if condition == "explain" else _CONTROL_POLICY

    if problem is None:
        # Free chat: no fixed problem, the student can ask about anything.
        return (
            f"{_SHARED_RULES}\n{policy}\n"
            "There is NO fixed problem in this session. The student may ask "
            "about any Calculus 1 topic (limits, derivatives, integrals, etc.). "
            "Work out the correct solution yourself, but never just hand over "
            "the final answer -- guide the student to it.\n\n"
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
        f"{reference}\n\n"
        f"Current hint level used so far: {hint_level} "
        f"(higher means the student has needed more help).\n\n"
        f"{_OUTPUT_SPEC}"
    )


def opening_message(problem: Optional[Problem], condition: Condition) -> str:
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
) -> TutorTurn:
    # 1. Input guardrail.
    flagged = guardrail.check_input(student_text)
    if flagged:
        return TutorTurn(
            tutor_message=guardrail.deflection_message(flagged),
            reasoning_assessment="none",
            action="blocked",
            asks_for_explanation=True,
            hint_level=hint_level,
            mastery=mastery,
            is_solved=False,
        )

    # 2. Build the conversation for the LLM.
    messages: List[Dict[str, str]] = [
        {"role": "system", "content": _system_prompt(problem, condition, hint_level)}
    ]
    messages.extend(history)
    messages.append({"role": "user", "content": student_text})

    # 3. Call the model and parse the line-based structured reply.
    try:
        raw = llm.chat(messages, retries=2)
        fields, message = _parse_response(raw)
    except Exception as exc:  # noqa: BLE001 - surface a safe fallback
        # Logged because this turn still gets recorded like a normal one; a
        # silent stream of these quietly skews the analytics.
        log.warning("Tutor turn fell back after LLM failure: %s", exc)
        return TutorTurn(
            tutor_message=(
                "Sorry, I had trouble forming a response. Could you restate "
                "your current thinking on this step?"
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
        message = "Let's keep going — what's your next step, and why?"

    # 4. Update bookkeeping.
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
