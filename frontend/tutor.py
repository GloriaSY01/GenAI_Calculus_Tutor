"""Tutor panel — on-demand guided help (content only, no stage navigation)."""

from __future__ import annotations

import streamlit as st

from i18n import tr
from quick_prompts import get_quick_prompts


def _context_label(
    ss, current_topic: str, tutor_entry: str | None, language: str
) -> str:
    if tutor_entry == "practice" and ss.problem is not None:
        return tr(language, "Guiding on current problem", "正在引导当前题目") + f" · {ss.problem['topic']}"
    if tutor_entry == "concept":
        return tr(language, "Concept explanation", "概念讲解") + f" · {current_topic}"
    return tr(language, "Topic", "主题") + f" · {current_topic}"


def _append_turn(ss, user_text: str, turn: dict):
    ss.messages.append({"role": "user", "content": user_text})
    ss.messages.append({
        "role": "assistant",
        "content": turn["tutor_message"],
        "citations": turn.get("citations", []),
    })
    ss.last_turn = turn


def send_preset(ss, send_message, text: str):
    turn = send_message(ss.session_id, text)
    _append_turn(ss, text, turn)
    st.rerun()


def render_tutor_panel(
    ss,
    current_topic: str,
    *,
    tutor_entry: str | None,
    instructor: bool,
    send_message,
    language: str = "en",
):
    st.markdown(f"##### {tr(language, 'Calculus tutor', '微积分导师')}")
    st.caption(_context_label(ss, current_topic, tutor_entry, language))

    with st.container(border=True):
        st.caption(tr(language, "Context", "当前上下文"))
        st.markdown(f"- **{tr(language, 'Topic', '主题')}：** {current_topic}")
        if ss.problem is not None:
            st.markdown(f"- **{tr(language, 'Problem', '题目')}：** {ss.problem['topic']}")
            st.markdown(ss.problem["statement"])
        elif ss.question is not None:
            st.markdown(f"- **{tr(language, 'Practice', '练习')}：** {ss.question['topic']}")
        goal = tr(
            language,
            "Understand {topic} and related problem-solving ideas",
            "理解 {topic} 及相关解题思路",
            topic=current_topic,
        )
        st.markdown(f"- **{tr(language, 'Goal', '目标')}：** {goal}")

    if instructor:
        cols = st.columns(4)
        cols[0].metric(tr(language, "Condition", "实验条件"), ss.condition)
        if ss.last_turn:
            cols[1].metric(tr(language, "Mastery", "掌握度"), ss.last_turn["mastery"])
            cols[2].metric(tr(language, "Hint level", "提示等级"), ss.last_turn["hint_level"])
            cols[3].metric(tr(language, "Reasoning", "推理质量"), ss.last_turn["reasoning_assessment"].title())
            signals = [
                value for value in (
                    ss.last_turn.get("safety_event"),
                    ss.last_turn.get("engagement_flag"),
                ) if value
            ]
            if signals:
                st.caption(tr(language, "Internal signals", "内部信号") + "：" + ", ".join(signals))
        st.caption(f"session_id: {ss.session_id}")
    else:
        mastery = ss.last_turn["mastery"] if ss.last_turn else 0
        st.progress(
            min(mastery, 100) / 100,
            text=f"{tr(language, 'Progress', '进度')}：{min(mastery, 100)}%",
        )
        st.caption(
            tr(
                language,
                "Based on your reasoning in this tutor session (not your practice score).",
                "此进度基于本次辅导中的推理表现，并非练习得分。",
            )
        )

    if ss.last_turn and ss.last_turn["is_solved"]:
        st.success(tr(language, "Well done — you reached the answer yourself.", "做得很好——你自己推导出了答案。"))
    elif ss.last_turn and ss.last_turn["action"] == "blocked":
        st.info(tr(language, "Let's work through this step by step rather than jumping to the answer.", "我们一步一步分析，而不是直接跳到答案。"))

    st.divider()
    for msg in ss.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            citations = msg.get("citations", [])
            if citations:
                source_url = citations[0]["url"].split("#", 1)[0]
                pages = sorted({
                    int(citation["page"])
                    for citation in citations
                    if citation.get("page")
                })
                page_text = (
                    f" · {tr(language, 'PDF pp.', 'PDF 页码')}"
                    f" {', '.join(map(str, pages))}"
                    if pages else ""
                )
                st.caption(
                    f"{tr(language, 'Source', '来源')}："
                    f"[MIT Calculus — Gilbert Strang]({source_url})"
                    f"{page_text}"
                )

    quick_prompts = get_quick_prompts(
        current_topic=current_topic,
        tutor_entry=tutor_entry,
        last_turn=ss.last_turn,
        has_problem=ss.problem is not None,
        language=language,
    )
    if quick_prompts:
        st.caption(tr(language, "Suggested prompts", "推荐问题"))
        for row_start in range(0, len(quick_prompts), 2):
            row = quick_prompts[row_start : row_start + 2]
            cols = st.columns(len(row))
            for col, prompt in zip(cols, row):
                if col.button(prompt.label, use_container_width=True, key=prompt.key):
                    send_preset(ss, send_message, prompt.message)

    with st.form("tutor_input", clear_on_submit=True):
        text = st.text_area(
            tr(language, "Your reasoning or next step", "你的推理或下一步"),
            height=80,
            label_visibility="collapsed",
            placeholder=tr(
                language,
                "Describe your reasoning or where you are stuck...",
                "请描述你的推理，或说明卡在了哪里……",
            ),
        )
        sent = st.form_submit_button(tr(language, "Send", "发送"), type="primary")
    if sent and text.strip():
        try:
            send_preset(ss, send_message, text.strip())
        except Exception as exc:  # noqa: BLE001
            st.error(
                tr(
                    language,
                    "Could not send message: {error}",
                    "消息发送失败：{error}",
                    error=exc,
                )
            )
