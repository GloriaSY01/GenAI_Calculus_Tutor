"""Practice accuracy — graded answers, as opposed to tutor solve rate.

`/grade` doesn't write an event log yet, so nothing about submitted practice
answers reaches analytics. The panel states that plainly instead of leaving the
teacher to assume the solve rate above covers it.

Data:
    practice: {
        n_answers,
        correct_rate,
        by_topic: [
            {
                topic,
                attempts,
                correct_rate,
                independent_count,
                ai_assisted_count,
                not_correct_count,
                independent_rate,
                ai_assisted_rate,
                not_correct_rate,
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
        bool(practice.get("practice_completion_modes"))
        or bool(practice.get("by_difficulty_completion"))
        or bool(practice.get("practice_completion_trend"))
        or bool(practice.get("practice_by_topic"))
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
            {"mode": "independent", "count": 8},
            {"mode": "ai_assisted", "count": 5},
            {"mode": "not_correct", "count": 3},
        ],
        "by_difficulty_completion": [
            {"difficulty": "easy", "independent_rate": 0.62, "ai_assisted_rate": 0.25, "attempts": 8},
            {"difficulty": "medium", "independent_rate": 0.38, "ai_assisted_rate": 0.33, "attempts": 6},
            {"difficulty": "hard", "independent_rate": 0.18, "ai_assisted_rate": 0.45, "attempts": 5},
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


def _format_count(value) -> str:
    if value is None:
        return t("teacher.practice_topic_no_data_value")
    return str(int(value))


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
    if df.empty and not all_topics:
        return

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

    st.markdown(f"**{t('teacher.practice_topic_table')}**")
    st.caption(t("teacher.practice_topic_filter_sub"))

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
    independent_count = selected.get("independent_count")
    ai_assisted_count = selected.get("ai_assisted_count")
    not_correct_count = selected.get("not_correct_count")
    known_completion_counts = (
        independent_count is not None
        and ai_assisted_count is not None
        and not_correct_count is not None
    )
    correct_count = (
        int(independent_count) + int(ai_assisted_count)
        if known_completion_counts
        else None
    )
    if selected and correct_count == 0 and selected.get("correct_rate") is not None:
        correct_count = round(attempts * selected.get("correct_rate", 0))
        not_correct_count = max(attempts - correct_count, 0)

    correct_rate = selected.get("correct_rate") if selected else None
    if selected and correct_count is None and correct_rate is not None:
        correct_count = round(attempts * correct_rate)

    c1, c2, c3 = st.columns(3)
    c1.metric(
        t("teacher.practice_topic_submissions"),
        f"{attempts}",
        help=t("teacher.practice_topic_submissions_help"),
    )
    c2.metric(
        t("teacher.practice_topic_correct_count"),
        _format_count(correct_count),
        help=t("teacher.practice_topic_correct_count_help"),
    )
    c3.metric(
        t("teacher.practice_topic_correct_rate"),
        _format_rate(correct_rate),
        help=t("teacher.practice_topic_correct_rate_help"),
    )

    c4, c5, c6 = st.columns(3)
    c4.metric(
        t("teacher.practice_topic_independent_count"),
        _format_count(independent_count),
        help=t("teacher.practice_topic_independent_count_help"),
    )
    c5.metric(
        t("teacher.practice_topic_ai_assisted_count"),
        _format_count(ai_assisted_count),
        help=t("teacher.practice_topic_ai_assisted_count_help"),
    )
    c6.metric(
        t("teacher.practice_topic_not_correct_count"),
        _format_count(not_correct_count),
        help=t("teacher.practice_topic_not_correct_count_help"),
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
        id_vars=["difficulty", "difficulty_label", "attempts"],
        value_vars=["independent_rate", "ai_assisted_rate"],
        var_name="mode",
        value_name="rate",
    )
    chart_df["mode"] = chart_df["mode"].map({
        "independent_rate": t("teacher.practice_independent"),
        "ai_assisted_rate": t("teacher.practice_ai_assisted"),
    })
    chart_df["rate_label"] = (chart_df["rate"] * 100).round().astype(int).astype(str) + "%"

    order = [difficulty_label("easy"), difficulty_label("medium"), difficulty_label("hard"),
             difficulty_label("unknown")]
    mode_order = [t("teacher.practice_independent"), t("teacher.practice_ai_assisted")]
    chart = (
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
                legend=alt.Legend(orient="bottom", direction="horizontal", labelLimit=220),
            ),
            tooltip=[
                alt.Tooltip("difficulty_label:N", title=t("teacher.difficulty")),
                alt.Tooltip("mode:N", title=t("teacher.practice_complete_mode")),
                alt.Tooltip("rate:Q", title=t("teacher.axis_rate"), format=".0%"),
                alt.Tooltip("attempts:Q", title=t("teacher.axis_attempts")),
            ],
        )
        .properties(height=300, padding={"left": 72, "right": 16, "top": 8, "bottom": 8})
    )
    st.altair_chart(chart, use_container_width=True)
