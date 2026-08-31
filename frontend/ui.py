"""Shared theming + top-right language toggle for both Streamlit pages.

Design tokens follow the UI/UX design-system pass for an education / learning
tool: a trustworthy "learning blue" primary, amber + status greens/reds for
data, neutral surfaces, soft rounded cards, and clear typographic hierarchy.
"""
import streamlit as st

import i18n

# --- Design tokens (education / learning) --------------------------------- #
PRIMARY = "#2563EB"        # learning blue
PRIMARY_DARK = "#1D4ED8"
SECONDARY = "#F59E0B"      # amber (accents)
SUCCESS = "#16A34A"
WARNING = "#D97706"
DANGER = "#DC2626"
BG = "#F4F7FE"             # soft blue-tinted background
SURFACE = "#FFFFFF"
FG = "#0F172A"
MUTED = "#64748B"
BORDER = "#E4ECFC"

_CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Fraunces:opsz,wght@9..144,600;9..144,700&display=swap');

:root {{
  --primary: {PRIMARY};
  --primary-dark: {PRIMARY_DARK};
  --secondary: {SECONDARY};
  --success: {SUCCESS};
  --danger: {DANGER};
  --bg: {BG};
  --surface: {SURFACE};
  --fg: {FG};
  --muted: {MUTED};
  --border: {BORDER};
}}

/* Base */
html, body, [class*="css"] {{ font-family: 'Inter', system-ui, sans-serif; }}
/* Soft blue canvas so white module cards visibly stand apart. */
.stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"],
[data-testid="stMain"], .main, section.main {{
  background: {BG} !important;
  color: {FG};
}}
.block-container, [data-testid="stMainBlockContainer"] {{
  padding-top: 2.2rem;
  max-width: 100% !important;
  padding-left: 3rem; padding-right: 3rem;
}}
/* Hide Streamlit's rainbow top bar; it clashes with the theme. */
[data-testid="stDecoration"] {{ display: none; }}

/* Headings */
h1, h2 {{ font-family: 'Fraunces', Georgia, serif; letter-spacing: -0.01em; color: {FG}; }}
h1 {{ font-weight: 700; }}
h3, h4 {{ font-family: 'Inter', sans-serif; font-weight: 600; color: {FG}; }}

/* Bordered containers -> module cards.
   Streamlit wraps plain layout blocks (columns, rows) in the same testid as
   st.container(border=True), but gives them the placeholder emotion class
   `st-emotion-cache-0`; excluding that keeps every column from turning into a
   card (which boxed stray labels and empty columns). */
div[data-testid="stVerticalBlockBorderWrapper"]:not(.st-emotion-cache-0) {{
  background: {SURFACE};
  border: 1px solid {BORDER} !important;
  border-radius: 18px !important;
  box-shadow: 0 1px 2px rgba(15,23,42,0.04), 0 8px 24px rgba(37,99,235,0.06);
  padding: 14px 16px;
}}
/* Nested cards (e.g. assignment rows) stay flat and compact. */
div[data-testid="stVerticalBlockBorderWrapper"]:not(.st-emotion-cache-0)
div[data-testid="stVerticalBlockBorderWrapper"]:not(.st-emotion-cache-0) {{
  box-shadow: none;
  border-radius: 12px !important;
  padding: 4px 8px;
}}

/* Buttons */
.stButton > button {{
  border-radius: 12px;
  border: 1px solid {BORDER};
  font-weight: 600;
  transition: transform .12s ease, box-shadow .15s ease, background .15s ease;
}}
.stButton > button:hover {{ transform: translateY(-1px); }}
.stButton > button[kind="primary"],
div[data-testid="stFormSubmitButton"] > button[kind="primaryFormSubmit"] {{
  background: {PRIMARY};
  border-color: {PRIMARY};
  color: #FFFFFF;
  box-shadow: 0 6px 16px rgba(37,99,235,0.25);
}}
.stButton > button[kind="primary"]:hover,
div[data-testid="stFormSubmitButton"] > button[kind="primaryFormSubmit"]:hover {{
  background: {PRIMARY_DARK};
}}
div[data-testid="stFormSubmitButton"] > button {{
  border-radius: 12px;
  font-weight: 600;
}}

/* Metrics -> cards */
div[data-testid="stMetric"] {{
  background: {SURFACE};
  border: 1px solid {BORDER};
  border-radius: 16px;
  padding: 14px 16px;
  box-shadow: 0 1px 2px rgba(15,23,42,0.04);
}}
div[data-testid="stMetricValue"] {{ color: {PRIMARY}; font-weight: 700; }}

/* Chat bubbles */
div[data-testid="stChatMessage"] {{
  border-radius: 14px;
  border: 1px solid {BORDER};
  background: {SURFACE};
}}

/* Progress bar */
div[data-testid="stProgress"] > div > div > div {{ background-image: none; background-color: {PRIMARY}; }}

/* Inputs */
div[data-baseweb="select"] > div, .stTextInput input, .stTextArea textarea {{
  border-radius: 12px !important;
}}

/* Sidebar */
section[data-testid="stSidebar"] {{ background: {SURFACE}; border-right: 1px solid {BORDER}; }}

/* Language toggle row (top-right) */
.lang-row {{ display: flex; justify-content: flex-end; margin-top: -0.6rem; }}

/* Insight cards accent bar */
.insight-info {{ border-left: 4px solid {SUCCESS} !important; }}
.insight-warning {{ border-left: 4px solid {WARNING} !important; }}
.insight-critical {{ border-left: 4px solid {DANGER} !important; }}

/* Equal-height cards inside a columns row (learning path). */
div[data-testid="stHorizontalBlock"] {{ align-items: stretch; }}
div[data-testid="column"] > div[data-testid="stVerticalBlockBorderWrapper"] {{
  height: 100%;
}}

/* --- Dashboard building blocks ------------------------------------------ */

/* Section header: eyebrow + title + subtitle */
.sec-eyebrow {{ font-size: .72rem; letter-spacing: .14em; text-transform: uppercase;
  color: {PRIMARY}; font-weight: 700; }}
.sec-title {{ font-family: 'Fraunces', Georgia, serif; font-size: 1.45rem;
  font-weight: 700; color: {FG}; margin: .1rem 0 .15rem; }}
.sec-sub {{ color: {MUTED}; font-size: .92rem; margin-bottom: .35rem; }}

/* Panel heading inside a section */
.panel-title {{ font-weight: 700; color: {FG}; font-size: 1rem; margin-bottom: .1rem; }}
.panel-sub {{ color: {MUTED}; font-size: .84rem; margin-bottom: .5rem; }}

/* Module card header: icon chip + title + plain-language description */
.ph {{ display: flex; gap: 12px; align-items: flex-start; margin: 2px 0 12px; }}
.ph-icon {{ flex: 0 0 36px; width: 36px; height: 36px; border-radius: 11px;
  background: #EFF4FF; border: 1px solid {BORDER};
  display: flex; align-items: center; justify-content: center; font-size: 1.05rem; }}
.ph-title {{ font-weight: 700; font-size: 1.02rem; color: {FG}; line-height: 1.3; }}
.ph-desc {{ color: {MUTED}; font-size: .84rem; margin-top: 3px; line-height: 1.5; }}

/* Primary KPI cards */
.kpi-grid {{ display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 14px; }}
.kpi-card {{ background: {SURFACE}; border: 1px solid {BORDER}; border-radius: 18px;
  padding: 18px 20px 16px; position: relative; overflow: hidden;
  box-shadow: 0 1px 2px rgba(15,23,42,.04), 0 8px 24px rgba(37,99,235,.05); }}
.kpi-card::before {{ content: ""; position: absolute; left: 0; top: 0; bottom: 0;
  width: 4px; background: var(--accent, {PRIMARY}); }}
.kpi-label {{ font-size: .8rem; color: {MUTED}; font-weight: 600; }}
.kpi-value {{ font-size: 2.05rem; font-weight: 800; color: {FG}; line-height: 1.2;
  margin-top: .1rem; }}
.kpi-sub {{ font-size: .78rem; color: {MUTED}; }}

/* Secondary stat strip */
.stat-strip {{ display: grid; grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 10px; margin-top: 12px; }}
.stat-item {{ display: flex; justify-content: space-between; align-items: baseline;
  background: {SURFACE}; border: 1px solid {BORDER}; border-radius: 12px;
  padding: 10px 14px; }}
.stat-label {{ font-size: .82rem; color: {MUTED}; }}
.stat-value {{ font-size: 1.05rem; font-weight: 700; color: {FG}; }}

/* Insight cards (severity accent drawn here, not via Streamlit containers) */
.insight {{ background: {SURFACE}; border: 1px solid {BORDER}; border-left-width: 4px;
  border-radius: 14px; padding: 12px 16px; margin-bottom: 10px; }}
.insight-title {{ font-weight: 700; color: {FG}; font-size: .95rem; }}
.insight-detail {{ color: {MUTED}; font-size: .85rem; margin-top: .25rem; line-height: 1.55; }}
.sev-info {{ border-left-color: {SUCCESS}; }}
.sev-warning {{ border-left-color: {WARNING}; }}
.sev-critical {{ border-left-color: {DANGER}; }}

/* Two-column mini stat card (condition comparison) */
.mini-card {{ background: {SURFACE}; border: 1px solid {BORDER}; border-radius: 14px;
  padding: 14px 16px; }}
.mini-head {{ font-weight: 700; color: {FG}; margin-bottom: .35rem; }}
.mini-row {{ display: flex; justify-content: space-between; font-size: .85rem;
  padding: 3px 0; }}
.mini-row span:first-child {{ color: {MUTED}; }}
.mini-row span:last-child {{ font-weight: 700; color: {FG}; }}

/* Pills / badges */
.badge {{ display: inline-block; font-size: .74rem; font-weight: 600; padding: 3px 10px;
  border-radius: 999px; border: 1px solid {BORDER}; color: {MUTED}; background: #F8FAFF; }}
.badge-warn {{ color: {WARNING}; border-color: #FDE68A; background: #FFFBEB; }}

/* Section guide rows (landing card) */
.guide-row {{ display: flex; gap: 10px; align-items: flex-start; margin-top: 10px; }}
.guide-icon {{ font-size: 1rem; line-height: 1.35; }}
.guide-name {{ display: block; font-weight: 600; color: {FG}; font-size: .92rem; }}
.guide-hint {{ display: block; color: {MUTED}; font-size: .82rem; line-height: 1.5; }}

/* Empty states */
.empty {{ border: 1px dashed {BORDER}; border-radius: 14px; padding: 22px 18px;
  text-align: center; color: {MUTED}; font-size: .87rem; background: #FBFCFF; }}

@media (max-width: 1200px) {{
  .kpi-grid, .stat-strip {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
}}
</style>
"""


def setup_page(title: str, icon: str):
    """Call once per page (after set_page_config) to apply theme + lang state."""
    st.session_state.setdefault("lang", "en")
    st.markdown(_CSS, unsafe_allow_html=True)


def section(eyebrow: str, title: str, subtitle: str = "") -> None:
    """Section header used to separate the dashboard's overview/diagnose/act blocks."""
    html = (f'<div class="sec-eyebrow">{eyebrow}</div>'
            f'<div class="sec-title">{title}</div>')
    if subtitle:
        html += f'<div class="sec-sub">{subtitle}</div>'
    st.markdown(html, unsafe_allow_html=True)


def panel_heading(title: str, subtitle: str = "") -> None:
    html = f'<div class="panel-title">{title}</div>'
    if subtitle:
        html += f'<div class="panel-sub">{subtitle}</div>'
    st.markdown(html, unsafe_allow_html=True)


def panel_header(icon: str, title: str, desc: str = "") -> None:
    """Card header: icon chip + title + one-line plain-language description."""
    inner = f'<div class="ph-title">{title}</div>'
    if desc:
        inner += f'<div class="ph-desc">{desc}</div>'
    st.markdown(
        f'<div class="ph"><div class="ph-icon">{icon}</div><div>{inner}</div></div>',
        unsafe_allow_html=True,
    )


def empty_state(message: str) -> None:
    st.markdown(f'<div class="empty">{message}</div>', unsafe_allow_html=True)


def rerun_fragment() -> None:
    """Rerun just the enclosing fragment; fall back to a full rerun when not in
    a fragment context (e.g. under Streamlit's AppTest harness)."""
    from streamlit.errors import StreamlitAPIException
    try:
        st.rerun(scope="fragment")
    except StreamlitAPIException:
        st.rerun()


def language_toggle():
    """Top-right language switch (English / 中文).

    The radio's widget state IS the shared `lang` key, so both the student page
    and the teacher page read/write the same value. Selecting a language just
    updates that key; Streamlit's automatic rerun then re-renders every t()
    string in the new language. No manual rerun (which caused websocket flaps).
    """
    st.session_state.setdefault("lang", "en")
    labels = {"en": "EN", "zh": "中文"}
    _, ctrl = st.columns([8, 1.2])
    with ctrl:
        st.radio(
            "language", ["en", "zh"],
            format_func=lambda o: labels[o],
            key="lang",
            horizontal=True, label_visibility="collapsed",
        )
