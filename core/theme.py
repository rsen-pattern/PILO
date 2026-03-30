"""Pattern-branded theme for PILO — dark navy + purple/cyan accents."""

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

/* Success alerts */
.stSuccess {
    background-color: rgba(34, 197, 94, 0.1) !important;
    border-left: 4px solid var(--success) !important;
    color: var(--success) !important;
}

/* Warning alerts */
.stWarning {
    background-color: rgba(245, 158, 11, 0.1) !important;
    border-left: 4px solid var(--warning) !important;
}

/* Error alerts */
.stError {
    background-color: rgba(239, 68, 68, 0.1) !important;
    border-left: 4px solid var(--error) !important;
}

/* ===== Dividers ===== */
hr {
    border-color: var(--border-subtle) !important;
}

/* ===== Status badge helpers (via markdown) ===== */
/* Use with st.markdown to create Pattern-style status pills */

/* ===== Slider ===== */
div[data-testid="stSlider"] > div > div > div {
    background: var(--accent-gradient) !important;
}

/* ===== Checkbox ===== */
div[data-testid="stCheckbox"] label span[data-testid="stCheckbox"] {
    border-color: var(--accent-purple) !important;
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

/* ===== Pattern Logo Area in Sidebar ===== */
.pattern-logo {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 8px;
}

.pattern-logo svg {
    width: 24px;
    height: 24px;
}

/* ===== Status pill CSS helper ===== */
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
.gauge-container {
    text-align: center;
    padding: 20px;
}
.gauge-value {
    font-size: 3em;
    font-weight: 700;
    background: linear-gradient(135deg, #7C3AED 0%, #06B6D4 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}
.gauge-label {
    color: #94A3B8;
    font-size: 0.9em;
    margin-top: 4px;
}
</style>
"""


def inject_pattern_css():
    """Inject Pattern brand CSS into the current Streamlit page."""
    import streamlit as st
    st.markdown(PATTERN_CSS, unsafe_allow_html=True)


def pattern_sidebar():
    """Render the Pattern-branded sidebar with workflow progress."""
    import streamlit as st

    with st.sidebar:
        # Pattern branding
        st.markdown(
            '<div style="display:flex;align-items:center;gap:10px;margin-bottom:4px;">'
            '<span style="font-size:1.4em;font-weight:700;background:linear-gradient(135deg,#7C3AED,#06B6D4);'
            '-webkit-background-clip:text;-webkit-text-fill-color:transparent;">PILO</span>'
            '</div>',
            unsafe_allow_html=True,
        )
        st.caption("Pattern Intelligence Listing Optimisation")
        st.divider()

        steps = [
            ("Settings", bool(st.session_state.get("settings", {}).get("brand_name"))),
            ("Data Ingestion", st.session_state.get("feed_df") is not None),
            ("Enrichment", st.session_state.get("enriched_df") is not None),
            ("Content Generation", bool(st.session_state.get("generated_results"))),
            ("QA Review", bool(st.session_state.get("qa_decisions"))),
            ("Export", False),
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
        st.markdown(
            '<div style="color:#64748B;font-size:0.75em;">Powered by '
            '<span style="color:#7C3AED;">Pattern</span></div>',
            unsafe_allow_html=True,
        )
