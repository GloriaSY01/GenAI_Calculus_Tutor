# Calculus I 教材来源调研

核查日期：2026-08-29

> 本文是面向毕业设计和试点准备的工程调研，不构成法律意见。正式使用前应由学校、
> 导师或权利人确认具体使用方式，尤其是本地复制、向量化、检索增强生成和对外部署。

## 1. 结论

当前建议分成两个结论：

1. **技术验证首选 Active Calculus Single Variable 2e**。它覆盖英文 Calculus I，
   提供稳定 HTML 和可获取的源文件，采用 PreTeXt 结构，公式、章节、活动与练习的
   语义边界比抓取渲染后的 OpenStax 页面更清晰。
2. **正式试点前必须取得书面确认**。Active Calculus 采用 CC BY-SA 4.0，官方明确
   允许复制、改编和商业使用，但没有单独说明 RAG/生成式 AI ingestion。应向作者
   说明“下载源文件、切块、生成向量、在非商业教学系统中检索并展示带出处片段”的
   完整流程并留存回复。

OpenStax Calculus Volume 1 不再作为正式来源推荐。其当前官方页面明确写明：

> This book may not be used in the training of large language models or otherwise
> be ingested into large language models or generative AI offerings without
> OpenStax's permission.

“otherwise be ingested into”直接触及本项目的本地 RAG 建库。无论该声明与页面同时
标注的 CC BY-NC-SA 4.0 如何解释，工程上都不应在未取得 OpenStax 许可时继续将其
用于正式试点或分发索引。

## 2. 筛选标准

候选教材按以下标准评估：

- **课程匹配**：覆盖函数、极限、导数、导数应用、积分与积分应用等 Calculus I 内容。
- **RAG 许可**：不仅查看 Creative Commons 名称，还检查 AI 训练、生成式 AI
  ingestion、网站条款和第三方素材例外。
- **结构化程度**：优先 PreTeXt/XML 或按小节组织的 HTML，其次 LaTeX，最后 PDF。
- **可追溯性**：每个片段能保留书名、版本、小节、原始 URL、许可证和署名。
- **内容质量**：有编辑审校、勘误机制、定义/定理/例题结构，并适合大学一年级课程。
- **迁移成本**：能映射到统一的 `chapter_id`、`section_id`、`title`、`text`、
  `source_url`，不要求 Tutor 和 Concept API 随教材重写。

## 3. 候选来源对比

| 来源 | 课程与格式 | 许可与 AI 条款 | RAG 适配 | 建议 |
| --- | --- | --- | --- | --- |
| Active Calculus Single Variable 2e | Calculus I/II；HTML、PDF、PreTeXt 源码；2025 年第二版 | CC BY-SA 4.0；允许复制、改编及商业使用，要求署名和相同方式共享；本次未发现单独 AI 禁令 | 源码结构清晰，可按 section、definition、activity、exercise 切分 | **首选技术候选**；正式建库前书面确认 RAG 使用 |
| UBC CLP-1 Differential Calculus | 标准大学 Calculus I；HTML、PDF、PreTeXt/LaTeX 源码 | CC BY-NC-SA 4.0；非商业、署名、相同方式共享；本次未发现单独 AI 说明 | 结构和习题质量好，但主要是微分微积分，积分覆盖需结合 CLP-2 | **备选**；确认非商业性质及跨册范围 |
| MIT Calculus Open Textbook | 单变量和多变量内容充分；按章 PDF | MIT OCW 通常为 CC BY-NC-SA 4.0；2026-08-11 条款明确允许符合条件的非商业 AI training/development | AI 条款清晰，但 PDF 公式、分页和章节抽取成本高 | **合规语言较明确的备选**；逐项核对教材组件许可 |
| LibreTexts Calculus | 教材与改编版本很多；网页结构较好 | 平台内容许可不统一，需逐页查看来源、许可证与第三方素材 | 抓取容易，但大规模来源和许可追踪复杂 | 只作补充，不把整个 Bookshelf 作为一个来源 |
| OpenStax Calculus Volume 1 | Calculus I 覆盖完整；网页/PDF；当前项目已做临时抓取 | 页面标注 CC BY-NC-SA 4.0，同时明确禁止未经许可用于 LLM training 或其他生成式 AI ingestion | 技术上可按小节抓取，但页面正文重复、公式/图注噪声明显 | **未获许可不得作为正式 RAG 来源** |

## 4. 推荐方案

### 4.1 第一选择：Active Calculus 2e

选择理由：

- PreTeXt 源文件比网页抓取更适合保留语义结构。
- Calculus I 对应前四章，范围明确。
- 教材强调概念理解、活动和数学表达，与 Explain-to-Unlock 的教学目标一致。
- CC BY-SA 4.0 不包含 NC 限制，未来使用边界比 BY-NC-SA 更宽。
- 官方维护第二版，HTML、PDF 和源文件均可获得。

它仍不是“拿来即可正式使用”。ShareAlike 对教材改编、索引和系统中展示的派生内容
如何适用，需要学校确认；图片、交互练习和外部 WeBWorK 内容也应与正文分开核查。

建议向作者发送的确认问题：

1. 是否允许在非商业毕业设计中下载 2e PreTeXt 源文件并建立本地向量索引？
2. 是否允许把检索片段发送给第三方 LLM 生成教学提示？
3. 是否允许在学生端展示短片段、公式、书名、小节和官方链接？
4. 项目仓库是否可以提交清洗后的文本/元数据，还是只允许提交抓取脚本？
5. 对 RAG 索引、生成内容和项目整体的 BY-SA 标注方式有何要求？

### 4.2 许可确认失败时

- 若项目严格非商业，可进一步向 MIT OCW 确认 RAG 是否属于其允许的 AI
  development；它的 AI 条款比其他候选更明确，但解析 PDF 的工程成本更高。
- UBC CLP 可作为微分微积分备选，但积分部分需要 CLP-2，且 NC 限制不适合未来
  可能的商业化场景。
- 最稳妥的正式试点来源仍是**学校或任课教师自行编写并明确授权给本项目的知识卡、
  定义和例题**。授权文本应明确包含本地存储、向量化、向 LLM 发送片段和学生端展示。

## 5. 建库前的验收门

在重新运行 ingest 之前，必须同时满足：

- 记录 `source_id`、书名、版本/发布日期、许可证 URL、核查日期和许可证明。
- 冻结一份可复现的源文件版本（release、commit SHA 或文件校验和）。
- 明确正文、图片、习题、答案和外部交互资源是否使用同一许可证。
- 确认是否允许把检索片段发送给当前 LLM 服务商。
- 设计每个数字页面的署名与来源链接，而不只在 README 中统一署名。
- 规定删除/替换来源后如何重建索引，并确保旧向量和文本快照同步删除。
- 通过教师抽样检查后，才将新知识库标记为可用于学生试点。

## 6. 对当前项目的影响

[`backend/textbook.py`](../backend/textbook.py) 当前只记录
`LICENSE = "CC BY-NC-SA 4.0"`，无法表达 OpenStax 的 AI 附加声明、核查时间和许可
证据。后续教材元数据至少应增加：

- `source_id`
- `edition`
- `license_name`
- `license_url`
- `ai_use_status`
- `permission_reference`
- `verified_at`
- `source_revision`

当前本地 OpenStax HTML 和向量索引只应视为临时技术样本，不应对外分发，也不应
用于正式学生数据采集。本轮不删除或重建现有索引。

## 7. 官方来源

- OpenStax Calculus Volume 1 Preface（包含许可和 AI ingestion 声明）：
  https://openstax.org/books/calculus-volume-1/pages/preface
- Active Calculus Single Variable 2e：
  https://activecalculus.org/acs2e/
- Active Calculus 2e Colophon（CC BY-SA 4.0）：
  https://activecalculus.org/single2e/frontmatter-3.html
- Active Calculus 源码仓库：
  https://github.com/active-calculus/active-calculus-single-mbx
- UBC CLP-1：
  https://personal.math.ubc.ca/~CLP/CLP1/
- MIT Calculus Open Textbook：
  https://ocw.mit.edu/courses/res-18-001-calculus-fall-2023/pages/open-textbook/
- MIT OCW Privacy and Terms of Use（含 Permitted Use of AI Training）：
  https://ocw.mit.edu/pages/privacy-and-terms-of-use/
- LibreTexts Terms & Conditions：
  https://libretexts.org/terms-conditions
