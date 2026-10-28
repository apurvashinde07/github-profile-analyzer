"""Page styling (CSS) for the GitHub Profile Analyzer.

The colours are semi-transparent, so the same styling works on both the light
and the dark Streamlit theme. Only fixed text is placed inside the HTML pieces
of the app, never data that comes from GitHub.
"""

PAGE_STYLE = """
<style>
.block-container { padding-top: 1.6rem; max-width: 1200px; }

/* ---------- header banner ---------- */
.hero {
    display: flex;
    align-items: center;
    gap: 22px;
    background: linear-gradient(120deg, rgba(47,129,247,0.30), rgba(163,113,247,0.24));
    border: 1px solid rgba(128,128,128,0.35);
    border-radius: 18px;
    padding: 24px 30px;
    margin-bottom: 22px;
    box-shadow: 0 6px 22px rgba(47,129,247,0.12);
}
.hero h1 { margin: 0; padding: 0; font-size: 2.3rem; line-height: 1.15; }
.hero p { margin: 6px 0 10px 0; opacity: 0.8; font-size: 1rem; }
.chip {
    display: inline-block;
    padding: 2px 11px;
    margin: 3px 6px 3px 0;
    border-radius: 999px;
    background: rgba(47,129,247,0.16);
    border: 1px solid rgba(47,129,247,0.45);
    font-size: 0.82rem;
}

/* ---------- cards and metric tiles ---------- */
.card {
    background: rgba(128,128,128,0.09);
    border: 1px solid rgba(128,128,128,0.32);
    border-radius: 14px;
    padding: 18px 20px 16px 20px;
    min-height: 150px;
    margin-bottom: 14px;
    box-shadow: inset 0 3px 0 #2F81F7;
    transition: transform 0.15s ease, box-shadow 0.15s ease, border-color 0.15s ease;
}
.card:hover {
    transform: translateY(-4px);
    border-color: rgba(47,129,247,0.7);
    box-shadow: inset 0 3px 0 #A371F7, 0 8px 20px rgba(47,129,247,0.18);
}
.card .icon { font-size: 1.9rem; line-height: 1; margin-bottom: 8px; }
.card h4 { margin: 0 0 6px 0; padding: 0; color: #2F81F7; font-size: 1.1rem; }
.card p { margin: 0; opacity: 0.8; font-size: 0.92rem; }

div[data-testid="stMetric"] {
    background: rgba(128,128,128,0.09);
    border: 1px solid rgba(128,128,128,0.32);
    border-left: 5px solid #2F81F7;
    border-radius: 14px;
    padding: 14px 18px;
    transition: transform 0.15s ease, border-color 0.15s ease;
}
div[data-testid="stMetric"]:hover { transform: translateY(-3px); border-color: rgba(47,129,247,0.7); }
div[data-testid="stMetricValue"] { color: #2F81F7; font-weight: 700; }

/* ---------- README summary ---------- */
.readme-note { opacity: 0.7; font-size: 0.85rem; margin-top: 6px; }

/* ---------- buttons ---------- */
.stButton > button, .stDownloadButton > button {
    border-radius: 12px;
    padding: 0.55rem 1.2rem;
    font-weight: 600;
    border: 1px solid rgba(47,129,247,0.6);
    transition: all 0.15s ease;
}
.stButton > button:hover, .stDownloadButton > button:hover {
    background: linear-gradient(120deg, #2F81F7, #A371F7);
    color: #FFFFFF;
    border-color: transparent;
    transform: translateY(-2px);
}

/* ---------- sidebar ---------- */
section[data-testid="stSidebar"] { border-right: 1px solid rgba(128,128,128,0.35); }
.side-brand { display: flex; align-items: center; gap: 12px; margin: 4px 0 14px 0; }
.side-brand b { font-size: 1.15rem; }
.side-brand small { opacity: 0.7; }
.nav-title { font-size: 1.5rem; font-weight: 800; margin: 10px 0 6px 0; }
section[data-testid="stSidebar"] [data-testid="stRadio"] label,
section[data-testid="stSidebar"] [role="radiogroup"] label {
    padding: 8px 12px;
    border-radius: 12px;
    transition: background 0.15s ease;
}
section[data-testid="stSidebar"] [data-testid="stRadio"] label:hover,
section[data-testid="stSidebar"] [role="radiogroup"] label:hover {
    background: rgba(47,129,247,0.14);
}
section[data-testid="stSidebar"] [data-testid="stRadio"] label p,
section[data-testid="stSidebar"] [role="radiogroup"] label p,
section[data-testid="stSidebar"] [role="radiogroup"] label div[data-testid="stMarkdownContainer"] p {
    font-size: 1.25rem !important;
    font-weight: 600;
}

/* ---------- misc ---------- */
div[data-testid="stImage"] img { border-radius: 16px; }
h2, h3 { letter-spacing: -0.01em; }
</style>
"""