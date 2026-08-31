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
        "en": "Switch sections with the bar below: overview, diagnosis, "
              "assignments, and the data assistant.",
        "zh": "用下方导航切换：总览、学情诊断、布置练习、数据助手。",
    },
    "teacher.nav_overview": {"en": "Overview", "zh": "总览"},
    "teacher.nav_diagnose": {"en": "Diagnose", "zh": "学情诊断"},
    "teacher.nav_assign": {"en": "Assign", "zh": "布置练习"},
    "teacher.nav_assistant": {"en": "Assistant", "zh": "数据助手"},
    "teacher.guide_title": {"en": "Where to go next", "zh": "接下来看哪里？"},
    "teacher.guide_sub": {
        "en": "Each section answers a different question.",
        "zh": "每个分区回答一个不同的问题。",
    },
    "teacher.guide_diagnose": {
        "en": "Topic-by-topic detail, and whether students explain their thinking.",
        "zh": "逐个知识点看细节，以及学生会不会讲思路。",
    },
    "teacher.guide_assign": {
        "en": "Turn a weak topic into a mixed practice worksheet.",
        "zh": "把薄弱知识点变成一份混合题型的练习卷。",
    },
    "teacher.guide_assistant": {
        "en": "Ask about this class in everyday language.",
        "zh": "用大白话问这个班级的情况。",
    },
    "teacher.guide_go": {"en": "Go to {name}", "zh": "去『{name}』"},
    "teacher.kpi_students": {"en": "Students", "zh": "学生人数"},
    "teacher.kpi_sessions": {"en": "Conversations", "zh": "对话次数"},
    "teacher.kpi_solve": {"en": "Solved it", "zh": "会做的比例"},
    "teacher.kpi_reasoning": {"en": "Explains why", "zh": "讲思路"},
    "teacher.kpi_mastery": {"en": "Mastery", "zh": "掌握度"},
    "teacher.kpi_turns": {"en": "Replies per conversation", "zh": "平均对话轮数"},
    "teacher.kpi_gaming": {"en": "Low effort", "zh": "应付行为"},
    "teacher.kpi_gaming_help": {
        "en": "Share of conversations where students rushed, replied with "
              "nothing, or demanded the answer.",
        "zh": "学生乱答、秒答或直接催答案的对话占比。",
    },
    "teacher.kpi_guardrail": {"en": "Asked for the answer", "zh": "催答案被拦"},
    "teacher.kpi_guardrail_help": {
        "en": "Share of replies where a student demanded the answer and the "
              "tutor refused.",
        "zh": "学生直接要答案、被助教拦下的回复占比。",
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
        "en": "Do students explain their thinking?",
        "zh": "学生会讲自己的思路吗？",
    },
    "teacher.reasoning_dist_caption": {
        "en": "Bars piling up on the left (none / weak) mean students mostly "
              "write steps without saying why — worth probing in class.",
        "zh": "柱子堆在左边（none / weak）说明学生大多只写步骤、不说明原因，"
              "课上值得多追问。",
    },
    "teacher.no_topic_data": {
        "en": "No topic data yet. Charts appear once students practise.",
        "zh": "暂无知识点数据。学生开始练习后会出现图表。",
    },
    "teacher.no_reasoning_data": {"en": "No reasoning data yet.",
                                  "zh": "暂无推理数据。"},
    "teacher.insights": {"en": "What the data says", "zh": "数据告诉你"},
    "teacher.insights_caption": {
        "en": "Automatic findings in plain language — read these first.",
        "zh": "系统自动总结的发现——先看这里。",
    },
    "teacher.ask_heading": {"en": "Ask about your class", "zh": "问一问班级数据"},
    "teacher.ask_caption": {
        "en": "Type a question the way you'd say it — answers use only this "
              "class's data.",
        "zh": "用平常说话的方式提问，助手只根据本班数据回答。",
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

    # ---- teacher · dashboard v2 sections ----
    "teacher.sec_overview": {"en": "Step 1 · Overview", "zh": "第一步 · 看整体"},
    "teacher.sec_overview_title": {"en": "How is the class doing?",
                                   "zh": "班级学得怎么样？"},
    "teacher.sec_overview_sub": {
        "en": "Four big numbers first, then the findings the system pulled out "
              "of them. Need detail? Open Diagnose.",
        "zh": "先看四个大数字，再看系统从中总结的发现。想看细节就切到"
              "『学情诊断』。",
    },
    "teacher.sec_diagnose": {"en": "Step 2 · Diagnose", "zh": "第二步 · 找问题"},
    "teacher.sec_diagnose_title": {"en": "Where do students struggle?",
                                   "zh": "学生卡在哪里？"},
    "teacher.sec_diagnose_sub": {
        "en": "Left: which topics are weak and whether students explain their "
              "thinking. Right: their actual quiz scores.",
        "zh": "左边：哪些知识点薄弱、学生会不会讲思路；右边：他们真实的做题成绩。",
    },
    "teacher.sec_act": {"en": "Step 3 · Act", "zh": "第三步 · 布置练习"},
    "teacher.sec_act_title": {"en": "Assign targeted practice",
                              "zh": "针对性布置练习"},
    "teacher.sec_act_sub": {
        "en": "Found a weak topic? Turn it into a practice task here.",
        "zh": "发现了薄弱知识点？在这里直接变成练习任务。",
    },
    "teacher.sec_assistant": {"en": "Anytime · Assistant", "zh": "随时可用 · 数据助手"},
    "teacher.sec_assistant_title": {"en": "Not sure? Ask the data",
                                    "zh": "有疑问？直接问数据"},
    "teacher.sec_assistant_sub": {
        "en": "Ask on the left; the findings on the right are there for "
              "reference while you ask.",
        "zh": "左边提问，右边是系统总结的发现，提问时可作参考。",
    },
    "teacher.more_metrics": {"en": "Effort & attitude", "zh": "学习态度"},
    "teacher.kpi_solve_sub": {
        "en": "solved it themselves with tutor guidance",
        "zh": "在助教引导下自己算出答案的比例",
    },
    "teacher.kpi_mastery_sub": {
        "en": "0-100, estimated from tutor conversations",
        "zh": "0–100 分，根据对话情况估计",
    },
    "teacher.kpi_students_sub": {"en": "students with tutoring records",
                                 "zh": "有辅导记录的学生人数"},
    "teacher.kpi_sessions_sub": {"en": "conversations, {n} messages in total",
                                 "zh": "次师生对话，共 {n} 条消息"},
    "teacher.kpi_turns_word": {"en": "turns logged", "zh": "个回合"},
    "teacher.kpi_reasoning_help": {
        "en": "How well students explain WHY they take each step: 0 = never, "
              "4 = fully justified.",
        "zh": "学生能不能讲清『为什么这么做』：0 分完全不解释，4 分解释充分。",
    },
    "teacher.badge_sim": {"en": "includes {n} simulated sessions",
                          "zh": "含 {n} 条模拟数据"},
    "teacher.data_scope": {"en": "Data scope", "zh": "数据范围"},
    "teacher.scope_all_time": {"en": "All logged sessions",
                               "zh": "开课以来的全部记录"},
    "teacher.sidebar_stats": {"en": "{s} conversations · {m} messages",
                              "zh": "{s} 次对话 · {m} 条消息"},
    "teacher.refreshed": {"en": "Data refreshed.", "zh": "数据已刷新。"},

    # topic health
    "teacher.topic_health": {"en": "Which topics need attention",
                             "zh": "哪些知识点需要补"},
    "teacher.topic_health_sub": {
        "en": "Each row is a topic; a shorter bar means fewer students could "
              "solve it. Start from the top.",
        "zh": "一行是一个知识点，条越短说明会做的学生越少；从最上面的开始补。",
    },
    "teacher.axis_solve": {"en": "Solved it", "zh": "会做的比例"},
    "teacher.axis_topic": {"en": "Topic", "zh": "知识点"},
    "teacher.axis_attempts": {"en": "Conversations", "zh": "对话次数"},
    "teacher.axis_reasoning": {"en": "Explains why (0-4)", "zh": "讲思路 (0–4)"},
    "teacher.axis_mastery": {"en": "Mastery (0-100)", "zh": "掌握度 (0–100)"},
    "teacher.axis_gaming": {"en": "Low effort", "zh": "应付比例"},
    "teacher.free_chat_note": {
        "en": "{n} other conversation(s) were open chat with no particular "
              "topic, so they are not in this chart.",
        "zh": "另有 {n} 次对话是随便聊聊、没有对应具体知识点，不算在这张图里。",
    },
    "teacher.assign_for": {"en": "One-click practice for the weakest topics:",
                           "zh": "一键给最薄弱的知识点布置练习："},

    # reasoning quality
    "teacher.reasoning_sub": {
        "en": "Every student reply is rated on how well it explains the "
              "reasoning: none = no explanation, strong = fully justified.",
        "zh": "学生的每条回复都会被评一个『讲思路』等级：none = 完全没解释，"
              "strong = 解释得很充分。",
    },
    "teacher.axis_share": {"en": "Share of replies", "zh": "回复占比"},
    "teacher.axis_level": {"en": "Explanation level", "zh": "讲思路的程度"},
    "teacher.explain_rate": {"en": "Replied when asked to explain",
                             "zh": "被要求解释时真的解释了"},

    # condition comparison
    "teacher.condition_heading": {"en": "Teaching-style experiment",
                                  "zh": "教学方式实验对比"},
    "teacher.condition_sub": {
        "en": "Half the students must explain their thinking before the next "
              "hint (explain group); the rest get hints directly (control group).",
        "zh": "一半学生必须先讲思路才能拿到下一个提示（explain 组），"
              "另一半直接给提示（control 组）。",
    },
    "teacher.condition_explain": {"en": "Must explain first",
                                  "zh": "explain 组 · 先解释才给提示"},
    "teacher.condition_control": {"en": "Hints directly",
                                  "zh": "control 组 · 直接给提示"},
    "teacher.condition_note": {
        "en": "Research comparison only — for teaching decisions use the topic "
              "chart above.",
        "zh": "这是研究用的对比；日常教学决策请看上面的知识点图。",
    },

    # assistant
    "teacher.assistant_empty": {
        "en": "No questions yet — tap a suggestion below to start.",
        "zh": "还没有提问，点下面的问题试试。",
    },
    "teacher.assistant_placeholder": {"en": "e.g. Which topic should I reteach?",
                                      "zh": "例如：哪个知识点需要重讲？"},
    "teacher.assistant_clear": {"en": "Clear", "zh": "清空"},
    "teacher.assistant_thinking": {"en": "Reading the class data...",
                                   "zh": "正在查看班级数据…"},
    "teacher.assistant_offline": {
        "en": "The AI model is unreachable, so this is an automatic rule-based "
              "summary, not an answer to your question. Check the LLM "
              "credentials in .env.",
        "zh": "AI 模型连不上，下面是按规则自动生成的班级摘要，并不是针对你这个问题的"
              "回答。请检查 .env 里的模型配置。",
    },
    "teacher.lang_hint": {
        "en": "(Answer in plain English, addressed to a teacher.)",
        "zh": "（请用中文、面向老师的通俗语言回答。）",
    },

    # practice stats (placeholder until answer_submitted logging lands)
    "teacher.practice_stats": {"en": "Quiz scores", "zh": "做题成绩"},
    "teacher.practice_stats_sub": {
        "en": "Diagnosis data: how students actually score on practice "
              "questions, per topic — cross-checks the tutor numbers on the left.",
        "zh": "诊断数据：学生做练习题的真实对错率（按知识点），"
              "用来和左边的辅导数据互相印证。",
    },
    "teacher.practice_empty": {
        "en": "Not connected yet: students' quiz answers aren't recorded, so "
              "this card is empty for now. Once connected, completion of the "
              "assignments from Step 3 will also show up here. Note the "
              "'Solved it' number above is about tutor conversations, not "
              "quiz scores.",
        "zh": "尚未接通：学生做题的对错还没有被记录，这里暂时是空的。"
              "接通后，第三步布置任务的完成情况也会在这里体现。"
              "注意上面『会做的比例』说的是助教对话，不是做题成绩。",
    },

    # assign panel additions
    "teacher.assign_prefill": {"en": "Prefilled from: {source}",
                               "zh": "已根据「{source}」自动填好"},
    "teacher.assign_prefill_tpl": {
        "en": "Blocks generated with the \u201c{tpl}\u201d template, chosen from "
              "this topic's solve rate.",
        "zh": "已按「{tpl}」模板生成题组（根据该知识点的解题率自动选择）。",
    },
    "teacher.assign_clear_prefill": {"en": "Clear", "zh": "清除"},
    "teacher.assign_not_connected": {
        "en": "Heads-up: students can't see assignments in their app yet, so "
              "completion stays empty for now.",
        "zh": "提醒：学生端暂时还看不到布置的任务，所以完成情况先显示为空。",
    },
    "teacher.assign_completion": {"en": "Completion", "zh": "完成情况"},

    # insights (built client-side from the analytics payload; bilingual)
    "insight.weak_topic.title": {"en": "\u201c{topic}\u201d needs a re-teach",
                                 "zh": "「{topic}」最需要补课"},
    "insight.weak_topic.detail": {
        "en": "Across {n} conversation(s) on this topic, only {solve}% of "
              "students solved it and explanations averaged {reasoning}/4. "
              "Review it in class or assign easier practice first.",
        "zh": "这个知识点一共 {n} 次辅导，只有 {solve}% 的学生自己做出来，"
              "讲思路平均 {reasoning}/4 分。建议课上再讲一遍，或先布置更简单的练习。",
    },
    "insight.gaming_high.title": {
        "en": "Many students are just going through the motions",
        "zh": "不少学生在应付",
    },
    "insight.gaming_high.detail": {
        "en": "About {rate}% of conversations show rushing, empty replies or "
              "asking for the answer outright — gaming the tutor instead of "
              "thinking.",
        "zh": "约 {rate}% 的对话出现乱答、秒答或直接催答案的情况——"
              "这些学生可能在应付，而不是在思考。",
    },
    "insight.gaming_low.title": {"en": "A little low-effort behaviour",
                                 "zh": "有零星的应付行为"},
    "insight.gaming_low.detail": {
        "en": "{rate}% of conversations show rushing or empty replies. Not "
              "widespread — just keep an eye on it.",
        "zh": "{rate}% 的对话有应付迹象，还不严重，留意即可。",
    },
    "insight.low_reasoning.title": {
        "en": "Students rarely explain their thinking",
        "zh": "学生普遍不讲思路",
    },
    "insight.low_reasoning.detail": {
        "en": "Explanation quality averages just {score}/4 — most students list "
              "steps without saying why. Ask 'why did you do that?' more often.",
        "zh": "讲思路平均只有 {score}/4 分：大多数学生只写步骤、不说明原因。"
              "课上可以多追问『为什么这么做』。",
    },
    "insight.high_reasoning.title": {"en": "The class explains itself well",
                                     "zh": "全班思路讲得很好"},
    "insight.high_reasoning.detail": {
        "en": "Explanation quality averages {score}/4 — students can justify "
              "their steps. Keep it up.",
        "zh": "讲思路平均 {score}/4 分，学生能说清自己的做法，继续保持。",
    },
    "insight.coverage.title": {"en": "Still early — data is thin",
                               "zh": "数据还比较少"},
    "insight.coverage.detail": {
        "en": "Only {n} conversation(s) logged so far, so treat these findings "
              "as tentative. They firm up as students practise more.",
        "zh": "目前只记录了 {n} 次对话，以上结论仅供参考；学生用得越多，"
              "这里就越准。",
    },
    "insight.healthy.title": {"en": "Class looks healthy", "zh": "班级状态良好"},
    "insight.healthy.detail": {
        "en": "No obviously weak topic and no low-effort pattern stands out in "
              "the current data.",
        "zh": "目前没有明显的薄弱知识点，也没有明显的应付行为。",
    },

    # topic names
    "topic.Limits": {"en": "Limits", "zh": "极限"},
    "topic.Continuity": {"en": "Continuity", "zh": "连续性"},
    "topic.Derivatives": {"en": "Derivatives", "zh": "导数"},
    "topic.Chain Rule": {"en": "Chain Rule", "zh": "链式法则"},
    "topic.Applications of Derivatives": {"en": "Applications of Derivatives",
                                          "zh": "导数应用"},
    "topic.Related Rates": {"en": "Related Rates", "zh": "相关变化率"},
    "topic.Integrals": {"en": "Integrals", "zh": "积分"},
    "topic.General / Free chat": {"en": "General / Free chat", "zh": "综合 / 自由聊天"},

    # question type labels
    "qtype.single_choice": {"en": "Single choice", "zh": "单选题"},
    "qtype.multiple_choice": {"en": "Multiple choice", "zh": "多选题"},
    "qtype.fill_blank": {"en": "Fill in the blank", "zh": "填空题"},
    "qtype.drag_order": {"en": "Drag to order steps", "zh": "步骤排序"},

    # difficulty labels
    "difficulty.easy": {"en": "Easy", "zh": "简单"},
    "difficulty.medium": {"en": "Medium", "zh": "中等"},
    "difficulty.hard": {"en": "Hard", "zh": "困难"},

    # class picker (sidebar)
    "teacher.class_label": {"en": "Class", "zh": "班级"},
    "teacher.class_all": {"en": "All students", "zh": "全部学生"},
    "teacher.class_hint": {
        "en": "Class switching unlocks once a class roster is connected.",
        "zh": "接入班级名单后，这里就能切换不同班级。",
    },

    # assign panel extras
    "teacher.assign_new": {"en": "New assignment", "zh": "新任务"},
    "teacher.questions_word": {"en": "questions", "zh": "道题"},
    "teacher.assign_quick": {
        "en": "Quick worksheet for the weakest topics (template auto-picked "
              "from class data):",
        "zh": "薄弱知识点快捷组卷（按班级数据自动选模板）：",
    },
    "teacher.assign_quick_source": {"en": "class weak-topic data",
                                    "zh": "班级薄弱知识点数据"},
    "teacher.assign_items_heading": {
        "en": "Question blocks — mix types and difficulties freely",
        "zh": "题组——题型、难度可自由搭配",
    },
    "teacher.assign_add_block": {"en": "+ Add a block", "zh": "＋ 添加题组"},
    "teacher.assign_templates": {"en": "Quick templates:", "zh": "一键组卷："},
    "teacher.tpl_foundation": {"en": "Foundation", "zh": "基础巩固"},
    "teacher.tpl_foundation_help": {
        "en": "For a weak topic: warm up with easy single choice, consolidate "
              "with easy fill-in-the-blank, finish with two medium questions.",
        "zh": "适合薄弱知识点：先用简单单选热身，再用简单填空巩固，"
              "最后两道中等题小提升。",
    },
    "teacher.tpl_mixed": {"en": "Mixed practice", "zh": "综合训练"},
    "teacher.tpl_mixed_help": {
        "en": "Balanced session: all four question types at medium difficulty.",
        "zh": "均衡训练：四种题型都练到，难度中等。",
    },
    "teacher.tpl_challenge": {"en": "Challenge", "zh": "挑战拔高"},
    "teacher.tpl_challenge_help": {
        "en": "For a strong class: hard fill-in-the-blank and step-ordering, "
              "which require real understanding.",
        "zh": "适合学得好的班级：以困难填空和步骤排序为主，最考验真实理解。",
    },
    "teacher.assign_total": {"en": "{n} questions in total · about {m} min",
                             "zh": "共 {n} 道题 · 预计 {m} 分钟"},
    "teacher.assign_need_items": {"en": "Add at least one question block.",
                                  "zh": "请至少保留一个题组。"},
    "teacher.count": {"en": "How many", "zh": "题数"},
    "teacher.assign_title_suggest": {"en": "{topic} practice set",
                                     "zh": "「{topic}」巩固练习"},
    "teacher.assign_block_word": {"en": "block(s)", "zh": "个题组"},
}


def tr(language: str, english: str, chinese: str, **values) -> str:
    """Translate inline copy used by the modular student interface."""
    template = chinese if language == "zh" else english
    return template.format(**values)


def current_lang() -> str:
    return st.session_state.get(
        "language", st.session_state.get("lang", "en")
    )


def t(key: str) -> str:
    entry = STRINGS.get(key)
    if not entry:
        return key
    return entry.get(current_lang(), entry.get("en", key))


def qtype_label(qtype: str) -> str:
    return t(f"qtype.{qtype}")


def topic_label(topic: str) -> str:
    """Localized topic name; unknown topics (e.g. generated ids) pass through."""
    return t(f"topic.{topic}") if f"topic.{topic}" in STRINGS else topic


def difficulty_label(difficulty: str) -> str:
    return t(f"difficulty.{difficulty}") if f"difficulty.{difficulty}" in STRINGS \
        else difficulty
