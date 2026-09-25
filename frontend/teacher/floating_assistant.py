"""Floating teacher assistant drawer.

The dashboard remains the source of truth; this helper is an on-demand layer
for explaining charts and suggesting next teaching actions.
"""
from __future__ import annotations

from typing import Callable

import streamlit as st

import ui
from i18n import current_lang, t


def _suggestions() -> list[str]:
    return [
        t("teacher.float_ai_explain"),
        t("teacher.float_ai_next"),
        t("teacher.float_ai_practice"),
        t("teacher.float_ai_ai_help"),
    ]


def _ask(ss, ask_fn: Callable[..., dict], question: str) -> None:
    history = list(ss.floating_assistant_history)
    ss.floating_assistant_history.append({"role": "user", "content": question})
    offline = False
    try:
        with st.spinner(t("teacher.assistant_thinking")):
            resp = ask_fn(
                question,
                class_id=ss.get("class_id"),
                language=current_lang(),
                history=history,
            )
        answer = resp["answer"]
        offline = not resp.get("llm_available", True)
    except Exception as exc:  # noqa: BLE001
        answer = f"{t('common.backend_error')} {exc}"
    ss.floating_assistant_history.append({
        "role": "assistant",
        "content": answer,
        "offline": offline,
    })


def is_open(ss) -> bool:
    requested = st.query_params.get("ai")
    if requested == "open":
        ss.teacher_ai_drawer_open = True
    elif requested == "closed":
        ss.teacher_ai_drawer_open = False
    return bool(ss.get("teacher_ai_drawer_open", False))


def _css() -> None:
    st.markdown(
        f"""
        <style>
        .teacher-ai-launcher {{
          position: fixed;
          right: 28px;
          bottom: 28px;
          z-index: 9999;
          display: flex;
          align-items: center;
          gap: 10px;
          padding: 14px 18px;
          border-radius: 999px;
          background: {ui.FG};
          color: #FFFFFF !important;
          text-decoration: none !important;
          font-weight: 700;
          box-shadow: 0 14px 34px rgba(15, 23, 42, .24);
          border: 1px solid rgba(255, 255, 255, .24);
        }}
        .teacher-ai-launcher span:first-child {{
          display: grid;
          place-items: center;
          width: 28px;
          height: 28px;
          border-radius: 999px;
          background: rgba(255, 255, 255, .16);
        }}
        .stApp:has(.teacher-ai-frame-marker) [data-testid="stMainBlockContainer"] {{
          width: calc(100vw - 380px) !important;
          max-width: calc(100vw - 380px) !important;
          box-sizing: border-box !important;
          margin-left: 0 !important;
          margin-right: 380px !important;
          padding-left: 2rem !important;
          padding-right: 1.25rem !important;
        }}
        .stApp:has(.teacher-ai-frame-marker) [data-testid="stSidebar"],
        .stApp:has(.teacher-ai-frame-marker) button[kind="header"] {{
          display: none !important;
        }}
        .stApp:has(.teacher-ai-frame-marker) [data-testid="stAppViewBlockContainer"],
        .stApp:has(.teacher-ai-frame-marker) [data-testid="stMain"] {{
          margin-left: 0 !important;
        }}
        .teacher-ai-frame {{
          position: fixed;
          top: 0;
          right: 0;
          bottom: 0;
          width: min(340px, calc(100vw - 24px));
          height: 100vh;
          z-index: 10000;
          border: 0;
          background: #FFFFFF;
          box-shadow: -18px 0 44px rgba(15, 23, 42, .14) !important;
        }}
        .teacher-ai-head {{
          display: flex;
          align-items: flex-start;
          justify-content: space-between;
          gap: 14px;
          margin-bottom: 14px;
        }}
        .teacher-ai-kicker {{
          color: {ui.PRIMARY};
          font-size: .72rem;
          font-weight: 800;
          letter-spacing: .12em;
          text-transform: uppercase;
        }}
        .teacher-ai-title {{
          color: {ui.FG};
          font-size: 1.18rem;
          font-weight: 800;
          margin-top: 2px;
        }}
        .teacher-ai-sub {{
          color: {ui.MUTED};
          font-size: .86rem;
          line-height: 1.55;
          margin-top: 5px;
        }}
        .teacher-ai-close {{
          flex: 0 0 auto;
          display: grid;
          place-items: center;
          width: 30px;
          height: 30px;
          border-radius: 999px;
          border: 1px solid {ui.BORDER};
          color: {ui.MUTED} !important;
          text-decoration: none !important;
          font-weight: 800;
          background: #FFFFFF;
        }}
        div[data-testid="stVerticalBlockBorderWrapper"]:has(.teacher-ai-drawer-marker)
        div[data-testid="stChatMessage"] {{
          box-shadow: none;
        }}
        div[data-testid="stVerticalBlockBorderWrapper"]:has(.teacher-ai-drawer-marker)
        .stButton > button {{
          min-height: 40px;
          text-align: left;
        }}
        @media (max-width: 720px) {{
          .stApp:has(.teacher-ai-frame-marker) [data-testid="stMainBlockContainer"] {{
            width: 100% !important;
            max-width: 100% !important;
            margin-right: 0 !important;
            padding-right: 1rem !important;
          }}
          .teacher-ai-launcher {{
            right: 16px;
            bottom: 16px;
            padding: 12px 14px;
          }}
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_launcher(ss) -> None:
    ss.setdefault("floating_assistant_history", [])
    ss.setdefault("teacher_ai_drawer_open", False)
    _css()
    lang = current_lang()
    class_id = ss.get("class_id", "")
    st.markdown(
        f"""
        <a class="teacher-ai-launcher" href="?ai=open&lang={lang}&class_id={class_id}" target="_self">
          <span>✦</span><span>{t("teacher.float_ai_button")}</span>
        </a>
        """,
        unsafe_allow_html=True,
    )


def render_drawer(
    ss,
    *,
    ask_fn: Callable[..., dict],
    show_close: bool = True,
) -> None:
    ss.setdefault("floating_assistant_history", [])
    ss.setdefault("teacher_ai_drawer_open", False)
    _css()
    with st.container(border=True):
        st.markdown('<span class="teacher-ai-drawer-marker"></span>',
                    unsafe_allow_html=True)
        lang = current_lang()
        class_id = ss.get("class_id", "")
        close = (
            f'<a class="teacher-ai-close" href="?ai=closed&lang={lang}&class_id={class_id}" '
            'target="_parent">×</a>'
            if show_close else ""
        )
        st.markdown(
            f"""
            <div class="teacher-ai-head">
              <div>
                <div class="teacher-ai-kicker">{t("teacher.float_ai_kicker")}</div>
                <div class="teacher-ai-title">{t("teacher.float_ai_title")}</div>
                <div class="teacher-ai-sub">{t("teacher.float_ai_sub")}</div>
              </div>
              {close}
            </div>
            """,
            unsafe_allow_html=True,
        )

        if ss.floating_assistant_history:
            with st.container(height=300):
                for msg in ss.floating_assistant_history:
                    with st.chat_message(msg["role"]):
                        if msg.get("offline"):
                            st.warning(t("teacher.assistant_offline"))
                        st.markdown(msg["content"])

        st.caption(t("teacher.float_ai_try"))
        for i, suggestion in enumerate(_suggestions()):
            if st.button(suggestion, key=f"floating_assistant_sugg_{i}",
                         use_container_width=True):
                _ask(ss, ask_fn, suggestion)
                st.rerun()

        with st.form("floating_assistant_form", clear_on_submit=True):
            question = st.text_area(
                t("teacher.your_question"),
                height=82,
                label_visibility="collapsed",
                placeholder=t("teacher.float_ai_placeholder"),
            )
            sent = st.form_submit_button(t("teacher.ask"), type="primary",
                                         use_container_width=True)

        if sent:
            if question.strip():
                _ask(ss, ask_fn, question.strip())
                st.rerun()
            else:
                st.warning(t("teacher.type_first"))

        if ss.floating_assistant_history:
            if st.button(t("teacher.assistant_clear"),
                         key="floating_assistant_clear",
                         use_container_width=True):
                ss.floating_assistant_history = []
                st.rerun()


def render_iframe_drawer() -> None:
    _css()
    lang = current_lang()
    class_id = st.session_state.get("class_id", "")
    st.markdown(
        f"""
        <span class="teacher-ai-frame-marker"></span>
        <iframe class="teacher-ai-frame" src="?assistant_only=1&lang={lang}&class_id={class_id}"></iframe>
        """,
        unsafe_allow_html=True,
    )


def render(ss, *, ask_fn: Callable[..., dict]) -> None:
    if is_open(ss):
        render_drawer(ss, ask_fn=ask_fn)
    else:
        render_launcher(ss)
