"""Teacher dashboard panels.

Each module owns one block of the dashboard and exposes a single
`render_*_panel(...)` entry point. Panels render UI only: analytics data and
API callables are injected by the orchestrator (`frontend/teacher_app.py`), so
no panel talks to the backend directly.

See docs/教师界面_模块化设计.md for the module map and data contracts.
"""
