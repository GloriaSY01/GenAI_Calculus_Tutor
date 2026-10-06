"""Top navigation bar: one section on screen at a time.

The dashboard used to stack every panel on a single page, which made it long
and buried the assignment editor at the bottom. Sections are now switched here,
so only the selected one renders (also meaning one section's widgets never
compete with another's for screen space or state).

Selection lives in `ss.nav_section` so it survives reruns and fragment updates.
"""
from __future__ import annotations

import streamlit as st

import ui
from i18n import t

OVERVIEW = "overview"
DIAGNOSE = "diagnose"
ASSIGN = "assign"
ASSISTANT = "assistant"
DEFAULT = OVERVIEW

# (section key, icon, i18n label key)
SECTIONS = [
    (OVERVIEW, "\U0001f4ca", "teacher.nav_overview"),
    (DIAGNOSE, "\U0001f3af", "teacher.nav_diagnose"),
    (ASSIGN, "\u270f\ufe0f", "teacher.nav_assign"),
    (ASSISTANT, "\U0001f916", "teacher.nav_assistant"),
]


def render_nav(ss) -> str:
    """Draw the nav bar and return the active section key."""
    ss.setdefault("nav_section", DEFAULT)

    cols = st.columns(len(SECTIONS))
    for col, (key, icon, label_key) in zip(cols, SECTIONS):
        is_active = ss.nav_section == key
        if col.button(f"{icon}  {t(label_key)}", key=f"nav_{key}",
                      type="primary" if is_active else "secondary",
                      use_container_width=True):
            ss.nav_section = key
            st.rerun()

    return ss.nav_section


def render_guide(ss) -> None:
    """Landing-page card telling the teacher what each other section holds."""
    hints = [(DIAGNOSE, "\U0001f3af", "teacher.nav_diagnose", "teacher.guide_diagnose"),
             (ASSIGN, "\u270f\ufe0f", "teacher.nav_assign", "teacher.guide_assign"),
             (ASSISTANT, "\U0001f916", "teacher.nav_assistant", "teacher.guide_assistant")]
    with st.container(border=True):
        ui.panel_header("\U0001f9ed", t("teacher.guide_title"), t("teacher.guide_sub"))
        for key, icon, label_key, hint_key in hints:
            st.markdown(
                f'<div class="guide-row"><span class="guide-icon">{icon}</span>'
                f'<span><span class="guide-name">{t(label_key)}</span>'
                f'<span class="guide-hint">{t(hint_key)}</span></span></div>',
                unsafe_allow_html=True,
            )
            if st.button(t("teacher.guide_go").format(name=t(label_key)),
                         key=f"guide_{key}", use_container_width=True):
                ss.nav_section = key
                st.rerun()
