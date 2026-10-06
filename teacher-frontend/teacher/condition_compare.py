"""Explain vs control comparison — the study's core contrast, on screen.

Data: `by_condition[]` from `GET /analytics/class`. The backend doesn't
aggregate this yet (the condition is in every log line, so it is a small
addition); until it does, the panel renders nothing rather than an empty frame.
"""
from __future__ import annotations

from typing import Optional

import streamlit as st

import ui
from i18n import t

_LABELS = {"explain": "teacher.condition_explain", "control": "teacher.condition_control"}


def _card(row: dict) -> str:
    heading = t(_LABELS.get(row.get("condition", ""), "teacher.condition_control"))
    rows = [
        (t("teacher.kpi_sessions"), row.get("n_sessions", 0)),
        (t("teacher.kpi_solve"), f"{round((row.get('solve_rate') or 0) * 100)}%"),
        (t("teacher.kpi_reasoning"), f"{row.get('avg_reasoning', 0)}/4"),
        (t("teacher.kpi_turns"), row.get("avg_turns_per_session", 0)),
    ]
    body = "".join(f'<div class="mini-row"><span>{k}</span><span>{v}</span></div>'
                   for k, v in rows)
    return f'<div class="mini-card"><div class="mini-head">{heading}</div>{body}</div>'


def render_condition_panel(by_condition: Optional[list[dict]]) -> None:
    if not by_condition:
        return

    with st.container(border=True):
        ui.panel_header("🧪", t("teacher.condition_heading"),
                        t("teacher.condition_sub"))
        cols = st.columns(len(by_condition))
        for col, row in zip(cols, by_condition):
            col.markdown(_card(row), unsafe_allow_html=True)
        st.caption(t("teacher.condition_note"))
