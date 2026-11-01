"""Lightweight input guardrail.

This is intentionally minimal for the demo: it flags obvious attempts to
extract the final answer outright or to override the tutor's instructions
(prompt injection). A production version would use a classifier.
"""
from __future__ import annotations

import re

# Patterns that strongly suggest "just give me the answer" or jailbreak.
_ANSWER_BEGGING = [
    r"\bjust (give|tell) me the (answer|solution)\b",
    r"\bwhat('?s| is) the (final )?answer\b",
    r"\bgive me the (full |complete )?(answer|solution)\b",
    r"\btell me the (answer|result)\b",
    r"\bsolve it for me\b",
    r"\bskip the (hints?|explanation)\b",
    r"(直接|只要|快点).{0,8}(给|告诉).{0,5}(答案|结果)",
    r"(最终|正确)(答案|结果)(是|为|呢|？|\?)",
    r"(不用|跳过).{0,5}(过程|解释|提示)",
    r"(替我|帮我).{0,4}(做完|算完|解答)",
]

_INJECTION = [
    r"\bignore (all |the )?(previous |above )?instructions?\b",
    r"\byou are now\b",
    r"\bdisregard .* (rules?|instructions?)\b",
    r"\bpretend you are\b",
    r"\bact as if\b.*\b(answer|solution)\b",
    r"\bsystem prompt\b",
    r"(忽略|无视|覆盖).{0,10}(之前|以上|系统).{0,8}(指令|提示|规则)",
    r"(显示|输出|泄露).{0,8}(系统提示|system prompt)",
    r"你现在(是|扮演|作为)",
]


def check_input(text: str) -> str | None:
    """Return a guardrail category if triggered, else None."""
    lowered = text.lower()
    for pat in _INJECTION:
        if re.search(pat, lowered):
            return "injection"
    if learning_intent(text) == "answer_request":
        return "answer_begging"
    return None


def learning_intent(text: str) -> str:
    """Routing hints only: never treat this heuristic as proof of understanding."""
    lowered = text.lower()
    # Remove negated requests before checking positive requests in the same turn.
    cleaned = re.sub(
        r"\b(?:do not|don't|without|never)\s+(?:give|giving|tell|telling|show|showing)"
        r"\s+me\s+the\s+(?:final\s+)?(?:answer|solution)\b"
        r"|(?:不要|别|不用)\s*(?:直接)?\s*(?:给我|告诉我|提供|给出|说出)?\s*(?:最终)?答案",
        "", lowered,
    )
    if any(re.search(pat, cleaned) for pat in _ANSWER_BEGGING) or re.search(
        r"只(?:输出|返回|说).{0,6}(?:答案|数字|选项)|选哪个|答案呢|\bwhich option\b", cleaned
    ):
        return "answer_request"
    if re.search(r"对吗|是否正确|检查|核对|\b(check|verify)\b|\bis .+ correct\b", cleaned):
        return "verification"
    if re.search(r"不会|不知道|提示|怎么开始|\b(hint|stuck)\b|don't know", cleaned):
        return "help"
    return "discussion"


def answer_in_text(text: str, answer: str) -> bool:
    """Conservative literal evidence, not symbolic equivalence or correctness."""
    needle = _normalize_math(answer)
    candidates = re.findall(r"\$([^$]+)\$", text) + re.split(r"[\s，。；：:=]+", text)
    return bool(needle) and any(_normalize_math(part) == needle for part in candidates)


def deflection_message(category: str, language: str = "en") -> str:
    if language == "zh":
        if category == "injection":
            return (
                "我会继续用相同的循序渐进方式引导你，不能取消教学规则，"
                "但可以帮助你自己推导出答案。你目前对这一步是怎么想的？"
            )
        return (
            "我不会直接给出最终答案，因为亲自推导才能真正掌握。"
            "我们先完成下一个小步骤：你认为应该先尝试什么，为什么？"
        )
    if category == "injection":
        return (
            "I'll keep guiding you the same way throughout. I'm not able to "
            "drop the step-by-step approach, but I'm happy to help you reach "
            "the answer yourself. What's your current thinking on this step?"
        )
    return (
        "I won't hand over the final answer, because working it out yourself "
        "is what makes it stick. Let's take the next small step together: "
        "what do you think we should try first, and why?"
    )


def _normalize_math(text: str) -> str:
    return re.sub(r"[\s$`*_\\{}()\[\],.;:]+", "", text).lower()


def check_output(text: str, final_answer: str,
                 solution_steps: list[str] | None = None,
                 allow_answer: bool = False) -> str | None:
    """Detect likely answer or worked-solution leakage in a tutor reply."""
    answer = _normalize_math(final_answer)
    output = _normalize_math(text)
    if answer and not allow_answer:
        if any(_normalize_math(span) == answer for span in re.findall(r"\$([^$]+)\$", text)):
            return "answer_leak"
        if len(answer) >= 4 and answer in output:
            return "answer_leak"
        if len(answer) < 4:
            escaped = re.escape(final_answer.strip())
            if escaped and re.search(
                rf"(final answer|answer|result|答案|结果|等于|=)\s*(is|为|:)?\s*\$?{escaped}\b",
                text,
                flags=re.IGNORECASE,
            ):
                return "answer_leak"

    for step in solution_steps or []:
        normalized_step = _normalize_math(step)
        if len(normalized_step) >= 30 and normalized_step in output:
            return "worked_solution_leak"
    return None


def engagement_signal(
    text: str,
    elapsed_seconds: float,
    recent_texts: list[str] | None = None,
    hint_streak: int = 0,
) -> str | None:
    """Flag low-evidence progress; this never treats speed alone as cheating."""
    compact = re.sub(r"\s+", "", text)
    normalized = compact.lower()
    if recent_texts and normalized in {
        re.sub(r"\s+", "", item).lower() for item in recent_texts[-3:]
    }:
        return "repeated_response"
    low_information = len(compact) < 12 and not re.search(
        r"[=+\-*/^]|because|since|therefore|因为|所以|由于", text, re.IGNORECASE
    )
    if elapsed_seconds < 4 and low_information:
        return "rapid_low_information"
    if hint_streak >= 2 and re.search(r"hint|提示|不会|不知道|下一步", text, re.IGNORECASE):
        return "repeated_hint_request"
    return None
