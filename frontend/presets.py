"""Preset tutor messages (sent via existing /session/{id}/message API)."""

from i18n import tr


def explain_concept(topic: str, language: str = "en") -> str:
    return tr(
        language,
        "Please explain the concept of {topic} in clear terms: what problem it "
        "addresses, and give a simple example. Do not jump straight to complex exercises.",
        "请清楚解释 {topic}：它解决什么问题，并给出一个简单例子。暂时不要进入复杂练习。",
        topic=topic,
    )


def hint_first_step(language: str = "en") -> str:
    return tr(language, "Please hint at the first step for this problem without giving the full answer.", "请提示这道题的第一步，但不要给出完整答案。")


def why_this_method(language: str = "en") -> str:
    return tr(language, "I do not understand why we use this approach. Can you explain the underlying idea?", "我不明白为什么要使用这个方法。能解释一下背后的思想吗？")


def still_confused(language: str = "en") -> str:
    return tr(language, "I am still confused. Could you explain it again in simpler terms?", "我还是不太明白。可以用更简单的方式再解释一次吗？")


def need_guidance(language: str = "en") -> str:
    return tr(
        language,
        "I am stuck on this problem. Please guide me from the first step. You may ask me questions, but do not give the complete answer.",
        "我卡在这道题上了。请从第一步开始引导我，可以向我提问，但不要给出完整答案。",
    )


def small_hint(language: str = "en") -> str:
    return tr(language, "Please give me a small hint without revealing the answer.", "请给我一个小提示，但不要透露答案。")


def tutor_first_step(language: str = "en") -> str:
    return tr(language, "Please walk me through the first step and help me think it through myself.", "请引导我完成第一步，并帮助我自己思考。")


def got_it(language: str = "en") -> str:
    return tr(language, "I understand now. Thank you.", "我现在明白了，谢谢。")


def more_hint(language: str = "en") -> str:
    return tr(language, "Could you give me a bit more of a hint?", "可以再给我一点提示吗？")


def explain_after_correct(language: str = "en") -> str:
    return tr(
        language,
        "I selected the correct answer, but I am not sure why. Please walk me through the reasoning for this problem without just stating the answer.",
        "我选对了答案，但不确定原因。请引导我理解这道题的推理过程，不要只陈述答案。",
    )


def give_example(topic: str, language: str = "en") -> str:
    return tr(language, "Please give a simple worked example for {topic}.", "请为 {topic} 给出一个简单的例题。", topic=topic)


def common_mistakes(topic: str, language: str = "en") -> str:
    return tr(language, "What are common mistakes students make with {topic}?", "学习 {topic} 时有哪些常见错误？", topic=topic)


def how_used_in_problems(topic: str, language: str = "en") -> str:
    return tr(language, "How is {topic} typically used when solving calculus problems?", "解微积分题时通常如何使用 {topic}？", topic=topic)


def check_my_reasoning(language: str = "en") -> str:
    return tr(
        language,
        "Here is my reasoning so far — please tell me if I am on the right track and what I should think about next.",
        "这是我目前的推理。请告诉我方向是否正确，以及下一步应该思考什么。",
    )


def why_this_step(language: str = "en") -> str:
    return tr(language, "Why is this the right step at this point in the problem?", "为什么这是当前正确的一步？")


def offer_reasoning(language: str = "en") -> str:
    return tr(
        language,
        "Here is my reasoning: I think the first step is to identify what the problem is asking. Please tell me if my approach makes sense.",
        "这是我的推理：我认为第一步是确认题目要求什么。请告诉我这个思路是否合理。",
    )


def explain_full_solution(language: str = "en") -> str:
    return tr(
        language,
        "Please walk me through the full solution step by step, focusing on the reasoning rather than only the final answer.",
        "请逐步引导我理解完整解法，重点说明推理过程，而不只是最终答案。",
    )
