"""Context-aware quick prompt buttons for the tutor panel."""

from __future__ import annotations

from dataclasses import dataclass

import presets
from i18n import tr
from stepper import STAGE_CONCEPT, STAGE_PRACTICE

_MAX_PROMPTS = 4


@dataclass(frozen=True)
class QuickPrompt:
    label: str
    message: str
    key: str


def _cap(prompts: list[QuickPrompt]) -> list[QuickPrompt]:
    return prompts[:_MAX_PROMPTS]


def _concept_prompts(topic: str, language: str) -> list[QuickPrompt]:
    return [
        QuickPrompt(tr(language, "Explain this concept", "解释这个概念"), presets.explain_concept(topic, language), "qp_concept_explain"),
        QuickPrompt(tr(language, "Give an example", "给出一个例子"), presets.give_example(topic, language), "qp_concept_example"),
        QuickPrompt(tr(language, "Common mistakes?", "常见错误？"), presets.common_mistakes(topic, language), "qp_concept_mistakes"),
        QuickPrompt(tr(language, "How used in problems?", "如何用于解题？"), presets.how_used_in_problems(topic, language), "qp_concept_used"),
    ]


def _problem_early_prompts(topic: str, language: str) -> list[QuickPrompt]:
    return [
        QuickPrompt(tr(language, "Hint: first step", "提示第一步"), presets.hint_first_step(language), "qp_early_hint"),
        QuickPrompt(tr(language, "Why this method?", "为什么用这个方法？"), presets.why_this_method(language), "qp_early_why"),
        QuickPrompt(tr(language, "I'm stuck", "我卡住了"), presets.need_guidance(language), "qp_early_stuck"),
        QuickPrompt(tr(language, "Review the concept", "复习概念"), presets.explain_concept(topic, language), "qp_early_concept"),
    ]


def _problem_mid_prompts(language: str) -> list[QuickPrompt]:
    return [
        QuickPrompt(tr(language, "Next hint", "下一个提示"), presets.more_hint(language), "qp_mid_hint"),
        QuickPrompt(tr(language, "Check my reasoning", "检查我的推理"), presets.check_my_reasoning(language), "qp_mid_check"),
        QuickPrompt(tr(language, "Why this step?", "为什么是这一步？"), presets.why_this_step(language), "qp_mid_why_step"),
        QuickPrompt(tr(language, "Still confused", "还是不明白"), presets.still_confused(language), "qp_mid_confused"),
    ]


def _blocked_prompts(language: str) -> list[QuickPrompt]:
    return [
        QuickPrompt(tr(language, "Next hint", "下一个提示"), presets.more_hint(language), "qp_blocked_hint"),
        QuickPrompt(tr(language, "Still confused", "还是不明白"), presets.still_confused(language), "qp_blocked_confused"),
    ]


def _solved_prompts(language: str) -> list[QuickPrompt]:
    return [
        QuickPrompt(tr(language, "Explain the full solution", "解释完整解法"), presets.explain_full_solution(language), "qp_solved_explain"),
        QuickPrompt(tr(language, "Why does this work?", "为什么成立？"), presets.why_this_method(language), "qp_solved_why"),
    ]


def get_quick_prompts(
    *,
    current_topic: str,
    tutor_entry: str | None,
    last_turn: dict | None,
    has_problem: bool,
    language: str = "en",
) -> list[QuickPrompt]:
    """Return up to four prompts appropriate for the current tutor context."""
    hint_level = last_turn["hint_level"] if last_turn else 0
    is_solved = last_turn.get("is_solved", False) if last_turn else False
    asks_for_explanation = last_turn.get("asks_for_explanation", False) if last_turn else False
    action = last_turn.get("action") if last_turn else None

    if is_solved:
        prompts = _solved_prompts(language)
    elif tutor_entry == STAGE_CONCEPT or not has_problem:
        prompts = _concept_prompts(current_topic, language)
    elif tutor_entry == STAGE_PRACTICE or has_problem:
        if action == "blocked":
            prompts = _blocked_prompts(language)
        elif hint_level == 0:
            prompts = _problem_early_prompts(current_topic, language)
        else:
            prompts = _problem_mid_prompts(language)
    else:
        prompts = _concept_prompts(current_topic, language)

    if asks_for_explanation and not is_solved and has_problem:
        reasoning = QuickPrompt(
            tr(language, "Here's my reasoning", "这是我的推理"),
            presets.offer_reasoning(language),
            "qp_offer_reasoning",
        )
        prompts = [reasoning] + [p for p in prompts if p.key != reasoning.key]

    return _cap(prompts)
