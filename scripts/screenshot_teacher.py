"""Capture a full-page screenshot of the Teacher Dashboard for visual review.

    python scripts/screenshot_teacher.py [url] [output.png] [en|zh] [nav label]

The optional nav label (e.g. "学情诊断" / "Diagnose") is clicked before the
shot, so each dashboard section can be reviewed on its own.
"""
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

URL = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8503"
OUT = Path(sys.argv[2] if len(sys.argv) > 2 else "reports/teacher_dashboard.png")
LANG = sys.argv[3] if len(sys.argv) > 3 else "en"
NAV = sys.argv[4] if len(sys.argv) > 4 else ""


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch()
        # Streamlit scrolls inside its own container, so a tall viewport (rather
        # than full_page) is what actually captures the whole dashboard.
        page = browser.new_page(viewport={"width": 1680, "height": 3200})
        page.goto(URL, wait_until="networkidle", timeout=60000)
        page.wait_for_timeout(6000)
        if LANG == "zh":
            page.get_by_text("中文", exact=True).click()
            page.wait_for_timeout(5000)
        if NAV:
            page.get_by_role("button", name=NAV).first.click()
            page.wait_for_timeout(5000)
        page.screenshot(path=str(OUT), full_page=True)
        browser.close()
    print(f"saved {OUT}")


if __name__ == "__main__":
    main()
