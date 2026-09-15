# 下一步工作计划 / Next Steps Plan

> 依据：Meng（代表本人及林教授）于评审后的反馈邮件 + 现有设计文档
> （`reference/ARIN7600_Capstone_Design.docx`）+ 当前原型代码。
> 目标：从「可演示的 demo」过渡到「可靠、可测试、可做研究」的系统。

---

## 0. 反馈摘要（导师 4 条意见）

| # | 优先级 | 主题 | 一句话要求 |
|---|---|---|---|
| 1 | **P0（最高）** | 内容验证模块 Content Validator | 题目在给学生用之前，必须验证数学正确性、答案一致性、格式、填空数量、解题步骤连贯性 |
| 2 | P1 | 苏格拉底导师对话状态管理 | 对话状态要更明确稳定；学生解释得好时要**显式肯定**并给针对性追问；内部状态标签（reasoning/hint/mastery/solved）要和**呈现给学生的反馈**紧密对应 |
| 3 | P1 | 学习分析与埋点 | 把参与度/学习分析的「构想」落成**可计算的具体指标**：记录哪些事件、每个指标怎么算、如何支撑最终评估 |
| 4 | P1 | 实验计划 | 明确研究问题、假设、对比条件、结果指标、分析计划（围绕 explanation-driven learning / explain-to-unlock） |

---

## 1. 现状速览（已完成 vs. 差距）

**已完成（demo 跑通）：**
- 后端 FastAPI（`backend/`）：题目生成 `/generate`、判分 `/grade`、苏格拉底会话 `/session/*`、主题 `/topics`。
- 内容生成 `backend/generator.py`：单选 / 多选 / 填空 / 拖拽排序 4 种题型 + 自动判分。
- 苏格拉底 Agent `backend/socratic.py`：line-based 结构化输出（ASSESSMENT/ACTION/ASKS_EXPLANATION/SOLVED/MASTERY_GAIN/MESSAGE）、explain-to-unlock、guardrail、free chat / 关联题目两种模式。
- 前端 `frontend/streamlit_app.py`：左右两块（练习 + 助教）、学生/老师双视图。
- 逐轮日志 `backend/store.py` + 分析脚本 `scripts/analyze_logs.py`（explain vs control 对比图）。

**关键差距（对应导师意见）：**
- ❌ **没有内容验证器**（设计文档 M5 仅在图上，未实现）。已观测到：填空 `___` 个数与答案数不一致、多选有冗余正确项、选项正确性偶有问题。
- ⚠️ 对话状态由每轮 LLM 输出**临时推断**，无显式状态机；学生优秀解释时缺少**明确肯定**；内部标签与学生可见反馈未强绑定。
- ⚠️ 日志只有 `latency_ms`（LLM 响应时间，**不是**学生 time-on-task）、缺 hint 使用 / 解释长度 / verification / 前后测等事件；指标定义未文档化。
- ⚠️ 实验计划（RQ / 假设 / 条件 / 指标 / 分析）尚未成文。

---

## 2. P0 — 内容验证模块（Content Validator）

### 2.1 目标
任何题目在进入题库 / 呈现给学生**之前**，必须通过一套验证；不通过则自动重生成（有限次）或丢弃，并记录验证报告。对应设计文档模块 **M5**。

### 2.2 导师原话
> 「在向学生实际使用这些生成题目之前，请增加针对数学正确性、答案一致性、格式、填空数量以及解题步骤连贯性的验证机制。采用基于规则的检查、SymPy/CAS 以及基于 RAG 的一致性检查。」

### 2.3 三层验证（建议落地顺序）

**A. 规则检查（Rule-based，先做，零依赖、收益最大）**
- 通用：所有字段非空；`stem` / `options` / `solution_steps` 不为空。
- 单选：恰好 1 个正确项；选项 ≥ 3 且互不重复（去空格/大小写后）。
- 多选：正确项 ≥ 1 且 **不等于全部**；选项互不重复。
- **填空：`stem` 中 `___` 标记数量 == `blanks` 数量**（直接修掉导师指出的 bug）。
- 拖拽排序：步骤 ≥ 3、互不重复、打乱后 ≠ 原顺序。
- 选项/答案格式：括号配平、`$...$` 配对、无明显截断。

**B. CAS / SymPy 数学正确性（核心）**
- 加一个**记号归一化层**：把我们生成的简洁记号（`^`→`**`、隐式乘法、`sqrt()`、`/`、`lim_{x->a}`、`integral`、`d/dx`）转成 SymPy 可解析表达式。
- 按题型/知识点校验：
  - 导数题：`sympy.diff` 重算，和标注答案 `simplify(a-b)==0` 比对。
  - 积分题：`sympy.integrate`（不定积分按导数反验，定积分数值/符号比对）。
  - 极限题：`sympy.limit` 比对。
  - 选择题：验证**标注正确项确实正确**，且**干扰项确实错误**（逐项算）。
- 解析失败/无法符号验证的，降级为「人工标记 + 数值抽样验证」。

**C. RAG 一致性检查（增强）**
- 建一个小知识库（教材片段 / 公式 / 规则，对应设计文档 M3「知识库/RAG」与 M1「知识点组织器」）。
- 检查 stem ↔ solution_steps ↔ final_answer 三者一致、且解法引用的规则在知识库中存在；输出「依据来源」（也服务于 Agent 的「每步引导有理论依据」目标）。

### 2.4 工程落地
- 新文件 `backend/validator.py`：`validate(question_record) -> ValidationReport{passed, checks:[{name,passed,detail}], severity}`。
- 新依赖：`sympy`（写入 `requirements.txt`）。
- 改 `backend/generator.py`：生成后进入 `validate`，失败则重生成（最多 N=2 次），仍失败则丢弃并报错；`/generate` 只返回通过验证的题。
- 记录：每道题保存 `validation_report`，老师视图可见（埋点：生成数、通过率、各检查失败分布）。

### 2.5 验收标准
- 4 种题型各跑 ≥ 50 道，规则检查 100% 自洽；填空 `___`/答案数不匹配率 = 0。
- 可符号验证的题型（导/积/极限）数学正确率 ≥ 95%（抽检）。
- `/generate` 返回的题 100% 带 `validation_report` 且 `passed=true`。

---

## 3. P1 — 苏格拉底导师对话状态管理

### 3.1 目标
让对话有**显式、稳定的状态机**，并把内部标签和学生看到的反馈强绑定；学生解释得好时给出**明确肯定 + 针对性后续引导**。

### 3.2 导师原话
> 「对话状态的管理应更加明确和稳定……当学生给出精彩的解释时，应更明确地肯定其推理，并给出针对性后续引导……将内部状态标签（推理质量、提示层级、掌握程度、解题状态）与实际呈现给学生的反馈内容更紧密对应。」

### 3.3 具体任务
- **显式状态机**：在 `Session` 中持久化 `dialogue_state`，如
  `AWAITING_FIRST_ATTEMPT → AWAITING_EXPLANATION → EVALUATING → ADVANCING → (next step | SOLVED)`；
  状态转移由「上一轮状态 + 本轮 ASSESSMENT/ACTION」决定，而非每轮全靠 LLM 重新推断。
- **肯定话术**：当 `ASSESSMENT ∈ {adequate, strong}`，要求 MESSAGE 必须含一句**具体的**肯定（指出对在哪），再给下一步；在 prompt 中强制，并在 UI 上用「✓ 推理被认可」标识。
- **标签↔反馈对齐**：
  - explain 与 control 两条件用**同一套**评估（已部分实现，需固化）。
  - UI（老师视图）展示的 reasoning/hint/mastery/solved 必须来自同一份 turn 记录，避免漂移。
  - mastery 增量规则文档化（当前：mastery_gain +10、solved +25），并校准。
- **稳健性**：保留「LLM 失败兜底」，但区分「兜底回复」与正常回复（打标，避免污染分析）。

### 3.4 涉及文件
`backend/socratic.py`（状态机 + prompt 调整）、`backend/store.py`（持久化 state）、`backend/schemas.py`（TutorTurn 增字段：`dialogue_state`、`is_fallback`）、`frontend/streamlit_app.py`（认可标识）。

### 3.5 验收标准
- 每轮返回带 `dialogue_state`；状态转移在脚本回放中确定、可复现。
- 给出强解释的样例对话中，100% 出现明确肯定 + 针对性追问。
- 老师视图标签与日志记录逐字段一致。

---

## 4. P1 — 学习分析与埋点（Metrics & Logging Spec）

### 4.1 目标
把「参与度/学习分析」从构想变成**有定义、可计算、可复现**的指标体系，并明确每个指标如何支撑最终评估。

### 4.2 待补的事件日志 schema（在 `store.py` 扩展）
建议统一事件流（每行一个 JSON 事件）：

| event | 关键字段 | 用途 |
|---|---|---|
| `session_start` | session_id, condition, student_id, problem_id/free | 分组 |
| `question_generated` | qid, type, topic, difficulty, validation_passed | 内容质量 |
| `answer_submitted` | qid, correct, **time_to_answer_ms**, attempt_no | 解题率 / 耗时 |
| `hint_requested` / turn(action) | hint_level, action | hint 使用 |
| `explanation_submitted` | text_len_words, **client_think_ms** | 解释长度 / time-on-task |
| `verification_question` | passed | 真实性验证 |
| `feedback_clicked` | type（懂了/要提示/没看懂/评分） | 反馈 |
| `guardrail_hit` | category, side | 防作弊/越狱 |
| `session_end` | duration_ms, turns | 总览 |

> ⚠️ 关键修正：当前 `latency_ms` 是 LLM 响应时间，**不能**当 time-on-task。需在**前端记录客户端时间戳**（学生看到题/收到回复 → 提交）并随请求上报。

### 4.3 指标定义（写成可计算公式）
- **Reasoning quality**：ASSESSMENT 映射 none/weak/partial/adequate/strong = 0/1/2/3/4，取会话均值。
- **Explanation length**：学生解释类消息的词数均值/中位数。
- **Hint usage**：hint/advance/correct 类动作次数 或 显式 hint 请求次数 / 每题。
- **Solve rate**：is_solved=true 的会话占比（或题目占比）。
- **Time-on-task**：客户端 think_ms 之和（排除 idle 超阈值）。
- **Pre/Post gain**：前测/后测同质题正确率之差（需引入前后测，见 §5）。
- **Perceived helpfulness**：课后 Likert 量表均分。

### 4.4 落地
- 扩展 `backend/store.py` 事件类型 + `frontend` 客户端计时上报。
- 升级 `scripts/analyze_logs.py`：按新 schema 出表/图，含上述全部指标的 explain vs control 对比。
- 老师视图（`?instructor=1`）接入实时 dashboard（对应设计文档 M7 / Instructor View）。

### 4.5 验收标准
- 一次完整会话能产出上表所有事件；`analyze_logs` 能算出 §4.3 全部指标且无缺失。

---

## 5. P1 — 实验计划（Study Design）

### 5.1 目标
把 explain-to-unlock 写成一个**可执行、可发表**的小规模研究方案。

### 5.2 建议框架（待团队/导师确认后定稿）
- **研究问题 RQ**
  - RQ1：相比普通提示（control），强制解释（explain-to-unlock）是否提升学习增益（pre/post gain）？
  - RQ2：两条件在 reasoning quality、解释长度、解题率、time-on-task 上有何差异？
  - RQ3：解释质量是否与学习增益相关？
- **假设 H**
  - H1：explain 组 pre/post gain 显著高于 control。
  - H2：explain 组 reasoning quality 与解释长度更高（代价可能是 time-on-task 更长）。
- **设计**：被试内或被试间随机分组（系统已支持随机分配 condition）；同质前后测；可控在线实验 + 课堂小样本。
- **结果指标**：§4.3 全部（主指标 = pre/post gain；过程指标 = reasoning/解释长度/hint/解题率/耗时；主观 = perceived helpfulness）。
- **分析计划**：组间用 t 检验 / Mann-Whitney；增益用 ANCOVA（前测为协变量）；相关用 Spearman；报告效应量。
- **样本与流程**：目标 N、招募、知情同意、题目集（经 §2 验证）、前测→学习→后测→问卷。

### 5.3 产出物
`reference/Study_Design.md`（独立文档，定稿后用于 IRB/伦理与最终报告）。

---

## 6. 建议里程碑（4–6 周，可按实际调整）

| 阶段 | 内容 | 关键产出 |
|---|---|---|
| 周 1 | P0-A 规则检查 + 填空 bug 修复；接入 SymPy 骨架 | `validator.py` v1、`/generate` 接验证 |
| 周 2 | P0-B CAS 数学验证（导/积/极限/选择）；验证报告埋点 | 数学正确率抽检报告 |
| 周 3 | P1 对话状态机 + 肯定话术 + 标签对齐 | `socratic.py` 状态机、UI 认可标识 |
| 周 4 | P1 埋点 schema + 客户端计时 + 指标脚本升级 | 新日志 + `analyze_logs` v2 + dashboard |
| 周 5 | P1 实验计划定稿 + 题集冻结 + 预实验（pilot） | `Study_Design.md`、pilot 数据 |
| 周 6 | 机动：RAG 一致性检查 / 修复 / 正式小规模研究 | 研究数据与初步分析 |

---

## 7. 风险与依赖
- **记号→SymPy 解析**是 P0 的最大技术风险：需要稳健的归一化与失败降级（数值抽样）。
- **time-on-task** 必须前端配合上报，否则指标不成立。
- **前后测题目同质性**直接影响 gain 的可信度，需配合 §2 的验证保证质量。
- LLM API（yunwu.ai）稳定性与成本：验证重生成会增加调用量，需评估。

---

## 8. 立即可做的「快速胜利」（本周）
1. 修复填空 `___` 数 == 答案数（规则检查最小版）。
2. 多选「不能全部正确 / 选项去重」规则。
3. 前端记录并上报 `time_to_answer_ms` / `client_think_ms`。
4. 起草 `Study_Design.md` 骨架（RQ/假设/条件/指标）。
