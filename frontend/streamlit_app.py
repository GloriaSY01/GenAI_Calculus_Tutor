"""Streamlit frontend for the GenAI Calculus Tutor.

Two blocks:
  Block A - Practice (2.1): AI generates calculus questions (single choice,
            multiple choice, fill-in-the-blank, drag-and-drop ordering); the
            student answers and gets auto-graded feedback.
  Block B - Tutor (2.2): a Socratic AI agent that guides the student on the
            current question without giving the answer away.

Student-facing by default. Add ?instructor=1 to the URL to reveal experiment
controls and live metrics.

Run the backend first (uvicorn), then:
    streamlit run frontend/streamlit_app.py
"""
import os
import random
import re

import requests
import streamlit as st
from dotenv import load_dotenv
from streamlit_sortables import sort_items

load_dotenv()
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

st.set_page_config(page_title="Calculus Tutor", page_icon="∫", layout="wide")


def is_instructor() -> bool:
    val = st.query_params.get("instructor", "0")
    if isinstance(val, list):
        val = val[0] if val else "0"
    return str(val).lower() in ("1", "true", "yes")


INSTRUCTOR = is_instructor()


# --------------------------------------------------------------------------- #
# Backend helpers
# --------------------------------------------------------------------------- #
@st.cache_data(ttl=60)
def fetch_topics():
    r = requests.get(f"{BACKEND_URL}/topics", timeout=15)
    r.raise_for_status()
    return r.json()


def generate_question(qtype, topic, difficulty):
    r = requests.post(f"{BACKEND_URL}/generate",
                      json={"type": qtype, "topic": topic, "difficulty": difficulty},
                      timeout=60)
    r.raise_for_status()
    return r.json()


def grade_answer(payload):
    r = requests.post(f"{BACKEND_URL}/grade", json=payload, timeout=30)
    r.raise_for_status()
    return r.json()


def start_session(problem_id, condition, student_id):
    r = requests.post(f"{BACKEND_URL}/session/start",
                      json={"problem_id": problem_id, "condition": condition,
                            "student_id": student_id}, timeout=30)
    r.raise_for_status()
    return r.json()


def send_message(session_id, text):
    r = requests.post(f"{BACKEND_URL}/session/{session_id}/message",
                      json={"text": text}, timeout=60)
    r.raise_for_status()
    return r.json()


def clean_label(text: str) -> str:
    """Strip $ delimiters so simple math reads cleanly in widget labels."""
    return re.sub(r"\$", "", text).strip()


def start_tutor(problem_id, student_id):
    """Start a tutor session. problem_id=None => free chat (no fixed problem)."""
    condition = random.choice(["explain", "control"])
    data = start_session(problem_id, condition, student_id.strip() or "anon")
    ss.session_id = data["session_id"]
    ss.problem = data.get("problem")          # None in free chat
    ss.condition = data["condition"]
    ss.messages = [{"role": "assistant", "content": data["opening_message"]}]
    ss.last_turn = None
    ss.linked_question_id = problem_id


# --------------------------------------------------------------------------- #
# Session state
# --------------------------------------------------------------------------- #
ss = st.session_state
ss.setdefault("question", None)       # active generated question (public)
ss.setdefault("grade", None)          # last grade result
ss.setdefault("linked_question_id", None)  # question linked to the tutor (or None)
ss.setdefault("session_id", None)     # tutor session
ss.setdefault("messages", [])
ss.setdefault("problem", None)
ss.setdefault("condition", None)
ss.setdefault("last_turn", None)


# --------------------------------------------------------------------------- #
# Sidebar
# --------------------------------------------------------------------------- #
with st.sidebar:
    st.header("∫ Calculus Tutor")
    student_id = st.text_input("Your name (optional)", value="")
    st.caption("**Block A** generates practice questions. "
               "**Block B** is your AI tutor for the current question.")
    if INSTRUCTOR:
        st.divider()
        st.caption("Instructor mode is ON (metrics & condition control visible).")

try:
    topics = fetch_topics()
except Exception as exc:  # noqa: BLE001
    st.error(f"Can't reach the tutor service at {BACKEND_URL}.\n\n{exc}")
    st.stop()


# --------------------------------------------------------------------------- #
# Layout: two blocks
# --------------------------------------------------------------------------- #
col_practice, col_tutor = st.columns(2, gap="large")


# =========================== BLOCK A: PRACTICE ============================== #
with col_practice:
    st.subheader("Practice  ·  generate & answer")
    c1, c2 = st.columns(2)
    topic = c1.selectbox("Topic", topics)
    difficulty = c2.selectbox("Difficulty", ["easy", "medium", "hard"], index=1)
    qtype = st.selectbox(
        "Type",
        ["single_choice", "multiple_choice", "fill_blank", "drag_order"],
        format_func=lambda t: {
            "single_choice": "Single choice",
            "multiple_choice": "Multiple choice",
            "fill_blank": "Fill in the blank",
            "drag_order": "Drag to order steps",
        }[t],
    )
    if st.button("Generate", type="primary", use_container_width=True):
        with st.spinner("Generating a question..."):
            try:
                ss.question = generate_question(qtype, topic, difficulty)
                ss.grade = None
            except Exception as exc:  # noqa: BLE001
                st.error(f"Generation failed: {exc}")

    q = ss.question
    if q is None:
        st.info("Pick a topic and type, then click **Generate**.")
    else:
        st.divider()
        st.markdown(f"**{q['topic']} · {q['difficulty']} · "
                    f"{q['type'].replace('_', ' ')}**")
        st.markdown(q["stem"])
        if q.get("instructions"):
            st.caption(q["instructions"])

        payload = {"question_id": q["id"]}

        if q["type"] == "single_choice":
            choice = st.radio("Your answer", q["options"],
                              index=None, format_func=clean_label,
                              key=f"single_{q['id']}")
            if choice is not None:
                payload["single"] = q["options"].index(choice)

        elif q["type"] == "multiple_choice":
            picked = []
            st.write("Select all that apply:")
            for i, opt in enumerate(q["options"]):
                if st.checkbox(clean_label(opt), key=f"mc_{q['id']}_{i}"):
                    picked.append(i)
            payload["multiple"] = picked

        elif q["type"] == "fill_blank":
            blanks = []
            for i in range(q.get("n_blanks", 1)):
                blanks.append(st.text_input(f"Blank {i + 1}",
                                            key=f"fb_{q['id']}_{i}"))
            payload["blanks"] = blanks

        elif q["type"] == "drag_order":
            st.write("Drag the steps into the correct order:")
            ordered = sort_items(q["steps"], direction="vertical",
                                 key=f"drag_{q['id']}")
            payload["order"] = ordered

        st.write("")
        if st.button("Submit answer", key=f"submit_{q['id']}"):
            try:
                ss.grade = grade_answer(payload)
            except Exception as exc:  # noqa: BLE001
                st.error(f"Grading failed: {exc}")

        if ss.grade is not None:
            if ss.grade["correct"]:
                st.success(ss.grade["feedback"])
            else:
                st.error(ss.grade["feedback"])
                st.caption(f"Correct answer: {ss.grade['correct_answer']}")

        st.divider()
        already_linked = ss.linked_question_id == q["id"]
        if st.button("🔗 Link this question to the tutor",
                     use_container_width=True, disabled=already_linked):
            start_tutor(q["id"], student_id)
            st.rerun()
        if already_linked:
            st.caption("This question is linked to the tutor on the right.")
        else:
            st.caption("Optional — the tutor on the right also works as free chat.")


# ============================ BLOCK B: TUTOR ================================ #
with col_tutor:
    st.subheader("Tutor  ·  guided help")

    # The tutor always works: start a free-chat session by default.
    if ss.session_id is None:
        try:
            start_tutor(None, student_id)
        except Exception as exc:  # noqa: BLE001
            st.error(f"Could not start the tutor: {exc}")
            st.stop()

    linked = ss.problem is not None
    head_l, head_r = st.columns([3, 1])
    if linked:
        head_l.caption(f"Linked to your current question "
                       f"({ss.problem['topic']} · {ss.problem['difficulty']}).")
        if head_r.button("Free chat", use_container_width=True):
            start_tutor(None, student_id)
            st.rerun()
        st.markdown(ss.problem["statement"])
    else:
        head_l.caption("Free chat — ask me anything about Calculus 1.")
        if ss.question is not None:
            if head_r.button("Link question", use_container_width=True):
                start_tutor(ss.question["id"], student_id)
                st.rerun()

    if INSTRUCTOR:
        cols = st.columns(4)
        cols[0].metric("Condition", ss.condition)
        if ss.last_turn:
            cols[1].metric("Mastery", ss.last_turn["mastery"])
            cols[2].metric("Hint level", ss.last_turn["hint_level"])
            cols[3].metric("Reasoning",
                           ss.last_turn["reasoning_assessment"].title())
        st.caption(f"session_id: {ss.session_id}")
    else:
        mastery = ss.last_turn["mastery"] if ss.last_turn else 0
        st.progress(min(mastery, 100) / 100,
                    text=f"Your progress: {min(mastery, 100)}%")

    if ss.last_turn and ss.last_turn["is_solved"]:
        st.success("Nicely done — you reached the answer yourself!")
    elif ss.last_turn and ss.last_turn["action"] == "blocked":
        st.info("Let's work it out together rather than jumping to the answer.")

    st.divider()
    for msg in ss.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    with st.form("tutor_input", clear_on_submit=True):
        text = st.text_area("Your reasoning or next step", height=80,
                            label_visibility="collapsed",
                            placeholder="Type your reasoning or next step...")
        sent = st.form_submit_button("Send", type="primary")
    if sent and text.strip():
        try:
            turn = send_message(ss.session_id, text)
            ss.messages.append({"role": "user", "content": text})
            ss.messages.append({"role": "assistant",
                                "content": turn["tutor_message"]})
            ss.last_turn = turn
            st.rerun()
        except Exception as exc:  # noqa: BLE001
            st.error(f"Something went wrong: {exc}")
