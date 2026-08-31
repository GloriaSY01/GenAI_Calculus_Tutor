"""Student-facing copy and label mappings."""

from i18n import tr

QUESTION_TYPE_LABELS = {
    "single_choice": "Single choice",
    "multiple_choice": "Multiple choice",
    "fill_blank": "Fill in the blank",
    "drag_order": "Order the steps",
}

DIFFICULTY_LABELS = {
    "easy": "Basic",
    "medium": "Intermediate",
    "hard": "Advanced",
}

DIFFICULTY_ORDER = ["easy", "medium", "hard"]

QUESTION_TYPES = list(QUESTION_TYPE_LABELS.keys())

_QUESTION_TYPE_ZH = {
    "single_choice": "单选题",
    "multiple_choice": "多选题",
    "fill_blank": "填空题",
    "drag_order": "步骤排序",
}

_DIFFICULTY_ZH = {
    "easy": "基础",
    "medium": "进阶",
    "hard": "挑战",
}


def question_type_label(value: str, language: str = "en") -> str:
    return tr(
        language,
        QUESTION_TYPE_LABELS.get(value, value),
        _QUESTION_TYPE_ZH.get(value, value),
    )


def difficulty_label(value: str, language: str = "en") -> str:
    return tr(
        language,
        DIFFICULTY_LABELS.get(value, value),
        _DIFFICULTY_ZH.get(value, value),
    )
