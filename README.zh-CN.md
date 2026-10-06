# GenAI 微积分助教（GenAI Calculus Tutor）

*[English](README.md) | 中文*

面向 **微积分 1** 的可溯源 GenAI 学习系统。学生按 MIT OpenCourseWare 上 Gilbert
Strang 的 *Calculus* 学习：读带出处的概念页、做教材题或生成题，并与苏格拉底式
导师对话（引导推理、不直接给答案）。教师从同一份交互日志看班级汇总。

技术栈：**FastAPI（后端）+ Vite + React（学生端）+ Streamlit（教师端）**。
学生端与教师端是两个明确分开的本地应用，共用同一个后端数据。

---

## 学生端与教师端

两个端口之间通过角色入口跳转：

- **学生：** 教材目录、概念页、自由练习 / 闯关、题下导师、收藏。支持中英文；
  教材正文可随界面语言显示。
- **教师（`teacher-frontend/`，8503）：** 总览、诊断、布置、助手。

导师仍支持两种条件（`explain` / `control`）。explain-to-unlock 要求先解释再给
下一步提示；control 只做渐进提示。两边用同一套评分。每轮写入
`data/logs/<session_id>.jsonl`。

---

## 项目结构

```
GenAI_Calculus_Tutor/
├── backend/                 # FastAPI：RAG、出题判分、导师、分析
├── student-frontend/           # 学生端：Vite + React，5173 端口
├── teacher-frontend/           # 教师端：Streamlit，8503 端口
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
cd student-frontend
npm install
```

Windows 上若 `npm install` 报全局缓存 `EPERM`：

```powershell
npm config set cache "$env:LOCALAPPDATA\npm-cache"
npm install
```

---

## 运行

本项目包含三个进程，均使用固定的本机端口：

| 进程 | 地址 | 技术栈 |
|---|---|---|
| 后端 API | http://127.0.0.1:8000 | FastAPI |
| 教师端（唯一） | http://127.0.0.1:8503/?lang=zh | Streamlit |
| 学生端 | http://127.0.0.1:5173 | React + Vite |

### 一键启动（推荐）

装好依赖（`pip install -r requirements.txt`，并在 `student-frontend/` 执行
`npm install`）后，从仓库根目录运行：

```bash
scripts/run_dev.sh
```

脚本会依次启动后端、教师端、学生端，按 `Ctrl+C` 一并停止。端口可用
`BACKEND_PORT / TEACHER_PORT / STUDENT_PORT` 环境变量覆盖。

### 手动启动（三个终端）

均从仓库根目录开始。

**终端 1 — 后端：**

```bash
python -m uvicorn backend.main:app --reload --reload-dir backend --host 127.0.0.1 --port 8000
```

`--reload-dir backend` 避免 `node_modules` 触发后端反复重启。Windows 上请用
`127.0.0.1`，不要用 `localhost`（Node 18+ 可能把 `localhost` 解析成 IPv6，
而 uvicorn 只听 IPv4）。

**终端 2 — 教师端：**

```bash
python -m streamlit run teacher-frontend/teacher_app.py \
  --server.address 127.0.0.1 --server.port 8503
```

**终端 3 — 学生端：**

```bash
cd student-frontend
npm run dev -- --host 127.0.0.1
```

### 师生切换

- 学生端 → 教师端：在右上角 **设置** 中点击 **教师**，会打开
  `http://127.0.0.1:8503/?lang=<当前语言>`。
- 教师端 → 学生端：顶部 **学生** 链接回到 `http://127.0.0.1:5173/`。

两端是各自独立的进程与端口，不共享同一页面，但跳转地址固定，不会指向其他版本。
教师端只保留 Streamlit 这一个界面，`student-frontend` 中不再包含 React 教师页面。

后端未启动时，看板会明确提示“无法连接后端”，而不会以演示数据冒充真实结果；
翻译接口（`POST /localize`）失败也会直接报错。

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
