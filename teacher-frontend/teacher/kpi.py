"""Class overview KPIs.

Four decision-driving numbers get large cards; lower-frequency indicators sit
in a compact strip below so the eye lands on what matters first.

Data: the `GET /analytics/class` payload.
Optional field `n_sim_sessions` (backend, not implemented yet) drives the
"simulated data" badge; the badge stays hidden while the field is absent.
"""
from __future__ import annotations

import streamlit as st

from i18n import t


def _pct(value) -> str:
    return f"{round((value or 0) * 100)}%"


def render_kpi_panel(data: dict) -> None:
    n_sim = data.get("n_sim_sessions") or 0
    if n_sim:
        st.warning(t("teacher.badge_sim").format(n=n_sim))

    c1, c2, c3, c4 = st.columns(4)
    c1.metric(t("teacher.kpi_students"), f"{data.get('n_students', 0)}",
              help=t("teacher.kpi_students_sub"))
    c2.metric(t("teacher.kpi_practice_submissions"),
              f"{data.get('practice_submission_count', 0)}",
              help=t("teacher.kpi_practice_submissions_help"))
    c3.metric(t("teacher.kpi_independent_solve"),
              _pct(data.get("independent_solve_rate")),
              help=t("teacher.kpi_independent_solve_help"))
    c4.metric(t("teacher.kpi_ai_assisted_solve"),
              _pct(data.get("ai_assisted_solve_rate")),
              help=t("teacher.kpi_ai_assisted_solve_help"))
