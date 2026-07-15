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
/* Solid white base filling the whole app (header + main + gaps). */
.stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"],
[data-testid="stMain"], .main, section.main {{
  background: {SURFACE} !important;
  color: {FG};
}}
.block-container {{ padding-top: 2.2rem; max-width: 100%;
  padding-left: 3.5rem; padding-right: 3.5rem; }}

/* Headings */
h1, h2 {{ font-family: 'Fraunces', Georgia, serif; letter-spacing: -0.01em; color: {FG}; }}
h1 {{ font-weight: 700; }}
h3, h4 {{ font-family: 'Inter', sans-serif; font-weight: 600; color: {FG}; }}

/* Bordered containers -> soft cards */
div[data-testid="stVerticalBlockBorderWrapper"] {{
  background: {SURFACE};
  border: 1px solid {BORDER} !important;
  border-radius: 18px !important;
  box-shadow: 0 1px 2px rgba(15,23,42,0.04), 0 8px 24px rgba(37,99,235,0.05);
  padding: 4px 6px;
}}

/* Buttons */
.stButton > button {{
  border-radius: 12px;
  border: 1px solid {BORDER};
  font-weight: 600;
  transition: transform .12s ease, box-shadow .15s ease, background .15s ease;
}}
.stButton > button:hover {{ transform: translateY(-1px); }}
.stButton > button[kind="primary"] {{
  background: {PRIMARY};
  border-color: {PRIMARY};
  box-shadow: 0 6px 16px rgba(37,99,235,0.25);
}}
.stButton > button[kind="primary"]:hover {{ background: {PRIMARY_DARK}; }}

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
</style>
"""


def setup_page(title: str, icon: str):
    """Call once per page (after set_page_config) to apply theme + lang state."""
    st.session_state.setdefault("lang", "en")
    st.markdown(_CSS, unsafe_allow_html=True)


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
