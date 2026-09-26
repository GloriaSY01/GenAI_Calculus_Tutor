"""Shared theming + top-right language toggle for both Streamlit pages.

Design tokens follow the UI/UX design-system pass for an education / learning
tool: a trustworthy "learning blue" primary, amber + status greens/reds for
data, neutral surfaces, soft rounded cards, and clear typographic hierarchy.
"""
import streamlit as st

import i18n

# --- Design tokens (education / learning) --------------------------------- #
PRIMARY = "#2A4ED6"        # aligned with the React student shell
PRIMARY_DARK = "#233FAE"
SECONDARY = "#F59E0B"      # amber (accents)
SUCCESS = "#16A34A"
WARNING = "#D97706"
DANGER = "#DC2626"
BG = "#F6F8FC"
SURFACE = "#FFFFFF"
FG = "#141A2E"
MUTED = "#7B849C"
BORDER = "#E6E9F2"

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
.stApp,
[data-testid="stAppViewContainer"],
[data-testid="stMain"],
[data-testid="stMain"] > div,
.main,
.main > div,
section.main,
section.main > div {{
  padding-top: 0 !important;
  margin-top: 0 !important;
}}
.block-container,
[data-testid="stMainBlockContainer"],
[data-testid="stAppViewBlockContainer"] {{
  padding-top: 0 !important;
  margin-top: 0 !important;
  max-width: 100% !important;
  padding-left: 4vw; padding-right: 4vw;
}}
[data-testid="stMainBlockContainer"] > div:first-child,
[data-testid="stAppViewBlockContainer"] > div:first-child,
.element-container:has(.sw-header),
.stMarkdown:has(.sw-header) {{
  margin-top: 0 !important;
  padding-top: 0 !important;
}}
/* Hide Streamlit's rainbow top bar; it clashes with the theme. */
[data-testid="stDecoration"] {{ display: none; }}
[data-testid="stHeader"], [data-testid="stToolbar"] {{
  display: none !important;
  height: 0 !important;
  min-height: 0 !important;
}}

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

/* Student header rules copied for the teacher shell. */
.sw-header {{
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24px;
  width: 100vw;
  padding: 20px 4vw;
  background: {SURFACE};
  border-bottom: 1px solid {BORDER};
  box-sizing: border-box;
}}
.sw-brand {{
  display: flex;
  align-items: center;
  gap: 12px;
  border: 0;
  background: none;
  color: {FG};
  text-align: left;
  font-size: 17px;
  font-weight: 750;
  cursor: pointer;
  font-family: 'Inter', system-ui, sans-serif;
}}
.sw-brand > span {{
  display: grid;
  place-items: center;
  width: 42px;
  height: 42px;
  border-radius: 14px;
  background: {PRIMARY};
  color: white;
  font: 32px Georgia, serif;
}}
.sw-brand small {{
  display: block;
  margin-top: 4px;
  font-weight: 400;
  font-size: 12px;
  color: {MUTED};
}}
.sw-account {{
  display: flex;
  align-items: center;
  gap: 10px;
}}
.sw-account > .inp {{
  width: 160px;
}}
.sw-account > select.inp {{
  width: 195px;
}}
.sw-preferences {{
  position: relative;
}}
.sw-preferences summary {{
  cursor: pointer;
  white-space: nowrap;
  padding: 10px;
}}
.sw-preferences > div {{
  position: absolute;
  right: 0;
  top: 42px;
  z-index: 30;
  padding: 20px;
  width: 240px;
  background: {SURFACE};
  border: 1px solid {BORDER};
  border-radius: 16px;
  box-shadow: 0 18px 40px rgba(20,26,46,.12), 0 6px 14px rgba(20,26,46,.06);
}}
.inp {{
  width: 100%;
  padding: 10px 12px;
  border-radius: 12px;
  border: 1px solid #D9DEEC;
  background: #FBFCFE;
  color: {FG};
  font-size: 14px;
  font-family: 'Inter', system-ui, sans-serif;
  transition: border-color .15s, box-shadow .15s;
}}
.inp:focus {{
  outline: none;
  border-color: #5D89FB;
  box-shadow: 0 0 0 3px #EEF4FF;
}}
select.inp {{
  cursor: pointer;
}}

/* Streamlit wrapper compensation; the copied header itself stays identical. */
.element-container:has(.sw-header),
.stMarkdown:has(.sw-header) {{
  margin-left: calc(50% - 50vw) !important;
  margin-right: calc(50% - 50vw) !important;
  margin-top: -12px !important;
  width: 100vw !important;
}}
.sw-main-spacer {{
  height: 28px;
  background: transparent;
  margin: 0;
}}
.sw-account > .inp::placeholder {{
  color: #7B849C;
}}
.sw-preferences > summary {{
  color: {FG} !important;
}}
.sw-preferences > summary::-webkit-details-marker {{
  display: inline-block;
}}
.teacher-settings-panel {{
  padding: 0;
}}
.teacher-settings-divider {{
  height: 1px;
  background: #E6E9F2;
  margin: 4px 0;
}}
.teacher-role-switch {{
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 6px;
  margin: 12px 0;
}}
.teacher-setting-pill,
.teacher-lang-pill {{
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  border: 1px solid #D9DEEC;
  border-radius: 12px;
  background: #FBFCFE;
  color: #4A5570 !important;
  text-decoration: none !important;
  font-size: 12.5px;
  font-weight: 400;
  box-shadow: none;
  cursor: pointer;
  transition: all .15s;
}}
.teacher-setting-pill {{
  padding: 8px 6px;
}}
.teacher-setting-pill.active {{
  background: linear-gradient(135deg, #3b66f0, #2a4ed6);
  border-color: transparent;
  color: #FFFFFF !important;
  box-shadow: 0 1px 2px rgba(20,26,46,.06), 0 1px 3px rgba(20,26,46,.05);
}}
.teacher-theme-row {{
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin: 12px 0;
  color: #7B849C !important;
  text-decoration: none !important;
  font-size: 13px;
  font-weight: 400;
}}
.teacher-switch {{
  position: relative;
  display: inline-block;
  width: 46px;
  height: 26px;
  border-radius: 999px;
  background: #D9DEEC;
  flex: 0 0 auto;
}}
.teacher-switch > span {{
  position: absolute;
  top: 3px;
  left: 3px;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #FFFFFF;
  box-shadow: 0 1px 2px rgba(20,26,46,.06), 0 1px 3px rgba(20,26,46,.05);
  transition: transform .2s ease;
}}
.teacher-switch.on {{
  background: #3b66f0;
}}
.teacher-switch.on > span {{
  transform: translateX(20px);
}}
.teacher-lang-row {{
  display: flex;
  gap: 6px;
  align-items: center;
}}
.teacher-lang-pill {{
  padding: 8px 13px;
  border-radius: 999px;
  font-size: 13px;
}}
.teacher-lang-pill.active {{
  background: #EEF4FF;
  border-color: #8FB2FF;
  color: #233FAE !important;
}}
@media (max-width: 760px) {{
  .block-container, [data-testid="stMainBlockContainer"] {{
    padding-left: 18px;
    padding-right: 18px;
  }}
  .sw-brand {{
    font-size: 15px;
  }}
}}

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

/* Section header: step label + title + subtitle */
.sec-eyebrow {{ font-family: 'Fraunces', Georgia, serif; font-size: 1.45rem;
  letter-spacing: 0; text-transform: none; color: {PRIMARY}; font-weight: 700;
  margin: .1rem 0 .15rem; }}
.sec-title {{ font-family: 'Fraunces', Georgia, serif; font-size: 1.12rem;
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

_DARK_CSS = """
<style>
:root {
  --bg: #0b0f1a;
  --surface: #141a2b;
  --fg: #eef1f9;
  --muted: #8791ab;
  --border: #242c44;
}
.stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"],
[data-testid="stMain"], .main, section.main {
  background: #0b0f1a !important;
  color: #eef1f9 !important;
}
h1, h2, h3, h4, .teacher-brand-name, .sec-title, .panel-title,
.kpi-value, .stat-value, .mini-head, .insight-title {
  color: #eef1f9 !important;
}
.teacher-brand-sub, .sec-sub, .panel-sub, .ph-desc, .kpi-label,
.kpi-sub, .stat-label, .insight-detail, .mini-row span:first-child,
.guide-hint, .empty {
  color: #8791ab !important;
}
div[data-testid="stVerticalBlockBorderWrapper"]:not(.st-emotion-cache-0),
div[data-testid="stMetric"], .kpi-card, .stat-item, .mini-card, .insight,
div[data-testid="stChatMessage"] {
  background: #141a2b !important;
  border-color: #242c44 !important;
}
div[data-baseweb="select"] > div,
.stTextInput input,
.stTextArea textarea {
  background: #141a2b !important;
  border-color: #242c44 !important;
  color: #eef1f9 !important;
}
.sw-main-spacer {
  background: transparent !important;
}
.sw-preferences > div,
.sw-account > .inp,
.teacher-setting-pill,
.teacher-lang-pill {
  background: #141a2b !important;
  border-color: #242c44 !important;
  color: #eef1f9 !important;
}
.sw-account > .inp::placeholder {
  color: #8791ab !important;
}
.sw-preferences > summary {
  color: #eef1f9 !important;
}
.teacher-settings-divider {
  background: #242c44 !important;
}
.teacher-setting-pill.active {
  background: #2F55E7 !important;
  border-color: #2F55E7 !important;
  color: #FFFFFF !important;
}
.teacher-lang-pill.active {
  background: #12203f !important;
  border-color: #8FB2FF !important;
  color: #8FB2FF !important;
}
.empty {
  background: #101524 !important;
}
</style>
"""


def setup_page(title: str, icon: str):
    """Call once per page (after set_page_config) to apply theme + lang state."""
    st.session_state.setdefault("lang", "en")
    st.session_state.setdefault("theme", "light")
    st.markdown(_CSS, unsafe_allow_html=True)
    if st.session_state.get("theme") == "dark":
        st.markdown(_DARK_CSS, unsafe_allow_html=True)


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
    previous_lang = st.session_state.get("_last_selected_lang")
    labels = {"en": "EN", "zh": "中文"}
    _, ctrl = st.columns([8, 1.2])
    with ctrl:
        st.radio(
            "language", ["en", "zh"],
            format_func=lambda o: labels[o],
            key="lang",
            horizontal=True, label_visibility="collapsed",
        )
    st.session_state.language = st.session_state.lang
    if previous_lang and previous_lang != st.session_state.lang:
        st.session_state._applied_query_lang = st.session_state.lang
        st.query_params["lang"] = st.session_state.lang
    st.session_state._last_selected_lang = st.session_state.lang
