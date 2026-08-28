"""Topic health: which topic needs teaching attention next (diagnosis only).

One horizontal bar chart sorted by solve rate (worst on top), colour-coded
red -> amber -> green, with the full table available on demand. Acting on a
weak topic (assigning practice) happens in the Act section, which offers
quick-start chips for the weakest topics.

Sessions that carry no topic (free chat, and — until the backend logs a topic
on session_start — generated-question sessions) land in a catch-all bucket.
That bucket is kept out of the chart and reported as a footnote instead, so it
can never be mistaken for a weak topic.

Data: `by_topic[]` from `GET /analytics/class`.
"""
from __future__ import annotations

import altair as alt
import pandas as pd
import streamlit as st

import ui
from i18n import t, topic_label

UNTIED_TOPICS = {"General / Free chat"}


def _split(by_topic: list[dict]) -> tuple[list[dict], int]:
    tied = [r for r in by_topic if r["topic"] not in UNTIED_TOPICS]
    untied = sum(r["attempts"] for r in by_topic if r["topic"] in UNTIED_TOPICS)
    return tied, untied


def _chart(df: pd.DataFrame) -> alt.LayerChart:
    y = alt.Y("label:N", title=None, sort=alt.SortField("solve_rate", "ascending"),
              axis=alt.Axis(labelLimit=220, labelFontSize=12, labelOverlap=False))
    tooltip = [
        alt.Tooltip("label:N", title=t("teacher.axis_topic")),
        alt.Tooltip("solve_rate:Q", title=t("teacher.axis_solve"), format=".0%"),
        alt.Tooltip("attempts:Q", title=t("teacher.axis_attempts")),
        alt.Tooltip("avg_reasoning:Q", title=t("teacher.axis_reasoning")),
        alt.Tooltip("avg_final_mastery:Q", title=t("teacher.axis_mastery")),
        alt.Tooltip("gaming_rate:Q", title=t("teacher.axis_gaming"), format=".0%"),
    ]
    base = alt.Chart(df)
    # A full-width track keeps every topic row readable even at a 0% solve rate.
    track = base.mark_bar(cornerRadius=6, height=22, color="#EEF3FE").encode(
        y=y, x=alt.X("max_scale:Q", title=t("teacher.axis_solve"),
                     axis=alt.Axis(format="%", grid=False), scale=alt.Scale(domain=[0, 1])),
        tooltip=tooltip,
    )
    bar = base.mark_bar(cornerRadius=6, height=22).encode(
        y=y, x=alt.X("solve_rate:Q", scale=alt.Scale(domain=[0, 1])),
        color=alt.Color("solve_rate:Q", legend=None,
                        scale=alt.Scale(domain=[0, 0.5, 1],
                                        range=[ui.DANGER, ui.SECONDARY, ui.SUCCESS])),
        tooltip=tooltip,
    )
    label = base.mark_text(align="left", dx=6, fontSize=11, color=ui.MUTED).encode(
        y=y, x=alt.X("solve_rate:Q", scale=alt.Scale(domain=[0, 1])),
        text=alt.Text("solve_rate:Q", format=".0%"),
    )
    return (
        alt.layer(track, bar, label)
        .properties(height=max(150, 52 * len(df)))
        .configure_view(strokeWidth=0)
        .configure_axis(labelColor=ui.MUTED, titleColor=ui.MUTED, domainColor=ui.BORDER,
                        gridColor="#EEF3FE", titleFontSize=11)
    )


def render_topic_health_panel(by_topic: list[dict]) -> None:
    with st.container(border=True):
        _render_body(by_topic)


def _render_body(by_topic: list[dict]) -> None:
    ui.panel_header("🎯", t("teacher.topic_health"), t("teacher.topic_health_sub"))

    tied, untied = _split(by_topic or [])
    if not tied:
        ui.empty_state(t("teacher.no_topic_data"))
        return

    df = pd.DataFrame(tied)
    df["label"] = df["topic"].map(topic_label)
    df["max_scale"] = 1.0
    st.altair_chart(_chart(df), use_container_width=True)

    if untied:
        st.caption(t("teacher.free_chat_note").format(n=untied))

    with st.expander(t("teacher.full_table")):
        table = df[["label", "attempts", "solve_rate", "avg_reasoning",
                    "avg_final_mastery", "gaming_rate"]].copy()
        table["solve_rate"] = (table["solve_rate"] * 100).round()
        table["gaming_rate"] = (table["gaming_rate"] * 100).round()
        table = table.rename(columns={
            "label": t("teacher.axis_topic"),
            "attempts": t("teacher.axis_attempts"),
            "solve_rate": t("teacher.axis_solve") + " %",
            "avg_reasoning": t("teacher.axis_reasoning"),
            "avg_final_mastery": t("teacher.axis_mastery"),
            "gaming_rate": t("teacher.axis_gaming") + " %",
        })
        st.dataframe(table, use_container_width=True, hide_index=True)
