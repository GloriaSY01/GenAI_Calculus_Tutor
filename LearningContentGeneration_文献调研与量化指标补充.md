# Learning Content Generation 模块：文献调研与量化指标补充

> 说明：本文档是对 `量化指标体系.docx` 中 **Learning Content Generation** 模块的补充，依据当前项目代码与 `design.docx` 的系统设计整理而成。本文档不修改原始 `.docx` 文件。

## 1. 模块在当前项目中的定位

当前项目 `GenAI_Calculus_Tutor` 的 Learning Content Generation 模块主要对应左侧 **Practice** 区域，其核心代码位于 `backend/generator.py`，并通过 `backend/main.py` 暴露 `/generate` 与 `/grade` 两个接口。

该模块目前承担三类职责：

1. **生成微积分练习题**：根据题型、知识点、难度调用 LLM 生成结构化题目。
2. **隐藏标准答案并支持自动评分**：生成后的答案、解析、步骤存储在后端 `_REGISTRY` 中，前端只接收无答案版本。
3. **与 Tutor Agent 对接**：生成题目可通过 `to_problem()` 转换为 Socratic Tutor 可使用的 `Problem` 对象，使右侧 Tutor 能围绕左侧生成题进行引导。

因此，本模块不是孤立的“出题器”，而是整个学习闭环的起点：

> 知识点选择 → 题目生成 → 学生作答 → 自动评分 → Tutor 引导 → 学习行为记录与分析

## 2. 当前实现概述

### 2.1 支持的题型

当前系统支持四类题型：

| 题型 | 代码标识 | 当前用途 |
|---|---|---|
| 单选题 | `single_choice` | 训练学生识别唯一正确答案 |
| 多选题 | `multiple_choice` | 训练概念辨析与多条件判断 |
| 填空题 | `fill_blank` | 检查学生能否给出数学表达式或数值答案 |
| 拖拽排序题 | `drag_order` | 训练学生理解解题步骤顺序与过程逻辑 |

这四类题型覆盖了从结果判断到过程理解的不同认知层级。其中 `drag_order` 与项目“explanation-driven learning”的目标尤其相关，因为它要求学生关注解题过程，而不仅是最终答案。

### 2.2 支持的知识点与难度

当前 `/topics` 接口包含以下 Calculus 1 主题：

- Limits
- Derivatives
- Integrals
- Applications of Derivatives
- Continuity
- Chain Rule
- Related Rates

难度字段支持 `easy / medium / hard`，生成 prompt 会将目标难度注入给 LLM。当前难度控制主要依赖 prompt，尚未实现基于步骤数、知识点复杂度或历史正确率的自动校准。

### 2.3 结构化输出设计

生成器要求 LLM 输出 JSON，不同题型具有不同字段。例如选择题包含 `stem / options / correct_index(s) / explanation / key_idea / solution_steps`；填空题包含 `blanks`；排序题包含 `steps / final_answer / key_idea`。

这种结构化设计有三点价值：

1. **便于前端渲染**：不同题型可以被统一封装为 `GeneratedQuestionPublic`。
2. **便于自动评分**：后端可以根据题型选择不同评分逻辑。
3. **便于 Tutor 调用**：`key_idea` 与 `solution_steps` 可作为 Tutor 引导的参考材料。

## 3. 文献调研补充（去除与 `量化指标体系.docx` 重复的文献）

> 去重说明：`量化指标体系.docx` 中已经包含 `MATHWELL`、`From Objectives to Questions`、`Multi-Agent Collaborative Framework For Math Problem Generation`、`Step-Wise Formal Verification for LLM-Based Mathematical Problem Solving`，因此本节不再重复引用这些文章。下面选取 4 篇新的、可核查的会议论文/综述，补充支持本项目 `Learning Content Generation` 模块中的题目鲁棒性、过程型提示、选择题选项质量和干扰项评价。

### 文献 1：Adversarial Math Word Problem Generation

**来源**：Xie et al., Findings of EMNLP 2024. DOI: 10.18653/v1/2024.findings-emnlp.292

#### 1. 论文核心内容

这篇文章研究如何生成对抗性数学应用题。作者用抽象语法树（AST）表示题目结构，通过修改题目中的数值，在尽量保持原题结构、推理路径和难度不变的情况下，生成更容易让 LLM 解错的新题目。

#### 2. 与我们项目最相关的设计点

- 生成题目后不能只看表面是否合理，还要检查数值变化后是否仍然可解
- 难度应在题目变体之间保持稳定
- 题目结构、解题路径和标准答案需要同步验证

#### 3. 可借鉴的核心机制

- 用结构化方式表示数学题的解题逻辑
- 通过数值扰动生成同结构变体题
- 比较原题与变体题在可解性、难度和答案稳定性上的差异

#### 4. 对我们项目的启发

我们可以在内容生成模块中加入“变体题生成”：对同一类极限、导数或积分题，只改变参数值，生成一组结构相似的练习，再用 CAS 或人工抽检验证答案是否正确、步骤是否一致、难度是否漂移。

#### 5. 这篇文献支撑的项目设计点

- M3 内容生成器（变体题生成）
- M4 难度控制器（难度保持）
- M5 内容验证器（数值扰动后的可解性与答案验证）

---

### 文献 2：Automatic Generation of Socratic Subquestions for Teaching Math Word Problems

**来源**：Shridhar et al., EMNLP 2022. DOI: 10.18653/v1/2022.emnlp-main.277

#### 1. 论文核心内容

这篇文章研究如何为数学应用题自动生成苏格拉底式子问题。模型不是直接给答案，而是生成一系列逐步引导问题，帮助学生沿着合理的推理路径思考。论文还使用输入条件控制和强化学习来提升子问题质量。

#### 2. 与我们项目最相关的设计点

- 生成内容不应只包含题目和答案，也应包含引导性提示
- `solution_steps` 可以进一步拆成可教学、可追问的步骤
- 生成题目应能与右侧 Tutor Agent 联动

#### 3. 可借鉴的核心机制

- 为每个解题步骤生成对应的 Socratic subquestion
- 用连续子问题组织学生的推理过程
- 通过问题质量约束，避免提示过强或直接剧透答案

#### 4. 对我们项目的启发

当前项目已经生成 `key_idea` 和 `solution_steps`，后续可以扩展为 `hint_sequence`、`socratic_subquestions` 和 `misconception_check`，让生成题目天然带有 Tutor 可调用的教学脚手架。

#### 5. 这篇文献支撑的项目设计点

- M3 内容生成器（Hint / 子问题生成）
- M6 结构化内容数据库（保存步骤、提示与子问题）
- 与 2.2 Tutor Agent 的联动设计

---

### 文献 3：Knowledge-Driven Distractor Generation for Cloze-Style Multiple Choice Questions

**来源**：Ren & Zhu, AAAI 2021. DOI: 10.1609/aaai.v35i5.16559

#### 1. 论文核心内容

这篇文章研究多选题中的干扰项生成。作者利用知识库构建候选干扰项，再用 learning-to-rank 方法选择高质量错误选项。好的干扰项应当与正确答案相关、看起来合理，但又不能与正确答案等价或造成歧义。

#### 2. 与我们项目最相关的设计点

- 选择题不能只检查选项数量，还要检查干扰项质量
- 错误选项必须“确实错误”且具有迷惑性
- 选项不能引入多个正确答案或歧义答案

#### 3. 可借鉴的核心机制

- 用知识库或知识点关系生成候选干扰项
- 对候选干扰项进行排序和筛选
- 同时评估干扰项的相关性、迷惑性和可靠性

#### 4. 对我们项目的启发

当前项目支持单选和多选题，后续可以要求 LLM 为每个错误选项生成 `why_wrong` 和 `misconception_tag`，并用规则或人工抽检判断干扰项是否有效，避免出现“多个答案都对”或“错误选项太明显”的问题。

#### 5. 这篇文献支撑的项目设计点

- M2 题型模板库（选择题选项设计）
- M3 内容生成器（干扰项生成）
- M5 内容验证器（选项正确性与歧义检查）

---

### 文献 4：Distractor Generation in Multiple-Choice Tasks: A Survey of Methods, Datasets, and Evaluation

**来源**：Alhazmi et al., EMNLP 2024 Main. DOI: 10.18653/v1/2024.emnlp-main.799

#### 1. 论文核心内容

这是一篇关于多选题干扰项生成的系统综述，梳理了干扰项生成任务、数据集、方法和评价指标。文章指出，多选题的测评质量很大程度上取决于干扰项质量，因为好的干扰项能区分学生是真懂概念还是只是猜中答案。

#### 2. 与我们项目最相关的设计点

- 多选题质量不仅取决于正确答案，也取决于错误选项设计
- 干扰项应覆盖常见 misconception
- 需要为干扰项设置独立量化指标

#### 3. 可借鉴的核心机制

- 从相关性、迷惑性、区分度等角度评价干扰项
- 统计干扰项是否覆盖常见错误概念
- 用人工评价或 LLM rubric 补充自动规则检查

#### 4. 对我们项目的启发

在微积分题中，干扰项可以对应常见错误，例如链式法则漏乘内函数导数、极限题忽略 `0/0` 不定式、积分题漏掉常数项。这样选择题不仅能评分，还能诊断学生薄弱点。

#### 5. 这篇文献支撑的项目设计点

- M2 题型模板库（常见 misconception 干扰项模板）
- M5 内容验证器（Distractor Validity / Option Ambiguity）
- 后续学生画像与薄弱知识点诊断

### 本节参考文献列表

1. Xie, R., Huang, C., Wang, J., & Dhingra, B. (2024). *Adversarial Math Word Problem Generation*. Findings of EMNLP 2024. https://doi.org/10.18653/v1/2024.findings-emnlp.292
2. Shridhar, K., Macina, J., El-Assady, M., Sinha, T., Kapur, M., & Sachan, M. (2022). *Automatic Generation of Socratic Subquestions for Teaching Math Word Problems*. EMNLP 2022. https://doi.org/10.18653/v1/2022.emnlp-main.277
3. Ren, S., & Zhu, K. Q. (2021). *Knowledge-Driven Distractor Generation for Cloze-Style Multiple Choice Questions*. AAAI 2021. https://doi.org/10.1609/aaai.v35i5.16559
4. Alhazmi, E., Sheng, Q. Z., Zhang, W. E., Zaib, M., & Alhazmi, A. (2024). *Distractor Generation in Multiple-Choice Tasks: A Survey of Methods, Datasets, and Evaluation*. EMNLP 2024. https://doi.org/10.18653/v1/2024.emnlp-main.799

## 4. 可写入 `量化指标体系.docx` 的 2. Learning Content Generation 模块

下面内容是在 `量化指标体系.docx` 原有 **2. Learning Content Generation 模块** 的量化指标基础上整理的版本：保留原有 `2.1 生成内容质量` 和 `2.2 生成与验证过程`，并在后面补充新增指标。

## 2. Learning Content Generation 模块

### 2.1 生成内容质量

逐题评估：客观项由 CAS / 规则自动判定，主观项由人工或 LLM 打分。

| 指标名称 | 指标含义 | 评分/计算方式 |
|---|---|---|
| 数学正确性 (Mathematical Correctness) | 题目标注的最终答案在数学上是否正确 | 经记号归一化后用 SymPy/CAS 重新求解，与标注答案化简后相等=1，否则=0；无法符号化的题目改用数值抽样比对 |
| 答案一致性 (Answer Consistency) | 题面、选项、解析、最终答案之间是否相互一致 | 规则检查：单选恰好 1 个正确项、多选正确项 ≥1 且不为全部、填空 `___` 数等于答案数；全部满足=1，否则=0 |
| 干扰项有效性 (Distractor Validity，仅选择题) | 错误选项是否“看似合理但确实错误” | 每个错误选项经 CAS/规则/人工判定确为错误的比例；可附加“是否对应常见误区”的人工标注 |
| 解题步骤连贯性 (Solution Step Coherence) | 解题步骤是否逻辑连贯、每步可由上一步推出 | 0-3 分：0=步骤断裂或跳步；1=部分连贯；2=基本连贯；3=每步均可由前一步推出 |
| 可解性 (Solvability) | 题目是否有明确且可判定的答案 | 可解=1；欠定、矛盾或无解=0 |
| 难度匹配度 (Difficulty Match) | 实际难度是否与目标难度 easy / medium / hard 一致 | 以解题步数、CAS 操作数或人工/LLM 评级与目标难度比对，一致=1，否则=0 |
| 格式合规性 (Format Validity) | 公式、括号、`$` 分隔符是否配对，有无截断 | 规则检查通过=1，否则=0 |
| 知识点对齐度 (Topic Alignment) | 题目是否覆盖指定知识点 | 题目标签与目标知识点一致，或经知识库检索确认=1，否则=0 |
| 清晰度 (Clarity) | 题面表述是否无歧义、易于理解 | 0-3 分：0=有歧义/不可理解；3=表述清晰无歧义 |
| 教学相关性 (Relevance) | 题目对该知识点是否相关且有练习价值 | 0-3 分，人工或 LLM 评分 |

### 2.2 生成与验证过程

系统级聚合统计。

| 指标名称 | 指标含义 | 评分/计算方式 |
|---|---|---|
| 一次通过率 (First-pass Validation Rate) | 首次生成即通过全部验证的题目比例 | 首次通过题数 / 总生成尝试数 |
| 平均重生成次数 (Average Regeneration Count) | 一道题通过验证平均需要的重试次数 | 总重试次数 / 最终通过题数 |
| 最终产出率 (Yield Rate) | 最终可用题目占全部尝试的比例 | 通过题数 / 总尝试数，含重试 |
| 各检查失败分布 (Failure Breakdown) | 各验证检查项的失败占比，用于定位薄弱环节 | 单项检查失败次数 / 总失败次数 |
| 填空数量不匹配率 (Blank–Answer Mismatch Rate) | 填空 `___` 数与答案数不一致的比例 | 不匹配题数 / 填空题总数，目标值趋近 0 |
| 选项正确性错误率 (Option Correctness Error Rate) | 选择题标注的正确项实际为错误的比例 | 标注错误题数 / 选择题总数 |
| 生成延迟 (Generation Latency) | 平均每题生成，含验证，耗时 | 总耗时 / 题目数 |
| 人工–自动评估一致性 (Human–Auto Agreement) | 自动评分与人工评分的吻合程度，用于检验自动验证是否可信 | 两者一致的题数 / 抽检题数，或相关系数 |
| 题库覆盖度 (Coverage) | 知识点 × 题型 × 难度各组合的覆盖情况 | 已覆盖组合数 / 目标组合总数 |

### 2.3 选择题干扰项与误区诊断质量（新增）

该部分补充选择题和多选题中“错误选项”的质量评价，避免只检查答案是否正确，而忽略干扰项是否有教学价值。

| 指标名称 | 指标含义 | 评分/计算方式 |
|---|---|---|
| 干扰项迷惑性 (Distractor Plausibility) | 错误选项是否看起来合理，能反映学生可能犯的错误 | 0-3 分：0=明显错误；1=较弱迷惑性；2=基本合理；3=高度贴近常见错误 |
| 选项歧义率 (Option Ambiguity Rate) | 是否存在多个选项都可被解释为正确答案 | 有歧义选择题数 / 选择题总数 |
| 误区覆盖率 (Misconception Coverage) | 错误选项是否覆盖常见微积分误区 | 带有明确 misconception 标签的干扰项数 / 干扰项总数 |
| 干扰项多样性 (Distractor Diversity) | 错误选项是否覆盖不同错误类型，而不是重复同一错误 | 不同 misconception 类型数 / 干扰项总数 |
| 干扰项诊断价值 (Diagnostic Usefulness) | 学生选择某个错误项后，系统是否能判断其薄弱点 | 可映射到具体 misconception 的错误选项数 / 错误选项总数 |
| 错误选项过易率 (Trivial Distractor Rate) | 错误选项是否过于明显，无法区分学生理解程度 | 被人工/LLM 判为“明显错误”的干扰项数 / 干扰项总数 |

### 2.4 题目变体与鲁棒性指标（新增）

该部分用于评估生成题目在数值扰动、结构保持和难度稳定方面的质量，避免题目只在单个样例上看起来正确。

| 指标名称 | 指标含义 | 评分/计算方式 |
|---|---|---|
| 变体题可解率 (Variant Solvability Rate) | 对原题进行数值或参数变化后，新题是否仍然可解 | 可解变体题数 / 生成变体题总数 |
| 结构保持度 (Structure Preservation) | 变体题是否保持原题的解题结构和知识点 | 0-3 分：0=结构改变；3=结构基本一致 |
| 难度漂移率 (Difficulty Drift Rate) | 变体题难度是否偏离原目标难度 | 难度不一致变体题数 / 变体题总数 |
| 答案同步正确率 (Answer Update Correctness) | 题目数值变化后，标准答案是否同步更新正确 | 答案正确变体题数 / 变体题总数 |
| 解题路径一致性 (Solution Path Consistency) | 变体题是否仍可使用相同或相近的解题步骤 | 路径一致题数 / 变体题总数 |
| 数值扰动鲁棒性 (Numerical Perturbation Robustness) | 小幅数值变化后，系统生成和验证结果是否稳定 | 通过验证的扰动题数 / 数值扰动题总数 |

### 2.5 与 Tutor Agent 联动的内容可用性（新增）

该部分衡量生成内容是否能被右侧 Socratic Tutor 使用，是否支持 step-by-step 引导，而不仅是生成一道孤立题目。

| 指标名称 | 指标含义 | 评分/计算方式 |
|---|---|---|
| Tutor 可接入率 (Tutor-Ready Rate) | 生成题是否能成功转换为 Tutor 可使用的 Problem 对象 | `to_problem()` 成功数 / 生成题总数 |
| 核心思想可用率 (Key Idea Availability) | 题目是否包含可供 Tutor 引导的核心思想 | `key_idea` 非空且相关的题数 / 生成题总数 |
| 步骤提示可用率 (Step Guidance Availability) | 题目是否包含可用于逐步引导的解题步骤 | 含有效 `solution_steps` 的题数 / 生成题总数 |
| 提示层级合理性 (Hint Gradation Quality) | Hint 是否从弱提示逐步过渡到强提示，而非直接给答案 | 0-3 分：0=直接剧透；3=层级清晰、逐步推进 |
| 子问题覆盖率 (Socratic Subquestion Coverage) | 每个关键步骤是否配有引导性子问题 | 有子问题的步骤数 / 总步骤数 |
| Hint 剧透率 (Hint Answer Leakage Rate) | 生成的 hint 是否提前泄露最终答案 | 泄露答案的 hint 数 / hint 总数 |
| 误区检查覆盖率 (Misconception Check Coverage) | 是否为关键步骤设计了 misconception 检查问题 | 有误区检查的问题数 / 生成题总数 |

### 2.6 当前项目可直接报告的基础指标（新增）

结合当前项目代码，可以先报告以下 baseline 指标：

| 指标名称 | 当前项目状态 |
|---|---|
| 支持题型数量 | 4 类：single choice、multiple choice、fill blank、drag order |
| 支持知识点数量 | 7 类 Calculus 1 topic |
| 支持难度档位 | 3 档：easy、medium、hard |
| 是否隐藏标准答案 | 是，前端只返回 public question，答案保存在后端 |
| 是否支持自动评分 | 是，四类题型均支持 |
| 是否支持 Tutor 联动 | 是，生成题可通过 `to_problem()` 转换为 Tutor 使用的 Problem |
| 是否支持过程型练习 | 是，`drag_order` 题型用于训练解题步骤顺序 |
| 是否支持外部 CAS 验证 | 暂未实现，后续可扩展 |
| 是否支持自适应推荐 | 暂未实现，后续可与学生模型结合 |

## 7. 可写入最终报告的总结段落

Learning Content Generation 模块在本项目中负责生成可交互、可评分、可连接 Tutor Agent 的微积分练习内容。与传统静态题库不同，该模块基于 LLM 动态生成不同知识点、题型和难度的题目，并以结构化 JSON 形式保存题干、选项、答案、解析、核心思想和解题步骤。当前系统已支持单选、多选、填空和步骤排序四类题型，其中步骤排序题尤其服务于 explanation-driven learning 的目标，帮助学生关注解题过程而非仅仅得到最终答案。

从文献调研来看，教育内容生成的核心挑战不在于语言生成本身，而在于生成内容是否数学正确、是否符合教学目标、是否难度合适、是否可验证。现有研究普遍强调“生成—验证—优化”的闭环，以及基于知识点、题型和难度的可控生成。因此，本项目后续可在现有 LLM 出题器基础上加入内容验证器，使用规则检查、SymPy/CAS 校验和人工抽检共同评估题目质量。

在量化指标方面，本模块可从生成内容质量、自动评分质量、难度与知识点覆盖、以及与 Tutor Agent 的联动效果四个维度评估。关键指标包括 JSON 解析成功率、题型字段完整率、数学答案正确率、填空数量匹配率、正确答案回判通过率、Topic-Type-Difficulty 覆盖率、Tutor 可接入率和答案隐藏合规率。这些指标能够同时反映系统工程稳定性、数学教学质量和学习交互闭环的完整性。
