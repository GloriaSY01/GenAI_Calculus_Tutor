"""Teacher Dashboard - GenAI Calculus Tutor (standalone app).

Runs as its OWN Streamlit app on its own root URL / port, completely separate
from the student app. This avoids the multipage /Teacher_Dashboard websocket
failure seen behind the preview proxy -- every app is a plain root URL.

This file is the orchestrator only: it loads data (cached), holds the shared
state, and hands data + callbacks to the panels in frontend/teacher/.

A nav bar splits the dashboard into four sections -- Overview, Diagnose,
Assign, Assistant -- and only the selected one renders, so panels no longer
stack into one very long page.

Run the backend first, then:
    streamlit run frontend/teacher_app.py --server.port 8502
"""
from __future__ import annotations

import streamlit as st

import api
import ui
from catalog import fetch_catalog
from i18n import t
from i18n import topic_label
from teacher import (
    assign,
    condition_compare,
    floating_assistant,
    insights,
    kpi,
    practice_stats,
    reasoning_quality,
    topic_health,
)

st.set_page_config(page_title="Teacher Dashboard", page_icon="📊", layout="wide")
ui.setup_page("Teacher Dashboard", "📊")

ss = st.session_state
ss.setdefault("assign_prefill", None)
ss.setdefault("assistant_history", [])
ss.setdefault("class_id", "calc1-a")

requested_lang = st.query_params.get("lang")
if (requested_lang in {"en", "zh"}
        and requested_lang != ss.get("_applied_query_lang")):
    ss.lang = requested_lang
    ss.language = requested_lang
    ss._applied_query_lang = requested_lang

requested_class = st.query_params.get("class_id")
if requested_class:
    ss.class_id = requested_class

if st.query_params.get("assistant_only") == "1":
    st.markdown(
        """
        <style>
        [data-testid="stHeader"], [data-testid="stToolbar"] { display: none; }
        [data-testid="stMainBlockContainer"] {
          padding: 1rem 1rem 1.25rem !important;
          max-width: none !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    floating_assistant.render_drawer(ss, ask_fn=api.ask_analytics)
    st.stop()


@st.cache_data(ttl=30, show_spinner=False)
def load_analytics(class_id: str | None) -> dict:
    """Cached so panel-level interactions don't re-aggregate every log file."""
    return api.fetch_class_analytics(class_id)


ui.language_toggle()

with st.sidebar:
    st.header(f"📊 {t('teacher.page_name')}")
    st.caption(t("teacher.sidebar_caption"))

    class_names = {"calc1-a": "微积分A", "calc1-b": "微积分B"}
    class_ids = list(class_names)
    default_class = ss.get("class_id", "calc1-a")
    default_index = class_ids.index(default_class) if default_class in class_ids else 0
    ss.class_id = st.selectbox(
        t("teacher.class_label"),
        class_ids,
        index=default_index,
        format_func=class_names.get,
        key="class_select_flat_v2",
    )

    if st.button(t("teacher.refresh"), use_container_width=True, type="primary"):
        load_analytics.clear()
        api.fetch_topics.clear()
        st.toast(t("teacher.refreshed"), icon="🔄")
        st.rerun()

try:
    topics = api.fetch_topics()
    catalog = fetch_catalog(api.BACKEND_URL)
    data = load_analytics(ss.get("class_id"))
except Exception as exc:  # noqa: BLE001
    st.error(f"{t('common.backend_error')} {api.BACKEND_URL}\n\n{exc}")
    st.stop()

with st.sidebar:
    st.divider()
    st.caption(f"**{t('teacher.data_scope')}** · {t('teacher.scope_all_time')}")
    st.caption(t("teacher.sidebar_stats").format(s=data.get("n_sessions", 0),
                                                 m=data.get("n_turns", 0)))


def _usable_topic_rows(data: dict) -> list[dict]:
    return [
        row for row in data.get("by_topic", [])
        if row.get("topic") != "General / Free chat"
    ]


def _weakest_topic(data: dict) -> dict | None:
    rows = _usable_topic_rows(data)
    if not rows:
        return None
    return min(rows, key=lambda row: (row.get("solve_rate", 0),
                                      row.get("avg_reasoning", 0)))


def _pct(value) -> str:
    return f"{round((value or 0) * 100)}%"


def _render_decision_brief(data: dict) -> None:
    weakest = _weakest_topic(data)
    if weakest:
        focus = topic_label(weakest.get("topic", ""))
        evidence = (
            f"{_pct(weakest.get('solve_rate'))} {t('teacher.flat_solved')} · "
            f"{weakest.get('avg_reasoning', 0)}/4 {t('teacher.flat_reasoning')}"
        )
        action = t("teacher.flat_action_assign")
    elif data.get("n_sessions", 0):
        focus = t("teacher.flat_no_weak_topic")
        evidence = t("teacher.flat_enough_data")
        action = t("teacher.flat_action_monitor")
    else:
        focus = t("teacher.flat_no_data_focus")
        evidence = t("teacher.flat_no_data_evidence")
        action = t("teacher.flat_action_collect")

    with st.container(border=True):
        ui.panel_header("🧭", t("teacher.flat_brief_title"),
                        t("teacher.flat_brief_sub"))
        cols = st.columns(3)
        items = [
            (t("teacher.flat_focus"), t("teacher.flat_focus_help"), focus),
            (t("teacher.flat_evidence"), t("teacher.flat_evidence_help"), evidence),
            (t("teacher.flat_next_action"), t("teacher.flat_next_action_help"), action),
        ]
        for col, (label, help_text, value) in zip(cols, items):
            col.markdown(f"**{label}**")
            col.caption(help_text)
            col.info(value)


def _render_dashboard() -> None:
    st.title(f"📊 {t('teacher.page_name')}")
    st.caption(t("teacher.subtitle"))

    _render_decision_brief(data)

    st.write("")
    ui.section(t("teacher.sec_overview"), t("teacher.sec_overview_title"),
               t("teacher.sec_overview_sub"))
    kpi.render_kpi_panel(data)
    st.write("")
    with st.container(border=True):
        ui.panel_header("📝", t("teacher.practice_overview"),
                        t("teacher.practice_overview_sub"))
        practice_stats.render_practice_stats_panel(data, embedded=True,
                                                   catalog=catalog)
        st.divider()
        insights.render_insights_panel(data, embedded=True)

    st.write("")
    ui.section(t("teacher.sec_diagnose"), t("teacher.sec_diagnose_title"),
               t("teacher.sec_diagnose_sub"))
    left, right = st.columns([3, 2], gap="large")
    with left:
        topic_health.render_topic_health_panel(data.get("by_topic", []))
    with right:
        reasoning_quality.render_reasoning_panel(
            data.get("reasoning_distribution", {}),
            explanation_rate=data.get("explanation_response_rate"),
        )

    if data.get("by_condition"):
        with st.expander(t("teacher.research_view")):
            condition_compare.render_condition_panel(data.get("by_condition"))

    st.write("")
    ui.section(t("teacher.sec_act"), t("teacher.sec_act_title"),
               t("teacher.sec_act_sub"))
    assign.render_assign_panel(ss, topics, list_fn=api.fetch_assignments,
                               create_fn=api.create_assignment,
                               delete_fn=api.delete_assignment,
                               by_topic=data.get("by_topic"))


if floating_assistant.is_open(ss):
    _render_dashboard()
    floating_assistant.render_iframe_drawer()
else:
    _render_dashboard()
    floating_assistant.render_launcher(ss)
