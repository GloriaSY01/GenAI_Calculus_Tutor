"""Read-only personal favorites view."""

from __future__ import annotations

from typing import Any, Callable

import streamlit as st

from i18n import tr
from labels import difficulty_label, question_type_label


def render_favorites_panel(
    favorites: list[dict[str, Any]],
    *,
    student_id: str,
    on_remove: Callable[[str], None],
    language: str = "en",
) -> None:
    st.markdown(f"##### {tr(language, 'Favorites', '收藏')}")

    if not student_id.strip():
        st.info(
            tr(
                language,
                "Enter your name in the sidebar to view and save personal favorites.",
                "请在侧边栏输入姓名，以查看和保存个人收藏。",
            )
        )
        return

    st.caption(
        tr(
            language,
            "{count} saved question(s)",
            "已收藏 {count} 道题",
            count=len(favorites),
        )
    )
    if not favorites:
        st.info(
            tr(
                language,
                "No favorites yet. Use ☆ on a practice question to save it here.",
                "还没有收藏。可点击练习题上的 ☆ 保存到这里。",
            )
        )
        return

    topics = sorted({item["topic"] for item in favorites})
    selected_topic = st.selectbox(
        tr(language, "Filter by topic", "按主题筛选"),
        [tr(language, "All topics", "全部主题"), *topics],
        key="favorite_topic_filter",
    )
    visible = (
        favorites
        if selected_topic == tr(language, "All topics", "全部主题")
        else [item for item in favorites if item["topic"] == selected_topic]
    )

    for item in visible:
        with st.container(border=True):
            details, remove = st.columns([10, 1])
            qtype = question_type_label(item["type"], language)
            difficulty = difficulty_label(item["difficulty"], language)
            details.markdown(f"**{difficulty} · {qtype}**")
            details.caption(item["topic"])
            if remove.button(
                "★",
                key=f"remove_favorite_{item['question_id']}",
                help=tr(language, "Remove from favorites", "取消收藏"),
            ):
                try:
                    on_remove(item["question_id"])
                except Exception as exc:  # noqa: BLE001
                    st.error(
                        tr(
                            language,
                            "Could not remove favorite: {error}",
                            "无法取消收藏：{error}",
                            error=exc,
                        )
                    )
                else:
                    st.rerun()

            st.markdown(item["stem"])
            if item.get("instructions"):
                st.caption(item["instructions"])
            if item.get("options"):
                for option in item["options"]:
                    st.markdown(f"- {option}")
            elif item.get("steps"):
                for index, step in enumerate(item["steps"], start=1):
                    st.markdown(f"{index}. {step}")
