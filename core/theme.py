"""Pattern-branded theme for PILO — dark navy + purple/cyan accents."""

import base64
import os
import streamlit as st

# ===== Load real Pattern logos from assets/ =====

_ASSETS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")


def _load_logo_bytes(filename):
    """Load logo file bytes from assets/."""
    filepath = os.path.join(_ASSETS_DIR, filename)
    if os.path.exists(filepath):
        with open(filepath, "rb") as f:
            return f.read()
    return None


def _logo_data_uri(filename, mime="image/svg+xml"):
    """Load a logo file from assets/ and return a base64 data URI."""
    data = _load_logo_bytes(filename)
    if data:
        b64 = base64.b64encode(data).decode()
        return f"data:{mime};base64,{b64}"
    return ""


# Pre-load both versions
_LOGO_PNG_BYTES = _load_logo_bytes("pattern_logo_white_med (1).png")
_LOGO_SVG_URI = _logo_data_uri("pattern_logo_blue_white.svg", "image/svg+xml")
_LOGO_PNG_URI = _logo_data_uri("pattern_logo_white_med (1).png", "image/png")
_LOGO_URI = _LOGO_PNG_URI or _LOGO_SVG_URI  # Prefer PNG for reliability


def _logo_img(height="28px"):
    """Return an HTML <img> tag for the Pattern logo at the specified height."""
    return (
        f'<img src="{_LOGO_URI}" alt="Pattern" '
        f'style="height:{height};width:auto;flex-shrink:0;" />'
    )


# --- HTML snippets used across the app ---

# Landing page: large hero logo
PATTERN_HERO_LOGO_HTML = (
    f'<div style="display:flex;align-items:center;margin-bottom:8px;">'
    f'{_logo_img("48px")}'
    f'</div>'
)

# Sidebar header: full Pattern logo (fallback if st.logo not available)
PATTERN_FULL_LOGO_HTML = (
    f'<div style="display:flex;align-items:center;margin-bottom:2px;">'
    f'{_logo_img("30px")}'
    f'</div>'
)

# Above every page title: logo + PILO
PATTERN_PAGE_HEADER_HTML = (
    f'<div style="display:flex;align-items:center;gap:10px;margin-bottom:4px;padding-top:4px;">'
    f'{_logo_img("22px")}'
    f'<span style="color:#2D3748;font-size:1em;">|</span>'
    f'<span style="font-size:0.9em;font-weight:600;'
    f'background:linear-gradient(135deg,#7C3AED,#06B6D4);'
    f'-webkit-background-clip:text;-webkit-text-fill-color:transparent;'
    f'background-clip:text;">PILO</span>'
    f'</div>'
)

# Sidebar footer
_FOOTER_LOGO = _logo_img("14px")


# ===== CSS =====

PATTERN_CSS = """
<style>
/* ===== Pattern Brand Colors ===== */
:root {
    --bg-primary: #0B0F19;
    --bg-card: #141B2D;
    --bg-card-hover: #1A2332;
    --border-subtle: #1E293B;
    --border-accent: #7C3AED;
    --text-primary: #E2E8F0;
    --text-secondary: #94A3B8;
    --text-muted: #64748B;
    --accent-purple: #7C3AED;
    --accent-cyan: #06B6D4;
    --accent-gradient: linear-gradient(135deg, #7C3AED 0%, #06B6D4 100%);
    --success: #22C55E;
    --warning: #F59E0B;
    --error: #EF4444;
    --info: #3B82F6;
}

/* ===== Global Overrides ===== */
.stApp {
    background-color: var(--bg-primary) !important;
}

/* Sidebar styling */
section[data-testid="stSidebar"] {
    background-color: var(--bg-card) !important;
    border-right: 1px solid var(--border-subtle) !important;
}

section[data-testid="stSidebar"] .stMarkdown p {
    color: var(--text-secondary) !important;
}

/* ===== Headers ===== */
h1 {
    background: var(--accent-gradient) !important;
    -webkit-background-clip: text !important;
    -webkit-text-fill-color: transparent !important;
    background-clip: text !important;
    font-weight: 700 !important;
}

h2, h3 {
    color: var(--text-primary) !important;
}

/* ===== Cards / Expanders ===== */
div[data-testid="stExpander"] {
    background-color: var(--bg-card) !important;
    border: 1px solid var(--border-subtle) !important;
    border-radius: 12px !important;
    overflow: hidden;
}

div[data-testid="stExpander"] summary {
    color: var(--text-primary) !important;
}

/* ===== Metrics ===== */
div[data-testid="stMetric"] {
    background-color: var(--bg-card) !important;
    border: 1px solid var(--border-subtle) !important;
    border-radius: 12px !important;
    padding: 16px 20px !important;
}

div[data-testid="stMetric"] label {
    color: var(--text-secondary) !important;
}

div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
    color: var(--text-primary) !important;
    font-weight: 600 !important;
}

/* ===== Primary Button — gradient ===== */
button[kind="primary"], .stButton > button[kind="primary"] {
    background: var(--accent-gradient) !important;
    border: none !important;
    color: white !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    transition: opacity 0.2s ease !important;
}

button[kind="primary"]:hover {
    opacity: 0.9 !important;
}

/* Secondary buttons */
.stButton > button:not([kind="primary"]) {
    background-color: var(--bg-card) !important;
    border: 1px solid var(--border-subtle) !important;
    color: var(--text-primary) !important;
    border-radius: 8px !important;
}

.stButton > button:not([kind="primary"]):hover {
    border-color: var(--accent-purple) !important;
    background-color: var(--bg-card-hover) !important;
}

/* ===== Download buttons ===== */
.stDownloadButton > button {
    background-color: var(--bg-card) !important;
    border: 1px solid var(--accent-purple) !important;
    color: var(--accent-purple) !important;
    border-radius: 8px !important;
}

.stDownloadButton > button:hover {
    background: var(--accent-gradient) !important;
    color: white !important;
    border: none !important;
}

/* ===== DataFrames ===== */
div[data-testid="stDataFrame"] {
    border: 1px solid var(--border-subtle) !important;
    border-radius: 12px !important;
    overflow: hidden;
}

/* ===== Inputs ===== */
div[data-testid="stTextInput"] input,
div[data-testid="stTextArea"] textarea,
div[data-testid="stNumberInput"] input {
    background-color: var(--bg-card) !important;
    border: 1px solid var(--border-subtle) !important;
    border-radius: 8px !important;
    color: var(--text-primary) !important;
}

div[data-testid="stTextInput"] input:focus,
div[data-testid="stTextArea"] textarea:focus,
div[data-testid="stNumberInput"] input:focus {
    border-color: var(--accent-purple) !important;
    box-shadow: 0 0 0 2px rgba(124, 58, 237, 0.2) !important;
}

/* ===== Selectbox / Multiselect ===== */
div[data-testid="stSelectbox"] > div,
div[data-testid="stMultiSelect"] > div {
    background-color: var(--bg-card) !important;
    border-radius: 8px !important;
}

/* ===== Tabs ===== */
button[data-baseweb="tab"] {
    color: var(--text-secondary) !important;
}

button[data-baseweb="tab"][aria-selected="true"] {
    color: var(--accent-purple) !important;
    border-bottom-color: var(--accent-purple) !important;
}

/* ===== Progress bars ===== */
div[data-testid="stProgress"] > div > div {
    background: var(--accent-gradient) !important;
}

/* ===== Alerts ===== */
div[data-testid="stAlert"][data-baseweb="notification"] {
    border-radius: 8px !important;
}

.stSuccess {
    background-color: rgba(34, 197, 94, 0.1) !important;
    border-left: 4px solid var(--success) !important;
    color: var(--success) !important;
}

.stWarning {
    background-color: rgba(245, 158, 11, 0.1) !important;
    border-left: 4px solid var(--warning) !important;
}

.stError {
    background-color: rgba(239, 68, 68, 0.1) !important;
    border-left: 4px solid var(--error) !important;
}

/* ===== Dividers ===== */
hr {
    border-color: var(--border-subtle) !important;
}

/* ===== Slider ===== */
div[data-testid="stSlider"] > div > div > div {
    background: var(--accent-gradient) !important;
}

/* ===== File Uploader ===== */
div[data-testid="stFileUploader"] {
    background-color: var(--bg-card) !important;
    border: 1px dashed var(--border-subtle) !important;
    border-radius: 12px !important;
}

div[data-testid="stFileUploader"]:hover {
    border-color: var(--accent-purple) !important;
}

/* ===== Status pills ===== */
.status-pill {
    display: inline-block;
    padding: 2px 10px;
    border-radius: 12px;
    font-size: 0.8em;
    font-weight: 600;
}
.status-active { background-color: rgba(34, 197, 94, 0.2); color: #22C55E; }
.status-review { background-color: rgba(245, 158, 11, 0.2); color: #F59E0B; }
.status-failed { background-color: rgba(239, 68, 68, 0.2); color: #EF4444; }
.status-pending { background-color: rgba(100, 116, 139, 0.2); color: #94A3B8; }
.status-running { background-color: rgba(59, 130, 246, 0.2); color: #3B82F6; }

/* ===== Completeness gauge ===== */
.gauge-container { text-align: center; padding: 20px; }
.gauge-value {
    font-size: 3em;
    font-weight: 700;
    background: linear-gradient(135deg, #7C3AED 0%, #06B6D4 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}
.gauge-label { color: #94A3B8; font-size: 0.9em; margin-top: 4px; }
</style>
"""


# ===== Functions =====

def inject_pattern_css():
    """Inject Pattern brand CSS into the current Streamlit page."""
    st.markdown(PATTERN_CSS, unsafe_allow_html=True)


def _get_logo_image():
    """Get the logo as a file path for st.logo()."""
    png_path = os.path.join(_ASSETS_DIR, "pattern_logo_white_med (1).png")
    if os.path.exists(png_path):
        return png_path
    svg_path = os.path.join(_ASSETS_DIR, "pattern_logo_blue_white.svg")
    if os.path.exists(svg_path):
        return svg_path
    return None


def pattern_page_header(title, caption=None):
    """Render the Pattern logo above a page title in the main content area."""
    # Use st.logo() to place logo at top of sidebar on every page
    logo_path = _get_logo_image()
    if logo_path:
        st.logo(logo_path)

    st.markdown(PATTERN_PAGE_HEADER_HTML, unsafe_allow_html=True)
    st.title(title)
    if caption:
        st.caption(caption)


def pattern_sidebar():
    """Render the Pattern-branded sidebar with workflow progress."""
    # Use st.logo() to put the logo at the TOP of sidebar (above nav)
    logo_path = _get_logo_image()
    if logo_path:
        st.logo(logo_path)

    with st.sidebar:
        st.markdown(
            '<div style="margin-top:2px;margin-bottom:4px;">'
            '<span style="font-size:1.3em;font-weight:700;'
            'background:linear-gradient(135deg,#7C3AED,#06B6D4);'
            '-webkit-background-clip:text;-webkit-text-fill-color:transparent;'
            'background-clip:text;">PILO</span>'
            '<span style="color:#64748B;font-size:0.8em;margin-left:8px;">'
            'Listing Optimisation</span>'
            '</div>',
            unsafe_allow_html=True,
        )
        st.divider()

        steps = [
            ("Control Centre", bool(st.session_state.get("brand_name"))),
            ("Data Ingestion", st.session_state.get("feed_df") is not None),
            ("Enrichment", st.session_state.get("enriched_df") is not None),
            ("Content Generation", bool(st.session_state.get("generated_results"))),
            ("QA Review", bool(st.session_state.get("qa_decisions"))),
            ("Export", False),
            ("Cost Dashboard", bool(st.session_state.get("generated_results"))),
        ]

        st.markdown("**Workflow**")
        for step_name, completed in steps:
            if completed:
                st.markdown(
                    f'<div style="padding:4px 0;color:#22C55E;">&#10003; {step_name}</div>',
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    f'<div style="padding:4px 0;color:#64748B;">&#9744; {step_name}</div>',
                    unsafe_allow_html=True,
                )

        st.divider()
        # Footer
        st.markdown(
            f'<div style="display:flex;align-items:center;gap:6px;color:#64748B;font-size:0.75em;">'
            f'Powered by {_FOOTER_LOGO}'
            f'</div>',
            unsafe_allow_html=True,
        )
