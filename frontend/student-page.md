# 学生页说明（Focus 模式）

Streamlit 学生端采用 **单阶段聚焦** 布局：同一时刻只展示 Concept / Practice / Tutor 中的一个，Tutor 按需进入，不再常驻右栏。

启动方式：

```powershell
uvicorn backend.main:app --host 127.0.0.1 --port 8000
streamlit run frontend/streamlit_app.py
```

---

## 整体结构

| 区域 | 作用 |
|------|------|
| **Sidebar** | 学生姓名、预置班级、收藏入口、主题目录 |
| **Stepper** | 顶部状态条，只显示当前阶段，不做假勾选 |
| **主内容区** | 根据 `learning_stage` 渲染对应面板 |
| **底部 CTA** | 各阶段统一的下一步操作按钮 |

收藏夹是独立的 `app_view`，不属于学习阶段。打开收藏夹时隐藏 Stepper，返回学习后
保留原来的 Concept / Practice / Tutor 阶段、主题和题目。

### 三个阶段

1. **Concept（学概念）** — 阅读从 MIT/Chroma 按小节加载的概念、例题、图片与引用
2. **Practice（做练习）** — 选难度、题型，答题提交；可返回概念或进 Tutor
3. **Tutor（问导师）** — 苏格拉底式对话；可从概念或练习进入

阶段常量见 `frontend/stepper.py`：`concept` / `practice` / `tutor`。

---

## 如何进入 Tutor

| 入口 | `tutor_entry` | 说明 |
|------|---------------|------|
| Concept 页「Ask the tutor」 | `concept` | 自动发「解释这个概念」类 preset |
| Practice 答错后「Get a hint」等 | `practice` | 带当前题目 `problem_id` |
| Practice「I'm stuck — guide me」 | `practice` | 带题目，请求引导 |
| 答对后「Correct, but explain why」 | `practice` | 带题目，请求讲清思路 |

进入 Tutor 时会把 `learning_stage` 设为 `tutor`，并记录 `tutor_entry` 来源。

---

## Tutor 面板布局（自上而下）

1. **Context 卡片** — 当前是概念讨论还是某道练习题
2. **Progress 进度条** — 见下文
3. **状态提示** — 已解出 / 被 guardrail 拦截等
4. **聊天记录**
5. **Suggested prompts** — 紧贴在输入框上方（最多 4 个）
6. **输入框 + Send**

相关文件：`frontend/tutor.py`、`frontend/quick_prompts.py`、`frontend/presets.py`。

---

## Suggested prompts 各阶段（重点）

逻辑在 `get_quick_prompts()`（`frontend/quick_prompts.py`）。**按优先级从上到下判断**，命中即返回对应按钮组（最多 4 个）。

### 决策流程

```
已解出 (is_solved)？
  └─ 是 → 【收尾阶段】
  └─ 否 → tutor_entry == concept 或没有题目？
            └─ 是 → 【概念阶段】
            └─ 否 → 有题目（练习入口）
                      └─ action == "blocked"（想直接要答案被拦）？
                            └─ 是 → 【被拦截】
                            └─ 否 → hint_level == 0？
                                      └─ 是 → 【练习早期】
                                      └─ 否 → 【练习进行中】

若 asks_for_explanation == true 且未解出、有题目：
  在最前面插入「Here's my reasoning」，并去掉重复项
```

### 1. 概念阶段（`tutor_entry == concept` 或尚无题目）

| 按钮 | 实际发送内容（摘要） |
|------|----------------------|
| Explain this concept | 请解释该概念、解决什么问题、给简单例子 |
| Give an example | 请给一个该主题的简单例题 |
| Common mistakes? | 学这个主题常犯什么错 |
| How used in problems? | 解题时通常怎么用这个概念 |

### 2. 练习早期（有题目，`hint_level == 0`，尚未被拦截）

| 按钮 | 实际发送内容（摘要） |
|------|----------------------|
| Hint: first step | 提示第一步，不要给完整答案 |
| Why this method? | 为什么用这种方法 |
| I'm stuck | 从第一步引导，可以提问但不给完整答案 |
| Review the concept | 回到概念解释（同概念阶段 preset） |

### 3. 练习进行中（有题目，`hint_level > 0`）

| 按钮 | 实际发送内容（摘要） |
|------|----------------------|
| Next hint | 再给一点提示 |
| Check my reasoning | 请判断我的思路对不对、下一步想什么 |
| Why this step? | 为什么这一步是对的 |
| Still confused | 用更简单的说法再讲一遍 |

### 4. 被拦截（`action == "blocked"`）

学生消息触发了 guardrail（例如直接要答案）。只显示 2 个按钮：

| 按钮 | 说明 |
|------|------|
| Next hint | 同上 |
| Still confused | 同上 |

### 5. 收尾阶段（`is_solved == true`）

| 按钮 | 实际发送内容（摘要） |
|------|----------------------|
| Explain the full solution | 逐步讲完整解法，强调推理 |
| Why does this work? | 为什么这个方法有效 |

### 6. 额外插入：Here's my reasoning

当 Tutor 上一轮返回 `asks_for_explanation: true`（希望你说明思路）时，会在**最前面**加这个按钮，文案见 `presets.offer_reasoning()`。

---

## Progress 进度条

- 显示的是 **Tutor 对话内对当前题推理掌握度**，不是练习得分，也不是概念阅读进度。
- 数值来自上一轮 API 返回的 `last_turn["mastery"]`（0–100）。
- 刚进入、还没发过消息时显示 **0%**。
- 后端规则（`backend/socratic.py`）：
  - LLM 标记 `MASTERY_GAIN=yes` → **+10%**
  - LLM 标记 `SOLVED=yes`（自己解出） → **+25%**
  - 上限 100%

---

## 关键状态字段（`streamlit_app.py` session state）

| 字段 | 含义 |
|------|------|
| `learning_stage` | 当前主阶段：`concept` / `practice` / `tutor` |
| `tutor_entry` | 从哪个阶段进的 Tutor：`concept` / `practice` / `None` |
| `current_topic` | 侧边栏选中的主题 |
| `last_turn` | 上一轮 Tutor API 返回（含 `mastery`、`hint_level`、`is_solved`、`action` 等） |
| `problem` / `question` | 练习/Tutor 绑定的题目 |
| `app_view` | 主内容视图：`learning` / `favorites` |
| `student_id` / `class_id` | 侧栏选择的学生标识和班级 |
| `favorite_records` | 当前学生的收藏题目快照 |

---

## 相关文件速查

| 文件 | 职责 |
|------|------|
| `streamlit_app.py` | 路由、阶段切换、底部 CTA |
| `stepper.py` | 阶段常量与顶部状态条 |
| `catalog.py` | 侧边栏主题列表 |
| `concept.py` | 概念面板 |
| `practice.py` | 练习面板 |
| `tutor.py` | Tutor 聊天 UI |
| `quick_prompts.py` | Suggested prompts 阶段判断 |
| `presets.py` | 各按钮对应的 preset 文案 |
| `labels.py` | 题型、难度等英文标签 |
