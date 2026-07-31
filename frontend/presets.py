"""Preset tutor messages (sent via existing /session/{id}/message API)."""


def explain_concept(topic: str) -> str:
    return (
        f"Please explain the concept of {topic} in clear terms: "
        "what problem it addresses, and give a simple example. "
        "Do not jump straight to complex exercises."
    )


def hint_first_step() -> str:
    return "Please hint at the first step for this problem without giving the full answer."


def why_this_method() -> str:
    return "I do not understand why we use this approach. Can you explain the underlying idea?"


def still_confused() -> str:
    return "I am still confused. Could you explain it again in simpler terms?"


def need_guidance() -> str:
    return (
        "I am stuck on this problem. Please guide me from the first step. "
        "You may ask me questions, but do not give the complete answer."
    )


def small_hint() -> str:
    return "Please give me a small hint without revealing the answer."


def tutor_first_step() -> str:
    return "Please walk me through the first step and help me think it through myself."


def got_it() -> str:
    return "I understand now. Thank you."


def more_hint() -> str:
    return "Could you give me a bit more of a hint?"


def explain_after_correct() -> str:
    return (
        "I selected the correct answer, but I am not sure why. "
        "Please walk me through the reasoning for this problem without just stating the answer."
    )


def give_example(topic: str) -> str:
    return f"Please give a simple worked example for {topic}."


def common_mistakes(topic: str) -> str:
    return f"What are common mistakes students make with {topic}?"


def how_used_in_problems(topic: str) -> str:
    return f"How is {topic} typically used when solving calculus problems?"


def check_my_reasoning() -> str:
    return (
        "Here is my reasoning so far — please tell me if I am on the right track "
        "and what I should think about next."
    )


def why_this_step() -> str:
    return "Why is this the right step at this point in the problem?"


def offer_reasoning() -> str:
    return (
        "Here is my reasoning: I think the first step is to identify what the "
        "problem is asking. Please tell me if my approach makes sense."
    )


def explain_full_solution() -> str:
    return (
        "Please walk me through the full solution step by step, "
        "focusing on the reasoning rather than only the final answer."
    )
