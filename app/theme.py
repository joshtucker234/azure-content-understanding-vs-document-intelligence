"""Dark theme for the Streamlit UI: Inter, blue primary, cyan accent, navy surfaces. No logo or external assets."""
import streamlit as st

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
:root {
  --bg:#080c18; --bg2:#0f172a; --surface:rgba(15,23,42,.6); --text:#f1f5f9; --text2:#94a3b8; --text3:#64748b;
  --border:rgba(148,163,184,.12); --border-strong:rgba(148,163,184,.24);
  --p400:#60a5fa; --p500:#3b82f6; --p600:#2563eb; --a400:#22d3ee; --a500:#06b6d4; --h400:#a78bfa;
  --ok:#10b981; --warn:#f59e0b; --err:#ef4444; --r-md:.5rem; --r-lg:.75rem; --r-xl:1rem;
}
html, body, [class*="css"], .stApp, button, input, textarea, select { font-family:'Inter',-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif !important; -webkit-font-smoothing:antialiased; }
.stApp { background: linear-gradient(to bottom right, #080c18, #0f172a) fixed; color:var(--text); }
[data-testid="stHeader"] { background:transparent; }
#MainMenu, footer, .stDeployButton, [data-testid="stToolbar"] { visibility:hidden; }
.block-container { padding-top:2.2rem; max-width:1400px; }

/* sidebar */
[data-testid="stSidebar"] { background:var(--bg2); border-right:1px solid var(--border); }
[data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 { font-size:.75rem; letter-spacing:.08em; text-transform:uppercase; color:var(--text2); font-weight:600; }

/* hero */
.hero { padding:1.6rem 1.8rem; border:1px solid var(--border); border-radius:var(--r-xl);
  background: radial-gradient(1200px 300px at 0% 0%, rgba(59,130,246,.18), transparent 60%), radial-gradient(800px 260px at 100% 0%, rgba(6,182,212,.12), transparent 60%), var(--surface);
  box-shadow:0 0 20px rgba(59,130,246,.12); margin-bottom:1.2rem; }
.hero .eyebrow { font-size:.6875rem; font-weight:600; letter-spacing:.12em; text-transform:uppercase; color:var(--a400); margin-bottom:.35rem; }
.hero h1 { font-size:2.25rem; line-height:1.2; letter-spacing:-.02em; font-weight:700; margin:0 0 .4rem 0; padding:0; color:var(--text); }
.hero p { color:var(--text2); font-size:1rem; line-height:1.6; margin:0 0 .9rem 0; max-width:62rem; }
.chip { display:inline-block; padding:.2rem .65rem; margin:0 .4rem .3rem 0; border-radius:9999px; font-size:.75rem; font-weight:500;
  border:1px solid var(--border-strong); color:var(--text2); background:rgba(15,23,42,.7); }
.chip.on { color:#93c5fd; border-color:rgba(59,130,246,.45); background:rgba(59,130,246,.12); }
.chip.ai { color:#c4b5fd; border-color:rgba(139,92,246,.45); background:rgba(139,92,246,.12); }

/* tabs */
.stTabs [data-baseweb="tab-list"] { gap:.25rem; border-bottom:1px solid var(--border); }
.stTabs [data-baseweb="tab"] { height:2.8rem; padding:0 1rem; color:var(--text2); font-weight:500; border-radius:var(--r-md) var(--r-md) 0 0; }
.stTabs [aria-selected="true"] { color:var(--p400) !important; }
.stTabs [data-baseweb="tab-highlight"] { background-color:var(--p500) !important; }

/* buttons and inputs */
.stButton > button, .stDownloadButton > button { border-radius:var(--r-md); font-weight:600; border:1px solid var(--border-strong); background:var(--bg2); color:var(--text); transition:all .15s; }
.stButton > button:hover { border-color:var(--p500); color:#fff; box-shadow:0 0 0 3px rgba(59,130,246,.18); }
.stButton > button[kind="primary"] { background:var(--p500); border-color:var(--p500); color:#fff; }
.stButton > button[kind="primary"]:hover { background:var(--p600); border-color:var(--p600); }
.stTextInput input, .stNumberInput input, [data-baseweb="select"] > div { border-radius:var(--r-md) !important; }
.stTextInput input:focus { box-shadow:0 0 0 2px var(--p500) !important; }

/* cards: expanders, metrics, dataframes, alerts */
[data-testid="stExpander"] { border:1px solid var(--border); border-radius:var(--r-lg); background:var(--surface); }
[data-testid="stExpander"] summary { font-weight:500; }
[data-testid="stMetric"] { background:var(--surface); border:1px solid var(--border); border-radius:var(--r-lg); padding:.8rem 1rem; }
[data-testid="stMetricLabel"] { color:var(--text2); }
[data-testid="stDataFrame"] { border:1px solid var(--border); border-radius:var(--r-lg); overflow:hidden; }
.answer { border:1px solid rgba(59,130,246,.3); border-left:4px solid var(--p500); border-radius:var(--r-lg); background:var(--surface); padding:1rem 1.2rem; margin:.4rem 0 1rem 0; }
.answer.refused { border-color:rgba(245,158,11,.4); border-left-color:var(--warn); }
.section-label { font-size:.75rem; font-weight:600; letter-spacing:.08em; text-transform:uppercase; color:var(--text2); margin:1.1rem 0 .4rem 0; }
.pdfmeta { color:var(--text2); font-size:.875rem; margin:.2rem 0 .6rem 0; }
h1, h2, h3 { letter-spacing:-.01em; }
</style>
"""


def setup():
    """Page config and theme CSS. Call once, first."""
    st.set_page_config(page_title="Content Understanding Explorer", page_icon="\N{PAGE FACING UP}", layout="wide")
    st.markdown(CSS, unsafe_allow_html=True)


def hero(chips_html: str):
    st.markdown(
        '<div class="hero"><div class="eyebrow">Azure AI &middot; Content Understanding and Document Intelligence</div>'
        "<h1>Content Understanding Explorer</h1>"
        "<p>See exactly what went in, what each tool pulled out, where they agree, and what the pipeline did with a video. "
        "Everything here is read from saved results, so browsing costs nothing.</p>" + chips_html + "</div>",
        unsafe_allow_html=True,
    )


def chip(text: str, kind: str = "") -> str:
    return f'<span class="chip {kind}">{text}</span>'
