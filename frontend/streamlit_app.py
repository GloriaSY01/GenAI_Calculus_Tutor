"""Streamlit frontend — focus-mode learning path with on-demand tutor.

Layout:
  Sidebar — name + topic catalog
  Main    — stepper + single stage (concept | practice | tutor) + bottom CTAs

Run the backend first (uvicorn), then:
    streamlit run frontend/streamlit_app.py
"""
import os
import random
import re

import requests
import streamlit as st
from dotenv import load_dotenv

import presets
from catalog import fetch_catalog, render_topic_catalog
from concept import render_concept_panel
from practice import render_practice_panel
from stepper import STAGE_CONCEPT, STAGE_PRACTICE, STAGE_TUTOR, render_stepper
from tutor import render_tutor_panel

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
    r = requests.post(
        f"{BACKEND_URL}/generate",
        json={"type": qtype, "topic": topic, "difficulty": difficulty},
        timeout=60,
    )
    r.raise_for_status()
    return r.json()


def grade_answer(payload):
    r = requests.post(f"{BACKEND_URL}/grade", json=payload, timeout=30)
    r.raise_for_status()
    return r.json()


def start_session(problem_id, condition, student_id):
    r = requests.post(
        f"{BACKEND_URL}/session/start",
        json={
            "problem_id": problem_id,
            "condition": condition,
            "student_id": student_id,
        },
        timeout=30,
    )
    r.raise_for_status()
    return r.json()


def send_message(session_id, text):
    r = requests.post(
        f"{BACKEND_URL}/session/{session_id}/message",
        json={"text": text},
        timeout=60,
    )
    r.raise_for_status()
    return r.json()


def clean_label(text: str) -> str:
    return re.sub(r"\$", "", text).strip()


# --------------------------------------------------------------------------- #
# Session state
# --------------------------------------------------------------------------- #
ss = st.session_state
ss.setdefault("question", None)
ss.setdefault("grade", None)
ss.setdefault("linked_question_id", None)
ss.setdefault("session_id", None)
ss.setdefault("messages", [])
ss.setdefault("problem", None)
ss.setdefault("condition", None)
ss.setdefault("last_turn", None)
ss.setdefault("difficulty", "medium")
ss.setdefault("qtype", "single_choice")
ss.setdefault("current_topic", None)
ss.setdefault("learning_stage", STAGE_CONCEPT)
ss.setdefault("tutor_entry", None)
ss.setdefault("pending_topic", None)


def clear_practice():
    ss.question = None
    ss.grade = None


def start_tutor(problem_id, student_id):
    condition = random.choice(["explain", "control"])
    data = start_session(problem_id, condition, student_id.strip() or "anon")
    ss.session_id = data["session_id"]
    ss.problem = data.get("problem")
    ss.condition = data["condition"]
    ss.messages = [{"role": "assistant", "content": data["opening_message"]}]
    ss.last_turn = None
    ss.linked_question_id = problem_id


def go_to_concept(*, clear_question: bool = False):
    ss.learning_stage = STAGE_CONCEPT
    ss.tutor_entry = None
    if clear_question:
        clear_practice()


def go_to_practice(student_id: str):
    ss.learning_stage = STAGE_PRACTICE
    ss.tutor_entry = None
    qtype = ss.get("qtype", "single_choice")
    difficulty = ss.get("difficulty", "medium")
    ss.question = generate_question(qtype, ss.current_topic, difficulty)
    ss.grade = None


def go_to_tutor(
    student_id: str,
    *,
    from_stage: str,
    problem_id=None,
    preset_text: str | None = None,
):
    ss.learning_stage = STAGE_TUTOR
    ss.tutor_entry = from_stage

    need_restart = (
        ss.session_id is None
        or (problem_id is not None and ss.linked_question_id != problem_id)
        or (problem_id is None and ss.linked_question_id is not None)
    )
    if need_restart:
        start_tutor(problem_id, student_id)

    if preset_text:
        turn = send_message(ss.session_id, preset_text)
        ss.messages.append({"role": "user", "content": preset_text})
        ss.messages.append({"role": "assistant", "content": turn["tutor_message"]})
        ss.last_turn = turn


def select_topic(topic: str):
    if topic == ss.current_topic:
        return
    if ss.learning_stage in (STAGE_PRACTICE, STAGE_TUTOR):
        ss.pending_topic = topic
    else:
        ss.current_topic = topic
        st.toast(f"Switched to {topic}")
        st.rerun()


def confirm_topic_switch():
    ss.current_topic = ss.pending_topic
    ss.pending_topic = None
    go_to_concept(clear_question=True)
    st.rerun()


def cancel_topic_switch():
    ss.pending_topic = None
    st.rerun()


def regenerate_question():
    qtype = ss.get("qtype", "single_choice")
    difficulty = ss.get("difficulty", "medium")
    ss.question = generate_question(qtype, ss.current_topic, difficulty)
    ss.grade = None


def next_question():
    regenerate_question()
    st.rerun()


# --------------------------------------------------------------------------- #
# Data load
# --------------------------------------------------------------------------- #
try:
    topics = fetch_topics()
    catalog = fetch_catalog(BACKEND_URL, fetch_topics)
except Exception as exc:  # noqa: BLE001
    st.error(f"Cannot reach the backend ({BACKEND_URL}):\n\n{exc}")
    st.stop()

if ss.current_topic is None or ss.current_topic not in topics:
    ss.current_topic = topics[0]

# --------------------------------------------------------------------------- #
# Sidebar
# --------------------------------------------------------------------------- #
with st.sidebar:
    st.header("∫ Calculus Tutor")
    student_id = st.text_input("Your name (optional)", value="")
    st.divider()
    render_topic_catalog(
        catalog,
        ss.current_topic,
        on_select=select_topic,
    )
    if INSTRUCTOR:
        st.divider()
        st.caption("Instructor mode is ON.")

# --------------------------------------------------------------------------- #
# Main layout
# --------------------------------------------------------------------------- #
st.title("Calculus Tutor")

if ss.pending_topic:
    st.warning(
        f"Switching to **{ss.pending_topic}** will return you to the concept step "
        "and clear your current practice progress."
    )
    c1, c2 = st.columns(2)
    if c1.button("Confirm", type="primary", key="confirm_topic"):
        confirm_topic_switch()
    if c2.button("Cancel", key="cancel_topic"):
        cancel_topic_switch()
    st.stop()

render_stepper(ss.learning_stage)
st.divider()

stage = ss.learning_stage
practice_payload = None

if stage == STAGE_CONCEPT:
    render_concept_panel(ss.current_topic)

elif stage == STAGE_PRACTICE:
    practice_payload = render_practice_panel(
        ss,
        current_topic=ss.current_topic,
        clean_label=clean_label,
        on_difficulty_change=regenerate_question,
    )

elif stage == STAGE_TUTOR:
    render_tutor_panel(
        ss,
        ss.current_topic,
        tutor_entry=ss.tutor_entry,
        instructor=INSTRUCTOR,
        send_message=send_message,
    )

# --------------------------------------------------------------------------- #
# Bottom CTAs (unified per stage)
# --------------------------------------------------------------------------- #
st.divider()

if stage == STAGE_CONCEPT:
    cta_left, cta_right = st.columns([1, 1])
    if cta_left.button("Ask the tutor", use_container_width=True, key="cta_ask_tutor"):
        try:
            go_to_tutor(
                student_id,
                from_stage=STAGE_CONCEPT,
                preset_text=presets.explain_concept(ss.current_topic),
            )
            st.rerun()
        except Exception as exc:  # noqa: BLE001
            st.error(f"Could not reach the tutor: {exc}")
    if cta_right.button(
        "Start practice", type="primary", use_container_width=True, key="cta_practice"
    ):
        try:
            with st.spinner("Generating a question..."):
                go_to_practice(student_id)
            st.rerun()
        except Exception as exc:  # noqa: BLE001
            st.error(f"Question generation failed: {exc}")

elif stage == STAGE_PRACTICE:
    q = ss.question
    answered_correct = ss.grade is not None and ss.grade.get("correct")

    if q is None:
        cta_left, cta_right = st.columns([1, 1])
        if cta_left.button("← Back to concept", use_container_width=True, key="cta_back_concept"):
            go_to_concept(clear_question=True)
            st.rerun()
        if cta_right.button("Generate again", type="primary", use_container_width=True, key="cta_regen"):
            try:
                go_to_practice(student_id)
                st.rerun()
            except Exception as exc:  # noqa: BLE001
                st.error(f"Question generation failed: {exc}")
    elif answered_correct:
        c1, c2, c3 = st.columns(3)
        if c1.button("← Back to concept", use_container_width=True, key="cta_back_concept_ok"):
            go_to_concept(clear_question=True)
            st.rerun()
        if c2.button("Correct, but explain why", use_container_width=True, key="cta_explain_ok"):
            try:
                go_to_tutor(
                    student_id,
                    from_stage=STAGE_PRACTICE,
                    problem_id=q["id"],
                    preset_text=presets.explain_after_correct(),
                )
                st.rerun()
            except Exception as exc:  # noqa: BLE001
                st.error(f"Could not reach the tutor: {exc}")
        if c3.button("Next question", type="primary", use_container_width=True, key="cta_next"):
            try:
                next_question()
            except Exception as exc:  # noqa: BLE001
                st.error(f"Question generation failed: {exc}")
    else:
        cta_left, cta_right = st.columns([1, 1])
        if cta_left.button("← Back to concept", use_container_width=True, key="cta_back_concept"):
            go_to_concept(clear_question=True)
            st.rerun()
        sub_col, guide_col = cta_right.columns(2)
        if sub_col.button("Submit answer", type="primary", use_container_width=True, key="cta_submit"):
            if practice_payload:
                try:
                    ss.grade = grade_answer(practice_payload)
                    st.rerun()
                except Exception as exc:  # noqa: BLE001
                    st.error(f"Grading failed: {exc}")
        if guide_col.button("I'm stuck — guide me", use_container_width=True, key="cta_guide"):
            try:
                go_to_tutor(
                    student_id,
                    from_stage=STAGE_PRACTICE,
                    problem_id=q["id"],
                    preset_text=presets.need_guidance(),
                )
                st.rerun()
            except Exception as exc:  # noqa: BLE001
                st.error(f"Could not reach the tutor: {exc}")

    if ss.grade is not None and not ss.grade.get("correct") and q is not None:
        hint_l, hint_r, retry = st.columns(3)
        if retry.button("Try again", key="cta_retry"):
            ss.grade = None
            st.rerun()
        if hint_l.button("Get a hint", key="cta_hint"):
            try:
                go_to_tutor(
                    student_id,
                    from_stage=STAGE_PRACTICE,
                    problem_id=q["id"],
                    preset_text=presets.small_hint(),
                )
                st.rerun()
            except Exception as exc:  # noqa: BLE001
                st.error(f"Could not reach the tutor: {exc}")
        if hint_r.button("Walk me through step 1", key="cta_step"):
            try:
                go_to_tutor(
                    student_id,
                    from_stage=STAGE_PRACTICE,
                    problem_id=q["id"],
                    preset_text=presets.tutor_first_step(),
                )
                st.rerun()
            except Exception as exc:  # noqa: BLE001
                st.error(f"Could not reach the tutor: {exc}")

elif stage == STAGE_TUTOR:
    cta_left, cta_right = st.columns([1, 1])
    if ss.tutor_entry == STAGE_PRACTICE:
        if cta_left.button("← Back to practice", use_container_width=True, key="cta_back_practice"):
            ss.learning_stage = STAGE_PRACTICE
            st.rerun()
        if cta_right.button("← Back to concept", use_container_width=True, key="cta_back_concept_from_tutor"):
            go_to_concept(clear_question=True)
            st.rerun()
    else:
        if cta_right.button("← Back to concept", type="primary", use_container_width=True, key="cta_back_concept_tutor"):
            go_to_concept()
            st.rerun()
