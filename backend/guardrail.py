"""Lightweight input guardrail.

This is intentionally minimal for the demo: it flags obvious attempts to
extract the final answer outright or to override the tutor's instructions
(prompt injection). A production version would use a classifier.
"""
import re

# Patterns that strongly suggest "just give me the answer" or jailbreak.
_ANSWER_BEGGING = [
    r"\bjust (give|tell) me the (answer|solution)\b",
    r"\bwhat('?s| is) the (final )?answer\b",
    r"\bgive me the (full |complete )?(answer|solution)\b",
    r"\btell me the (answer|result)\b",
    r"\bsolve it for me\b",
    r"\bskip the (hints?|explanation)\b",
]

_INJECTION = [
    r"\bignore (all |the )?(previous |above )?instructions?\b",
    r"\byou are now\b",
    r"\bdisregard .* (rules?|instructions?)\b",
    r"\bpretend you are\b",
    r"\bact as if\b.*\b(answer|solution)\b",
    r"\bsystem prompt\b",
]


def check_input(text: str) -> str | None:
    """Return a guardrail category if triggered, else None."""
    lowered = text.lower()
    for pat in _INJECTION:
        if re.search(pat, lowered):
            return "injection"
    for pat in _ANSWER_BEGGING:
        if re.search(pat, lowered):
            return "answer_begging"
    return None


def deflection_message(category: str) -> str:
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
