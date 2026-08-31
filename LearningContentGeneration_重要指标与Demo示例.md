# Learning Content Generation 量化指标重要性说明（结合 Demo 示例）

> 依据 `量化指标体系.docx` 中 **二、量化指标 → 2. Learning Content Generation 模块** 的指标整理。Demo 示例来自当前左侧 Practice 页面：Topic = `Limits`，Difficulty = `medium`，Type = `Single choice`，题目为 `lim_{x->0}(sqrt(x+4)-2)/x`，选项包含 `1/4`、`1/2`、`0`、`Does not exist`，学生选择 `1/2` 后系统反馈正确答案为 `1/4`。

## 1. 最重要的逐题质量指标（2.1 生成内容质量）

这些指标直接决定“生成出来的题能不能给学生用”，优先级最高。

| 指标 | 重要性 | Demo 示例说明 |
|---|---|---|
| 数学正确性 (Mathematical Correctness) | 最高 | Demo 题 `lim_{x->0}(sqrt(x+4)-2)/x` 的正确答案应为 `1/4`。如果系统标注为 `1/2`，即使题面正常，也不能使用。 |
| 答案一致性 (Answer Consistency) | 最高 | Demo 中 feedback 推导结果是 `1/(sqrt(4)+2)=1/4`，页面下方也显示 `Correct answer: 1/4`，两者一致。如果解释说 `1/4`，但正确选项标成 `1/2`，就是答案一致性失败。 |
| 可解性 (Solvability) | 最高 | Demo 题虽然直接代入得到 `0/0`，但可通过有理化求解，最终有明确答案 `1/4`，所以可解性通过。若生成了条件缺失或无唯一答案的题，则不可用。 |
| 知识点对齐度 (Topic Alignment) | 很高 | Demo 中选择的 Topic 是 `Limits`，生成题确实是求极限，因此对齐。如果 Topic 选 `Limits`，却生成导数题，就是 topic alignment 失败。 |
| 难度匹配度 (Difficulty Match) | 很高 | Demo 难度为 `medium`。该题不是直接代入型，需要识别 `0/0` 并用共轭有理化，符合 medium。若生成只需直接代入的极限题，则更像 easy。 |
| 格式合规性 (Format Validity) | 很高 | Demo 题需要正确显示 `lim`、`sqrt(x+4)`、分式 `/x`。如果公式括号缺失、`$` 不配对、根号显示错误，会影响学生理解。 |
| 干扰项有效性 (Distractor Validity，仅选择题) | 很高 | Demo 的错误选项 `1/2`、`0`、`Does not exist` 应该都“看似可能但确实错误”。例如 `1/2` 可对应学生错误约分或忽略分母变化，具有诊断价值。 |
| 解题步骤连贯性 (Solution Step Coherence) | 很高 | Demo feedback 按“乘以共轭 → 化简 → 消去 x → 代入 x=0 → 得到 1/4”推进，逻辑连贯。若直接从题目跳到答案，就不利于学习。 |
| 清晰度 (Clarity) | 中高 | Demo 题干 “Evaluate the following limit” 清楚说明任务。如果题干缺少变量趋近方向或表达式排版混乱，就会有歧义。 |
| 教学相关性 (Relevance) | 中高 | Demo 题练习的是极限中的 `0/0` 和共轭有理化，属于 Calculus 1 重要知识点，有教学价值。 |

## 2. 最重要的系统过程指标（2.2 生成与验证过程）

这些指标不只看单道题，而是看生成系统是否稳定、可扩展、可持续使用。

| 指标 | 重要性 | Demo 示例说明 |
|---|---|---|
| 一次通过率 (First-pass Validation Rate) | 很高 | 学生点击 `Generate` 后，如果第一次生成的 Demo 题就通过格式、答案、选项检查并显示出来，则记为一次通过。一次通过率越高，说明生成 prompt 和验证规则越稳定。 |
| 平均重生成次数 (Average Regeneration Count) | 很高 | 如果系统生成 Demo 题时第一次输出 JSON 错误、第二次才成功，则重生成次数为 1。次数越多，说明生成质量不稳定、等待时间更长。 |
| 最终产出率 (Yield Rate) | 很高 | 学生点击生成后最终拿到可用题目，例如当前 Demo 成功显示题目，则该次产出成功。若多次重试仍失败，则产出率下降。 |
| 各检查失败分布 (Failure Breakdown) | 很高 | 如果 Demo 类题经常失败，要知道失败原因是“公式格式错”“答案错”“选项错”还是“题目不符合 Limits”。这能帮助我们定位模块问题。 |
| 选项正确性错误率 (Option Correctness Error Rate) | 最高，选择题核心 | Demo 中正确选项应是 `1/4`。如果系统把 `1/2` 标为正确，前端会错误判分，这是选择题最严重的问题之一。 |
| 填空数量不匹配率 (Blank–Answer Mismatch Rate) | 高，填空题核心 | 当前 Demo 是单选题，不涉及填空。但如果同样生成 Fill blank，题干有一个 `___`，答案列表也必须只有一个答案；否则学生无法正确提交。 |
| 生成延迟 (Generation Latency) | 中高 | 从点击 `Generate` 到 Demo 题显示的时间就是生成延迟。延迟过高会影响课堂或自学体验。 |
| 人工–自动评估一致性 (Human–Auto Agreement) | 很高 | 对 Demo 题，人工教师也会判断答案是 `1/4`，且系统也判 `1/4`，则一致。该指标用于验证自动评分是否可信。 |
| 题库覆盖度 (Coverage) | 中高 | 当前 Demo 覆盖了 `Limits × Single choice × medium` 这个组合。系统还需要覆盖 `Derivatives / Integrals`、`Multiple choice / Fill blank / Drag order`、`easy / hard` 等组合。 |

## 3. 建议重点补充的指标（结合当前 Demo）

在原有 2.1 和 2.2 基础上，下面这些补充指标也比较重要，因为它们更贴近当前 demo 的真实使用场景。

| 新增指标 | 为什么重要 | Demo 示例说明 |
|---|---|---|
| 干扰项迷惑性 (Distractor Plausibility) | 选择题质量不只看正确答案，也看错误选项是否能反映真实误区 | Demo 中 `1/2` 比 `Does not exist` 更可能对应学生的计算错误，因此迷惑性更强。 |
| 选项歧义率 (Option Ambiguity Rate) | 防止多个选项都可能被认为正确 | Demo 中只有 `1/4` 正确。如果 `1/4` 和 `0.25` 同时作为不同选项出现，就会造成歧义。 |
| 误区覆盖率 (Misconception Coverage) | 让错误选项能诊断学生薄弱点 | 学生选择 `1/2` 后，系统可推测其可能没有正确处理共轭化简；选择 `Does not exist` 则可能是不理解可去间断型极限。 |
| Tutor 可接入率 (Tutor-Ready Rate) | 左侧生成题应能交给右侧 Tutor 继续引导 | Demo 题若能通过 `to_problem()` 转成 Problem，Tutor 就可以基于该题追问：“为什么要乘以共轭？” |
| 步骤提示可用率 (Step Guidance Availability) | 支持 step-by-step 引导，而不是只显示答案 | Demo feedback 中的有理化步骤可以拆成多个 hint：先看直接代入、再想到共轭、再化简。 |
| Hint 剧透率 (Hint Answer Leakage Rate) | 确保 Tutor 不直接给答案 | 如果第一条 hint 就说“答案是 1/4”，会破坏 Socratic learning；应先提示“试试看乘以共轭”。 |
| 变体题可解率 (Variant Solvability Rate) | 检查题目生成是否稳定 | 可把 Demo 题变成 `lim_{x->0}(sqrt(x+9)-3)/x`，正确答案应为 `1/6`。若变体仍可解且答案正确，说明生成逻辑稳健。 |
| 难度漂移率 (Difficulty Drift Rate) | 防止变体题难度突然变简单或变难 | 如果把 Demo 题改成 `lim_{x->0}(x+1)`，就从 medium 变成 easy，难度漂移过大。 |

## 4. 最建议在报告中优先强调的指标

如果报告篇幅有限，建议优先写以下 8 个指标，因为它们最能体现 demo 的核心质量：

1. **数学正确性**：保证标准答案如 Demo 中 `1/4` 是对的。
2. **答案一致性**：题面、选项、feedback、correct answer 必须一致。
3. **可解性**：生成题不能欠定或无解。
4. **难度匹配度**：`medium` 应对应有一定步骤的题，如共轭有理化。
5. **知识点对齐度**：选择 `Limits` 就必须生成极限题。
6. **干扰项有效性**：错误选项要合理且确实错误。
7. **选项正确性错误率**：选择题最关键的系统级错误指标。
8. **Tutor 可接入率 / 步骤提示可用率**：体现左侧 Practice 与右侧 Tutor 的联动价值。

## 5. 可直接写入文档的总结段落

结合当前 demo，Learning Content Generation 模块中最重要的指标应优先覆盖“题目能不能用、答案对不对、是否符合学生选择的 topic/type/difficulty、以及能否支撑后续 Tutor 引导”。以 demo 中 `Limits · medium · single choice` 的极限题为例，系统不仅要生成正确答案 `1/4`，还要保证题面、选项、解析和正确答案一致；错误选项如 `1/2`、`0`、`Does not exist` 应当是合理但错误的干扰项；解析步骤应按照“识别 0/0 → 乘以共轭 → 化简 → 代入”的顺序展开。对于系统层面，还需要统计一次通过率、重生成次数、选项正确性错误率和覆盖度，以判断生成模块是否稳定。进一步地，如果生成题能够被右侧 Tutor 调用并拆解成逐步 hint，则可以更好地服务 explanation-driven learning 的整体设计。
