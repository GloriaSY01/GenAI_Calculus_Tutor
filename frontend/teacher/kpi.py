"""Class overview KPIs.

Four decision-driving numbers get large cards; lower-frequency indicators sit
in a compact strip below so the eye lands on what matters first.

Data: the `GET /analytics/class` payload.
Optional field `n_sim_sessions` (backend, not implemented yet) drives the
"simulated data" badge; the badge stays hidden while the field is absent.
"""
from __future__ import annotations

import streamlit as st

import ui
from i18n import t


def _pct(value) -> str:
    return f"{round((value or 0) * 100)}%"


def _card(label: str, value: str, sub: str, accent: str) -> str:
    return (f'<div class="kpi-card" style="--accent:{accent}">'
            f'<div class="kpi-label">{label}</div>'
            f'<div class="kpi-value">{value}</div>'
            f'<div class="kpi-sub">{sub}</div></div>')


def _stat(label: str, value: str, tooltip: str) -> str:
    return (f'<div class="stat-item" title="{tooltip}">'
            f'<span class="stat-label">{label}</span>'
            f'<span class="stat-value">{value}</span></div>')


def render_kpi_panel(data: dict) -> None:
    n_sim = data.get("n_sim_sessions") or 0
    if n_sim:
        st.markdown(
            f'<span class="badge badge-warn">'
            f'{t("teacher.badge_sim").format(n=n_sim)}</span>',
            unsafe_allow_html=True,
        )

    cards = "".join([
        _card(t("teacher.kpi_solve"), _pct(data.get("solve_rate")),
              t("teacher.kpi_solve_sub"), ui.PRIMARY),
        _card(t("teacher.kpi_mastery"), f"{data.get('avg_final_mastery', 0)}",
              t("teacher.kpi_mastery_sub"), ui.SUCCESS),
        _card(t("teacher.kpi_students"), f"{data.get('n_students', 0)}",
              t("teacher.kpi_students_sub"), ui.SECONDARY),
        _card(t("teacher.kpi_sessions"), f"{data.get('n_sessions', 0)}",
              t("teacher.kpi_sessions_sub").format(n=data.get("n_turns", 0)),
              ui.MUTED),
    ])
    st.markdown(f'<div class="kpi-grid">{cards}</div>', unsafe_allow_html=True)

    stats = "".join([
        _stat(t("teacher.kpi_reasoning"), f"{data.get('avg_reasoning', 0)}/4",
              t("teacher.kpi_reasoning_help")),
        _stat(t("teacher.kpi_turns"), f"{data.get('avg_turns_per_session', 0)}", ""),
        _stat(t("teacher.kpi_gaming"), _pct(data.get("gaming_rate")),
              t("teacher.kpi_gaming_help")),
        _stat(t("teacher.kpi_guardrail"), _pct(data.get("guardrail_rate")),
              t("teacher.kpi_guardrail_help")),
    ])
    st.markdown(
        f'<div style="margin-top:14px" class="panel-sub">{t("teacher.more_metrics")}'
        f'</div><div class="stat-strip" style="margin-top:2px">{stats}</div>',
        unsafe_allow_html=True,
    )
