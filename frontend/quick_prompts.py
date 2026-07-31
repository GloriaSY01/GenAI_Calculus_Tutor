"""Context-aware quick prompt buttons for the tutor panel."""

from __future__ import annotations

from dataclasses import dataclass

import presets
from stepper import STAGE_CONCEPT, STAGE_PRACTICE

_MAX_PROMPTS = 4


@dataclass(frozen=True)
class QuickPrompt:
    label: str
    message: str
    key: str


def _cap(prompts: list[QuickPrompt]) -> list[QuickPrompt]:
    return prompts[:_MAX_PROMPTS]


def _concept_prompts(topic: str) -> list[QuickPrompt]:
    return [
        QuickPrompt("Explain this concept", presets.explain_concept(topic), "qp_concept_explain"),
        QuickPrompt("Give an example", presets.give_example(topic), "qp_concept_example"),
        QuickPrompt("Common mistakes?", presets.common_mistakes(topic), "qp_concept_mistakes"),
        QuickPrompt("How used in problems?", presets.how_used_in_problems(topic), "qp_concept_used"),
    ]


def _problem_early_prompts(topic: str) -> list[QuickPrompt]:
    return [
        QuickPrompt("Hint: first step", presets.hint_first_step(), "qp_early_hint"),
        QuickPrompt("Why this method?", presets.why_this_method(), "qp_early_why"),
        QuickPrompt("I'm stuck", presets.need_guidance(), "qp_early_stuck"),
        QuickPrompt("Review the concept", presets.explain_concept(topic), "qp_early_concept"),
    ]


def _problem_mid_prompts() -> list[QuickPrompt]:
    return [
        QuickPrompt("Next hint", presets.more_hint(), "qp_mid_hint"),
        QuickPrompt("Check my reasoning", presets.check_my_reasoning(), "qp_mid_check"),
        QuickPrompt("Why this step?", presets.why_this_step(), "qp_mid_why_step"),
        QuickPrompt("Still confused", presets.still_confused(), "qp_mid_confused"),
    ]


def _blocked_prompts() -> list[QuickPrompt]:
    return [
        QuickPrompt("Next hint", presets.more_hint(), "qp_blocked_hint"),
        QuickPrompt("Still confused", presets.still_confused(), "qp_blocked_confused"),
    ]


def _solved_prompts() -> list[QuickPrompt]:
    return [
        QuickPrompt("Explain the full solution", presets.explain_full_solution(), "qp_solved_explain"),
        QuickPrompt("Why does this work?", presets.why_this_method(), "qp_solved_why"),
    ]


def get_quick_prompts(
    *,
    current_topic: str,
    tutor_entry: str | None,
    last_turn: dict | None,
    has_problem: bool,
) -> list[QuickPrompt]:
    """Return up to four prompts appropriate for the current tutor context."""
    hint_level = last_turn["hint_level"] if last_turn else 0
    is_solved = last_turn.get("is_solved", False) if last_turn else False
    asks_for_explanation = last_turn.get("asks_for_explanation", False) if last_turn else False
    action = last_turn.get("action") if last_turn else None

    if is_solved:
        prompts = _solved_prompts()
    elif tutor_entry == STAGE_CONCEPT or not has_problem:
        prompts = _concept_prompts(current_topic)
    elif tutor_entry == STAGE_PRACTICE or has_problem:
        if action == "blocked":
            prompts = _blocked_prompts()
        elif hint_level == 0:
            prompts = _problem_early_prompts(current_topic)
        else:
            prompts = _problem_mid_prompts()
    else:
        prompts = _concept_prompts(current_topic)

    if asks_for_explanation and not is_solved and has_problem:
        reasoning = QuickPrompt(
            "Here's my reasoning",
            presets.offer_reasoning(),
            "qp_offer_reasoning",
        )
        prompts = [reasoning] + [p for p in prompts if p.key != reasoning.key]

    return _cap(prompts)
