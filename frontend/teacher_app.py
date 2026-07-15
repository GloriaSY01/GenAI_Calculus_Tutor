"""Teacher Dashboard - GenAI Calculus Tutor (standalone app).

Runs as its OWN Streamlit app on its own root URL / port, completely separate
from the student app. This avoids the multipage /Teacher_Dashboard websocket
failure seen behind the preview proxy — every app is a plain root URL.

Fully redesigned for teachers (per review feedback):
- CLASS-LEVEL, not individual.
- Not just descriptive stats: an Insights panel + an ask-in-natural-language
  assistant grounded on the class data.
- Simple, focused charts.
- Assign practice to the class.

Run the backend first, then:
    streamlit run frontend/teacher_app.py --server.port 8502
"""
import pandas as pd
import streamlit as st

import api
import i18n
import ui
from i18n import t

st.set_page_config(page_title="Teacher Dashboard", page_icon="📊", layout="wide")
ui.setup_page("Teacher Dashboard", "📊")

QTYPES = ["single_choice", "multiple_choice", "fill_blank", "drag_order"]
SEVERITY_ICON = {"info": "🟢", "warning": "🟠", "critical": "🔴"}
SEVERITY_CLASS = {"info": "insight-info", "warning": "insight-warning",
                  "critical": "insight-critical"}
ASSESSMENT_ORDER = ["none", "weak", "partial", "adequate", "strong"]

ss = st.session_state
ss.setdefault("insight_answer", None)

ui.language_toggle()

try:
    topics = api.fetch_topics()
    data = api.fetch_class_analytics()
except Exception as exc:  # noqa: BLE001
    st.error(f"{t('common.backend_error')} {api.BACKEND_URL}\n\n{exc}")
    st.stop()

with st.sidebar:
    st.header(f"📊 {t('teacher.page_name')}")
    st.caption(t("teacher.sidebar_caption"))
    if st.button(t("teacher.refresh"), use_container_width=True):
        st.rerun()

st.title(t("teacher.title"))
st.caption(t("teacher.subtitle"))

# KPIs ---------------------------------------------------------------------- #
k = st.columns(4)
k[0].metric(t("teacher.kpi_students"), data["n_students"])
k[1].metric(t("teacher.kpi_sessions"), data["n_sessions"])
k[2].metric(t("teacher.kpi_solve"), f"{int(data['solve_rate'] * 100)}%")
k[3].metric(t("teacher.kpi_reasoning"), f"{data['avg_reasoning']}/4")

k2 = st.columns(4)
k2[0].metric(t("teacher.kpi_mastery"), f"{data['avg_final_mastery']}/100")
k2[1].metric(t("teacher.kpi_turns"), data["avg_turns_per_session"])
k2[2].metric(t("teacher.kpi_gaming"), f"{int(data['gaming_rate'] * 100)}%",
             help=t("teacher.kpi_gaming_help"))
k2[3].metric(t("teacher.kpi_guardrail"), f"{int(data['guardrail_rate'] * 100)}%",
             help=t("teacher.kpi_guardrail_help"))

st.divider()

left, right = st.columns([3, 2], gap="large")

with left:
    st.subheader(t("teacher.by_topic"))
    by_topic = data.get("by_topic", [])
    if by_topic:
        df = pd.DataFrame(by_topic)
        st.markdown(f"**{t('teacher.solve_per_topic')}**")
        st.bar_chart(df.set_index("topic")[["solve_rate"]], height=240,
                     color=ui.PRIMARY)
        st.markdown(f"**{t('teacher.reasoning_per_topic')}**")
        st.bar_chart(df.set_index("topic")[["avg_reasoning"]], height=240,
                     color=ui.SECONDARY)
        with st.expander(t("teacher.full_table")):
            st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info(t("teacher.no_topic_data"))

    st.subheader(t("teacher.reasoning_dist"))
    dist = data.get("reasoning_distribution", {})
    if dist and sum(dist.values()) > 0:
        dist_df = pd.DataFrame(
            {"level": ASSESSMENT_ORDER,
             "share": [dist.get(l, 0) for l in ASSESSMENT_ORDER]}
        ).set_index("level")
        st.bar_chart(dist_df, height=220, color=ui.PRIMARY)
        st.caption(t("teacher.reasoning_dist_caption"))
    else:
        st.info(t("teacher.no_reasoning_data"))

with right:
    st.subheader(t("teacher.insights"))
    st.caption(t("teacher.insights_caption"))
    for ins in data.get("insights", []):
        icon = SEVERITY_ICON.get(ins["severity"], "🟢")
        with st.container(border=True):
            st.markdown(f"{icon} **{ins['title']}**")
            st.caption(ins["detail"])

    st.divider()
    st.subheader(t("teacher.ask_heading"))
    st.caption(t("teacher.ask_caption"))
    examples = [t("teacher.ex1"), t("teacher.ex2"), t("teacher.ex3")]
    ex = st.selectbox(t("teacher.examples"), [t("teacher.type_own")] + examples)
    default_q = "" if ex == t("teacher.type_own") else ex
    question = st.text_input(t("teacher.your_question"), value=default_q)
    if st.button(t("teacher.ask"), type="primary", use_container_width=True):
        if question.strip():
            with st.spinner(t("teacher.analysing")):
                try:
                    resp = api.ask_analytics(question.strip())
                    ss.insight_answer = resp["answer"]
                except Exception as exc:  # noqa: BLE001
                    st.error(f"{exc}")
        else:
            st.warning(t("teacher.type_first"))
    if ss.insight_answer:
        st.info(ss.insight_answer)

st.divider()

# Assign practice ----------------------------------------------------------- #
st.subheader(t("teacher.assign_heading"))
st.caption(t("teacher.assign_caption"))

assign_l, assign_r = st.columns([2, 3], gap="large")

with assign_l:
    with st.form("assign_form", clear_on_submit=True):
        title = st.text_input(t("teacher.assign_title"),
                              placeholder=t("teacher.assign_title_ph"))
        a_topic = st.selectbox(t("teacher.topic"), topics)
        a_type = st.selectbox(t("teacher.format"), QTYPES,
                              format_func=i18n.qtype_label)
        cc = st.columns(2)
        a_diff = cc[0].select_slider(t("teacher.difficulty"),
                                     options=["easy", "medium", "hard"],
                                     value="easy")
        a_n = cc[1].number_input(t("teacher.questions"), min_value=1,
                                 max_value=20, value=5)
        note = st.text_area(t("teacher.note"), height=70)
        submitted = st.form_submit_button(t("teacher.assign_btn"), type="primary",
                                          use_container_width=True)
    if submitted:
        if not title.strip():
            st.warning(t("teacher.assign_need_title"))
        else:
            try:
                api.create_assignment({
                    "title": title.strip(), "topic": a_topic, "qtype": a_type,
                    "difficulty": a_diff, "n_questions": int(a_n),
                    "note": note.strip(),
                })
                st.success(t("teacher.assign_created"))
                st.rerun()
            except Exception as exc:  # noqa: BLE001
                st.error(f"{exc}")

with assign_r:
    st.markdown(f"**{t('teacher.current_assignments')}**")
    try:
        assignments = api.fetch_assignments()
    except Exception as exc:  # noqa: BLE001
        st.error(f"{exc}")
        assignments = []
    if not assignments:
        st.info(t("teacher.no_assignments"))
    for a in assignments:
        with st.container(border=True):
            row = st.columns([5, 1])
            with row[0]:
                st.markdown(f"**{a['title']}**")
                st.caption(f"{a['topic']} · {i18n.qtype_label(a['qtype'])} · "
                           f"{a['difficulty']} · {a['n_questions']}")
                if a.get("note"):
                    st.caption(f"📝 {a['note']}")
            if row[1].button(t("teacher.delete"), key=f"del_{a['id']}"):
                try:
                    api.delete_assignment(a["id"])
                    st.rerun()
                except Exception as exc:  # noqa: BLE001
                    st.error(f"{exc}")
