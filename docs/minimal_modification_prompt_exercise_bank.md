# 最小修改 Prompt：外部习题接入、Difficulty Rubric 与独立 Exercise Chroma

请基于你刚刚的实施计划做一次**最小修改**，不要重新设计一套复杂架构，也不要开始改代码。

整体目标仍然是：

**接入两个 MIT 外部习题来源 → 建立初始 Easy / Medium / Hard 难度标准 → 将习题映射到现有课程 section → 作为 LLM 出题参考。**

请按下面要求修改原 Plan。

---

## 1. 外部习题来源保持不变

只使用两个来源：

### Source 1
Gilbert Strang Calculus Study Guide

主要使用：
- Model Problems
- Extra Drill Problems

### Source 2
MIT 18.01SC Single Variable Calculus

主要使用：
- Worked Examples
- Problem Sets

暂时不批量使用 Exams。

---

## 2. 外部文件获取方式必须明确

请首先尝试从 MIT OpenCourseWare 官方网站自动下载所需资源。

如果当前运行环境无法自动下载，请明确告诉我：

- 需要人工下载哪些文件；
- 对应 MIT OCW 官方 URL；
- 建议保存的文件名；
- 应保存到项目中的具体目录。

统一保存到类似：

```text
data/exercises/raw/
├── mit_strang_study_guide/
└── mit_18_01sc/
```

第一步不要直接批量处理全部文件。

先使用：

- 1 个 Study Guide chapter；
- 1 个 MIT 18.01SC Worked Example / Problem Set；

完成一次 pilot，确认解析和后续流程正常后再批量处理。

---

## 3. 外部 PDF 优先复用 MinerU

如果当前项目已有 MinerU PDF 解析流程，请优先复用。

流程：

```text
MIT PDF
↓
MinerU
↓
Markdown / structured text
↓
Exercise extraction
↓
一题一条结构化记录
```

原始 PDF 保存在 `raw/`。

解析后的习题统一保存为：

```text
data/exercises/exercise_bank.jsonl
```

或者在开发过程中先输出 draft JSONL，最终再合并。

---

## 4. Exercise Bank 使用 JSONL + 独立 Chroma

第一版不要只把习题直接写进 Chroma。

采用：

```text
MIT PDF
↓
MinerU
↓
exercise_bank.jsonl
↓
MiniLM embedding
↓
独立 Exercise Chroma collection
```

其中：

### JSONL

`exercise_bank.jsonl` 是 Exercise Bank 的 **source of truth**。

完整保存：

- exercise_id
- source
- source_problem_id
- stem
- solution
- final_answer
- knowledge_points
- primary_section_id
- related_section_ids
- designed_difficulty
- difficulty_reason
- cognitive_task
- source_form
- attribution / license information

### Chroma

Chroma 只是 Exercise Bank 的 **semantic retrieval index**。

不要把 external exercises 写进现有教材 collection。

现有：

```text
mit_calculus
```

继续保存：

- textbook concepts
- textbook examples

新增独立 collection，例如：

```text
mit_calculus_exercises
```

主要 embedding：

```text
exercise stem
```

metadata 至少保存：

- exercise_id
- primary_section_id
- difficulty
- source

完整 solution / answer / difficulty_reason 不需要全部作为 embedding 内容，仍然从 JSONL 中通过 `exercise_id` 获取。



---

## 6. Study Guide 和 18.01SC 的 section mapping 不要采用同一种方式

### Study Guide

它与当前 Gilbert Strang Calculus 基本按 section 对应，因此优先直接映射到当前 51 个 section。

### MIT 18.01SC

不要按照：

```text
18.01SC Chapter / Unit
→
Strang Chapter / Section
```

强行一一对应。

应该针对每一道题：

1. 提取题目涉及的 `knowledge_points`；
2. 再映射到当前系统的 51 个 section；
3. 保存：

```text
primary_section_id
related_section_ids
```

一道题可以涉及多个知识点。

第一版允许使用 LLM 辅助完成：

```text
exercise
↓
knowledge point extraction
↓
选择最合适的 current section
```

我只做少量人工抽查。

如果你认为 MiniLM 有帮助，也可以在离线建库阶段使用：

```text
exercise embedding
↓
retrieve Top-K similar textbook sections
↓
LLM 从候选 section 中做最终 mapping
```

但不要因此把 mapping 逻辑设计得过于复杂。

---

## 7. Difficulty Rubric 使用基于文献的 operational rubric

第一版的 Easy / Medium / Hard 不直接依赖学生正确率。

这是：

```text
Designed / Cognitive Difficulty
```

而不是最终的 empirical difficulty。

Difficulty Rubric 主要综合以下研究思想：

### MATH Taxonomy

用于区分：

- routine procedure
- application / information transfer
- interpretation / justification

注意：

MATH Taxonomy 的 Group A / B / C 是 cognitive activity classification，  
**不能简单直接等于 Easy / Medium / Hard。**

### Lithner reasoning framework

重点区分：

- routine / imitative reasoning
- strategy selection
- strategy construction
- mathematical justification

### Calculus item-analysis research

说明：

```text
designed difficulty
≠
empirical difficulty
```

真实难度之后需要通过学生表现验证。

### Prior-knowledge research

Hard 不能主要来自：

- 更大的数字；
- 更长的代数计算；
- 与当前学习目标无关的 prerequisite knowledge。

---

## 8. 第一版 Difficulty Rubric

请将下面四个维度作为主要判断依据：

### Dimension 1 — Knowledge Integration

Easy:
- 单一知识点。

Medium:
- 1–2 个相关知识点。

Hard:
- 多知识点综合。

### Dimension 2 — Strategy Selection

Easy:
- 方法基本明确；
- 学生知道应该使用什么公式或规则。

Medium:
- 需要判断应该使用哪种方法；
- 或组合已学过的方法。

Hard:
- 需要自主选择、组合或构造解题策略。

### Dimension 3 — Reasoning Process

Easy:
- 少量直接步骤；
- routine procedure。

Medium:
- 多步骤 reasoning；
- 存在一定中间判断。

Hard:
- 多阶段 reasoning；
- 需要更强的逻辑组织或 problem decomposition。

### Dimension 4 — Transfer / Interpretation

Easy:
- 熟悉的标准形式。

Medium:
- 变式、新表示或简单应用。

Hard:
- 新情境；
- modelling；
- interpretation；
- justification。

同时增加全局约束：

```text
Hard difficulty must not mainly result from
longer arithmetic,
more complicated numbers,
unnecessary algebraic manipulation,
or knowledge not yet taught in the current learning scope.
```

---

## 9. Difficulty 不要求我人工从零标 Gold Labels

请删除“要求我人工为每个难度从零建立 Gold Labels”的方案。

第一版改成：

```text
Difficulty Rubric
↓
LLM-assisted annotation
↓
manual spot check
```

让 LLM 对每一道 external exercise 自动输出：

- `designed_difficulty`
- `difficulty_reason`
- `cognitive_task`

其中 `difficulty_reason` 至少反映：

- knowledge integration
- strategy selection
- reasoning process
- transfer / interpretation

例如：

```json
{
  "designed_difficulty": "medium",
  "difficulty_reason": {
    "knowledge_integration": "two related concepts",
    "strategy_selection": "required",
    "reasoning_process": "multi-step",
    "transfer_interpretation": "routine variation"
  },
  "cognitive_task": "strategy_selection"
}
```

我只需要人工抽查少量代表性题目。

这些结果只作为：

```text
initial / designed difficulty
```

不作为最终 ground truth。

未来 Human Study 再使用：

- accuracy
- completion time
- attempts
- hint usage

校准 empirical difficulty。

---

## 10. 第一版 Exercise Chroma 的作用要简单

Exercise Chroma 只负责：

```text
semantic retrieval of relevant reference exercises
```

例如学生选择：

```text
section + difficulty + question type
```

先通过 metadata：

```text
primary_section_id
difficulty
```

限制候选范围。

再根据需要做 semantic retrieval，找到 2–3 道最适合作为 reference 的外部习题。

不要设计复杂的全库检索 pipeline。

---

## 11. 最终出题流程

保持简单：

```text
Student selects:

section
+
difficulty
+
question type

↓
```

教材知识：

```text
Textbook Chroma
↓
retrieve concept / example context
```

同时：

```text
Exercise Chroma
↓
retrieve relevant MIT reference exercises
↓
use exercise_id to read full records from exercise_bank.jsonl
```

然后：

```text
Textbook context
+
Difficulty Rubric
+
MIT reference exercises
+
Requested question type

↓
LLM Question Generator
↓
new exercise
```

External MIT exercises 的主要作用是：

- difficulty reference；
- reasoning structure reference；
- question generation reference。

不是要求直接原样展示给学生。

---

## 12. 暂时不要做

本阶段不要扩展以下功能：

- Independent Difficulty Evaluator
- Human Study implementation
- empirical difficulty calibration
- expression_input
- SymPy grading
- free response changes
- Exams ingestion
- 大规模架构重构

先完成一个 end-to-end MVP。

---

# 请基于以上要求修改原 Implementation Plan

修改后的 Plan 只需要重点明确：

1. 每一步具体做什么；
2. 涉及哪些现有文件；
3. 新增哪些文件；
4. MIT 文件由谁下载、保存到哪里；
5. MinerU 后产物保存在哪里；
6. `exercise_bank.jsonl` 如何生成；
7. Exercise Chroma 如何建立；
8. 18.01SC 如何映射到现有 51 个 section；
9. Difficulty Rubric 如何保存和使用；
10. LLM 如何自动完成初始 difficulty annotation；
11. 出题时 Textbook Chroma 和 Exercise Chroma 分别承担什么职责；
12. 每一步如何验证成功。

请优先复用现有项目中的：

- MinerU
- MiniLM
- Chroma
- current section metadata
- current question generation pipeline

不要为了这个功能进行不必要的重构。

**现在只修改并输出 Plan，不要开始修改代码。**
