# Calculus Tutor：教材知识库 + RAG 初始接入计划

## 1. 目标

基于微积分教材 PDF 构建统一知识库，并接入现有三个阶段：

- **Learn**：展示教材知识内容
- **Practice**：随机使用教材原题或基于教材生成新题
- **Tutor**：通过 RAG 检索教材内容，为苏格拉底式教学 Agent 提供依据

第一版重点是先跑通：

> PDF 解析 → 知识切分 → 向量入库 → Learn / Practice / Tutor 三阶段接入

暂不加入 reranker、复杂学生画像、错误概念诊断、多模态向量检索等高级功能。

---

## 2. 总体流程

```text
Textbook PDF
    ↓
MinerU
    ↓
Markdown + JSON + Images
    ↓
结构化切分
    ↓
concept / example / exercise
    ↓
Embedding + Metadata
    ↓
Vector Database
    ↓
Learn / Practice / Tutor
```

---

## 3. 教材解析

使用 MinerU 将教材 PDF 转换为：

```text
chapter01/
├── chapter01.md
├── content_list.json
└── images/
```

需要尽量保留：

- Chapter / Section 标题
- 正文
- 数学公式
- 图片及 caption
- 页码
- 原始内容顺序

第一版允许人工检查少量公式、图片和版面解析错误。

---

## 4. 知识块切分

第一版统一分为三类：

### concept
包括概念、定义、原理解释、总结和关键结论。

### example
包括教材中的 worked example、示例推导和示例计算过程。

### exercise
包括教材原始练习题。

优先按照教材结构切分：

```text
Chapter
→ Section
→ concept / example / exercise
```

不要直接按照固定字数机械切分。相关图片应和对应 concept 或 example 建立关联。

---

## 5. Chunk 数据结构

每个知识块至少保存：

```json
{
  "chunk_id": "ch1_sec1_001",
  "chapter": "1",
  "section": "1.1",
  "title": "Velocity and Distance",
  "content_type": "concept",
  "text": "...",
  "figures": [
    {
      "path": "images/fig_1_2.png",
      "caption": "..."
    }
  ],
  "source_page": 2
}
```

其中：

```text
content_type = concept | example | exercise
```

Exercise 可额外增加：

```json
{
  "difficulty": "intermediate",
  "question_type": "single_choice"
}
```

如果教材本身没有 difficulty / question_type，可先通过规则或 LLM 自动标注。

---

## 6. Embedding 与 Metadata

对每个 chunk 生成 embedding，并存入向量数据库。第一版推荐使用 Chroma。

Embedding 内容可以组合：

```text
section title
+
content type
+
text
+
figure caption
```

同时保存 metadata，例如：

```json
{
  "chapter": "1",
  "section": "1.1",
  "content_type": "concept",
  "source_page": 2
}
```

Exercise 可额外保存：

```json
{
  "difficulty": "intermediate",
  "question_type": "single_choice"
}
```

---

# 7. Learn 阶段

Learn 不需要实时向量检索。

学生已经选择具体 section，因此直接按 section 读取：

```text
concept + example
```

以及它们关联的图片。

流程：

```text
User selects section
    ↓
Query by section
    ↓
concept + example + figures
    ↓
Frontend display
```

目标：

> Learn 页面中的教材内容统一来自知识库，而不是硬编码在前端。

---

# 8. Practice 阶段

Practice 同时支持两种题目来源：

```text
1. Textbook Exercise
2. Generated Exercise
```

每次开始练习时随机决定本题来源，例如：

```text
50% 教材原题
50% 生成题
```

比例做成可配置参数，后续可调整。

## 8.1 教材原题

根据：

```text
section
difficulty
question_type
```

从 `exercise` 中筛选符合条件的题目，再随机抽取。

```text
section + difficulty + question_type
    ↓
Filter exercise chunks
    ↓
Random select
    ↓
Practice UI
```

## 8.2 自动生成题目

如果本轮选择 Generated Exercise：

根据当前 section，从知识库中检索：

```text
concept + example
```

作为出题上下文。

```text
section + difficulty + question_type
    ↓
Retrieve relevant concept + example
    ↓
LLM Question Generator
    ↓
Generated Exercise
    ↓
Practice UI
```

生成新题时优先参考 concept 和 example，不要求直接参考教材 exercise，避免生成题过度复刻原题。

---

# 9. Tutor 阶段

Tutor 是第一版 RAG 的主要使用场景。

输入包括：

```text
current section
current problem
student message
conversation history
```

构造 retrieval query，从知识库检索相关：

```text
concept + example
```

第一版直接使用：

```text
top_k = 4~5
```

不需要 reranker。

流程：

```text
Student message
+
Current problem
    ↓
RAG Retrieval
    ↓
Top-k concept / example chunks
    ↓
Socratic Tutor Agent
    ↓
Ask question / Give hint / Explain concept
```

优先限制当前 section；必要时后续再支持跨 section 检索前置知识。

---

## 10. Tutor 基本规则

```text
You are a Socratic calculus tutor.

Use the retrieved textbook context as the main teaching reference.

Do not immediately provide the final answer.

Guide the student one step at a time.

Prefer asking questions and giving hints.

If the student is confused about a concept, briefly explain the relevant concept.

Use the current problem and conversation history when generating the next response.
```

---

# 11. 三阶段与知识库关系

```text
                    Knowledge Base
                         │
          ┌──────────────┼──────────────┐
          ↓              ↓              ↓
       concept         example       exercise
          │              │              │
          ├──── Learn ────┘              │
          │                              │
          ├──── Practice Generation      │
          │                              │
          └──── Tutor RAG                └──── Practice Original
```

| 阶段 | 使用内容 | 使用方式 |
|---|---|---|
| Learn | concept + example | 按 section 直接读取 |
| Practice 原题 | exercise | metadata 筛选 + 随机抽取 |
| Practice 生成题 | concept + example | RAG 检索后给 LLM 出题 |
| Tutor | concept + example | RAG Top-k 后给 Socratic Agent |

---

# 12. 第一版开发顺序

## Step 1：解析 Chapter 1

```text
PDF
→ MinerU
→ Markdown + JSON + Images
```

确认标题、正文、数学公式和图片基本可用。

## Step 2：生成知识块

```text
MinerU output
→ concept / example / exercise
→ chunks.json
```

## Step 3：建立向量库

```text
chunks.json
→ embedding
→ Chroma
```

同时保存 metadata。

## Step 4：接入 Learn

```text
section
→ concept + example
→ frontend
```

## Step 5：接入 Practice

实现：

```text
随机选择题目来源
    ↓
Textbook Exercise
或
Generated Exercise
```

## Step 6：接入 Tutor RAG

实现：

```text
student message + current problem
→ retrieve top-k concept/example
→ Socratic Agent
```

完成以上六步，即认为第一版教材知识库和 RAG 接入完成。

---

# 13. 后续优化

第一版完成后再考虑：

- Reranker
- 更细粒度 knowledge point
- Misconception Detection
- Student State
- Adaptive Retrieval
- Prerequisite Retrieval
- Image Semantic Description
- Multimodal RAG
- 自动公式验证
- 更完善的 Exercise difficulty / type 标注

---

# 14. 第一版核心原则

> **Learn：直接读知识库。**

> **Practice：教材原题和生成题随机混合。**

> **Tutor：使用 RAG 检索 concept + example，再进行苏格拉底式教学。**

> **先把教材解析、切分和三阶段接入跑通，再逐步增加复杂 RAG 能力。**
