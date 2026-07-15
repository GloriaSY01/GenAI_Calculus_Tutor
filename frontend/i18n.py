"""Bilingual (English / Chinese) strings for the student and teacher pages.

Usage:
    from i18n import t, current_lang, language_toggle
    t("student.title")            # -> localized string for the active language
"""
import streamlit as st

# key -> {"en": ..., "zh": ...}
STRINGS = {
    # ---- shared ----
    "app.name": {"en": "Calculus Tutor", "zh": "微积分助教"},
    "lang.label": {"en": "Language", "zh": "语言"},
    "common.backend_error": {
        "en": "Can't reach the tutor service at",
        "zh": "无法连接后端服务：",
    },

    # ---- student sidebar ----
    "student.name_label": {"en": "Your name (optional)", "zh": "你的名字（可选）"},
    "student.sidebar_caption": {
        "en": "A guided way to learn Calculus 1: follow the path, practise, and "
              "let the tutor help you reason it out.",
        "zh": "一步步学好微积分：跟着学习路径走、动手练习，让助教引导你自己想通。",
    },
    "student.teacher_hint": {
        "en": "Teacher? The **Teacher Dashboard** runs as a separate app at "
              "`http://localhost:8502`.",
        "zh": "老师？**教师仪表盘** 是独立应用，地址：`http://localhost:8502`。",
    },

    # ---- student main ----
    "student.title": {"en": "Learn Calculus 1, step by step",
                      "zh": "一步步学习微积分 1"},
    "student.subtitle": {
        "en": "New here? Start at Step 1 and work down. Each topic builds on the "
              "ones before it.",
        "zh": "第一次来？从第 1 步开始往下学，每个知识点都建立在前面的基础上。",
    },
    "student.path_heading": {"en": "Your learning path", "zh": "你的学习路径"},
    "student.studying": {"en": "Studying", "zh": "学习中"},
    "student.start": {"en": "Start", "zh": "开始"},
    "student.step_prefix": {"en": "Step", "zh": "当前"},
    "student.best_after": {"en": "Best after:", "zh": "建议先学："},
    "student.setup_heading": {"en": "1  ·  Set up your practice",
                              "zh": "1 · 设置练习"},
    "student.difficulty": {"en": "How hard?", "zh": "难度"},
    "student.format": {"en": "Question format", "zh": "题型"},
    "student.generate": {"en": "Generate a question", "zh": "生成题目"},
    "student.generating": {"en": "Creating a question for you...",
                           "zh": "正在为你出题…"},
    "student.answer_heading": {"en": "2  ·  Answer the question", "zh": "2 · 作答"},
    "student.your_answer": {"en": "Your answer", "zh": "你的答案"},
    "student.select_all": {"en": "Select all that apply:", "zh": "选择所有正确项："},
    "student.blank": {"en": "Blank", "zh": "空格"},
    "student.drag_hint": {"en": "Drag the steps into the correct order:",
                          "zh": "把步骤拖动到正确顺序："},
    "student.submit": {"en": "Submit answer", "zh": "提交答案"},
    "student.wrong_hint": {
        "en": "Stuck? Scroll down — the tutor can walk you through it.",
        "zh": "卡住了？往下滚动，助教可以一步步带你。",
    },
    "student.help_heading": {"en": "3  ·  Get guided help", "zh": "3 · 获取引导"},
    "student.help_caption": {
        "en": "Want step-by-step help on this question without being given the "
              "answer?",
        "zh": "想在不被直接告知答案的情况下，获得这道题的逐步引导吗？",
    },
    "student.ask_tutor": {"en": "Ask the tutor about this question",
                          "zh": "就这道题向助教提问"},
    "student.linked_note": {
        "en": "The tutor is helping you with this question below.",
        "zh": "下方的助教正在帮你解决这道题。",
    },
    "student.empty_practice": {
        "en": "Pick a difficulty and format above, then click "
              "**Generate a question** to begin.",
        "zh": "先在上方选择难度和题型，然后点击 **生成题目** 开始。",
    },
    "student.tutor_heading": {"en": "Tutor", "zh": "助教"},
    "student.tutor_linked": {"en": "Helping with your", "zh": "正在帮助你解决"},
    "student.free_chat": {"en": "Free chat", "zh": "自由提问"},
    "student.tutor_free_caption": {
        "en": "Ask me anything about Calculus 1 — I'll guide you, not just give "
              "the answer.",
        "zh": "关于微积分 1 尽管问我——我会引导你，而不是直接给答案。",
    },
    "student.progress": {"en": "Your progress:", "zh": "你的进度："},
    "student.solved": {"en": "Nicely done — you reached the answer yourself!",
                       "zh": "太棒了——你自己想出了答案！"},
    "student.blocked": {
        "en": "Let's work it out together rather than jumping to the answer.",
        "zh": "我们一起一步步来，而不是直接跳到答案。",
    },
    "student.input_placeholder": {
        "en": "Type your reasoning or next step...",
        "zh": "输入你的思路或下一步…",
    },
    "student.send": {"en": "Send", "zh": "发送"},

    # ---- teacher ----
    "teacher.page_name": {"en": "Teacher Dashboard", "zh": "教师仪表盘"},
    "teacher.sidebar_caption": {
        "en": "Class-level view of how students are learning. No individual "
              "student is identified here.",
        "zh": "以班级为单位查看学生的学习情况，这里不展示任何单个学生的身份。",
    },
    "teacher.refresh": {"en": "Refresh data", "zh": "刷新数据"},
    "teacher.title": {"en": "Class overview", "zh": "班级概览"},
    "teacher.subtitle": {
        "en": "How the whole class is doing right now. Use the insights on the "
              "right to decide what to teach or assign next.",
        "zh": "全班当前的整体表现。右侧的洞察可以帮你决定接下来讲什么、布置什么。",
    },
    "teacher.kpi_students": {"en": "Students active", "zh": "活跃学生"},
    "teacher.kpi_sessions": {"en": "Sessions", "zh": "会话数"},
    "teacher.kpi_solve": {"en": "Solve rate", "zh": "解题率"},
    "teacher.kpi_reasoning": {"en": "Avg reasoning", "zh": "平均推理质量"},
    "teacher.kpi_mastery": {"en": "Avg mastery", "zh": "平均掌握度"},
    "teacher.kpi_turns": {"en": "Avg turns / session", "zh": "平均每会话轮数"},
    "teacher.kpi_gaming": {"en": "Gaming signals", "zh": "刷量/应付信号"},
    "teacher.kpi_gaming_help": {
        "en": "Share of sessions with rushing, empty replies, or 'just give me "
              "the answer' attempts.",
        "zh": "出现赶答、空洞回复或“直接给我答案”行为的会话占比。",
    },
    "teacher.kpi_guardrail": {"en": "Guardrail hits", "zh": "护栏拦截率"},
    "teacher.kpi_guardrail_help": {
        "en": "Share of turns blocked for answer-begging / prompt injection.",
        "zh": "因索要答案 / 提示注入被拦截的回合占比。",
    },
    "teacher.by_topic": {"en": "By topic", "zh": "按知识点"},
    "teacher.solve_per_topic": {
        "en": "Solve rate per topic — lower bars = class needs help",
        "zh": "各知识点解题率——柱子越低说明班级越需要补",
    },
    "teacher.reasoning_per_topic": {
        "en": "Average reasoning per topic (0–4)",
        "zh": "各知识点平均推理质量（0–4）",
    },
    "teacher.full_table": {"en": "See the full table", "zh": "查看完整表格"},
    "teacher.reasoning_dist": {
        "en": "Reasoning quality across the class",
        "zh": "全班推理质量分布",
    },
    "teacher.reasoning_dist_caption": {
        "en": "Share of tutor turns at each reasoning level. A left-heavy chart "
              "(none/weak) means students state steps without explaining why.",
        "zh": "各推理等级在所有回合中的占比。若集中在左侧（none/weak），"
              "说明学生只写步骤、不解释原因。",
    },
    "teacher.no_topic_data": {
        "en": "No topic data yet. Charts appear once students practise.",
        "zh": "暂无知识点数据。学生开始练习后会出现图表。",
    },
    "teacher.no_reasoning_data": {"en": "No reasoning data yet.",
                                  "zh": "暂无推理数据。"},
    "teacher.insights": {"en": "Insights", "zh": "洞察"},
    "teacher.insights_caption": {
        "en": "Auto-generated findings — what to look at first.",
        "zh": "自动生成的发现——先看这些。",
    },
    "teacher.ask_heading": {"en": "Ask about your class", "zh": "向助手提问"},
    "teacher.ask_caption": {
        "en": "Ask a question in plain language; the assistant answers using only "
              "your class data.",
        "zh": "用自然语言提问，助手只根据你班级的数据来回答。",
    },
    "teacher.examples": {"en": "Example questions", "zh": "示例问题"},
    "teacher.type_own": {"en": "(type your own)", "zh": "（自己输入）"},
    "teacher.ex1": {"en": "Which topic should I review next?",
                    "zh": "接下来应该复习哪个知识点？"},
    "teacher.ex2": {"en": "Are students gaming the tutor?",
                    "zh": "学生是否在应付/糊弄助教？"},
    "teacher.ex3": {"en": "How engaged is the class overall?",
                    "zh": "全班整体的参与度如何？"},
    "teacher.your_question": {"en": "Your question", "zh": "你的问题"},
    "teacher.ask": {"en": "Ask", "zh": "提问"},
    "teacher.analysing": {"en": "Analysing class data...", "zh": "正在分析班级数据…"},
    "teacher.type_first": {"en": "Type a question first.", "zh": "请先输入问题。"},
    "teacher.assign_heading": {"en": "Assign practice", "zh": "布置练习"},
    "teacher.assign_caption": {
        "en": "Create a practice assignment for the class based on what the data "
              "above suggests.",
        "zh": "根据上方数据的提示，为班级创建一个练习任务。",
    },
    "teacher.assign_title": {"en": "Assignment title", "zh": "任务标题"},
    "teacher.assign_title_ph": {"en": "e.g. Limits review — 0/0 forms",
                                "zh": "例如：极限复习——0/0 型"},
    "teacher.topic": {"en": "Topic", "zh": "知识点"},
    "teacher.format": {"en": "Format", "zh": "题型"},
    "teacher.difficulty": {"en": "Difficulty", "zh": "难度"},
    "teacher.questions": {"en": "Questions", "zh": "题目数"},
    "teacher.note": {"en": "Note to students (optional)",
                     "zh": "给学生的说明（可选）"},
    "teacher.assign_btn": {"en": "Assign to class", "zh": "布置给班级"},
    "teacher.assign_need_title": {"en": "Give the assignment a title.",
                                  "zh": "请填写任务标题。"},
    "teacher.assign_created": {"en": "Assignment created.", "zh": "任务已创建。"},
    "teacher.current_assignments": {"en": "Current assignments", "zh": "当前任务"},
    "teacher.no_assignments": {"en": "No assignments yet.", "zh": "暂无任务。"},
    "teacher.delete": {"en": "Delete", "zh": "删除"},

    # question type labels
    "qtype.single_choice": {"en": "Single choice", "zh": "单选题"},
    "qtype.multiple_choice": {"en": "Multiple choice", "zh": "多选题"},
    "qtype.fill_blank": {"en": "Fill in the blank", "zh": "填空题"},
    "qtype.drag_order": {"en": "Drag to order steps", "zh": "步骤排序"},
}


def current_lang() -> str:
    return st.session_state.get("lang", "en")


def t(key: str) -> str:
    entry = STRINGS.get(key)
    if not entry:
        return key
    return entry.get(current_lang(), entry.get("en", key))


def qtype_label(qtype: str) -> str:
    return t(f"qtype.{qtype}")
