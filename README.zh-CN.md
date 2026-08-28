# GenAI 微积分助教（GenAI Calculus Tutor）

*[English](README.md) | 中文*

一个面向 **微积分 1（Calculus 1）** 的 GenAI 系统原型。页面**左右并排**分为两块：

- **块 A（左）— 练习（内容生成，2.1）**：由 LLM 自动生成四种题型——**单选、多选、填空、
  拖拽排序（过程题）**——学生作答并**自动判分**。
- **块 B（右）— 助教（AI Agent，2.2）**：一个**苏格拉底式 AI 助教**，绝不直接给答案、要求
  学生**解释推理**、一步步引导。**默认即为自由对话**（可问任何问题），并可选择**关联**到
  左侧当前题目。

两块相互独立：助教本身就能单独使用，关联只是一次点击的操作。

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
│   ├── problems.py    # 加载静态题库
│   ├── store.py       # 内存会话 + JSONL 事件日志
│   ├── schemas.py     # pydantic 模型
│   └── config.py      # 环境变量 / 路径
├── frontend/
│   └── streamlit_app.py   # 两块：练习 + 助教
├── data/
│   ├── problems.json  # 12 道种子 Calc 1 题（助教也会用）
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

2. 配置凭据：把 `.env.example` 复制为 `.env`，填入你的 key：

```
LLM_BASE_URL=https://api.openlux.ai/v1
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

然后打开 Streamlit 地址（默认 http://localhost:8501）。页面左右分栏：

- **左（Practice 练习）**：选主题/题型，点 **Generate** 生成题目，作答后点 **Submit** 自动判分。
- **右（Tutor 助教）**：打开即可**自由提问**。若想针对生成的题目获得引导，点左侧
  **🔗 Link this question to the tutor**（关联当前题目）或右侧 **Link question**；点 **Free chat**
  可解除关联、回到自由问答。

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
| `POST` | `/generate` | 生成题目（类型/主题/难度） |
| `POST` | `/grade` | 自动判分 |
| `GET` | `/problems` | 公开种子题列表（不含答案） |
| `POST` | `/session/start` | 创建助教会话（种子题或生成题 id） |
| `POST` | `/session/{sid}/message` | 发送学生消息，返回助教回合 |
| `GET` | `/session/{sid}` | 当前会话状态 |

交互式文档：http://localhost:8000/docs 。

---

## 测试

后端运行时：

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

**本 Demo（v0.2）：** 四种题型的 AI 内容生成 + 自动判分（2.1）、带 explain-to-unlock 的
苏格拉底 Agent（2.2）、学生双块界面（练习 + 助教）、基础 guardrail、LaTeX 公式渲染、
逐轮日志、A/B 条件随机分配、学生/老师双视图。

**后续工作（已推迟）：** 自动生题、多模态输入（手写 / 图片 / 语音）、BKT/DKT 学生建模、
老师仪表盘、自适应难度、更强的越狱检测、以及 Learnvia 集成（LTI / 嵌入）。
