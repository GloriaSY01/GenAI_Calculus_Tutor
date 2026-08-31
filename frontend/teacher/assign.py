"""Assign practice to the class, composed like a real worksheet.

An assignment is a list of question BLOCKS (topic x type x difficulty x count),
so one task can warm up with easy single choice, consolidate with fill-in-the-
blank and finish with a couple of hard ordering exercises. Three pedagogical
templates build such a mix in one click, and the editor shows the total
question count and a rough time estimate while composing.

Prefill from the diagnose section (`ss.assign_prefill`, set by a weak-topic
insight or the topic chart) seeds the Foundation template on that topic plus a
suggested title, so "this topic is weak" becomes a ready-to-send progressive
worksheet.

Runs as a fragment: composing, creating and deleting refresh this panel only.

Injected: `list_fn()`, `create_fn(payload)`, `delete_fn(assignment_id)`.
Payload shape: {title, note, items: [{topic, qtype, difficulty, count}]}.

NOTE: this file is kept pure ASCII (symbols via unicode escapes) because it
was once corrupted by an encoding round-trip on Windows.
"""
from __future__ import annotations

import uuid
from typing import Callable

import streamlit as st

import i18n
import ui
from i18n import t, topic_label

_DOT = "\u00b7"          # middle dot separator
_TIMES = "\u00d7"        # multiplication sign
_CROSS = "\u2715"        # delete-block button
_CHECK = "\u2705"        # toast icon
_PENCIL = "\u270f\ufe0f"  # new-assignment card icon
_CLIPBOARD = "\U0001f4cb"  # assignment-list card icon
_MEMO = "\U0001f4dd"     # note icon

QTYPES = ["single_choice", "multiple_choice", "fill_blank", "drag_order"]
DIFFICULTIES = ["easy", "medium", "hard"]
_MAX_BLOCKS = 8

# Rough minutes per question, scaled by difficulty, for the time estimate.
_EST_MIN = {"single_choice": 1.5, "multiple_choice": 2.0,
            "fill_blank": 3.0, "drag_order": 3.0}
_DIFF_MULT = {"easy": 0.8, "medium": 1.0, "hard": 1.4}

# One-click worksheet templates: (qtype, difficulty, count).
_TEMPLATES = {
    "foundation": [("single_choice", "easy", 4), ("fill_blank", "easy", 3),
                   ("single_choice", "medium", 2)],
    "mixed": [("single_choice", "medium", 3), ("multiple_choice", "medium", 2),
              ("fill_blank", "medium", 3), ("drag_order", "medium", 2)],
    "challenge": [("multiple_choice", "medium", 2), ("fill_blank", "hard", 3),
                  ("drag_order", "hard", 2)],
}


def _new_block(topic: str, qtype: str = "single_choice",
               difficulty: str = "easy", count: int = 3) -> dict:
    return {"id": uuid.uuid4().hex[:6], "topic": topic, "qtype": qtype,
            "difficulty": difficulty, "count": count}


def _template_blocks(kind: str, topic: str) -> list[dict]:
    return [_new_block(topic, q, d, c) for q, d, c in _TEMPLATES[kind]]


def _estimate_minutes(items: list[dict]) -> int:
    return max(1, round(sum(_EST_MIN[i["qtype"]] * _DIFF_MULT[i["difficulty"]]
                            * i["count"] for i in items)))


def _total_questions(items: list[dict]) -> int:
    return sum(i["count"] for i in items)


def _block_caption(item: dict) -> str:
    return (f"{topic_label(item['topic'])} {_DOT} {item['count']}{_TIMES} "
            f"{i18n.qtype_label(item['qtype'])} {_DOT} "
            f"{i18n.difficulty_label(item['difficulty'])}")


# --------------------------------------------------------------------------- #
# Form (left card)
# --------------------------------------------------------------------------- #
def _pick_template(solve_rate) -> str:
    """Match the worksheet mix to how the class is doing on this topic."""
    if solve_rate is None or solve_rate < 0.4:
        return "foundation"
    if solve_rate <= 0.7:
        return "mixed"
    return "challenge"


def _render_quick_start(ss, by_topic: list[dict]) -> None:
    """Chips for the weakest topics: one click seeds a full worksheet whose
    template matches that topic's solve rate. This is the single place where
    diagnosis turns into an assignment (Step 2 stays action-free)."""
    from teacher.topic_health import UNTIED_TOPICS
    rows = [r for r in (by_topic or []) if r["topic"] not in UNTIED_TOPICS]
    weakest = sorted(rows, key=lambda r: r["solve_rate"])[:3]
    if not weakest:
        return
    st.caption(t("teacher.assign_quick"))
    cols = st.columns(len(weakest))
    for col, row in zip(cols, weakest):
        if col.button(topic_label(row["topic"]), key=f"quick_{row['topic']}",
                      use_container_width=True):
            ss.assign_prefill = {"topic": row["topic"], "difficulty": "easy",
                                 "source": t("teacher.assign_quick_source"),
                                 "solve_rate": row["solve_rate"]}
            ui.rerun_fragment()


def _apply_prefill(ss, topics: list[str]) -> None:
    """Turn a weak-topic prefill into a ready worksheet, once."""
    prefill = ss.get("assign_prefill") or {}
    if not prefill or prefill.get("applied"):
        return
    topic = prefill.get("topic") if prefill.get("topic") in topics else topics[0]
    kind = _pick_template(prefill.get("solve_rate"))
    ss.assign_blocks = _template_blocks(kind, topic)
    ss[f"assign_title_{ss.assign_form_gen}"] = \
        t("teacher.assign_title_suggest").format(topic=topic_label(topic))
    prefill["applied"] = True
    prefill["template"] = kind


def _render_template_row(ss, topics: list[str]) -> None:
    st.caption(t("teacher.assign_templates"))
    cols = st.columns(3)
    specs = [("foundation", "teacher.tpl_foundation", "teacher.tpl_foundation_help"),
             ("mixed", "teacher.tpl_mixed", "teacher.tpl_mixed_help"),
             ("challenge", "teacher.tpl_challenge", "teacher.tpl_challenge_help")]
    base_topic = (ss.assign_blocks[0]["topic"] if ss.assign_blocks else topics[0])
    for col, (kind, label, help_key) in zip(cols, specs):
        if col.button(t(label), key=f"tpl_{kind}", help=t(help_key),
                      use_container_width=True):
            ss.assign_blocks = _template_blocks(kind, base_topic)
            ui.rerun_fragment()


def _render_blocks(ss, topics: list[str]) -> None:
    st.caption(t("teacher.assign_items_heading"))
    header = st.columns([3, 3, 2.2, 1.6, 0.8])
    for col, key in zip(header, ["teacher.topic", "teacher.format",
                                 "teacher.difficulty", "teacher.count"]):
        col.markdown(f'<span class="panel-sub">{t(key)}</span>',
                     unsafe_allow_html=True)

    for block in list(ss.assign_blocks):
        bid = block["id"]
        cols = st.columns([3, 3, 2.2, 1.6, 0.8])
        block["topic"] = cols[0].selectbox(
            "topic", topics, index=topics.index(block["topic"]),
            format_func=topic_label, key=f"blk_topic_{bid}",
            label_visibility="collapsed")
        block["qtype"] = cols[1].selectbox(
            "qtype", QTYPES, index=QTYPES.index(block["qtype"]),
            format_func=i18n.qtype_label, key=f"blk_qtype_{bid}",
            label_visibility="collapsed")
        block["difficulty"] = cols[2].selectbox(
            "difficulty", DIFFICULTIES,
            index=DIFFICULTIES.index(block["difficulty"]),
            format_func=i18n.difficulty_label, key=f"blk_diff_{bid}",
            label_visibility="collapsed")
        block["count"] = cols[3].number_input(
            "count", min_value=1, max_value=10, value=block["count"],
            key=f"blk_count_{bid}", label_visibility="collapsed")
        if cols[4].button(_CROSS, key=f"blk_del_{bid}"):
            ss.assign_blocks = [b for b in ss.assign_blocks if b["id"] != bid]
            ui.rerun_fragment()

    if len(ss.assign_blocks) < _MAX_BLOCKS:
        base_topic = (ss.assign_blocks[-1]["topic"] if ss.assign_blocks
                      else topics[0])
        if st.button(t("teacher.assign_add_block"), key="blk_add",
                     use_container_width=True):
            ss.assign_blocks.append(_new_block(base_topic))
            ui.rerun_fragment()


def _render_form(ss, topics: list[str], create_fn: Callable[[dict], dict]) -> None:
    prefill = ss.get("assign_prefill") or {}
    if prefill:
        note_col, clear_col = st.columns([4, 1])
        message = t("teacher.assign_prefill").format(source=prefill.get("source", ""))
        if prefill.get("template"):
            tpl_name = t(f"teacher.tpl_{prefill['template']}")
            message += "\n\n" + t("teacher.assign_prefill_tpl").format(tpl=tpl_name)
        note_col.info(message)
        if clear_col.button(t("teacher.assign_clear_prefill"), key="clear_prefill",
                            use_container_width=True):
            ss.assign_prefill = None
            ss.assign_blocks = [_new_block(topics[0])]
            ss.assign_form_gen += 1
            ui.rerun_fragment()

    gen = ss.assign_form_gen
    title = st.text_input(t("teacher.assign_title"),
                          placeholder=t("teacher.assign_title_ph"),
                          key=f"assign_title_{gen}")

    _render_template_row(ss, topics)
    _render_blocks(ss, topics)

    if ss.assign_blocks:
        total = t("teacher.assign_total").format(
            n=_total_questions(ss.assign_blocks),
            m=_estimate_minutes(ss.assign_blocks))
        st.markdown(
            f'<div class="stat-strip" style="grid-template-columns:1fr;margin:6px 0">'
            f'<div class="stat-item"><span class="stat-label">{total}</span>'
            f'</div></div>',
            unsafe_allow_html=True,
        )

    note = st.text_area(t("teacher.note"), height=70, key=f"assign_note_{gen}")

    if not st.button(t("teacher.assign_btn"), type="primary",
                     use_container_width=True, key="assign_submit"):
        return
    if not title.strip():
        st.warning(t("teacher.assign_need_title"))
        return
    if not ss.assign_blocks:
        st.warning(t("teacher.assign_need_items"))
        return
    try:
        create_fn({
            "title": title.strip(), "note": note.strip(),
            "items": [{"topic": b["topic"], "qtype": b["qtype"],
                       "difficulty": b["difficulty"], "count": int(b["count"])}
                      for b in ss.assign_blocks],
        })
    except Exception as exc:  # noqa: BLE001
        st.error(f"{exc}")
        return
    ss.assign_prefill = None
    ss.assign_blocks = [_new_block(topics[0])]
    ss.assign_form_gen += 1  # fresh widget keys -> cleared title/note
    st.toast(t("teacher.assign_created"), icon=_CHECK)
    ui.rerun_fragment()


# --------------------------------------------------------------------------- #
# List (right card)
# --------------------------------------------------------------------------- #
def _render_list(list_fn: Callable[[], list], delete_fn: Callable[[str], dict]) -> None:
    try:
        assignments = list_fn()
    except Exception as exc:  # noqa: BLE001
        st.error(f"{exc}")
        return

    if not assignments:
        ui.empty_state(t("teacher.no_assignments"))
        return

    # Long lists scroll in place instead of stretching the page.
    wrapper = st.container(height=460) if len(assignments) > 3 else st.container()
    with wrapper:
        _render_items(assignments, delete_fn)


def _render_items(assignments: list, delete_fn: Callable[[str], dict]) -> None:
    for item in assignments:
        blocks = item.get("items", [])
        with st.container(border=True):
            body, action = st.columns([6, 1])
            with body:
                st.markdown(f"**{item['title']}**")
                total = t("teacher.assign_total").format(
                    n=_total_questions(blocks), m=_estimate_minutes(blocks))
                st.caption(f"{total} {_DOT} {t('teacher.assign_completion')}: -")
                for block in blocks:
                    st.caption(f"{_DOT} {_block_caption(block)}")
                if item.get("note"):
                    st.caption(f"{_MEMO} {item['note']}")
            if action.button(t("teacher.delete"), key=f"del_{item['id']}",
                             use_container_width=True):
                try:
                    delete_fn(item["id"])
                except Exception as exc:  # noqa: BLE001
                    st.error(f"{exc}")
                    return
                ui.rerun_fragment()


@st.fragment
def render_assign_panel(ss, topics: list[str], *, list_fn: Callable[[], list],
                        create_fn: Callable[[dict], dict],
                        delete_fn: Callable[[str], dict],
                        by_topic: list[dict] | None = None) -> None:
    ss.setdefault("assign_form_gen", 0)
    ss.setdefault("assign_blocks", [_new_block(topics[0])])
    _apply_prefill(ss, topics)

    left, right = st.columns([3, 2], gap="medium")
    with left, st.container(border=True):
        ui.panel_header(_PENCIL, t("teacher.assign_new"), t("teacher.assign_caption"))
        _render_quick_start(ss, by_topic or [])
        _render_form(ss, topics, create_fn)
    with right, st.container(border=True):
        ui.panel_header(_CLIPBOARD, t("teacher.current_assignments"),
                        t("teacher.assign_not_connected"))
        _render_list(list_fn, delete_fn)
