# GenAI 微积分助教（GenAI Calculus Tutor）

*[English](README.md) | 中文*

一个面向 **微积分 1（Calculus 1）** 的可溯源 GenAI 学习原型，采用聚焦式三阶段路径：

1. **Concept 概念**：检索 MIT Calculus 教材并生成带章节出处的知识卡；
2. **Practice 练习**：使用已验证教材题或生成四类题型，并在服务端判分；
3. **Tutor 助教**：通过 Chroma RAG 增强的苏格拉底 Agent，引导学生解释而非直接给答案。

系统同时实现输入/输出双向护栏、服务端 Explain-to-unlock 门控、轻量学习真实性检查和
可复现评测集。

技术栈为 **FastAPI（后端）+ Streamlit（前端）**。这是毕业设计课题「大学数学中的解释驱动
学习（explanation-driven learning）」的演示 Demo，架构上预留了之后接入 Learnvia 的空间。

---

## 设计理念

课题背景强调采集学生的**解释、论证与修正（explanations, justifications, revisions）**。
为了把这一点作为核心（同时给后续研究一个干净的对照），助教支持两种**实验条件**：

| 条件 | 行为 | 角色 |
|---|---|---|
| `explain` | **先解释才放行（Explain-to-unlock）**：学生必须先说明"为什么/怎么做"，助教才会给出下一步提示。 | 实验组（treatment） |
| `control` | 普通的渐进式苏格拉底提示，不强制解释。 | 对照组（control） |

每一轮对话都会写入 `data/logs/<session_id>.jsonl`（学生文本、推理质量评估、采取的动作、
延迟、掌握度），这是分析解释驱动学习的原始数据。

> 方法学要点：**两个条件用同样的方式测量**推理质量，唯一的区别是助教**是否要求**学生先
> 解释再推进。这样 explain 与 control 的对比才公平。

---

## 项目结构

```
GenAI_Calculus_Tutor/
├── backend/
│   ├── main.py        # FastAPI 应用与接口
│   ├── generator.py   # AI 内容生成（2.1）+ 自动判分
│   ├── socratic.py    # 苏格拉底式 Agent + explain-to-unlock 策略（2.2）
│   ├── llm.py         # OpenAI 兼容客户端（重试 + 稳健 JSON）
│   ├── guardrail.py   # 拦截"直接给我答案" / prompt injection
│   ├── rag.py         # Chroma 检索、引用与概念卡
│   ├── problems.py    # 加载静态题库
│   ├── store.py       # 内存会话 + JSONL 事件日志
│   ├── schemas.py     # pydantic 模型
│   └── config.py      # 环境变量 / 路径
├── frontend/
│   └── streamlit_app.py   # 概念 → 练习 → 助教聚焦流程
├── data/
│   ├── problems.json  # 12 道种子 Calc 1 题（助教也会用）
│   ├── eval/          # 安全与评测固定样例
│   ├── textbook/      # MIT 元数据、PDF、人工校验内容与解析资源
│   ├── chroma/        # 本地生成的向量索引（不提交）
│   └── logs/          # 每会话 JSONL 日志（已 gitignore）
├── scripts/           # 冒烟/API/生成 测试 + 分析
├── requirements.txt
└── .env               # LLM 凭据（已 gitignore）
```

---

## 安装

1. 准备 Python 环境（Python 3.9+），安装依赖：

```bash
pip install -r requirements.txt
```

2. 解析 MIT Fall 2017 章节 PDF，并建立 Chroma 索引：

```bash
mineru -p data/textbook/mit-calculus/pdfs -o data/textbook/mit-calculus/parsed -b pipeline -m txt -f false -t true
python -m scripts.build_mit_toc --write
python -m scripts.ingest_mit --chapters 1 2 3 4 5 6 7 8
```

仓库已包含八章 PDF 和人工校验后的元数据。MinerU 解析结果与 Chroma 索引属于本地运行
产物；如果 embedding 模型不在默认位置，请配置 `RAG_EMBEDDING_MODEL_DIR`。

3. 配置凭据：把 `.env.example` 复制为 `.env`，填入你的 key：

```
LLM_BASE_URL=https://yunwu.ai/v1
LLM_API_KEY=你的-api-key
LLM_MODEL=gpt-4o-mini
BACKEND_URL=http://localhost:8000
```

> 安全提示：切勿提交 `.env`。如果 key 曾在聊天/他处暴露，请到服务商后台**重置**。

---

## 运行

打开两个终端。

**终端 1 — 后端：**

```bash
uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

**终端 2 — 前端：**

```bash
streamlit run frontend/streamlit_app.py
```

打开 http://localhost:8501，按照 **Concept → Practice → Tutor** 学习。概念卡和 Tutor
会展示用于回答的 MIT 教材章节；练习答错时答案保持隐藏，可重试或进入引导。

### 学生视图 vs 老师视图

页面**默认面向学生**：隐藏实验内部信息（条件、推理评分、提示等级），只展示干净的界面
和一个鼓励性的进度条。实验条件会在**后台随机分配**，并照常记录到日志。

如果需要查看实验控制项和实时指标（用于测试或向评审演示），打开**老师视图**：

```
http://localhost:8501/?instructor=1
```

---

## API

| 方法 | 路径 | 用途 |
|---|---|---|
| `GET` | `/health` | 存活检查 + 模型信息 |
| `GET` | `/topics` | 微积分主题列表 |
| `GET` | `/concept` | 带引用的 RAG 概念卡 |
| `GET` | `/retrieve` | 检索结果调试/老师接口 |
| `POST` | `/generate` | 生成题目（类型/主题/难度） |
| `POST` | `/grade` | 自动判分 |
| `GET` | `/problems` | 公开种子题列表（不含答案） |
| `POST` | `/session/start` | 创建助教会话（种子题或生成题 id） |
| `POST` | `/session/{sid}/message` | 发送学生消息，返回助教回合 |
| `GET` | `/session/{sid}` | 当前会话状态 |

交互式文档：http://localhost:8000/docs 。

---

## 测试与评测

无需真实 LLM 的确定性检查：

```bash
python -m pytest -q
python -m scripts.evaluate_agent
```

可选的在线检查（需启动后端）：

```bash
python -m scripts.smoke_test       # LLM + Agent 行为
python -m scripts.api_test         # 走 API 的完整对话
python -m scripts.test_generation  # 四种题型的生成 + 判分
```

## 数据分析（用于实证研究）

每一轮都会记录到 `data/logs/<session_id>.jsonl`。把日志变成对比表格与图表：

```bash
python -m scripts.seed_sessions   # 可选：生成演示会话（后端需在跑）
python -m scripts.analyze_logs    # 生成 reports/ 表格与图
```

产物在 `reports/`：
- `turns.csv`、`sessions.csv`、`condition_summary.csv`
- `figures/condition_comparison.png` — 推理质量、解释字数、解题率、最终掌握度
  （explain vs control）
- `figures/assessment_distribution.png` — 推理质量分布

---

## 范围与路线图

**已实现（v0.4）：** MIT Calculus 第 1–8 章单一 Chroma collection、按 metadata 检索
concept/example、已验证教材题与四类 RAG 出题、带引用的苏格拉底 Tutor、答错不泄露答案的
服务端判分、Explain-to-unlock、中英文护栏、JSONL 事件日志、确定性测试与评测脚本。

**路线图（尚未实现）：** 生成数学内容的符号验算、持久化会话、经过验证的 BKT/DKT 学生
模型、多模态输入、聚合教师面板、自适应推荐和 LTI 集成。

## 教材授权与署名

知识片段来自 Gilbert Strang 编写、MIT OpenCourseWare 提供的 *Calculus*，采用
CC BY-NC-SA 4.0 许可。本项目使用 Fall 2017 的第 1–8 章 PDF 资源；每个索引片段保留
章节、小节、页码、图片、来源和署名信息。解析资源和生成索引不提交到仓库。

## 演示与简历表述

推荐演示路径：选择 **Chain Rule** → 查看带出处概念卡 → 生成练习 → 直接索答被拦截 →
给出理由后解锁下一步提示 → 在老师视图查看推理质量、安全事件与掌握度。

可用于简历的客观表述：

> 构建面向微积分学习的 RAG 增强苏格拉底式 Agent，基于 Chroma 对 MIT Calculus 八章内容
> 实现 metadata 过滤、语义检索与引用溯源；设计服务端 Explain-to-Unlock 策略及双向防剧透，并通过
> Golden Set 评测检索命中率、引用覆盖率、策略遵循率和答案泄漏率。
