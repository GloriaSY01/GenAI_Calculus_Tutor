"""Tutor panel — on-demand guided help (content only, no stage navigation)."""

from __future__ import annotations

import streamlit as st

from quick_prompts import get_quick_prompts


def _context_label(ss, current_topic: str, tutor_entry: str | None) -> str:
    if tutor_entry == "practice" and ss.problem is not None:
        return f"Guiding on current problem · {ss.problem['topic']}"
    if tutor_entry == "concept":
        return f"Concept explanation · {current_topic}"
    return f"Topic · {current_topic}"


def _append_turn(ss, user_text: str, turn: dict):
    ss.messages.append({"role": "user", "content": user_text})
    ss.messages.append({"role": "assistant", "content": turn["tutor_message"]})
    ss.last_turn = turn


def send_preset(ss, send_message, text: str):
    turn = send_message(ss.session_id, text)
    _append_turn(ss, text, turn)
    st.rerun()


def render_tutor_panel(
    ss,
    current_topic: str,
    *,
    tutor_entry: str | None,
    instructor: bool,
    send_message,
):
    st.markdown("##### Calculus tutor")
    st.caption(_context_label(ss, current_topic, tutor_entry))

    with st.container(border=True):
        st.caption("Context")
        st.markdown(f"- **Topic:** {current_topic}")
        if ss.problem is not None:
            st.markdown(f"- **Problem:** {ss.problem['topic']}")
            st.markdown(ss.problem["statement"])
        elif ss.question is not None:
            st.markdown(f"- **Practice:** {ss.question['topic']}")
        st.markdown(f"- **Goal:** Understand {current_topic} and related problem-solving ideas")

    if instructor:
        cols = st.columns(4)
        cols[0].metric("Condition", ss.condition)
        if ss.last_turn:
            cols[1].metric("Mastery", ss.last_turn["mastery"])
            cols[2].metric("Hint level", ss.last_turn["hint_level"])
            cols[3].metric("Reasoning", ss.last_turn["reasoning_assessment"].title())
        st.caption(f"session_id: {ss.session_id}")
    else:
        mastery = ss.last_turn["mastery"] if ss.last_turn else 0
        st.progress(min(mastery, 100) / 100, text=f"Progress: {min(mastery, 100)}%")
        st.caption(
            "Based on your reasoning in this tutor session "
            "(not your practice score)."
        )

    if ss.last_turn and ss.last_turn["is_solved"]:
        st.success("Well done — you reached the answer yourself.")
    elif ss.last_turn and ss.last_turn["action"] == "blocked":
        st.info("Let's work through this step by step rather than jumping to the answer.")

    st.divider()
    for msg in ss.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    quick_prompts = get_quick_prompts(
        current_topic=current_topic,
        tutor_entry=tutor_entry,
        last_turn=ss.last_turn,
        has_problem=ss.problem is not None,
    )
    if quick_prompts:
        st.caption("Suggested prompts")
        for row_start in range(0, len(quick_prompts), 2):
            row = quick_prompts[row_start : row_start + 2]
            cols = st.columns(len(row))
            for col, prompt in zip(cols, row):
                if col.button(prompt.label, use_container_width=True, key=prompt.key):
                    send_preset(ss, send_message, prompt.message)

    with st.form("tutor_input", clear_on_submit=True):
        text = st.text_area(
            "Your reasoning or next step",
            height=80,
            label_visibility="collapsed",
            placeholder="Describe your reasoning or where you are stuck...",
        )
        sent = st.form_submit_button("Send", type="primary")
    if sent and text.strip():
        try:
            send_preset(ss, send_message, text.strip())
        except Exception as exc:  # noqa: BLE001
            st.error(f"Could not send message: {exc}")
