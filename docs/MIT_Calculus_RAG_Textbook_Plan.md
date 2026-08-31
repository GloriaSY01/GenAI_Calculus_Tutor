# MIT Calculus Open Textbook 作为 RAG 教材来源的选择与处理方案

> 核查日期：2026-08-29  
> 用途：英语微积分教学 Agent / RAG 知识库

## 1. 推荐教材

**教材名称：** *Calculus*  
**作者：** Prof. Gilbert Strang  
**来源：** MIT OpenCourseWare（MIT Department of Mathematics）  
**资源标识：** Fall 2017 章节 PDF  
**适用范围：** Single-variable and multivariable calculus

本项目仅对已取得并核验的 Fall 2017 Chapter 1–8 PDF 建库，不把当前网页上其他版本的说明
套用到这些文件。

## 2. 选择这本教材的原因

### 2.1 学术与教学权威性强

- 作者 Gilbert Strang 是 MIT 数学教授。
- 教材由 MIT OpenCourseWare 官方发布，来源清晰、可追溯。
- 内容覆盖单变量和多变量微积分，包含导数、导数应用、链式法则、积分、积分技巧、积分应用、无穷级数等标准大学微积分内容。
- 对毕业设计而言，使用 MIT 官方开放教材作为知识来源，比一般开放教材更容易说明教材来源的可靠性和学术权威性。

### 2.2 与 Calculus I 教学范围匹配

对于当前英语微积分教学 Agent，可优先使用以下章节：

- Chapter 1: Introduction to Calculus
- Chapter 2: Derivatives
- Chapter 3: Applications of the Derivative
- Chapter 4: Derivatives by the Chain Rule
- Chapter 5: Integrals
- Chapter 6: Exponentials and Logarithms
- Chapter 7: Techniques of Integration
- Chapter 8: Applications of the Integral

当前 MVP 已导入 Chapter 1–8，后续可按照课程 syllabus 决定是否扩展。

### 2.3 官方已按章节提供 PDF

MIT OCW 不仅提供整本 PDF，还提供 Chapter 0–16 的独立 PDF，并在网页中列出每章的 section 结构。

例如：

```text
Chapter 2: Derivatives
├── 2.1 The Derivative of a Function
├── 2.2 Powers and Polynomials
├── 2.3 The Slope and the Tangent Line
├── 2.4 Derivative of the Sine and Cosine
├── 2.5 The Product and Quotient and Power Rules
├── 2.6 Limits
└── 2.7 Continuous Functions
```

因此无需直接对整本 PDF 做固定长度切块，可以利用 MIT 已有的 chapter / section 层级进行结构化处理。

### 2.4 AI 使用条款相对明确

MIT OCW 内容采用 **CC BY-NC-SA 4.0**：

- **BY**：使用时需要署名；
- **NC**：仅限非商业用途；
- **SA**：对内容进行改编后，相关派生内容需按照相同或兼容的许可共享。

MIT OCW 的新版条款页面还包含针对 AI training / development 的说明：在遵守适用 Creative Commons 许可及相关限制的前提下，允许将 OCW 内容用于人工智能和机器学习模型的训练、开发与改进，其中明确要求署名和非商业使用。

因此，对于当前**非商业毕业设计 / 教学研究性质**的 RAG 系统，MIT OCW 相比商业版权教材更适合作为正式知识来源。

> 注意：正式学生试点前仍建议保存当时的 MIT OCW 许可页面、核查日期和教材版本。MIT 官网不同页面的条款更新可能存在同步时间差，因此应以实际使用时可访问的最新官方条款为准，并在有疑问时向 MIT OCW 进一步确认 RAG 检索片段发送给第三方 LLM 的具体使用方式。

## 3. 官方链接

### 教材

- MIT Calculus Open Textbook  
  https://ocw.mit.edu/courses/res-18-001-calculus-fall-2023/pages/open-textbook/

- Complete Textbook PDF  
  可从上述 Open Textbook 页面中的 **complete textbook (PDF)** 获取。

- About the Book  
  https://ocw.mit.edu/courses/res-18-001-calculus-fall-2023/pages/about-the-book/

### 许可与使用条款

- MIT OpenCourseWare Privacy and Terms of Use  
  https://ocw.mit.edu/pages/privacy-and-terms-of-use/

- MIT OCW AI-related Terms（当前可检索到包含 Permitted Use of AI Training 的 MIT OCW 页面）  
  https://live.ocw.mit.edu/pages/privacy-and-terms-of-use/

## 4. RAG 建库总体方案

不建议：

```text
整本 PDF
    ↓
固定 500 tokens 切块
    ↓
Embedding
    ↓
Vector DB
```

这种方式容易将定义、公式、例题和小节边界切断，同时可能混入页眉、页脚、图注等噪声。

推荐采用：

```text
MIT Chapter PDF
        ↓
PDF 文本与版面解析
        ↓
Chapter / Section 结构恢复
        ↓
数学公式与正文清洗
        ↓
Section 内语义切块
        ↓
补充 metadata
        ↓
Embedding
        ↓
Vector Database
        ↓
RAG Retrieval
        ↓
Socratic Tutor Agent
```

## 5. 具体切分方案

### Step 1：按 Chapter 下载，而不是直接处理整本 PDF

建议按课程范围分别下载：

```text
chapter_01.pdf
chapter_02.pdf
chapter_03.pdf
...
```

这样可以天然保留一级章节边界，同时便于后续更新和重建索引。

### Step 2：恢复 Section 层级

结合 MIT 官方目录，将 PDF 内容映射到：

```text
Book
└── Chapter
    └── Section
```

例如：

```text
Calculus
└── Chapter 2: Derivatives
    └── Section 2.1: The Derivative of a Function
```

**Section 应作为知识库最基本的逻辑组织单位，但不一定直接作为最终 embedding chunk。**

### Step 3：Section 内进行语义切块

每个 section 内进一步按内容语义切分，优先保留完整的：

- Definition
- Concept Explanation
- Theorem / Rule
- Example
- Application
- Exercise

建议目标 chunk 大小：

```text
约 300–700 tokens / chunk
```

但不要为了满足 token 数强行截断公式、定义或完整例题。

推荐原则：

```text
语义完整性 > 固定 token 长度
```

可以设置少量 overlap，例如：

```text
50–100 tokens
```

用于保持相邻解释之间的上下文连续性。

## 6. 数学 PDF 的特殊处理

### 6.1 公式

PDF 是该方案最大的工程难点。

例如原公式：

```text
[f(x+h) - f(x)] / h
```

普通 PDF parser 可能提取成错乱的线性文本。

因此需要在 ingestion 阶段增加公式质量检查：

1. 检查分式、上下标、积分号、极限符号是否完整；
2. 尽量将公式转换或保留为 LaTeX / 可读数学文本；
3. 无法可靠恢复的复杂公式不要直接进入正式知识库；
4. 对核心定义和定理进行人工抽样验证。

### 6.2 页眉、页脚和页码

应在 embedding 前移除：

- repeated header
- repeated footer
- page number
- 无意义的版权重复文本

避免这些内容污染向量表示。

### 6.3 图片和图表

第一版 RAG 可暂时不将教材图片作为主要知识来源。

对于：

- function graph
- tangent line
- area diagram
- geometric illustration

可以先保留 metadata：

```json
{
  "has_figure": true,
  "figure_page": 65
}
```

但正文 RAG 主要使用可验证的文本和公式。

后续如果需要再扩展 multimodal RAG。

## 7. 推荐的数据结构

每个 chunk 至少保存：

```json
{
  "source_id": "mit_strang_calculus_3e",
  "book": "Calculus",
  "author": "Gilbert Strang",
  "publisher_source": "MIT OpenCourseWare",
  "term": "Fall 2017",

  "chapter_id": "2",
  "chapter_title": "Derivatives",
  "section_id": "2.1",
  "section_title": "The Derivative of a Function",

  "content_type": "concept_explanation",
  "page_start": 1,
  "page_end": 2,

  "text": "...",

  "source_url": "...",
  "license": "CC BY-NC-SA 4.0",
  "verified_at": "2026-08-29"
}
```

其中 `content_type` 建议至少区分：

```text
definition
concept_explanation
theorem
rule
example
application
exercise
```

这样 Tutor Agent 可以根据教学场景控制检索结果。

例如：

```text
学生询问概念
→ definition + concept_explanation 优先

学生需要进一步提示
→ example / application 优先

学生需要练习
→ exercise 优先
```

## 8. Retrieval 层建议

查询时不要只进行全库向量相似度搜索。

推荐：

```text
User Query
    ↓
Topic / Section Identification
    ↓
Metadata Filter
    ↓
Vector Similarity Search
    ↓
Reranking
    ↓
Top-k Context
    ↓
Tutor Agent
```

例如用户询问：

```text
Why is the derivative defined as a limit?
```

可以先确定：

```text
chapter = 2
topic = derivative
```

再在 Chapter 2 / 对应 section 中进行向量检索，而不是直接搜索整本教材。

这有助于减少语义相近但教学位置不同的内容被错误召回。

## 9. 建库质量检查

正式使用前建议完成以下检查：

### 文本质量

- [ ] 页眉页脚已删除
- [ ] section 边界正确
- [ ] chunk 没有在一句话中间截断
- [ ] definition / theorem 没有被拆开

### 数学质量

- [ ] 公式没有明显解析错误
- [ ] 上下标正确
- [ ] 分式结构正确
- [ ] 积分、极限和求和符号正确
- [ ] 例题条件与答案没有被拆开

### Metadata

- [ ] chapter_id
- [ ] section_id
- [ ] section_title
- [ ] page
- [ ] source_url
- [ ] license
- [ ] verified_at

### Retrieval

建立一组测试问题，检查：

```text
Recall@k
MRR
人工相关性评分
```

尤其检查：

- 问某个 section 时是否能准确召回对应教材内容；
- 是否会召回邻近但错误的知识点；
- 检索出的 chunk 是否包含完整数学语义；
- Tutor 最终回答是否能够给出明确教材来源。

## 10. 最终建议

对于当前英语微积分教学 Agent，推荐采用：

> **Gilbert Strang, Calculus, Fall 2017 chapter resources, MIT OpenCourseWare**

作为主要 RAG 教材来源。

主要理由不是单纯因为“MIT 更权威”，而是它同时满足：

```text
较高学术权威性
        +
标准 Calculus 教学覆盖
        +
官方免费电子版
        +
按 Chapter 提供 PDF
        +
清晰的 Section 目录
        +
开放教育许可
        +
对非商业 AI 使用具有相对明确的官方说明
```

其主要缺点是 **PDF 不具备 PreTeXt/XML 那样天然的语义结构**，需要额外完成数学公式解析和 section/chunk 结构恢复。

但对于目前规模有限的 Calculus I RAG 知识库，这部分工程成本是可控的，并且能够换来更清晰、权威、可追溯的教材来源。
