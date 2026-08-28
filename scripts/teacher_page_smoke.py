"""Headless render check for the Teacher Dashboard (backend must be running).

Runs the Streamlit script without a browser and reports any exception raised
during rendering, plus a summary of what got drawn.

    python -m scripts.teacher_page_smoke
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "frontend"))

from streamlit.testing.v1 import AppTest  # noqa: E402


def main() -> int:
    at = AppTest.from_file(str(ROOT / "frontend" / "teacher_app.py"), default_timeout=60)
    at.run()

    if at.exception:
        for exc in at.exception:
            print("EXCEPTION:", exc.value)
            print(exc.stack_trace)
        return 1

    print("OK - no exceptions")
    print(f"markdown blocks : {len(at.markdown)}")
    print(f"buttons         : {len(at.button)}")
    print(f"errors on page  : {[e.value for e in at.error]}")
    print(f"warnings        : {[w.value for w in at.warning]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
