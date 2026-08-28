"""Ask-about-your-class assistant.

A running conversation rather than a single question box: suggestions are
one-click chips, past exchanges stay visible, and the whole panel is a fragment
so asking a question doesn't re-run (and re-fetch) the entire dashboard.

The backend answers one question at a time from the aggregate stats, so the
history here is a client-side transcript, not multi-turn context. A language
hint rides along with each request so answers match the UI language; the
transcript shows the teacher's question as typed.

Injected: `ask_fn(question) -> {"answer": str}`.
"""
from __future__ import annotations

from typing import Callable

import streamlit as st

import ui
from i18n import t


def _suggestions() -> list[str]:
    return [t("teacher.ex1"), t("teacher.ex2"), t("teacher.ex3")]


def _ask(ss, ask_fn: Callable[[str], dict], question: str) -> None:
    ss.assistant_history.append({"role": "user", "content": question})
    offline = False
    try:
        with st.spinner(t("teacher.assistant_thinking")):
            resp = ask_fn(f"{question}\n{t('teacher.lang_hint')}")
        answer = resp["answer"]
        # The backend answers from rules when the model is unreachable; flag it
        # so the same canned summary isn't mistaken for a real reply.
        offline = not resp.get("llm_available", True)
    except Exception as exc:  # noqa: BLE001
        answer = f"{t('common.backend_error')} {exc}"
    ss.assistant_history.append({"role": "assistant", "content": answer,
                                 "offline": offline})


@st.fragment
def render_assistant_panel(ss, *, ask_fn: Callable[[str], dict]) -> None:
    ss.setdefault("assistant_history", [])

    with st.container(border=True):
        ui.panel_header("\U0001f916", t("teacher.ask_heading"),
                        t("teacher.ask_caption"))

        if not ss.assistant_history:
            ui.empty_state(t("teacher.assistant_empty"))
        else:
            # Fixed-height transcript: long conversations scroll here instead
            # of stretching the whole page.
            with st.container(height=320):
                for msg in ss.assistant_history:
                    teacher_avatar = "\U0001f469\u200d\U0001f3eb"
                    avatar = teacher_avatar if msg["role"] == "user" else "\U0001f916"
                    with st.chat_message(msg["role"], avatar=avatar):
                        if msg.get("offline"):
                            st.warning(t("teacher.assistant_offline"))
                        st.markdown(msg["content"])
            if st.button(t("teacher.assistant_clear"), key="assistant_clear"):
                ss.assistant_history = []
                ui.rerun_fragment()

        for i, suggestion in enumerate(_suggestions()):
            if st.button(suggestion, key=f"assistant_sugg_{i}",
                         use_container_width=True):
                _ask(ss, ask_fn, suggestion)
                ui.rerun_fragment()

        with st.form("assistant_form", clear_on_submit=True):
            question = st.text_area(
                t("teacher.your_question"), height=70, label_visibility="collapsed",
                placeholder=t("teacher.assistant_placeholder"),
            )
            sent = st.form_submit_button(t("teacher.ask"), type="primary",
                                         use_container_width=True)
        if sent:
            if question.strip():
                _ask(ss, ask_fn, question.strip())
                ui.rerun_fragment()
            else:
                st.warning(t("teacher.type_first"))
