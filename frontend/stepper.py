"""Learning-path stage indicator — current step only, no fake completion marks."""

from __future__ import annotations

import streamlit as st

from i18n import tr

STAGE_CONCEPT = "concept"
STAGE_PRACTICE = "practice"
STAGE_TUTOR = "tutor"

_STAGE_INFO = {
    STAGE_CONCEPT: (
        "1. Learn the concept",
        "Select a topic from the sidebar, then continue to practice.",
    ),
    STAGE_PRACTICE: (
        "2. Practice",
        "Choose difficulty and question type, answer, and submit; ask the tutor if stuck.",
    ),
    STAGE_TUTOR: (
        "3. Ask the tutor",
        "Get guided help here; return to practice or the concept when ready.",
    ),
}


def render_stepper(current_stage: str, language: str = "en") -> None:
    label, hint = _STAGE_INFO.get(current_stage, ("", ""))
    zh_info = {
        STAGE_CONCEPT: ("1. 学习概念", "从侧边栏选择小节，然后进入练习。"),
        STAGE_PRACTICE: ("2. 练习", "选择难度和题型并提交答案；遇到困难可询问导师。"),
        STAGE_TUTOR: ("3. 询问导师", "在这里获得引导，准备好后返回练习或概念页。"),
    }
    if language == "zh":
        label, hint = zh_info.get(current_stage, ("", ""))
    st.markdown(
        f'<div style="padding:12px 16px;border-radius:8px;border:1px solid #ddd;'
        f'background:#fafafa;">'
        f"<strong>{tr(language, 'Current', '当前阶段')}：{label}</strong>"
        f'<span style="color:#666;margin-left:12px;">{hint}</span>'
        f"</div>",
        unsafe_allow_html=True,
    )
