"""Practice panel — question rendering and answer payload (no navigation CTAs)."""

from __future__ import annotations

from typing import Any, Callable, Optional

import streamlit as st
from streamlit_sortables import sort_items

from labels import DIFFICULTY_LABELS, DIFFICULTY_ORDER, QUESTION_TYPE_LABELS, QUESTION_TYPES


def _type_label(qtype: str) -> str:
    return QUESTION_TYPE_LABELS.get(qtype, qtype)


def _diff_label(diff: str) -> str:
    return DIFFICULTY_LABELS.get(diff, diff)


def render_practice_panel(
    ss,
    *,
    current_topic: str,
    clean_label,
    on_difficulty_change: Callable[[], None] | None = None,
) -> Optional[dict[str, Any]]:
    """Render practice UI; return grade payload when a question is active."""
    st.markdown("##### Practice")
    st.caption(f"Topic: **{current_topic}**")

    diff_cols = st.columns(3)
    difficulty = ss.get("difficulty", "medium")
    for i, diff in enumerate(DIFFICULTY_ORDER):
        if diff_cols[i].button(
            _diff_label(diff),
            use_container_width=True,
            type="primary" if difficulty == diff else "secondary",
            key=f"diff_{diff}",
        ):
            ss.difficulty = diff
            if ss.question is not None and on_difficulty_change is not None:
                with st.spinner("Generating a new question at this difficulty..."):
                    on_difficulty_change()
            st.rerun()

    qtype = st.selectbox(
        "Question type",
        QUESTION_TYPES,
        index=QUESTION_TYPES.index(ss.get("qtype", "single_choice")),
        format_func=_type_label,
    )
    ss.qtype = qtype

    q = ss.question
    if q is None:
        st.info("Preparing your question… If nothing appears, return to the concept step.")
        return None

    with st.container(border=True):
        st.markdown(f"**{_diff_label(q['difficulty'])} · {_type_label(q['type'])}**")
        st.markdown(q["stem"])
        if q.get("instructions"):
            st.caption(q["instructions"])

        payload: dict[str, Any] = {"question_id": q["id"]}

        if q["type"] == "single_choice":
            choice = st.radio(
                "Select one",
                q["options"],
                index=None,
                format_func=clean_label,
                key=f"single_{q['id']}",
            )
            if choice is not None:
                payload["single"] = q["options"].index(choice)

        elif q["type"] == "multiple_choice":
            st.write("Select all that apply:")
            picked = []
            for i, opt in enumerate(q["options"]):
                if st.checkbox(clean_label(opt), key=f"mc_{q['id']}_{i}"):
                    picked.append(i)
            payload["multiple"] = picked

        elif q["type"] == "fill_blank":
            blanks = []
            for i in range(q.get("n_blanks", 1)):
                blanks.append(st.text_input(f"Blank {i + 1}", key=f"fb_{q['id']}_{i}"))
            payload["blanks"] = blanks

        elif q["type"] == "drag_order":
            st.write("Drag the steps into the correct order:")
            ordered = sort_items(q["steps"], direction="vertical", key=f"drag_{q['id']}")
            payload["order"] = ordered

        if ss.grade is not None:
            if ss.grade["correct"]:
                st.success(ss.grade["feedback"])
            else:
                st.error(ss.grade["feedback"])
                st.caption(f"Correct answer: {ss.grade['correct_answer']}")

        return payload
