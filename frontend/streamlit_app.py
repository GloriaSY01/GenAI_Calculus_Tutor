"""Student page - GenAI Calculus Tutor.

Redesigned for first-time learners (per review feedback):
- Single, top-to-bottom guided flow instead of two side-by-side blocks.
- A Learning Path banner up top so beginners know the recommended order.
- A clear 3-step flow per topic: set up -> answer -> guided help.
- Experiment internals stay hidden; the student sees a friendly progress bar.

Now also: unified education theme (frontend/ui.py) and an English / 中文
toggle in the top-right (frontend/i18n.py).

Run the backend first, then: streamlit run frontend/streamlit_app.py
"""
import random
import re

import streamlit as st
from streamlit_sortables import sort_items

import api
import i18n
import ui
from i18n import t

st.set_page_config(page_title="Calculus Tutor", page_icon="∫", layout="wide")
ui.setup_page("Calculus Tutor", "∫")

QTYPES = ["single_choice", "multiple_choice", "fill_blank", "drag_order"]


def clean_label(text: str) -> str:
    return re.sub(r"\$", "", text).strip()


ss = st.session_state
ss.setdefault("student_id", "")
ss.setdefault("focus_topic", None)
ss.setdefault("question", None)
ss.setdefault("grade", None)
ss.setdefault("session_id", None)
ss.setdefault("messages", [])
ss.setdefault("problem", None)
ss.setdefault("condition", None)
ss.setdefault("last_turn", None)
ss.setdefault("linked_question_id", None)


def start_tutor(problem_id):
    condition = random.choice(["explain", "control"])
    data = api.start_session(problem_id, condition, ss.student_id.strip() or "anon")
    ss.session_id = data["session_id"]
    ss.problem = data.get("problem")
    ss.condition = data["condition"]
    ss.messages = [{"role": "assistant", "content": data["opening_message"]}]
    ss.last_turn = None
    ss.linked_question_id = problem_id


# --------------------------------------------------------------------------- #
ui.language_toggle()

try:
    topics = api.fetch_topics()
    path = api.fetch_learning_path()
except Exception as exc:  # noqa: BLE001
    st.error(f"{t('common.backend_error')} {api.BACKEND_URL}\n\n{exc}")
    st.stop()

with st.sidebar:
    st.header(f"∫ {t('app.name')}")
    ss.student_id = st.text_input(t("student.name_label"), value=ss.student_id)
    st.caption(t("student.sidebar_caption"))
    st.divider()
    st.caption(t("student.teacher_hint"))


# 1) Learning path banner ---------------------------------------------------- #
st.title(t("student.title"))
st.caption(t("student.subtitle"))

if ss.focus_topic is None:
    ss.focus_topic = path[0]["topic"] if path else (topics[0] if topics else None)

st.subheader(t("student.path_heading"))
cols = st.columns(len(path)) if path else []
for i, step in enumerate(path):
    with cols[i]:
        is_active = step["topic"] == ss.focus_topic
        with st.container(border=True):
            title = f"{step['order']}. {step['title']}"
            color = ui.PRIMARY if is_active else ui.FG
            # Fixed-height header + summary block so every card is equal height
            # and the button lines up across the row.
            st.markdown(
                f"<div style='min-height:126px'>"
                f"<div style='font-weight:700;color:{color};margin-bottom:6px'>{title}</div>"
                f"<div style='font-size:0.82rem;color:{ui.MUTED};line-height:1.35'>"
                f"{step['summary']}</div></div>",
                unsafe_allow_html=True,
            )
            btn_label = (f"● {t('student.studying')}" if is_active
                         else t("student.start"))
            if st.button(btn_label, key=f"path_{step['order']}",
                         use_container_width=True,
                         type="primary" if is_active else "secondary"):
                ss.focus_topic = step["topic"]
                ss.question = None
                ss.grade = None
                st.rerun()

st.divider()

# 2) Practice ---------------------------------------------------------------- #
current_step = next((s for s in path if s["topic"] == ss.focus_topic), None)
st.header(f"{t('student.step_prefix')}: {ss.focus_topic}")
if current_step:
    if current_step.get("prerequisites"):
        st.caption(f"{t('student.best_after')} " +
                   ", ".join(current_step["prerequisites"]))
    st.write(current_step["summary"])

with st.container(border=True):
    st.markdown(f"#### {t('student.setup_heading')}")
    c1, c2 = st.columns(2)
    difficulty = c1.select_slider(t("student.difficulty"),
                                  options=["easy", "medium", "hard"], value="easy")
    qtype = c2.selectbox(t("student.format"), QTYPES,
                         format_func=i18n.qtype_label)
    if st.button(t("student.generate"), type="primary", use_container_width=True):
        with st.spinner(t("student.generating")):
            try:
                ss.question = api.generate_question(qtype, ss.focus_topic, difficulty)
                ss.grade = None
            except Exception as exc:  # noqa: BLE001
                st.error(f"{exc}")

q = ss.question
if q is not None:
    with st.container(border=True):
        st.markdown(f"#### {t('student.answer_heading')}")
        st.caption(f"{q['topic']} · {q['difficulty']} · "
                   f"{i18n.qtype_label(q['type'])}")
        st.markdown(q["stem"])
        if q.get("instructions"):
            st.caption(q["instructions"])

        payload = {"question_id": q["id"]}
        if q["type"] == "single_choice":
            choice = st.radio(t("student.your_answer"), q["options"], index=None,
                              format_func=clean_label, key=f"single_{q['id']}")
            if choice is not None:
                payload["single"] = q["options"].index(choice)
        elif q["type"] == "multiple_choice":
            picked = []
            st.write(t("student.select_all"))
            for i, opt in enumerate(q["options"]):
                if st.checkbox(clean_label(opt), key=f"mc_{q['id']}_{i}"):
                    picked.append(i)
            payload["multiple"] = picked
        elif q["type"] == "fill_blank":
            blanks = []
            for i in range(q.get("n_blanks", 1)):
                blanks.append(st.text_input(f"{t('student.blank')} {i + 1}",
                                            key=f"fb_{q['id']}_{i}"))
            payload["blanks"] = blanks
        elif q["type"] == "drag_order":
            st.write(t("student.drag_hint"))
            ordered = sort_items(q["steps"], direction="vertical",
                                 key=f"drag_{q['id']}")
            payload["order"] = ordered

        if st.button(t("student.submit"), key=f"submit_{q['id']}",
                     use_container_width=True):
            try:
                ss.grade = api.grade_answer(payload)
            except Exception as exc:  # noqa: BLE001
                st.error(f"{exc}")

        if ss.grade is not None:
            if ss.grade["correct"]:
                st.success(ss.grade["feedback"])
            else:
                st.error(ss.grade["feedback"])
                st.caption(t("student.wrong_hint"))

    with st.container(border=True):
        st.markdown(f"#### {t('student.help_heading')}")
        already_linked = ss.linked_question_id == q["id"]
        if not already_linked:
            st.caption(t("student.help_caption"))
            if st.button(t("student.ask_tutor"), use_container_width=True):
                start_tutor(q["id"])
                st.rerun()
        else:
            st.caption(t("student.linked_note"))
else:
    st.info(t("student.empty_practice"))


# 3) Tutor conversation ------------------------------------------------------ #
st.divider()
with st.container(border=True):
    st.markdown(f"#### {t('student.tutor_heading')}")
    if ss.session_id is None:
        try:
            start_tutor(None)
        except Exception as exc:  # noqa: BLE001
            st.error(f"{exc}")
            st.stop()

    linked = ss.problem is not None
    head_l, head_r = st.columns([3, 1])
    if linked:
        head_l.caption(f"{t('student.tutor_linked')} {ss.problem['topic']} "
                       f"({ss.problem['difficulty']}).")
        if head_r.button(t("student.free_chat"), use_container_width=True):
            start_tutor(None)
            st.rerun()
    else:
        head_l.caption(t("student.tutor_free_caption"))

    mastery = ss.last_turn["mastery"] if ss.last_turn else 0
    st.progress(min(mastery, 100) / 100,
                text=f"{t('student.progress')} {min(mastery, 100)}%")

    if ss.last_turn and ss.last_turn["is_solved"]:
        st.success(t("student.solved"))
    elif ss.last_turn and ss.last_turn["action"] == "blocked":
        st.info(t("student.blocked"))

    for msg in ss.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    with st.form("tutor_input", clear_on_submit=True):
        text = st.text_area("input", height=80, label_visibility="collapsed",
                            placeholder=t("student.input_placeholder"))
        sent = st.form_submit_button(t("student.send"), type="primary")
    if sent and text.strip():
        try:
            turn = api.send_message(ss.session_id, text)
            ss.messages.append({"role": "user", "content": text})
            ss.messages.append({"role": "assistant", "content": turn["tutor_message"]})
            ss.last_turn = turn
            st.rerun()
        except Exception as exc:  # noqa: BLE001
            st.error(f"{exc}")
