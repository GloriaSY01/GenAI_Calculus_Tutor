"""Practice accuracy — graded answers, as opposed to tutor solve rate.

`/grade` doesn't write an event log yet, so nothing about submitted practice
answers reaches analytics. The panel states that plainly instead of leaving the
teacher to assume the solve rate above covers it.

Data (once the backend logs `answer_submitted`):
    practice: {n_answers, correct_rate, by_topic: [{topic, attempts, correct_rate}]}
"""
from __future__ import annotations

from typing import Optional

import pandas as pd
import streamlit as st

import ui
from i18n import t, topic_label


def render_practice_stats_panel(practice: Optional[dict]) -> None:
    with st.container(border=True):
        _render_body(practice)


def _render_body(practice: Optional[dict]) -> None:
    ui.panel_header("📝", t("teacher.practice_stats"), t("teacher.practice_stats_sub"))

    if not practice or not practice.get("by_topic"):
        ui.empty_state(t("teacher.practice_empty"))
        return

    df = pd.DataFrame(practice["by_topic"])
    df["topic"] = df["topic"].map(topic_label)
    df["correct_rate"] = (df["correct_rate"] * 100).round()
    st.dataframe(
        df.rename(columns={"topic": t("teacher.axis_topic"),
                           "attempts": t("teacher.axis_attempts"),
                           "correct_rate": t("teacher.practice_stats") + " %"}),
        use_container_width=True, hide_index=True,
    )
