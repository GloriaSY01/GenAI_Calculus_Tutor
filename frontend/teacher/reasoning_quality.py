"""Reasoning quality distribution across the class.

The x axis is pinned to the none -> strong order (Streamlit's default bar chart
sorted it alphabetically, which scrambled the scale) and coloured on the same
red-to-green ramp used elsewhere.

Data: `reasoning_distribution` from `GET /analytics/class`.
Optional `explanation_response_rate` (backend, not implemented yet) fills the
small indicator under the chart; it stays hidden while the field is absent.
"""
from __future__ import annotations

from typing import Optional

import altair as alt
import pandas as pd
import streamlit as st

import ui
from i18n import t

LEVELS = ["none", "weak", "partial", "adequate", "strong"]
_LEVEL_COLORS = [ui.DANGER, "#F97316", ui.SECONDARY, "#65A30D", ui.SUCCESS]


def _chart(df: pd.DataFrame) -> alt.Chart:
    return (
        alt.Chart(df)
        .mark_bar(cornerRadiusEnd=6, size=46)
        .encode(
            x=alt.X("level:N", title=t("teacher.axis_level"), sort=LEVELS,
                    axis=alt.Axis(labelAngle=0, labelFontSize=12)),
            y=alt.Y("share:Q", title=t("teacher.axis_share"),
                    axis=alt.Axis(format="%", grid=True)),
            color=alt.Color("level:N", legend=None, sort=LEVELS,
                            scale=alt.Scale(domain=LEVELS, range=_LEVEL_COLORS)),
            tooltip=[alt.Tooltip("level:N", title=t("teacher.axis_level")),
                     alt.Tooltip("share:Q", title=t("teacher.axis_share"), format=".1%")],
        )
        .properties(height=230)
        .configure_view(strokeWidth=0)
        .configure_axis(labelColor=ui.MUTED, titleColor=ui.MUTED, domainColor=ui.BORDER,
                        gridColor="#EEF3FE", titleFontSize=11)
    )


def render_reasoning_panel(distribution: dict, *,
                           explanation_rate: Optional[float] = None) -> None:
    with st.container(border=True):
        ui.panel_header("💬", t("teacher.reasoning_dist"), t("teacher.reasoning_sub"))

        distribution = distribution or {}
        if sum(distribution.values()) <= 0:
            ui.empty_state(t("teacher.no_reasoning_data"))
            return

        df = pd.DataFrame({"level": LEVELS,
                           "share": [distribution.get(lvl, 0) for lvl in LEVELS]})
        st.altair_chart(_chart(df), use_container_width=True)
        st.caption(t("teacher.reasoning_dist_caption"))

        if explanation_rate is not None:
            st.markdown(
                f'<div class="stat-strip" style="grid-template-columns:1fr">'
                f'<div class="stat-item"><span class="stat-label">'
                f'{t("teacher.explain_rate")}</span>'
                f'<span class="stat-value">{round(explanation_rate * 100)}%</span>'
                f'</div></div>',
                unsafe_allow_html=True,
            )
