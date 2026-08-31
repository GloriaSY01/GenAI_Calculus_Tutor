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
from catalog import fetch_catalog, render_topic_catalog, flatten_section_ids, section_title
from concept import render_concept_panel
from favorites import render_favorites_panel
from i18n import tr
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


def ui(english: str, chinese: str, **values) -> str:
    return tr(st.session_state.get("language", "en"), english, chinese, **values)


# --------------------------------------------------------------------------- #
# Backend helpers
# --------------------------------------------------------------------------- #
@st.cache_data(ttl=60)
def fetch_topics():
    r = requests.get(f"{BACKEND_URL}/topics", timeout=15)
    r.raise_for_status()
    return r.json()


@st.cache_data(ttl=60)
def fetch_classes():
    r = requests.get(f"{BACKEND_URL}/classes", timeout=15)
    r.raise_for_status()
    return r.json()


def generate_question(qtype, topic, difficulty, language):
    r = requests.post(
        f"{BACKEND_URL}/generate",
        json={
            "type": qtype,
            "topic": topic,
            "difficulty": difficulty,
            "language": language,
        },
        timeout=60,
    )
    r.raise_for_status()
    return r.json()


def grade_answer(payload):
    r = requests.post(f"{BACKEND_URL}/grade", json=payload, timeout=30)
    r.raise_for_status()
    return r.json()


def start_session(problem_id, condition, student_id, class_id, topic, language):
    r = requests.post(
        f"{BACKEND_URL}/session/start",
        json={
            "problem_id": problem_id,
            "condition": condition,
            "student_id": student_id,
            "class_id": class_id,
            "topic": topic,
            "language": language,
        },
        timeout=30,
    )
    r.raise_for_status()
    return r.json()


def fetch_favorites(student_id):
    r = requests.get(
        f"{BACKEND_URL}/favorites",
        params={"student_id": student_id},
        timeout=15,
    )
    r.raise_for_status()
    return r.json()


def save_favorite(student_id, class_id, question_id):
    r = requests.post(
        f"{BACKEND_URL}/favorites",
        json={
            "student_id": student_id,
            "class_id": class_id,
            "question_id": question_id,
        },
        timeout=15,
    )
    r.raise_for_status()
    return r.json()


def delete_favorite(student_id, question_id):
    r = requests.delete(
        f"{BACKEND_URL}/favorites/{question_id}",
        params={"student_id": student_id},
        timeout=15,
    )
    r.raise_for_status()


def send_message(session_id, text):
    r = requests.post(
        f"{BACKEND_URL}/session/{session_id}/message",
        json={"text": text, "language": st.session_state.get("language", "en")},
        timeout=60,
    )
    r.raise_for_status()
    return r.json()


def clean_label(text: str) -> str:
    return re.sub(r"\$", "", text).strip()


def current_section_title(section_id: str | None = None) -> str:
    sid = section_id or st.session_state.get("current_topic")
    try:
        return section_title(fetch_catalog(BACKEND_URL), sid)
    except Exception:
        return sid or ""


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
ss.setdefault("app_view", "learning")
ss.setdefault("student_id", "")
ss.setdefault("class_id", "demo")
ss.setdefault("favorite_records", [])
ss.setdefault("language", "en")


def clear_practice():
    ss.question = None
    ss.grade = None


def start_tutor(problem_id, student_id, class_id):
    condition = random.choice(["explain", "control"])
    data = start_session(
        problem_id,
        condition,
        student_id.strip() or "anon",
        class_id,
        ss.current_topic,
        ss.language,
    )
    ss.session_id = data["session_id"]
    ss.problem = data.get("problem")
    ss.condition = data["condition"]
    ss.messages = [{
        "role": "assistant", "content": data["opening_message"], "citations": []
    }]
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
    ss.question = generate_question(qtype, ss.current_topic, difficulty, ss.language)
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
        start_tutor(problem_id, student_id, ss.class_id)

    if preset_text:
        turn = send_message(ss.session_id, preset_text)
        ss.messages.append({"role": "user", "content": preset_text})
        ss.messages.append({
            "role": "assistant",
            "content": turn["tutor_message"],
            "citations": turn.get("citations", []),
        })
        ss.last_turn = turn


def select_topic(topic: str):
    ss.app_view = "learning"
    if topic == ss.current_topic:
        st.rerun()
        return
    if ss.learning_stage in (STAGE_PRACTICE, STAGE_TUTOR):
        ss.pending_topic = topic
    else:
        ss.current_topic = topic
        st.toast(
            ui(
                "Switched to {topic}",
                "已切换到 {topic}",
                topic=current_section_title(topic),
            )
        )
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
    ss.question = generate_question(qtype, ss.current_topic, difficulty, ss.language)
    ss.grade = None


def next_question():
    regenerate_question()
    st.rerun()


def refresh_favorites(student_id: str):
    ss.favorite_records = (
        fetch_favorites(student_id.strip()) if student_id.strip() else []
    )


def toggle_current_favorite(student_id: str, class_id: str):
    q = ss.question
    if q is None or not student_id.strip():
        return
    favorite_ids = {item["question_id"] for item in ss.favorite_records}
    if q["id"] in favorite_ids:
        delete_favorite(student_id.strip(), q["id"])
    else:
        save_favorite(student_id.strip(), class_id, q["id"])
    refresh_favorites(student_id)


def remove_saved_favorite(student_id: str, question_id: str):
    delete_favorite(student_id.strip(), question_id)
    refresh_favorites(student_id)


# --------------------------------------------------------------------------- #
# Data load
# --------------------------------------------------------------------------- #
try:
    catalog = fetch_catalog(BACKEND_URL)
    classes = fetch_classes()
    section_ids = flatten_section_ids(catalog)
except Exception as exc:  # noqa: BLE001
    st.error(
        ui(
            "Cannot reach the backend ({url}):\n\n{error}",
            "无法连接后端（{url}）：\n\n{error}",
            url=BACKEND_URL,
            error=exc,
        )
    )
    st.stop()

if ss.current_topic is None or ss.current_topic not in section_ids:
    ss.current_topic = catalog.get("default_section_id") or section_ids[0]

class_ids = [item["id"] for item in classes]
class_labels = {item["id"]: item["label"] for item in classes}
if ss.class_id not in class_ids:
    ss.class_id = class_ids[0]


def display_class_label(value: str) -> str:
    label = class_labels[value]
    if ss.language != "zh":
        return label
    return {
        "demo": "演示班级",
        "calc1-a": "微积分 I · A 班",
        "calc1-b": "微积分 I · B 班",
    }.get(value, label)


# --------------------------------------------------------------------------- #
# Sidebar
# --------------------------------------------------------------------------- #
with st.sidebar:
    st.header("∫ Calculus Tutor")
    student_id = st.text_input(
        ui("Your name (optional)", "你的姓名（可选）"), key="student_id"
    ).strip()
    class_id = st.selectbox(
        ui("Class", "班级"),
        class_ids,
        format_func=display_class_label,
        key="class_id",
    )
    if not student_id:
        st.caption(ui("Enter your name to save personal favorites.", "输入姓名后可保存个人收藏。"))
    if ss.app_view == "favorites":
        if st.button(ui("← Back to learning", "← 返回学习"), use_container_width=True):
            ss.app_view = "learning"
            st.rerun()
    elif st.button(ui("☆ Favorites", "☆ 收藏"), use_container_width=True):
        ss.app_view = "favorites"
        st.rerun()
    st.divider()
    render_topic_catalog(
        catalog,
        ss.current_topic,
        on_select=select_topic,
        language=ss.language,
    )
    if INSTRUCTOR:
        st.divider()
        st.caption(ui("Instructor mode is ON.", "教师模式已开启。"))
    st.divider()
    language_label = "中文" if ss.language == "en" else "English"
    if st.button(f"🌐 {language_label}", use_container_width=True, key="language_toggle"):
        ss.language = "zh" if ss.language == "en" else "en"
        st.rerun()

# --------------------------------------------------------------------------- #
# Main layout
# --------------------------------------------------------------------------- #
st.title("Calculus Tutor")

try:
    refresh_favorites(student_id)
except Exception as exc:  # noqa: BLE001
    ss.favorite_records = []
    st.warning(
        ui(
            "Favorites are temporarily unavailable: {error}",
            "收藏功能暂时不可用：{error}",
            error=exc,
        )
    )

if ss.app_view == "favorites":
    render_favorites_panel(
        ss.favorite_records,
        student_id=student_id,
        on_remove=lambda question_id: remove_saved_favorite(
            student_id, question_id
        ),
        language=ss.language,
    )
    st.stop()

if ss.pending_topic:
    st.warning(
        ui(
            "Switching to **{topic}** will return you to the concept step and "
            "clear your current practice progress.",
            "切换到 **{topic}** 将返回概念学习阶段，并清除当前练习进度。",
            topic=current_section_title(ss.pending_topic),
        )
    )
    c1, c2 = st.columns(2)
    if c1.button(ui("Confirm", "确认"), type="primary", key="confirm_topic"):
        confirm_topic_switch()
    if c2.button(ui("Cancel", "取消"), key="cancel_topic"):
        cancel_topic_switch()
    st.stop()

render_stepper(ss.learning_stage, ss.language)
st.divider()

stage = ss.learning_stage
practice_payload = None

if stage == STAGE_CONCEPT:
    render_concept_panel(ss.current_topic, BACKEND_URL, ss.language)

elif stage == STAGE_PRACTICE:
    practice_payload = render_practice_panel(
        ss,
        current_topic=current_section_title(),
        clean_label=clean_label,
        on_difficulty_change=regenerate_question,
        is_favorite=(
            ss.question is not None
            and ss.question["id"] in {
                item["question_id"] for item in ss.favorite_records
            }
        ),
        can_favorite=bool(student_id),
        on_favorite_toggle=lambda: toggle_current_favorite(
            student_id, class_id
        ),
        language=ss.language,
    )

elif stage == STAGE_TUTOR:
    render_tutor_panel(
        ss,
        current_section_title(),
        tutor_entry=ss.tutor_entry,
        instructor=INSTRUCTOR,
        send_message=send_message,
        language=ss.language,
    )

# --------------------------------------------------------------------------- #
# Bottom CTAs (unified per stage)
# --------------------------------------------------------------------------- #
st.divider()

if stage == STAGE_CONCEPT:
    cta_left, cta_right = st.columns([1, 1])
    if cta_left.button(
        ui("Ask the tutor", "询问导师"),
        use_container_width=True,
        key="cta_ask_tutor",
    ):
        try:
            go_to_tutor(
                student_id,
                from_stage=STAGE_CONCEPT,
                preset_text=presets.explain_concept(
                    current_section_title(), ss.language
                ),
            )
            st.rerun()
        except Exception as exc:  # noqa: BLE001
            st.error(ui("Could not reach the tutor: {error}", "无法连接导师：{error}", error=exc))
    if cta_right.button(
        ui("Start practice", "开始练习"),
        type="primary",
        use_container_width=True,
        key="cta_practice",
    ):
        try:
            with st.spinner(ui("Generating a question...", "正在生成题目……")):
                go_to_practice(student_id)
            st.rerun()
        except Exception as exc:  # noqa: BLE001
            st.error(ui("Question generation failed: {error}", "题目生成失败：{error}", error=exc))

elif stage == STAGE_PRACTICE:
    q = ss.question
    answered_correct = ss.grade is not None and ss.grade.get("correct")

    if q is None:
        cta_left, cta_right = st.columns([1, 1])
        if cta_left.button(ui("← Back to concept", "← 返回概念"), use_container_width=True, key="cta_back_concept"):
            go_to_concept(clear_question=True)
            st.rerun()
        if cta_right.button(ui("Generate again", "重新生成"), type="primary", use_container_width=True, key="cta_regen"):
            try:
                go_to_practice(student_id)
                st.rerun()
            except Exception as exc:  # noqa: BLE001
                st.error(ui("Question generation failed: {error}", "题目生成失败：{error}", error=exc))
    elif answered_correct:
        c1, c2, c3 = st.columns(3)
        if c1.button(ui("← Back to concept", "← 返回概念"), use_container_width=True, key="cta_back_concept_ok"):
            go_to_concept(clear_question=True)
            st.rerun()
        if c2.button(ui("Correct, but explain why", "答对了，但解释原因"), use_container_width=True, key="cta_explain_ok"):
            try:
                go_to_tutor(
                    student_id,
                    from_stage=STAGE_PRACTICE,
                    problem_id=q["id"],
                    preset_text=presets.explain_after_correct(ss.language),
                )
                st.rerun()
            except Exception as exc:  # noqa: BLE001
                st.error(ui("Could not reach the tutor: {error}", "无法连接导师：{error}", error=exc))
        if c3.button(ui("Next question", "下一题"), type="primary", use_container_width=True, key="cta_next"):
            try:
                next_question()
            except Exception as exc:  # noqa: BLE001
                st.error(ui("Question generation failed: {error}", "题目生成失败：{error}", error=exc))
    else:
        cta_left, cta_right = st.columns([1, 1])
        if cta_left.button(ui("← Back to concept", "← 返回概念"), use_container_width=True, key="cta_back_concept"):
            go_to_concept(clear_question=True)
            st.rerun()
        sub_col, guide_col = cta_right.columns(2)
        if sub_col.button(ui("Submit answer", "提交答案"), type="primary", use_container_width=True, key="cta_submit"):
            if practice_payload:
                try:
                    ss.grade = grade_answer({
                        **practice_payload,
                        "student_id": student_id or "anon",
                        "class_id": class_id,
                    })
                    st.rerun()
                except Exception as exc:  # noqa: BLE001
                    st.error(ui("Grading failed: {error}", "判分失败：{error}", error=exc))
        if guide_col.button(ui("I'm stuck — guide me", "我卡住了——请引导我"), use_container_width=True, key="cta_guide"):
            try:
                go_to_tutor(
                    student_id,
                    from_stage=STAGE_PRACTICE,
                    problem_id=q["id"],
                    preset_text=presets.need_guidance(ss.language),
                )
                st.rerun()
            except Exception as exc:  # noqa: BLE001
                st.error(ui("Could not reach the tutor: {error}", "无法连接导师：{error}", error=exc))

    if ss.grade is not None and not ss.grade.get("correct") and q is not None:
        hint_l, hint_r, retry = st.columns(3)
        if retry.button(ui("Try again", "重试"), key="cta_retry"):
            ss.grade = None
            st.rerun()
        if hint_l.button(ui("Get a hint", "获取提示"), key="cta_hint"):
            try:
                go_to_tutor(
                    student_id,
                    from_stage=STAGE_PRACTICE,
                    problem_id=q["id"],
                    preset_text=presets.small_hint(ss.language),
                )
                st.rerun()
            except Exception as exc:  # noqa: BLE001
                st.error(ui("Could not reach the tutor: {error}", "无法连接导师：{error}", error=exc))
        if hint_r.button(ui("Walk me through step 1", "引导我完成第一步"), key="cta_step"):
            try:
                go_to_tutor(
                    student_id,
                    from_stage=STAGE_PRACTICE,
                    problem_id=q["id"],
                    preset_text=presets.tutor_first_step(ss.language),
                )
                st.rerun()
            except Exception as exc:  # noqa: BLE001
                st.error(ui("Could not reach the tutor: {error}", "无法连接导师：{error}", error=exc))

elif stage == STAGE_TUTOR:
    cta_left, cta_right = st.columns([1, 1])
    if ss.tutor_entry == STAGE_PRACTICE:
        if cta_left.button(ui("← Back to practice", "← 返回练习"), use_container_width=True, key="cta_back_practice"):
            ss.learning_stage = STAGE_PRACTICE
            st.rerun()
        if cta_right.button(ui("← Back to concept", "← 返回概念"), use_container_width=True, key="cta_back_concept_from_tutor"):
            go_to_concept(clear_question=True)
            st.rerun()
    else:
        if cta_right.button(ui("← Back to concept", "← 返回概念"), type="primary", use_container_width=True, key="cta_back_concept_tutor"):
            go_to_concept()
            st.rerun()
