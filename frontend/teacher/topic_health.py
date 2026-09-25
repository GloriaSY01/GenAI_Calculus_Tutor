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

import html

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


def _demo_rows() -> list[dict]:
    return [
        {
            "topic": t("teacher.demo_topic_limits"),
            "attempts": 18,
            "avg_reasoning": 1.4,
            "solve_rate": 0.32,
            "avg_final_mastery": 38,
            "gaming_rate": 0.18,
        },
        {
            "topic": t("teacher.demo_topic_derivatives"),
            "attempts": 15,
            "avg_reasoning": 2.1,
            "solve_rate": 0.58,
            "avg_final_mastery": 62,
            "gaming_rate": 0.08,
        },
        {
            "topic": t("teacher.demo_topic_chain_rule"),
            "attempts": 11,
            "avg_reasoning": 2.8,
            "solve_rate": 0.74,
            "avg_final_mastery": 76,
            "gaming_rate": 0.04,
        },
    ]


def _render_solve_rate_help() -> None:
    label = html.escape(t("teacher.axis_solve"))
    help_text = html.escape(t("teacher.axis_solve_help"), quote=True)
    st.markdown(
        f"""
        <div class="topic-health-help" style="position:relative;display:inline-flex;align-items:center;
             gap:8px;font-size:1rem;font-weight:600;color:{ui.FG};
             margin:0.35rem 0 -0.1rem;">
          {label}
          <span style="
            position:relative;display:inline-flex;align-items:center;
            justify-content:center;">
            <span style="
            display:inline-flex;align-items:center;justify-content:center;
            width:18px;height:18px;border-radius:999px;
            border:1.5px solid #6B7280;color:#6B7280;font-size:12px;
            font-weight:700;line-height:18px;vertical-align:middle;
            cursor:default;">?</span>
            <span style="
              visibility:hidden;opacity:0;position:absolute;left:50%;
              bottom:30px;transform:translateX(-50%);min-width:360px;
              max-width:520px;background:#FFFFFF;color:{ui.FG};
              border:1px solid {ui.BORDER};border-radius:12px;
              padding:12px 14px;box-shadow:0 8px 24px rgba(15,23,42,.16);
              font-size:0.9rem;font-weight:400;line-height:1.45;
              z-index:9999;transition:opacity .12s ease;">
              {help_text}
            </span>
          </span>
        </div>
        <style>
        .topic-health-help > span:hover > span:last-child {{
          visibility: visible !important;
          opacity: 1 !important;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


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
                        scale=alt.Scale(domain=[0, 0.55, 1],
                                        range=["#E76F51", "#E9C46A", "#2A9D55"])),
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
        message = (
            t("teacher.only_free_chat_data").format(n=untied)
            if untied
            else t("teacher.no_topic_data")
        )
        ui.empty_state(message)
        st.caption(t("teacher.topic_health_demo_note"))
        demo_df = pd.DataFrame(_demo_rows())
        demo_df["label"] = demo_df["topic"]
        demo_df["max_scale"] = 1.0
        _render_solve_rate_help()
        st.altair_chart(_chart(demo_df), use_container_width=True)
        return

    df = pd.DataFrame(tied)
    df["label"] = df["topic"].map(topic_label)
    df["max_scale"] = 1.0
    _render_solve_rate_help()
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
