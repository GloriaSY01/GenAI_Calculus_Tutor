"""Practice panel — question rendering and answer payload (no navigation CTAs)."""

from __future__ import annotations

from typing import Any, Callable, Optional

import streamlit as st
from streamlit_sortables import sort_items

from i18n import tr
from labels import DIFFICULTY_ORDER, QUESTION_TYPES, difficulty_label, question_type_label


def _type_label(qtype: str, language: str = "en") -> str:
    return question_type_label(qtype, language)


def _diff_label(diff: str, language: str = "en") -> str:
    return difficulty_label(diff, language)


def render_practice_panel(
    ss,
    *,
    current_topic: str,
    clean_label,
    on_difficulty_change: Callable[[], None] | None = None,
    is_favorite: bool = False,
    can_favorite: bool = False,
    on_favorite_toggle: Callable[[], None] | None = None,
    language: str = "en",
) -> Optional[dict[str, Any]]:
    """Render practice UI; return grade payload when a question is active."""
    st.markdown(f"##### {tr(language, 'Practice', '练习')}")
    st.caption(f"{tr(language, 'Topic', '主题')}：**{current_topic}**")

    diff_cols = st.columns(3)
    difficulty = ss.get("difficulty", "medium")
    for i, diff in enumerate(DIFFICULTY_ORDER):
        if diff_cols[i].button(
            _diff_label(diff, language),
            use_container_width=True,
            type="primary" if difficulty == diff else "secondary",
            key=f"diff_{diff}",
        ):
            ss.difficulty = diff
            if ss.question is not None and on_difficulty_change is not None:
                with st.spinner(
                    tr(
                        language,
                        "Generating a new question at this difficulty...",
                        "正在按此难度生成新题……",
                    )
                ):
                    on_difficulty_change()
            st.rerun()

    qtype = st.selectbox(
        tr(language, "Question type", "题型"),
        QUESTION_TYPES,
        index=QUESTION_TYPES.index(ss.get("qtype", "single_choice")),
        format_func=lambda value: _type_label(value, language),
    )
    ss.qtype = qtype

    q = ss.question
    if q is None:
        st.info(
            tr(
                language,
                "Preparing your question… If nothing appears, return to the concept step.",
                "正在准备题目……如果长时间未显示，请返回概念页。",
            )
        )
        return None

    with st.container(border=True):
        heading, favorite = st.columns([10, 1])
        heading.markdown(
            f"**{_diff_label(q['difficulty'], language)} · "
            f"{_type_label(q['type'], language)}**"
        )
        if favorite.button(
            "★" if is_favorite else "☆",
            key=f"favorite_{q['id']}",
            help=(
                tr(language, "Remove from favorites", "取消收藏") if is_favorite
                else tr(language, "Add to favorites", "加入收藏") if can_favorite
                else tr(language, "Enter your name to save favorites", "输入姓名后可收藏")
            ),
            disabled=not can_favorite,
        ) and on_favorite_toggle is not None:
            try:
                on_favorite_toggle()
            except Exception as exc:  # noqa: BLE001
                st.error(
                    tr(language, "Could not update favorites: {error}", "无法更新收藏：{error}", error=exc)
                )
            else:
                st.rerun()
        st.markdown(q["stem"])
        if q.get("source") == "textbook":
            st.caption(
                tr(
                    language,
                    "Adapted from a verified MIT textbook exercise",
                    "改编自已验证的 MIT 教材练习",
                )
            )
        else:
            st.caption(
                tr(
                    language,
                    "Generated from verified MIT textbook context",
                    "基于已验证的 MIT 教材内容生成",
                )
            )
        if q.get("instructions"):
            st.caption(q["instructions"])
        citations = q.get("citations", [])
        if citations:
            with st.expander(tr(language, "Textbook source", "教材来源")):
                for citation in citations:
                    page = (
                        tr(
                            language,
                            " · page {page}",
                            " · 第 {page} 页",
                            page=citation["page"],
                        )
                        if citation.get("page") else ""
                    )
                    st.markdown(
                        f"- [{citation['title']} — {citation['section']}]"
                        f"({citation['url']}){page}"
                    )

        payload: dict[str, Any] = {"question_id": q["id"]}

        if q["type"] == "single_choice":
            choice = st.radio(
                tr(language, "Select one", "请选择一项"),
                q["options"],
                index=None,
                format_func=clean_label,
                key=f"single_{q['id']}",
            )
            if choice is not None:
                payload["single"] = q["options"].index(choice)

        elif q["type"] == "multiple_choice":
            st.write(tr(language, "Select all that apply:", "请选择所有符合项："))
            picked = []
            for i, opt in enumerate(q["options"]):
                if st.checkbox(clean_label(opt), key=f"mc_{q['id']}_{i}"):
                    picked.append(i)
            payload["multiple"] = picked

        elif q["type"] == "fill_blank":
            blanks = []
            for i in range(q.get("n_blanks", 1)):
                blanks.append(
                    st.text_input(
                        tr(
                            language,
                            "Blank {number}",
                            "第 {number} 空",
                            number=i + 1,
                        ),
                        key=f"fb_{q['id']}_{i}",
                    )
                )
            payload["blanks"] = blanks

        elif q["type"] == "drag_order":
            st.write(
                tr(
                    language,
                    "Drag the steps into the correct order:",
                    "请拖动步骤并排列为正确顺序：",
                )
            )
            ordered = sort_items(q["steps"], direction="vertical", key=f"drag_{q['id']}")
            payload["order"] = ordered

        if ss.grade is not None:
            if ss.grade["correct"]:
                st.success(ss.grade["feedback"])
            else:
                st.error(ss.grade["feedback"])
                st.caption(
                    tr(
                        language,
                        "Attempt {attempt} · The answer stays hidden while you retry.",
                        "第 {attempt} 次尝试 · 重试期间答案仍会隐藏。",
                        attempt=ss.grade.get("attempts", 1),
                    )
                )

        return payload
