# GenAI 微积分助教（GenAI Calculus Tutor）

*[English](README.md) | 中文*

面向 **微积分 1** 的可溯源 GenAI 学习系统。学生按 MIT OpenCourseWare 上 Gilbert
Strang 的 *Calculus* 学习：读带出处的概念页、做教材题或生成题，并与苏格拉底式
导师对话（引导推理、不直接给答案）。教师从同一份交互日志看班级汇总。

技术栈：**FastAPI（后端）+ Vite + React（前端）**。学生端和教师端是同一个应用。
`frontend/` 下的 Streamlit 代码不是现行界面。

---

## 学生端与教师端

在侧栏底部切换角色：

- **学生：** 教材目录、概念页、自由练习 / 闯关、题下导师、收藏。支持中英文；
  教材正文可随界面语言显示。
- **教师：** 总览、诊断、布置、助手。图表用 ECharts。

导师仍支持两种条件（`explain` / `control`）。explain-to-unlock 要求先解释再给
下一步提示；control 只做渐进提示。两边用同一套评分。每轮写入
`data/logs/<session_id>.jsonl`。

---

## 项目结构

```
GenAI_Calculus_Tutor/
├── backend/                 # FastAPI：RAG、出题判分、导师、分析
├── frontend-web/            # Vite + React（现行界面）
├── frontend/                # Streamlit 原型（运行时不用）
├── data/textbook/mit-calculus/
├── data/chroma/             # 本地向量索引（不提交）
├── data/logs/               # 会话 JSONL（不提交）
├── scripts/
├── tests/
├── requirements.txt
└── .env                     # LLM 凭据（不提交）
```

---

## 安装

1. Python 3.9+（本仓库常用 conda 环境 `yolo8`）：

```bash
pip install -r requirements.txt
```

2. 用已打包的 MIT 八章内容建 Chroma 索引（首次，或教材更新后）。embedding 模型
   若本地没有会在第一次运行时下载：

```bash
python -m scripts.ingest_mit --chapters 1 2 3 4 5 6 7 8
```

只有要从 PDF 重新抽文本时才需要 MinerU。仓库已包含校验过的段落、习题、插图和目录。

3. 复制 `.env.example` 为 `.env`，填写 `LLM_API_KEY`。不要提交 `.env`。

4. 前端依赖：

```bash
cd frontend-web
npm install
```

Windows 上若 `npm install` 报全局缓存 `EPERM`：

```powershell
npm config set cache "$env:LOCALAPPDATA\npm-cache"
npm install
```

---

## 运行

两个终端，均从仓库根目录开始。

**终端 1 — 后端：**

```bash
python -m uvicorn backend.main:app --reload --reload-dir backend --host 127.0.0.1 --port 8000
```

`--reload-dir backend` 避免 `node_modules` 触发后端反复重启。Windows 上请用
`127.0.0.1`，不要用 `localhost`（Node 18+ 可能把 `localhost` 解析成 IPv6，
而 uvicorn 只听 IPv4）。

**终端 2 — 前端：**

```bash
cd frontend-web
npx vite --host 127.0.0.1
```

PowerShell 也可以显式指定后端：

```powershell
cd frontend-web
$env:VITE_BACKEND_URL="http://127.0.0.1:8000"
npm run dev
```

打开 http://127.0.0.1:5175（或以 Vite 打印的端口为准）。在侧栏底部切换
**教师 / 学生**。

后端未启动时，教师页可能出现 `● demo data`。翻译接口（`POST /localize`）
不会用演示文案冒充译文，失败会直接报错。

可选：给教师看板灌演示日志：

```bash
python scripts/seed_demo_logs.py
```

---

## API

交互文档：http://127.0.0.1:8000/docs

| 方法 | 路径 | 用途 |
|---|---|---|
| `GET` | `/health` | 存活、模型、RAG 状态 |
| `GET` | `/catalog` | 教材目录 |
| `GET` | `/concept` | 带引用的概念卡 |
| `POST` | `/generate` | 生成练习题 |
| `POST` | `/grade` | 服务端判分 |
| `POST` | `/session/start` | 开始导师会话 |
| `POST` | `/session/{sid}/message` | 一轮导师对话 |
| `POST` | `/localize` | 仅用于显示的翻译 |
| `GET` | `/analytics/class` | 班级指标 |
| `POST` | `/analytics/ask` | 教师助手 |

---

## 测试

```bash
python -m pytest -q
python -m scripts.evaluate_agent
```

后端已启动时：

```bash
python -m scripts.smoke_test
python -m scripts.api_test
python -m scripts.test_generation
```

---

## 教材授权

内容来自 Gilbert Strang《Calculus》，MIT OpenCourseWare，CC BY-NC-SA 4.0
（Fall 2017，第 1–8 章）。解析结果和 Chroma 索引不提交到仓库。
