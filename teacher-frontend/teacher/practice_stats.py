"""Practice accuracy by AI-use condition, separate from tutor solve rate.

Every `/grade` submission is counted, including retries. For each difficulty,
accuracy is calculated independently for submissions made without the AI
Companion and submissions made after using it.

Data:
    practice: {
        n_answers,
        correct_rate,
        by_topic: [
            {
                topic,
                attempts,
                correct_rate,
                independent_submissions,
                ai_assisted_submissions,
                independent_correct_count,
                ai_assisted_correct_count,
                independent_count,
                ai_assisted_count,
                not_correct_count,
                independent_rate,
                ai_assisted_rate,
            }
        ],
    }
"""
from __future__ import annotations

from typing import Optional

import altair as alt
import pandas as pd
import streamlit as st

import ui
from i18n import difficulty_label, t, topic_label


def render_practice_stats_panel(
    practice: Optional[dict],
    *,
    embedded: bool = False,
    catalog: Optional[dict] = None,
) -> None:
    if embedded:
        _render_body(practice, show_header=False, catalog=catalog)
        return

    with st.container(border=True):
        _render_body(practice, show_header=True, catalog=catalog)


def _render_body(
    practice: Optional[dict],
    *,
    show_header: bool = True,
    catalog: Optional[dict] = None,
) -> None:
    if show_header:
        ui.panel_header("📝", t("teacher.practice_stats"), t("teacher.practice_stats_sub"))

    if not practice:
        practice = {}

    has_real_practice = (
        int(practice.get("n_answers", 0) or 0) > 0
        and bool(practice.get("by_difficulty_completion"))
    )
    if not has_real_practice:
        st.info(t("teacher.practice_demo_note"))
        practice = _demo_practice()

    st.markdown(f"**{t('teacher.practice_difficulty_chart')}**")
    st.caption(t("teacher.practice_difficulty_chart_sub"))
    _render_difficulty_chart(practice.get("by_difficulty_completion") or [])

    _render_topic_selector(practice.get("practice_by_topic") or [], catalog)


def _demo_practice() -> dict:
    return {
        "practice_completion_modes": [
            {"mode": "independent", "count": 18},
            {"mode": "ai_assisted", "count": 14},
        ],
        "by_difficulty_completion": [
            {"difficulty": "easy", "independent_rate": 0.78, "ai_assisted_rate": 0.64,
             "independent_submissions": 9, "ai_assisted_submissions": 5, "attempts": 14},
            {"difficulty": "medium", "independent_rate": 0.62, "ai_assisted_rate": 0.58,
             "independent_submissions": 8, "ai_assisted_submissions": 7, "attempts": 15},
            {"difficulty": "hard", "independent_rate": 0.41, "ai_assisted_rate": 0.49,
             "independent_submissions": 6, "ai_assisted_submissions": 8, "attempts": 14},
        ],
        "practice_completion_trend": [
            {"date": t("teacher.week_label").format(n=1), "independent_rate": 0.45, "ai_assisted_rate": 0.20, "attempts": 10},
            {"date": t("teacher.week_label").format(n=2), "independent_rate": 0.52, "ai_assisted_rate": 0.24, "attempts": 12},
            {"date": t("teacher.week_label").format(n=3), "independent_rate": 0.58, "ai_assisted_rate": 0.28, "attempts": 16},
        ],
        "practice_by_topic": [],
    }


def _rate_to_percent(value) -> int:
    value = value or 0
    if value <= 1:
        value *= 100
    return round(value)


def _format_rate(value) -> str:
    if value is None:
        return t("teacher.practice_topic_no_data_value")
    return f"{_rate_to_percent(value)}%"


def _catalog_topic_titles(catalog: Optional[dict]) -> list[str]:
    if not catalog:
        return []
    return [
        section["title"]
        for chapter in catalog.get("chapters", [])
        for section in chapter.get("sections", [])
        if section.get("title")
    ]


def _render_topic_selector(rows: list[dict], catalog: Optional[dict]) -> None:
    all_topics = _catalog_topic_titles(catalog)
    df = pd.DataFrame(rows)
    st.markdown(f"**{t('teacher.practice_topic_table')}**")

    if df.empty:
        stats_by_topic = {}
    else:
        df["topic_label"] = df["topic"].map(topic_label)
        df["score_percent"] = df["correct_rate"].map(_rate_to_percent)
        df = df.sort_values(["score_percent", "attempts"], ascending=[True, False])
        stats_by_topic = {
            row["topic"]: row
            for row in df.to_dict("records")
        }

    if not all_topics:
        all_topics = df["topic"].tolist()
    topics = list(dict.fromkeys(all_topics + list(stats_by_topic)))

    default_topic = df.iloc[0]["topic"] if not df.empty else topics[0]
    default_index = topics.index(default_topic) if default_topic in topics else 0
    selected_topic = st.selectbox(
        t("teacher.practice_topic_filter"),
        topics,
        index=default_index,
        format_func=lambda topic: topic_label(topic),
        key="practice_topic_filter",
    )
    selected = stats_by_topic.get(selected_topic, {})

    st.caption(f"{t('teacher.practice_topic_selected')}: {topic_label(selected_topic)}")

    attempts = int(selected.get("attempts", 0))
    correct_rate = selected.get("correct_rate") if selected else None
    independent_rate = selected.get("independent_rate") if selected else None
    ai_assisted_rate = selected.get("ai_assisted_rate") if selected else None

    c1, c2, c3, c4 = st.columns(4)
    c1.metric(
        t("teacher.practice_topic_submissions"),
        f"{attempts}",
        help=t("teacher.practice_topic_submissions_help"),
    )
    c2.metric(
        t("teacher.practice_topic_correct_rate"),
        _format_rate(correct_rate),
        help=t("teacher.practice_topic_correct_rate_help"),
    )
    c3.metric(
        t("teacher.practice_topic_independent_rate"),
        _format_rate(independent_rate),
        help=t("teacher.practice_topic_independent_rate_help"),
    )
    c4.metric(
        t("teacher.practice_topic_ai_assisted_rate"),
        _format_rate(ai_assisted_rate),
        help=t("teacher.practice_topic_ai_assisted_rate_help"),
    )


def _render_difficulty_chart(rows: list[dict]) -> None:
    if not rows:
        ui.empty_state(t("teacher.practice_empty"))
        return

    df = pd.DataFrame(rows)
    if df.empty:
        ui.empty_state(t("teacher.practice_empty"))
        return

    df["difficulty_label"] = df["difficulty"].map(difficulty_label)
    chart_df = df.melt(
        id_vars=[
            "difficulty",
            "difficulty_label",
            "attempts",
            "independent_submissions",
            "ai_assisted_submissions",
        ],
        value_vars=["independent_rate", "ai_assisted_rate"],
        var_name="mode",
        value_name="rate",
    )
    chart_df["mode"] = chart_df["mode"].map({
        "independent_rate": t("teacher.practice_independent"),
        "ai_assisted_rate": t("teacher.practice_ai_assisted"),
    })
    chart_df["submission_count"] = chart_df.apply(
        lambda row: (
            row["independent_submissions"]
            if row["mode"] == t("teacher.practice_independent")
            else row["ai_assisted_submissions"]
        ),
        axis=1,
    )
    chart_df["rate_label"] = (chart_df["rate"] * 100).round().astype(int).astype(str) + "%"

    order = [difficulty_label("easy"), difficulty_label("medium"), difficulty_label("hard"),
             difficulty_label("unknown")]
    mode_order = [t("teacher.practice_independent"), t("teacher.practice_ai_assisted")]
    bars = (
        alt.Chart(chart_df)
        .mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4)
        .encode(
            x=alt.X("difficulty_label:N", title=t("teacher.difficulty"),
                    sort=order, axis=alt.Axis(labelAngle=0)),
            xOffset=alt.XOffset("mode:N"),
            y=alt.Y("rate:Q", title=None,
                    axis=alt.Axis(format="%", labelFlush=False, labelPadding=8),
                    scale=alt.Scale(domain=[0, 1])),
            color=alt.Color(
                "mode:N",
                title=None,
                sort=mode_order,
                scale=alt.Scale(
                    domain=mode_order,
                    range=["#1D4ED8", "#93C5FD"],
                ),
                legend=alt.Legend(orient="bottom", direction="horizontal", labelLimit=220),
            ),
            tooltip=[
                alt.Tooltip("difficulty_label:N", title=t("teacher.difficulty")),
                alt.Tooltip("mode:N", title=t("teacher.practice_complete_mode")),
                alt.Tooltip("rate:Q", title=t("teacher.axis_rate"), format=".0%"),
                alt.Tooltip("submission_count:Q", title=t("teacher.axis_submissions")),
            ],
        )
    )
    labels = bars.mark_text(dy=-9, fontSize=12, color=ui.MUTED).encode(
        text=alt.Text("rate_label:N"),
    )
    chart = (
        alt.layer(bars, labels)
        .properties(height=300, padding={"left": 56, "right": 16, "top": 22, "bottom": 8})
        .configure_view(strokeWidth=0)
        .configure_axis(
            labelColor=ui.MUTED,
            titleColor=ui.MUTED,
            domainColor=ui.BORDER,
            gridColor="#EEF3FE",
        )
    )
    st.altair_chart(chart, use_container_width=True)
