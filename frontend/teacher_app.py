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
import streamlit as st

import api
import ui
from i18n import t
from teacher import (
    assign,
    assistant,
    condition_compare,
    insights,
    kpi,
    nav,
    practice_stats,
    reasoning_quality,
    topic_health,
)

st.set_page_config(page_title="Teacher Dashboard", page_icon="📊", layout="wide")
ui.setup_page("Teacher Dashboard", "📊")

ss = st.session_state
ss.setdefault("assign_prefill", None)
ss.setdefault("assistant_history", [])
ss.setdefault("nav_section", nav.DEFAULT)


@st.cache_data(ttl=30, show_spinner=False)
def load_analytics(class_id: str | None) -> dict:
    """Cached so panel-level interactions don't re-aggregate every log file."""
    return api.fetch_class_analytics(class_id)


ui.language_toggle()

with st.sidebar:
    st.header(f"📊 {t('teacher.page_name')}")
    st.caption(t("teacher.sidebar_caption"))

    # Class picker. The backend has no class roster yet (GET /classes), so this
    # renders as a single locked option; once the roster API exists, the same
    # selector switches classes and the chosen id rides along to analytics.
    classes = api.fetch_classes()
    if classes:
        names = {c["id"]: c["label"] for c in classes}
        ss.class_id = st.selectbox(t("teacher.class_label"), list(names),
                                   format_func=names.get, key="class_select")
    else:
        st.selectbox(t("teacher.class_label"), [t("teacher.class_all")],
                     key="class_select_placeholder", disabled=True)
        st.caption(t("teacher.class_hint"))
        ss.class_id = None

    if st.button(t("teacher.refresh"), use_container_width=True, type="primary"):
        load_analytics.clear()
        api.fetch_topics.clear()
        api.fetch_classes.clear()
        st.toast(t("teacher.refreshed"), icon="🔄")
        st.rerun()

try:
    topics = api.fetch_topics()
    data = load_analytics(ss.get("class_id"))
except Exception as exc:  # noqa: BLE001
    st.error(f"{t('common.backend_error')} {api.BACKEND_URL}\n\n{exc}")
    st.stop()

with st.sidebar:
    st.divider()
    st.caption(f"**{t('teacher.data_scope')}** · {t('teacher.scope_all_time')}")
    st.caption(t("teacher.sidebar_stats").format(s=data.get("n_sessions", 0),
                                                 m=data.get("n_turns", 0)))

st.title(f"📊 {t('teacher.page_name')}")
st.caption(t("teacher.subtitle"))

section = nav.render_nav(ss)
st.divider()

if section == nav.OVERVIEW:
    ui.section(t("teacher.sec_overview"), t("teacher.sec_overview_title"),
               t("teacher.sec_overview_sub"))
    kpi.render_kpi_panel(data)
    st.write("")
    left, right = st.columns([3, 2], gap="large")
    with left:
        insights.render_insights_panel(data)
    with right:
        nav.render_guide(ss)
        st.write("")
        condition_compare.render_condition_panel(data.get("by_condition"))

elif section == nav.DIAGNOSE:
    ui.section(t("teacher.sec_diagnose"), t("teacher.sec_diagnose_title"),
               t("teacher.sec_diagnose_sub"))
    left, right = st.columns([3, 2], gap="large")
    with left:
        topic_health.render_topic_health_panel(data.get("by_topic", []))
        st.write("")
        reasoning_quality.render_reasoning_panel(
            data.get("reasoning_distribution", {}),
            explanation_rate=data.get("explanation_response_rate"),
        )
    with right:
        practice_stats.render_practice_stats_panel(data.get("practice"))

elif section == nav.ASSIGN:
    ui.section(t("teacher.sec_act"), t("teacher.sec_act_title"),
               t("teacher.sec_act_sub"))
    assign.render_assign_panel(ss, topics, list_fn=api.fetch_assignments,
                               create_fn=api.create_assignment,
                               delete_fn=api.delete_assignment,
                               by_topic=data.get("by_topic"))

elif section == nav.ASSISTANT:
    ui.section(t("teacher.sec_assistant"), t("teacher.sec_assistant_title"),
               t("teacher.sec_assistant_sub"))
    left, right = st.columns([3, 2], gap="large")
    with left:
        assistant.render_assistant_panel(ss, ask_fn=api.ask_analytics)
    with right:
        insights.render_insights_panel(data)
