# Exercise Bank Expansion & Difficulty Calibration Plan

## 1. 目标

本阶段主要完成两个任务：

1. **增加外部高质量微积分习题来源**
   - 在现有 Gilbert Strang《Calculus》教材知识库基础上，引入额外的 MIT 习题资源；
   - 将外部习题映射到当前系统已有的 Chapter / Section / Knowledge Point；
   - 避免与原教材已有 Examples / Exercises 大量重复。

2. **建立统一的 Easy / Medium / Hard 难度标准**
   - 不再仅依赖 LLM 自己判断题目难度；
   - 根据数学教育相关研究建立初始 Difficulty Rubric；
   - 使用该 Rubric 约束 LLM 生成题目；
   - 后续通过 Human Study，根据真实学生表现校准难度标签。

---

## 2. External Exercise Sources

### 2.1 当前已有资源：Gilbert Strang《Calculus》

当前知识库已经基于 MIT OCW 的 Gilbert Strang《Calculus》Chapter 1–8 建立。

教材本身包含：

- Concepts / Definitions
- Worked Examples
- Read-through Questions
- Exercises

由于当前知识库是从完整教材 PDF 解析并按照 Section 切分，因此如果预处理阶段没有主动删除 Exercise / Example 部分，这些内容理论上已经存在于当前知识库中。

#### 后续检查

检查解析后的 Markdown 中是否存在：

- `EXERCISES`
- `Example`
- `Problems`
- `Read-through`

确认教材 Example / Exercise 是否完整保留。

如果已经存在，则这些题不重复加入新的 Exercise Bank。

---

### 2.2 External Source 1：MIT Calculus Study Guide

来源：

Gilbert Strang, *Calculus Study Guide*, MIT OpenCourseWare.

Study Guide 与当前教材按照 Chapter / Section 对应，可以直接进行课程结构映射。

主要使用：

- Model Problems
- Extra Drill Problems

不重点重复导入：

- 已经存在于原教材中的 Exercise
- 对原教材 Exercise 的重复解答

#### 优势

- 与当前 51 个 Sections 高度对应；
- 几乎不需要重新设计 curriculum mapping；
- 题目来源与现有教材一致；
- 适合补充标准计算题和练习题。

---

### 2.3 External Source 2：MIT 18.01SC Single Variable Calculus

MIT 18.01SC 是另一套完整的 MIT Single Variable Calculus 课程。

课程包含：

- Worked Examples
- Problem Sets
- Problem Set Solutions
- Exams
- Exam Solutions

其中 Problem Sets 来源于 MIT 实际课程 homework；课程 Exams 整体较有挑战性。

#### 第一阶段计划导入

优先：

- Worked Examples
- Problem Sets

暂时不大量引入：

- Exams

原因：

Exam 可以作为后续 Hard Questions 的参考或 benchmark，但对于普通练习模式可能整体偏难。

---

## 3. 为什么不能直接让 LLM 判断 Easy / Medium / Hard

题目难度至少包含两个不同概念。

### 3.1 Designed / Cognitive Difficulty

题目在设计时要求学生完成多复杂的数学活动，例如：

- 是否只是直接套公式；
- 是否需要选择解题策略；
- 是否组合多个知识点；
- 是否需要建模；
- 是否需要解释或论证。

这是题目生成阶段可以提前判断的。

### 3.2 Empirical Difficulty

真实学生做题之后表现出的实际难度，例如：

- Correct Rate
- First-attempt Accuracy
- Completion Time
- Number of Attempts
- Hint Usage

两者可能不一致。

因此系统中的 Easy / Medium / Hard 应首先是 **Designed Difficulty**，之后再通过 Human Study 获得 **Empirical Difficulty** 并进行校准。

---

## 4. Literature Review：数学题认知复杂度与难度

### 4.1 MATH Taxonomy

Smith et al. (1996) 提出了专门针对大学数学 assessment 的 **MATH Taxonomy**。

论文：

Smith, G., Wood, L., Coupland, M., Stephenson, B., Crawford, K., & Ball, G. (1996).  
*Constructing mathematical examinations to assess a range of knowledge and skills.*

分类如下：

| Group | Cognitive Activity |
|---|---|
| Group A | Factual Knowledge / Comprehension / Routine Procedures |
| Group B | Information Transfer / Application to New Situations |
| Group C | Justifying & Interpreting / Conjectures & Comparisons / Evaluation |

核心含义：

#### Group A

学生基本知道应该使用什么方法。

例如：

> Differentiate \(x^3+2x\).

主要属于直接程序性计算。

#### Group B

知识本身已经学过，但是学生需要：

- 将知识迁移到新的表示或情境；
- 自己判断应该选择哪种方法。

例如：

> 根据实际场景建立 Related Rates 方程并求变化率。

#### Group C

要求更高层次的：

- interpretation；
- justification；
- comparison；
- evaluation。

例如：

> 根据 \(f'(x)\) 的图像解释为什么 \(f(x)\) 在某区间 concave down。

#### 对本项目的意义

MATH Taxonomy 可以作为 Difficulty Rubric 的一个重要维度。

但需要注意：

**原论文强调该 taxonomy 按“完成任务所需活动的性质”分类，而不是一个 difficulty hierarchy。**

因此不能简单定义：

> Group A = Easy  
> Group B = Medium  
> Group C = Hard

而应把它作为判断难度的其中一个因素。

---

### 4.2 MATH Taxonomy 的可靠性研究

Kinnear et al. (2020)：

*Reliable application of the MATH taxonomy sheds light on assessment practices.*

研究让多个 novice coders 使用 MATH Taxonomy 对数学考试题进行分类。

主要结果：

- 经过 calibration 后，不同标注者可以对题目进行较稳定的一致分类；
- 最终 inter-rater reliability 达到 **Krippendorff's α = 0.94**。

#### 对本项目的意义

我们也可以采用类似方法：

> Difficulty Definition  
> + Example Questions  
> + Few-shot Calibration

而不是只给 LLM：

> “Generate a medium question.”

即通过一组明确规则和已标注样例，使 LLM 对 Easy / Medium / Hard 的理解更加一致。

---

### 4.3 Mathematical Reasoning：Routine vs Creative Reasoning

Lithner (2008)：

*A research framework for creative and imitative reasoning.*

该研究区分：

#### Imitative Reasoning

主要依赖：

- memorized procedures；
- familiar algorithms；
- 已知解题模板。

#### Creative Mathematically Founded Reasoning

需要：

- strategy construction；
- strategy selection；
- mathematical justification；
- reasoning based on mathematical properties。

#### 对本项目的意义

可以把：

**“是否需要学生自己选择 / 组合 strategy”**

作为 Difficulty Rubric 的重要指标。

例如：

Easy：

> 明确告诉学生求导，直接使用 Power Rule。

Medium：

> 学生需要判断应该使用 Product Rule + Chain Rule。

Hard：

> 学生首先需要建立数学模型，然后自主确定求解方法。

---

## 5. Calculus-specific Difficulty Research

### 5.1 Vector Calculus Item Analysis

Zainuri et al. (2016) 对 Engineering Mathematics 中的 Vector Calculus final exam 进行了 item analysis。

研究对象：

- 80 名学生；
- 分析 calculus examination questions。

结果：

- Difficulty Index 范围约为 **0.2–0.8**；
- Discrimination Index 范围约为 **0.2–0.6**；
- 不同 calculus questions 对学生表现出了明显不同的实际难度。

#### 对本项目的意义

题目在设计阶段的“预估难度”不能完全代替实际学生表现。

因此后续需要比较：

> LLM / Expert-assigned Difficulty  
> vs  
> Student Performance Difficulty

---

### 5.2 Integral Questions Item Analysis

一项针对 Engineering Mathematics 中 Integral MCQs 的研究分析了：

- 35 道积分题；
- 83 名学生。

结果包括：

- 28 道题（80%）被认为具有合适的 difficulty；
- 3 道题过难；
- 4 道题过易；
- 平均 Difficulty Index 约为 **61.83%**；
- 所有题目的 discrimination 均达到 acceptable 到 very good。

#### 对本项目的意义

Human Study 后不仅可以看 accuracy，还可以进一步看：

- Difficulty Index
- Discrimination Index

判断一道题不仅“难不难”，还判断它能否区分不同掌握水平的学生。

---

### 5.3 Prior Knowledge 对 Calculus Question Difficulty 的影响

Mahadewsing & Getrouw (2026)：

*Are you assessing learning goals or prior knowledge? A critical approach in constructing calculus exam questions.*

研究分析了真实 Calculus Exam Questions 及学生答案。

核心发现：

某些题目的困难并不完全来自目标 calculus knowledge，而是额外的 prerequisite knowledge 干扰了对目标 Learning Goal 的测量。

#### 对本项目的意义

Hard Question 不应该只是：

> 加入更多复杂的代数运算  
> 或加入学生还没有学习的知识。

否则测试的可能是：

> Prior Knowledge

而不是：

> 当前 Calculus Knowledge Point。

因此 LLM 生成题目时应加入约束：

**题目难度增加必须主要来源于当前知识点的 reasoning complexity，而不能主要来源于额外的 prerequisite knowledge。**

---

## 6. Proposed Difficulty Rubric

结合 MATH Taxonomy、Mathematical Reasoning Framework 以及现有系统需求，第一版计划按照以下维度定义难度。

| Dimension | Easy | Medium | Hard |
|---|---|---|---|
| Knowledge Points | 单一知识点 | 1–2 个相关知识点 | 多知识点综合 |
| Method Selection | 方法明确 | 需要判断合适方法 | 需要自主选择或组合策略 |
| Reasoning Steps | 少量直接步骤 | 多步骤推理 | 多阶段推理 |
| Familiarity | 熟悉的标准形式 | 变式或新表示 | 新情境 / 综合应用 |
| Mathematical Reasoning | Routine / algorithmic | 部分 strategy selection | 较强 strategy construction |
| Interpretation | 基本无 | 少量解释 | 解释 / 比较 / justification |
| Modelling | 无 | 简单情境转换 | 建模 / 应用问题 |
| Prior Knowledge | 只需基础前置知识 | 同上 | **不能通过额外前置知识人为增加难度** |

---

## 7. Example

以 Chain Rule 为例。

### Easy

> Find the derivative of  
> \(f(x)=(x^2+1)^3\).

特点：

- 单一核心知识点；
- 方法明确；
- routine procedure。

### Medium

> Find the derivative of  
> \(f(x)=(x^2+1)^3\sin x\).

特点：

- Product Rule + Chain Rule；
- 需要识别并组合方法；
- reasoning steps 增加。

### Hard

给出一个实际变化过程，需要学生：

1. 建立变量之间的关系；
2. 判断需要使用 implicit differentiation / chain rule；
3. 对时间求导；
4. 代入条件；
5. 解释最终结果。

Hard 的核心不是：

> 数字更大 / 公式更长，

而是：

> strategy selection + reasoning + application 增加。

---

## 8. LLM Difficulty Alignment

### Stage 1：建立人工 Difficulty Rubric

首先固定：

- Easy Definition
- Medium Definition
- Hard Definition

并为每个等级准备若干人工确认过的示例。

### Stage 2：External Exercise Annotation

从：

- MIT Calculus Study Guide
- MIT 18.01SC Worked Examples
- MIT 18.01SC Problem Sets

选择题目。

每道题记录：

```json
{
  "source": "MIT 18.01SC",
  "chapter": "...",
  "section": "...",
  "knowledge_points": ["..."],
  "question_type": "...",
  "difficulty": "medium",
  "difficulty_reason": {
    "knowledge_points": 2,
    "strategy_selection": true,
    "reasoning_steps": 4,
    "application": false
  }
}
```

即除了 Easy / Medium / Hard 标签，还保存：

**为什么判断为这个难度。**

### Stage 3：LLM Few-shot Calibration

不再使用简单 Prompt：

> Generate a hard calculus question.

而改为：

> Difficulty: Medium  
>
> Definition:
> - requires multiple reasoning steps;
> - may combine 1–2 related techniques;
> - requires some strategy selection;
> - should not rely on knowledge outside the current section.
>
> Reference Medium Questions:
> ...
>
> Generate a question for Section X.

通过：

**Difficulty Definition + Reference Examples + Knowledge Constraint**

提高 LLM 难度生成的一致性。

### Stage 4：Independent Difficulty Evaluator

生成题目之后，由独立 Prompt / LLM Judge 判断：

- Knowledge points involved
- Required reasoning
- Strategy selection
- Application / modelling
- Estimated difficulty

流程：

```text
Requested difficulty
        ↓
Question Generator
        ↓
Generated Question
        ↓
Difficulty Evaluator
        ↓
Matched?
   ↙          ↘
 Yes          No
 ↓             ↓
Keep       Regenerate
```

Generator 与 Evaluator 分开，避免模型仅仅重复自己的 difficulty label。

---

## 9. Human Study：Empirical Difficulty Calibration

后续 Human Study 计划招募约 30 名参与者。

对每道题记录：

- Correct / Incorrect
- First-attempt Accuracy
- Completion Time
- Number of Attempts
- Hint Usage
- Tutor Interaction Count
- Student Background
- Prior Calculus Knowledge

计算：

\[
DifficultyIndex =
\frac{\text{Number of Correct Students}}
{\text{Number of Students Attempting the Question}}
\]

注意：

**Difficulty Index 高意味着正确率高，因此题目实际上更容易。**

---

## 10. Designed Difficulty vs Empirical Difficulty

Human Study 后比较：

| LLM / Designed Label | Student Accuracy | Result |
|---|---:|---|
| Easy | 85% | aligned |
| Medium | 58% | aligned |
| Hard | 32% | aligned |
| Medium | 88% | possible mismatch |
| Easy | 35% | possible mismatch |

进一步分析 mismatch 的原因：

- LLM 难度判断错误；
- prerequisite knowledge 不足；
- wording 过于复杂；
- question type 本身影响表现；
- distractor 设计问题；
- 学生 prior knowledge 差异。

最终利用真实数据调整 Difficulty Rubric。

---

## 11. Research Questions

### RQ1

**To what extent do LLM-assigned difficulty levels align with students' empirical performance on calculus exercises?**

### RQ2

**Which features of a calculus problem—such as the number of knowledge components, strategy selection, reasoning steps, and application context—are most associated with students' perceived and empirical difficulty?**

---

## 12. Implementation Plan

### Phase 1 — Current Corpus Check

- 检查原 Calculus Markdown；
- 确认教材 Examples / Exercises 是否已经存在；
- 避免重复导题。

### Phase 2 — External Exercise Collection

导入：

1. MIT Calculus Study Guide
   - Model Problems
   - Extra Drill Problems

2. MIT 18.01SC
   - Worked Examples
   - Problem Sets

暂不大量导入 Exams。

### Phase 3 — Curriculum Mapping

将所有外部习题映射到：

```text
Chapter
→ Section
→ Knowledge Point
```

与当前 51 sections 对齐。

### Phase 4 — Difficulty Annotation

根据统一 Rubric：

```text
Easy / Medium / Hard
+
difficulty_reason
```

先人工标注一批 Gold Examples。

### Phase 5 — LLM Alignment

使用：

```text
Rubric
+
Few-shot examples
+
Knowledge-point constraint
```

让 LLM：

- 对已有题进行 difficulty classification；
- 按指定难度生成新题。

### Phase 6 — Automatic Evaluation

增加独立 Difficulty Evaluator：

```text
Generator → Evaluator → Accept / Regenerate
```

评估生成难度是否与目标一致。

### Phase 7 — Human Study

让真实学生完成：

- Easy
- Medium
- Hard

不同类型题目。

记录：

```text
accuracy
time
attempts
hint usage
Tutor usage
prior knowledge
```

### Phase 8 — Difficulty Calibration

比较：

```text
Designed Difficulty
      VS
Empirical Difficulty
```

修改：

- Difficulty thresholds
- Prompt
- Few-shot examples
- Question-generation rules

形成最终 Difficulty Calibration Pipeline。

---

## 13. Expected Final Pipeline

```text
MIT Textbook
        +
MIT Study Guide
        +
MIT 18.01SC
        ↓
Exercise Collection
        ↓
Chapter / Section / Knowledge Mapping
        ↓
Difficulty Rubric
        ↓
Human-labelled Gold Examples
        ↓
LLM Difficulty Alignment
        ↓
Question Generator
        ↓
Independent Difficulty Evaluator
        ↓
Student Practice
        ↓
Human Study Data
        ↓
Empirical Difficulty
        ↓
Difficulty Calibration
```

---

## 14. Key References

1. Smith, G., Wood, L., Coupland, M., Stephenson, B., Crawford, K., & Ball, G. (1996).  
   *Constructing mathematical examinations to assess a range of knowledge and skills.*  
   International Journal of Mathematical Education in Science and Technology, 27(1), 65–77.

2. Kinnear, G., Bennett, M., Binnie, R., Bolt, R., & Zheng, Y. (2020).  
   *Reliable application of the MATH taxonomy sheds light on assessment practices.*  
   Teaching Mathematics and its Applications, 39(4), 281–295.

3. Lithner, J. (2008).  
   *A research framework for creative and imitative reasoning.*  
   Educational Studies in Mathematics, 67, 255–276.

4. Zainuri, N. A., et al. (2016).  
   *Item analysis for final exam questions of engineering mathematics course (Vector Calculus) in UKM.*  
   Journal of Engineering Science and Technology.

5. Mahadewsing, R., & Getrouw, D. (2026).  
   *Are you assessing learning goals or prior knowledge? A critical approach in constructing calculus exam questions.*  
   Journal of Mathematics and Science Teacher, 6(2), em099.
