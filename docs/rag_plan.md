# Calculus Tutor：RAG 知识库与 Socratic Tutor 集成方案

# 1. 目标

在现有 Calculus Tutor 系统中引入基于教材的 RAG（Retrieval-Augmented Generation）能力。

当前系统已有三个主要阶段：

1. Learn：学习知识点
2. Practice：练习题
3. Tutor：苏格拉底式教学 Agent

本次改造目标不是让所有模块都强制使用 RAG，而是建立一套统一的教材知识库，并根据不同模块采用不同的访问方式：

- Learn：使用结构化教材内容直接展示
- Practice：使用知识点 + 题型模板 + 可选 RAG 上下文生成练习题
- Tutor：使用 RAG 动态检索教材内容，并由 Socratic Agent 决定教学策略

总体原则：

> 同一份教材知识库，Learn 使用结构化查询，Practice 使用受控生成，Tutor 使用向量检索 + Agent。

---

# 2. 总体架构

```text
Textbook PDF
    ↓
MinerU
    ↓
Markdown + JSON + Figures
    ↓
Document Processing
    ↓
Structured Knowledge Chunks
    ↓
┌───────────────────────────────┐
│       Knowledge Storage       │
│                               │
│ Structured metadata + text    │
│ Vector embeddings             │
└───────────────────────────────┘
        │               │
        │               │
        ↓               ↓
      Learn           RAG Retrieval
                        │
                        ↓
                retrieve top-k
                        ↓
                     rerank
                        ↓
              relevant textbook context
                        │
               ┌────────┴────────┐
               ↓                 ↓
           Practice            Tutor
               │                 │
      Question Generator   Socratic Agent
               │                 │
      Content Validator   Student Modeling
                                 │
                        Pedagogical Decision
```

# 3. PDF 解析

## 3.1 输入

教材 PDF，例如：

```text
data/raw/chapter01.pdf
```

## 3.2 使用 MinerU

使用 MinerU 将 PDF 解析为：

```text
data/parsed/chapter01/
├── chapter01.md
├── content_list.json
├── images/
│   ├── figure_1_1.png
│   ├── figure_1_2.png
│   └── ...
└── raw/
```

优先保留：

- 标题层级
- 正文
- 数学公式 LaTeX
- figure caption
- 图片
- 页码
- block 顺序
- section 信息

不要只保留 Markdown。

同时保存 MinerU 输出的 JSON，以便后续进行结构化处理。

------

# 4. 教材后处理

MinerU 输出不能直接进入向量数据库。

增加一个 Document Processing 模块：

```text
src/rag/document_processor.py
```

负责以下任务。

## 4.1 标题识别

识别层级，例如：

```text
Chapter 1
1.1 Velocity and Distance
CONSTANT VELOCITY
VELOCITY vs. DISTANCE: SLOPE vs. AREA
FUNCTIONS
1.1 EXERCISES
```

将每一个 block 关联到：

```json
{
  "chapter": "1",
  "section": "1.1",
  "subsection": "Velocity vs. Distance: Slope vs. Area"
}
```

------

## 4.2 内容类型识别

每个内容块应尽量归类为以下类型之一：

```text
concept
definition
example
figure
exercise
solution
summary
note
```

例如：

```json
{
  "content_type": "example"
}
```

------

## 4.3 图片绑定

不要把图片作为独立、无上下文的文件存储。

每张图片至少需要：

```json
{
  "figure_id": "fig_1_7",
  "path": "images/fig_1_7.png",
  "caption": "...",
  "section": "1.2",
  "related_chunk_ids": []
}
```

图片应与：

- 前面的解释
- caption
- 后面的分析

建立关联。

------

## 4.4 图片语义描述

建议调用 multimodal LLM 对教材图片生成简短语义描述。

例如：

```json
{
  "figure_id": "fig_1_7",
  "description": "The figure compares a piecewise constant velocity graph with the corresponding piecewise linear distance graph. The heights 1, 3, 5, 7 represent velocity values, while accumulated rectangular areas correspond to distance values 0, 1, 4, 9, 16."
}
```

该 description 后续参与 embedding。

------

## 4.5 公式质量检查

对 MinerU 输出的公式做基础 validation：

- 检查 LaTeX 是否为空
- 检查括号是否明显缺失
- 检查 `\frac{}`、`\sqrt{}` 是否完整
- 检查乱码字符
- 检查 equation 是否被截断

第一版不要求完全自动修复。

发现异常时记录：

```json
{
  "validation_status": "warning"
}
```

------

# 5. Knowledge Chunk 设计

不要简单按照固定 token 长度切分教材。

采用：

> structural + semantic chunking

优先按照：

```text
Chapter
→ Section
→ Subsection
→ Knowledge Point
→ Concept / Example / Figure / Exercise
```

进行切分。

只有单个知识块过长时，再按照 token 长度进行二次切分。

------

# 6. Chunk Schema

统一使用如下结构：

```json
{
  "chunk_id": "ch1_sec1_velocity_area_001",

  "chapter": "1",
  "chapter_title": "Introduction to Calculus",

  "section": "1.1",
  "section_title": "Velocity and Distance",

  "subsection": "Velocity vs. Distance: Slope vs. Area",

  "knowledge_point": "relationship_between_velocity_distance",

  "content_type": "concept",

  "title": "Velocity and Distance",

  "text": "Velocity is the slope of the distance graph...",

  "latex": [],

  "figures": [
    {
      "figure_id": "fig_1_4",
      "path": "images/fig_1_4.png",
      "caption": "...",
      "description": "..."
    }
  ],

  "prerequisites": [
    "linear_function",
    "slope"
  ],

  "difficulty": "basic",

  "source_page_start": 3,
  "source_page_end": 4,

  "source_file": "chapter01.pdf",

  "validation_status": "ok"
}
```

并允许以下 `content_type`：

```text
concept
definition
example
figure
exercise
solution
summary
note
```

------

# 7. Embedding 内容

不要只 embedding `text`。

构造 embedding_text：

```text
[Chapter]
Introduction to Calculus

[Section]
1.1 Velocity and Distance

[Knowledge Point]
Relationship between velocity and distance

[Type]
Concept

[Content]
Velocity is the slope of the distance graph...

[Figure Description]
The velocity graph shows...
```

即：

```python
embedding_text = (
    title
    + section_title
    + knowledge_point
    + text
    + figure_description
)
```

------

# 8. Vector Database

第一版可以选择以下任一种：

```text
Chroma
FAISS
Qdrant
```

如果当前项目已有 Chroma，则优先继续使用 Chroma。

每条向量必须同时保存 metadata：

```json
{
  "chunk_id": "...",
  "chapter": "1",
  "section": "1.1",
  "knowledge_point": "...",
  "content_type": "concept",
  "difficulty": "basic"
}
```

------

# 9. Learn 模块

## 9.1 原则

Learn 页面不需要实时 RAG。

学生已经选择明确 section，例如：

```text
2.2 The Limit of a Function
```

系统直接根据 section 查询结构化知识库。

流程：

```text
selected_section
    ↓
structured query
    ↓
concept
definition
example
figure
    ↓
frontend
```

------

## 9.2 查询规则

例如：

```python
get_section_content(
    section="2.2",
    content_types=[
        "concept",
        "definition",
        "example",
        "figure"
    ]
)
```

按照教材原始顺序展示。

------

## 9.3 前端展示建议

Learn 页面展示：

```text
Section Title

Key Idea

Definition

Example

Relevant Figure

Optional Summary
```

不要把正文硬编码在 Streamlit 页面。

所有内容均从知识库读取。

------

# 10. Practice 模块

Practice 不使用完全自由的 RAG 出题。

使用：

```text
Knowledge Point
+
Difficulty
+
Question Type
+
Question Template
+
Retrieved textbook context
```

进行受控生成。

------

## 10.1 当前输入

已有：

```text
section
difficulty:
    basic
    intermediate
    advanced

question_type:
    single_choice
    multiple_choice
    fill_blank
    ordering
```

保留现有 UI。

------

## 10.2 出题流程

```text
Current section
+
difficulty
+
question type
    ↓
select question template
    ↓
retrieve relevant concept/example chunks
    ↓
Question Generator LLM
    ↓
Content Validator
    ↓
Question
```

------

## 10.3 Retrieval filter

Practice retrieval 优先限制：

```text
content_type IN:
    concept
    definition
    example

section = current_section
```

不检索：

```text
solution
```

除非内部 validation 需要。

------

## 10.4 生成输入

示例：

```json
{
  "section": "2.2",
  "knowledge_point": "function_limit",
  "difficulty": "intermediate",
  "question_type": "single_choice",
  "retrieved_context": [],
  "template": {}
}
```

------

# 11. Tutor 模块

Tutor 是本次 RAG 的主要使用场景。

学生点击：

```text
I'm stuck — guide me
```

或者输入：

```text
Why can't I substitute x = 2?
```

系统执行：

```text
student input
+
current problem
+
current section
+
conversation history
    ↓
retrieval query construction
    ↓
retrieve top-k
    ↓
rerank
    ↓
relevant textbook context
    ↓
Socratic Tutor Agent
```

------

# 12. Retrieval Pipeline

实现：

```text
src/rag/retriever.py
```

------

## 12.1 Query Construction

不要只使用学生一句话。

构造 query：

```text
current section
+
current problem
+
student latest message
+
detected misconception
```

例如：

```text
Section: 2.2 The Limit of a Function

Problem:
Evaluate lim x→2 (3x² - 12)/(x - 2)

Student:
I substituted 2 and got 0/0.

Possible misconception:
Student does not know how to handle an indeterminate form.
```

------

# 13. Metadata Filtering

Tutor retrieval 优先限定当前章节或 section。

第一层：

```text
section = current_section
```

如果检索结果不足，再扩展：

```text
chapter = current_chapter
```

如果检测到 prerequisite gap，可以跨 section 检索 prerequisite。

------

# 14. Top-k

第一版：

```python
retrieve_k = 8
final_k = 4
```

即：

```text
vector search
↓
top 8
↓
rerank
↓
top 4
```

如果第一版暂时没有 reranker：

```text
retrieve top 5
→ directly pass to Agent
```

允许后续再增加 reranker。

------

# 15. Reranker

创建：

```text
src/rag/reranker.py
```

输入：

```text
query
+
retrieved chunks
```

输出：

```text
reranked chunks
```

排序依据：

1. 与当前问题相关性
2. 与当前 section 相关性
3. 与学生错误相关性
4. prerequisite relevance
5. 教学价值

第一版可以直接使用 LLM reranking。

后续可以替换成专门 reranker model。

------

# 16. Socratic Tutor Agent

RAG 只负责：

> 找到应该给 Agent 看的教材内容。

Agent 负责：

> 决定下一步如何教学。

不要把这两个职责混在一起。

------

# 17. Tutor Agent 输入

```json
{
  "problem": "...",

  "student_message": "...",

  "conversation_history": [],

  "student_state": {},

  "retrieved_context": [],

  "current_section": "2.2"
}
```

------

# 18. Pedagogical Actions

Tutor Agent 每轮必须先选择一个 pedagogical action。

允许：

```text
ASK_DIAGNOSTIC_QUESTION

ASK_GUIDING_QUESTION

GIVE_HINT

EXPLAIN_PREREQUISITE

CHECK_REASONING

CORRECT_MISCONCEPTION

ADVANCE

SUMMARIZE
```

禁止默认直接生成完整解答。

------

# 19. Socratic Policy

推荐基础策略：

```text
IF student has not attempted:
    ASK_DIAGNOSTIC_QUESTION

IF student response is partially correct:
    CHECK_REASONING
    OR ASK_GUIDING_QUESTION

IF student shows misconception:
    CORRECT_MISCONCEPTION
    OR EXPLAIN_PREREQUISITE

IF student is stuck:
    GIVE_HINT

IF student completes current reasoning step:
    ADVANCE

IF problem is completed:
    SUMMARIZE
```

------

# 20. Student State

维护简单 student state：

```json
{
  "current_problem_id": "...",

  "mastered_steps": [],

  "current_step": "",

  "misconceptions": [],

  "prerequisite_gaps": [],

  "hint_level": 0,

  "attempt_count": 0
}
```

------

# 21. Hint Level

建议支持三级 hint：

```text
Level 1:
Conceptual hint

Level 2:
Method hint

Level 3:
Concrete next-step hint
```

例如极限题：

Level 1：

```text
What happens when you substitute x = 2 directly?
```

Level 2：

```text
Can the numerator be factored?
```

Level 3：

```text
Try factoring 3x² - 12 as 3(x² - 4).
```

尽量不直接给最终答案。

------

# 22. Misconception Detection

增加：

```text
src/tutor/misconception_detector.py
```

输入：

```text
problem
student response
conversation history
```

输出：

```json
{
  "has_misconception": true,
  "type": "invalid_cancellation",
  "confidence": 0.88,
  "description": "Student cancels terms instead of common factors."
}
```

第一版可以使用 LLM classification。

------

# 23. Adaptive Retrieval

如果检测到 misconception：

将 misconception 加入 retrieval query。

例如：

```text
invalid algebraic cancellation
factoring rational expressions
limit
```

如果检测到 prerequisite gap：

优先 retrieve：

```text
content_type:
    concept
    example

knowledge_point:
    prerequisite knowledge
```

------

# 24. Tutor Prompt 约束

Tutor system prompt 必须包含以下规则：

```text
You are a Socratic calculus tutor.

Use the retrieved textbook context as the primary instructional grounding.

Do not immediately provide the final answer.

Guide the student one reasoning step at a time.

Prefer asking targeted questions over giving explanations.

If the student has a misconception, identify the misconception and guide them to repair it.

If the student lacks prerequisite knowledge, briefly explain or retrieve the prerequisite before returning to the original problem.

Do not introduce unnecessary methods that are not supported by the provided textbook context.

When the student demonstrates understanding of the current step, advance to the next step.
```

------

# 25. Textbook Sources

Tutor 页面保留当前：

```text
Textbook sources
```

折叠组件。

每次回答应记录所使用的 chunk：

```json
{
  "chunk_id": "...",
  "section": "...",
  "title": "...",
  "source_page": 69
}
```

前端可展示：

```text
Textbook sources

1. 1.3 The Velocity at an Instant
   Page 69

2. 1.2 Calculus Without Limits
   Page 61
```

------

# 26. Suggested Project Structure

```text
project/
│
├── data/
│   ├── raw/
│   │   └── chapter01.pdf
│   │
│   ├── parsed/
│   │   └── chapter01/
│   │       ├── chapter01.md
│   │       ├── content_list.json
│   │       └── images/
│   │
│   └── processed/
│       └── chunks.json
│
├── src/
│   │
│   ├── ingestion/
│   │   ├── mineru_parser.py
│   │   ├── document_processor.py
│   │   ├── chunker.py
│   │   └── validator.py
│   │
│   ├── knowledge/
│   │   ├── repository.py
│   │   └── schemas.py
│   │
│   ├── rag/
│   │   ├── embedding.py
│   │   ├── vector_store.py
│   │   ├── retriever.py
│   │   ├── query_builder.py
│   │   └── reranker.py
│   │
│   ├── practice/
│   │   ├── question_generator.py
│   │   ├── template_library.py
│   │   └── question_validator.py
│   │
│   └── tutor/
│       ├── tutor_agent.py
│       ├── student_state.py
│       ├── misconception_detector.py
│       └── pedagogical_policy.py
│
└── app.py
```

------

# 27. Implementation Priority

不要一次性实现全部功能。

按照以下顺序逐步开发。

## Phase 1：教材解析

完成：

```text
PDF
→ MinerU
→ Markdown / JSON / Images
```

Acceptance criteria：

- 能成功解析 Chapter 1
- 标题基本正确
- 数学公式基本可读
- 图片能够提取
- 图片路径可访问

------

## Phase 2：Knowledge Chunking

完成：

```text
MinerU output
→ structured chunks.json
```

Acceptance criteria：

每个 chunk 至少包含：

```text
chunk_id
chapter
section
content_type
text
source_page
```

并尽可能包含：

```text
knowledge_point
figures
prerequisites
```

------

## Phase 3：Learn 页面接入

将当前 Learn 页面从硬编码 / 原始网页抓取方式改为：

```text
section_id
→ knowledge repository
→ frontend
```

Acceptance criteria：

选择一个 section 后可以正确展示：

```text
concept
definition
example
figure
```

------

## Phase 4：Basic RAG

完成：

```text
chunks
→ embedding
→ vector database
→ query
→ top-k
```

Acceptance criteria：

输入：

```text
Why does instantaneous velocity use a limit?
```

能够 retrieve 出与：

```text
average velocity
h → 0
instantaneous velocity
```

相关的教材 chunk。

------

## Phase 5：Tutor 接入 RAG

将：

```text
problem + student message
```

构造为 query。

然后：

```text
retrieve top-k
→ pass context to Tutor
```

Acceptance criteria：

Tutor 回答明显使用教材相关内容，同时仍然遵守 Socratic teaching，不直接给最终答案。

------

## Phase 6：Student State

增加：

```text
current_step
mastered_steps
misconceptions
hint_level
```

Acceptance criteria：

Tutor 能根据上一轮学生回答决定：

```text
continue
hint
correct
advance
```

------

## Phase 7：Reranker

增加：

```text
retrieve top 8
→ rerank
→ top 4
```

并与无 reranker 的结果进行简单对比。

------

## Phase 8：Adaptive Retrieval

加入：

```text
misconception detection
+
prerequisite detection
```

根据学生状态动态修改 retrieval query。

------

# 28. 第一版暂时不要实现

为控制开发复杂度，第一版不要实现：

```text
Multimodal vector retrieval
Image embeddings
Knowledge graph database
Complex student model
Reinforcement learning policy
Fine-tuning
Multi-agent architecture
```

图片第一版只需要：

```text
image path
+
caption
+
LLM-generated semantic description
```

然后将 description 加入文本 embedding。

------

# 29. 核心设计原则

开发过程中必须遵循以下原则。

### Principle 1

Knowledge Base 和 RAG 不是同一件事。

Knowledge Base 是教材内容本身。

RAG 是动态寻找相关教材内容的方法。

### Principle 2

Learn 页面不用强制使用向量检索。

已知 section 时直接查询结构化知识。

### Principle 3

Practice 使用受控生成。

不要让 RAG 随机决定题目内容。

### Principle 4

Tutor 是 RAG 的核心使用场景。

### Principle 5

Retrieval 与 Teaching Decision 分离。

```text
Retriever:
What textbook knowledge is relevant?

Tutor Agent:
How should I teach the student now?
```

### Principle 6

Tutor 不直接给最终答案。

目标是逐步引导学生完成 reasoning。

### Principle 7

教材中的 Example 和 Figure 属于知识的一部分。

切 chunk 时不得随意将强相关的图、例子和概念完全分离。

------

# 30. 最终目标

系统最终应形成：

```text
                 Textbook Knowledge Base
                         │
        ┌────────────────┼─────────────────┐
        ↓                ↓                 ↓
      Learn           Practice           Tutor
        │                │                 │
 Structured Query  Controlled RAG     Adaptive RAG
        │                │                 │
 Concept          Question Generator   Retrieval
 Definition              │                 ↓
 Example            Validator          Reranker
 Figure                                  ↓
                                  Socratic Agent
                                         ↓
                                  Student State
                                         ↓
                              Adaptive Teaching
```

核心定位：

> Learn provides structured textbook learning content.

> Practice generates controlled exercises grounded in textbook knowledge.

> Tutor uses RAG-enhanced Socratic tutoring to provide adaptive guidance based on the student's current reasoning and misconceptions.

```
这版你可以**整个复制给 Agent**。

我建议实际让 Agent 执行时，不要一句“全部实现”，而是先让它严格按照 **Phase 1 → Phase 2 → Phase 3** 做，因为你们现在最大的风险不是 Agent 部分，而是 **MinerU 输出之后的数据结构如果一开始设计乱了，后面 RAG、练习生成、Tutor 都得跟着重构**。
```