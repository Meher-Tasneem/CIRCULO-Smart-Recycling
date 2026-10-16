import streamlit as st
import pandas as pd
from datetime import datetime
from PIL import Image
import sqlite3
from pathlib import Path
import os
import html
from scanner import scan_waste_bytes, ScannerError

# ============================================================
# CIRCULO | SMART RECYCLING ASSISTANT
# Complete replacement app.py — Streamlit
# ============================================================

st.set_page_config(
    page_title="CIRCULO | Smart Recycling",
    page_icon="♻️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -------------------------- LOCAL DATABASE --------------------------
# SQLite keeps material records after Streamlit restarts.
DB_PATH = Path(__file__).resolve().parent / "circulo.db"

def init_database():
    with sqlite3.connect(DB_PATH) as connection:
        connection.execute("""CREATE TABLE IF NOT EXISTS materials (
            id INTEGER PRIMARY KEY, date TEXT NOT NULL, material TEXT NOT NULL,
            weight REAL NOT NULL, status TEXT NOT NULL, notes TEXT DEFAULT ''
        )""")
        # Separate table for the demo reward feature; existing materials are untouched.
        connection.execute("""CREATE TABLE IF NOT EXISTS reward_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT NOT NULL,
            material TEXT NOT NULL, weight REAL NOT NULL, rate REAL NOT NULL,
            amount REAL NOT NULL, status TEXT NOT NULL DEFAULT 'Pending verification',
            notes TEXT DEFAULT ''
        )""")

def load_records():
    with sqlite3.connect(DB_PATH) as connection:
        rows = connection.execute(
            "SELECT id, date, material, weight, status, notes FROM materials ORDER BY id"
        ).fetchall()
    return [{"ID": r[0], "Date": r[1], "Material": r[2], "Weight (kg)": r[3], "Status": r[4], "Notes": r[5] or ""} for r in rows]

def insert_record(record):
    with sqlite3.connect(DB_PATH) as connection:
        connection.execute(
            "INSERT INTO materials (id, date, material, weight, status, notes) VALUES (?, ?, ?, ?, ?, ?)",
            (record["ID"], record["Date"], record["Material"], record["Weight (kg)"], record["Status"], record["Notes"])
        )

def update_record_status(record_id, status):
    with sqlite3.connect(DB_PATH) as connection:
        connection.execute("UPDATE materials SET status = ? WHERE id = ?", (status, record_id))

def delete_record(record_id):
    with sqlite3.connect(DB_PATH) as connection:
        connection.execute("DELETE FROM materials WHERE id = ?", (record_id,))

def clear_database():
    with sqlite3.connect(DB_PATH) as connection:
        connection.execute("DELETE FROM materials")

init_database()
if "records" not in st.session_state:
    st.session_state.records = load_records()
if "circulo_navigation" not in st.session_state:
    st.session_state.circulo_navigation = "Overview"

# -------------------------- DESIGN SYSTEM --------------------------
st.markdown(
    """
    <style>
    :root {
        --bg: #07130F;
        --panel: #0D2018;
        --panel-2: #11291E;
        --border: #244936;
        --text: #F0F7F1;
        --muted: #A9C0B0;
        --green: #36D887;
        --lime: #C4F36A;
    }
    html, body, [class*="css"] {
        font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }
    .stApp {
        background: radial-gradient(ellipse at 85% 0%, rgba(28,105,65,.18), transparent 34%), linear-gradient(180deg,#07130F 0%,#091710 100%);
        color: var(--text);
    }
    [data-testid="stHeader"] { background: rgba(7,19,15,.88); }
    .block-container { max-width: 1500px; padding-top: 1.6rem; padding-bottom: 3rem; }
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg,#0D2118 0%,#081710 100%);
        border-right: 1px solid #1D3B2B;
        min-width: 275px;
        width: 275px;
    }
    [data-testid="stSidebar"] > div { background: transparent; }
    [data-testid="stSidebar"] * { color: #EDF8F0; }
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p { color: #A9C0B0; }
    [data-testid="stSidebar"] [role="radiogroup"] { gap: 7px; }
    [data-testid="stSidebar"] [role="radiogroup"] > label {
        background: #10291D; border: 1px solid #244936; border-radius: 11px;
        padding: 10px 12px; transition: background .15s ease,border-color .15s ease;
    }
    [data-testid="stSidebar"] [role="radiogroup"] > label:hover { background: #183C2A; border-color: #3A8B5C; }
    [data-testid="stSidebar"] [role="radiogroup"] > label:has(input:checked) { background: #174A30; border: 1px solid #36D887; }
    h1,h2,h3,h4 { color: #F2FBF4 !important; letter-spacing: -.025em; }
    p,li,label,[data-testid="stCaptionContainer"] { color: #B8CCBE; }
    [data-testid="stMarkdownContainer"] p,[data-testid="stMarkdownContainer"] li { color: #C5D8CB; }
    .eyebrow { color:#8EE8B6; text-transform:uppercase; letter-spacing:.15em; font-size:.72rem; font-weight:800; margin-bottom:.55rem; }
    .hero {
        background: radial-gradient(circle at 90% 10%,rgba(196,243,106,.15),transparent 28%),linear-gradient(120deg,#103B28 0%,#12583A 52%,#0D3525 100%);
        border:1px solid #2B7550; border-radius:24px; padding:30px 32px; margin:0 0 25px 0;
        box-shadow:0 18px 50px rgba(0,0,0,.18);
    }
    .hero h1 { color:#FFFFFF !important; font-size:clamp(2rem,4vw,3rem); line-height:1.08; margin:0 0 12px 0; }
    .hero p { color:#D1E9D8 !important; font-size:1.02rem; max-width:720px; margin:0; line-height:1.6; }
    .hero-pill { display:inline-block; background:rgba(5,24,14,.32); color:#C4F36A; border:1px solid rgba(196,243,106,.32); border-radius:100px; padding:6px 11px; margin-bottom:15px; font-size:.75rem; font-weight:750; letter-spacing:.06em; }
    .section-kicker { color:#8EE8B6; text-transform:uppercase; font-size:.72rem; letter-spacing:.13em; font-weight:800; margin-bottom:5px; }
    [data-testid="stMetric"] { background:linear-gradient(145deg,#11291E,#0D2118)!important; border:1px solid #244936!important; border-radius:17px!important; padding:18px 19px!important; min-height:124px; box-shadow:0 8px 24px rgba(0,0,0,.12); }
    [data-testid="stMetricLabel"],[data-testid="stMetricLabel"] *,[data-testid="stMetricValue"],[data-testid="stMetricValue"] *,[data-testid="stMetricDelta"],[data-testid="stMetricDelta"] * { color:#F0F7F1!important; opacity:1!important; visibility:visible!important; }
    [data-testid="stMetricLabel"] { font-size:.82rem!important; }
    [data-testid="stMetricValue"] { font-size:clamp(1.45rem,2vw,2rem)!important; font-weight:800!important; letter-spacing:-.04em; }
    .surface { background:linear-gradient(145deg,#10271C,#0C1E16); border:1px solid #244936; border-radius:17px; padding:20px; height:100%; }
    .surface h3,.surface h4 { color:#F1FAF3!important; margin-top:0; }
    .surface p { color:#B8CCBE!important; line-height:1.55; }
    .surface-icon { display:inline-flex; align-items:center; justify-content:center; width:42px; height:42px; border-radius:12px; background:#1B4931; color:#A7F3C5; font-size:1.3rem; margin-bottom:12px; }
    .status-chip { display:inline-block; background:#173D2A; color:#9AF0B9; border:1px solid #2E6D48; border-radius:999px; padding:4px 9px; font-size:.75rem; font-weight:750; }
    .mini-note { color:#A9C0B0; font-size:.83rem; line-height:1.55; }
    .stButton > button,.stDownloadButton > button,[data-testid="stFormSubmitButton"] > button {
        background:linear-gradient(120deg,#1A9A5B,#137B4B)!important; color:#FFFFFF!important;
        border:1px solid #39B978!important; border-radius:10px!important; min-height:43px; font-weight:750!important;
    }
    .stButton > button:hover,.stDownloadButton > button:hover,[data-testid="stFormSubmitButton"] > button:hover { filter:brightness(1.12); border-color:#7BE5A6!important; color:#FFFFFF!important; }
    input,textarea,[data-baseweb="select"] > div,[data-testid="stNumberInput"] input { color:#F0F7F1!important; }
    [data-baseweb="select"] > div,[data-testid="stTextInput"] input,[data-testid="stNumberInput"] input,[data-testid="stTextArea"] textarea { background:#10271C!important; border-color:#315640!important; border-radius:9px!important; }
    [data-baseweb="popover"] { background:#10271C!important; }
    [data-testid="stFileUploader"] { background:#10271C; border:1px dashed #3A7953; border-radius:14px; padding:12px; }
    [data-testid="stFileUploader"] * { color:#D9EADF; }
    [data-testid="stForm"] { background:#0D2118; border:1px solid #244936; border-radius:17px; padding:22px; }
    [data-testid="stDataFrame"] { border:1px solid #244936; border-radius:12px; overflow:hidden; }
    [data-testid="stAlert"] { border-radius:12px; }
    hr { border-color:#244936!important; margin-top:1.4rem; margin-bottom:1.4rem; }
    [data-testid="stProgress"] > div > div { background:#36D887!important; }
    .footer { color:#789684; text-align:center; font-size:.78rem; padding-top:4px; }

    /* CIRCULO motion system: subtle, performance-friendly animations */
    @keyframes riseIn { from { opacity:0; transform:translateY(14px); } to { opacity:1; transform:translateY(0); } }
    @keyframes softPulse { 0%,100% { box-shadow:0 0 0 0 rgba(54,216,135,.05); } 50% { box-shadow:0 0 26px 2px rgba(54,216,135,.12); } }
    @keyframes floatLeaf { 0%,100% { transform:translateY(0) rotate(-3deg); } 50% { transform:translateY(-8px) rotate(3deg); } }
    @keyframes shimmer { 0% { background-position:-200% 0; } 100% { background-position:200% 0; } }
    .hero, .surface, [data-testid="stMetric"], [data-testid="stForm"] { animation:riseIn .55s ease both; }
    .hero { animation:riseIn .65s ease both, softPulse 6s ease-in-out infinite; }
    .hero-pill { animation:riseIn .7s ease both; }
    .surface-icon { display:inline-block; animation:floatLeaf 5s ease-in-out infinite; }
    .stButton > button, .stDownloadButton > button { transition:transform .18s ease, filter .18s ease, box-shadow .18s ease; }
    .stButton > button:hover, .stDownloadButton > button:hover { transform:translateY(-2px); box-shadow:0 8px 24px rgba(30,180,100,.16); }
    [data-testid="stProgress"] > div > div { background:linear-gradient(90deg,#36D887,#C4F36A,#36D887)!important; background-size:200% 100%!important; animation:shimmer 4s linear infinite; }
    @media (prefers-reduced-motion: reduce) { *, *::before, *::after { animation-duration:.01ms!important; animation-iteration-count:1!important; scroll-behavior:auto!important; transition-duration:.01ms!important; } }

    /* Extra polish: layered motion, animated borders and responsive hover states */
    html { scroll-behavior:smooth; }
    @keyframes borderFlow { 0% { background-position:0% 50%; } 100% { background-position:200% 50%; } }
    @keyframes orbDrift { 0%,100% { transform:translate3d(0,0,0) scale(1); } 50% { transform:translate3d(18px,-12px,0) scale(1.04); } }
    @keyframes glowBreath { 0%,100% { opacity:.42; } 50% { opacity:.8; } }
    @keyframes cardEnter { from { opacity:0; transform:translateY(18px) scale(.985); } to { opacity:1; transform:translateY(0) scale(1); } }
    .stApp { background-image:radial-gradient(ellipse at 12% 18%,rgba(54,216,135,.075),transparent 27%),radial-gradient(ellipse at 88% 42%,rgba(196,243,106,.055),transparent 25%),linear-gradient(180deg,#07130F 0%,#091710 100%); background-size:100% 100%; }
    .hero { position:relative; overflow:hidden; isolation:isolate; }
    .hero::before { content:""; position:absolute; z-index:-1; width:260px; height:260px; right:-55px; top:-115px; border-radius:50%; background:radial-gradient(circle,rgba(196,243,106,.19),rgba(54,216,135,.035) 62%,transparent 70%); animation:orbDrift 9s ease-in-out infinite; pointer-events:none; }
    .hero::after { content:""; position:absolute; left:0; right:0; bottom:0; height:2px; background:linear-gradient(90deg,transparent,#C4F36A,#36D887,transparent); background-size:200% 100%; animation:borderFlow 7s linear infinite; opacity:.8; }
    .surface { transition:transform .24s ease,border-color .24s ease,box-shadow .24s ease; position:relative; overflow:hidden; }
    .surface:hover { transform:translateY(-5px); border-color:#3B8C5D; box-shadow:0 16px 34px rgba(0,0,0,.22),0 0 0 1px rgba(54,216,135,.06); }
    [data-testid="stMetric"] { transition:transform .22s ease,border-color .22s ease,box-shadow .22s ease; position:relative; overflow:hidden; }
    [data-testid="stMetric"]:hover { transform:translateY(-4px); border-color:#3B8C5D!important; box-shadow:0 14px 30px rgba(0,0,0,.2),0 0 22px rgba(54,216,135,.08)!important; }
    [data-testid="stMetric"]::after { content:""; position:absolute; top:0; left:-120%; width:65%; height:1px; background:linear-gradient(90deg,transparent,#C4F36A,transparent); animation:borderFlow 8s linear infinite; }
    .stButton > button, .stDownloadButton > button, [data-testid="stFormSubmitButton"] > button { position:relative; overflow:hidden; transition:transform .2s ease,filter .2s ease,box-shadow .2s ease; }
    .stButton > button::after, .stDownloadButton > button::after { content:""; position:absolute; top:-20%; bottom:-20%; left:-65%; width:35%; transform:skewX(-20deg); background:linear-gradient(90deg,transparent,rgba(255,255,255,.22),transparent); transition:left .55s ease; pointer-events:none; }
    .stButton > button:hover::after, .stDownloadButton > button:hover::after { left:130%; }
    [data-testid="stFileUploader"] { transition:border-color .2s ease,box-shadow .2s ease,transform .2s ease; }
    [data-testid="stFileUploader"]:hover { border-color:#67D997; box-shadow:0 0 0 3px rgba(54,216,135,.06); }
    [data-testid="stSidebar"] [role="radiogroup"] > label { transition:transform .18s ease,background .18s ease,border-color .18s ease; }
    [data-testid="stSidebar"] [role="radiogroup"] > label:hover { transform:translateX(3px); }
    [data-testid="stAlert"] { animation:cardEnter .35s ease both; }
    .section-kicker { animation:glowBreath 4.5s ease-in-out infinite; }
    @media (prefers-reduced-motion: reduce) { .hero::before,.hero::after,.section-kicker,[data-testid="stMetric"]::after { animation:none!important; } .surface:hover,[data-testid="stMetric"]:hover { transform:none!important; } }

    @media(max-width:800px) {
        .block-container { padding:1rem 1rem 2rem 1rem; }
        .hero { padding:23px 20px; border-radius:18px; }
        [data-testid="stMetric"] { padding:14px!important; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# -------------------------- HELPERS --------------------------
MATERIAL_TYPES = ["Plastic", "Paper", "Cardboard", "Glass", "Metal", "Organic", "Electronic waste", "Textile", "Other"]
STATUSES = ["Collected", "Sorted", "Ready for recycling", "Recycled", "Reused"]
COLUMNS = ["ID", "Date", "Material", "Weight (kg)", "Status", "Notes"]


def make_dataframe():
    if not st.session_state.records:
        return pd.DataFrame(columns=COLUMNS)
    data = pd.DataFrame(st.session_state.records)
    for column in COLUMNS:
        if column not in data.columns:
            data[column] = ""
    return data[COLUMNS]


def page_heading(title, subtitle):
    st.markdown('<div class="eyebrow">CIRCULO WORKSPACE</div>', unsafe_allow_html=True)
    st.title(title)
    st.caption(subtitle)
    st.divider()


def calculate_metrics(data):
    if data.empty:
        return {"records": 0, "total": 0.0, "recycled": 0.0, "reused": 0.0, "pending": 0.0, "progress": 0.0}
    weights = pd.to_numeric(data["Weight (kg)"], errors="coerce").fillna(0)
    total = float(weights.sum())
    recycled = float(weights[data["Status"] == "Recycled"].sum())
    reused = float(weights[data["Status"] == "Reused"].sum())
    processed = recycled + reused
    return {
        "records": len(data),
        "total": total,
        "recycled": recycled,
        "reused": reused,
        "pending": max(total - processed, 0.0),
        "progress": processed / total if total > 0 else 0.0,
    }


def set_navigation(page):
    # Called before the radio widget is instantiated on the next rerun.
    st.session_state.pending_circulo_navigation = page


def navigate(page):
    # Use this only from buttons; defer the widget-key change to the
    # top of the next script run, before the radio widget is created.
    st.session_state.pending_circulo_navigation = page
    st.rerun()


def render_empty_state(icon, title, message):
    st.markdown(
        f'<div class="surface"><div class="surface-icon">{icon}</div><h3>{title}</h3><p>{message}</p></div>',
        unsafe_allow_html=True,
    )


def format_weight(value):
    return f"{float(value):,.2f} kg"


# -------------------------- SIDEBAR --------------------------
# Apply navigation requests before creating the radio widget.
if "pending_circulo_navigation" in st.session_state:
    st.session_state.circulo_navigation = st.session_state.pop("pending_circulo_navigation")

with st.sidebar:
    st.markdown(
        """
        <div style="padding:8px 0 14px 0;">
          <div style="display:flex;align-items:center;gap:11px;">
            <div style="font-size:2rem;">♻️</div>
            <div>
              <div style="font-size:1.45rem;font-weight:900;letter-spacing:-.04em;color:#F2FBF4;">CIRCULO</div>
              <div style="font-size:.66rem;letter-spacing:.16em;font-weight:800;color:#8EE8B6;">SMART RECYCLING</div>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.caption("Track waste. Recover value. Close the loop.")
    st.divider()
    selected_page = st.radio(
        "WORKSPACE",
        ["Overview", "Waste Scanner", "Material Passport", "Earn & Return", "Impact Lab", "Records & Export"],
        format_func=lambda item: {
            "Overview": "⌂   Overview",
            "Waste Scanner": "◎   Waste Scanner",
            "Material Passport": "▤   Material Passport",
            "Earn & Return": "₹   Earn & Return",
            "Impact Lab": "↗   Impact Lab",
            "Records & Export": "▣   Records & Export",
        }[item],
        key="circulo_navigation",
    )
    st.divider()
    st.markdown(
        '<div class="surface" style="padding:15px;"><div class="eyebrow">OUR MISSION</div><div style="font-weight:750;color:#F0F7F1;margin-bottom:6px;">Waste is a resource.</div><div class="mini-note">Make materials easier to record, sort, track and recover.</div></div>',
        unsafe_allow_html=True,
    )
    st.write("")
    st.caption("CODE CLASH 2.0 · PROTOTYPE")

# -------------------------- SHARED DATA --------------------------
df = make_dataframe()
metrics = calculate_metrics(df)
record_count = metrics["records"]
total_weight = metrics["total"]
recycled_weight = metrics["recycled"]
reused_weight = metrics["reused"]
pending_weight = metrics["pending"]
progress = metrics["progress"]

# ============================================================
# OVERVIEW
# ============================================================
if selected_page == "Overview":
    st.markdown(
        """
        <div class="hero">
          <div class="hero-pill">♻ &nbsp; CIRCULAR ECONOMY · INTELLIGENCE WORKSPACE</div>
          <h1>Give waste a<br>second life.</h1>
          <p>CIRCULO helps communities track material recovery, organize recycling workflows,
          and build a clearer picture of what happens to waste after collection.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown('<div class="section-kicker">LIVE WORKSPACE SUMMARY</div>', unsafe_allow_html=True)
    st.subheader("Recycling at a glance")
    st.caption("All figures below are calculated from the records entered in this session.")
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Materials logged", f"{record_count:,}")
    k2.metric("Total tracked", format_weight(total_weight))
    k3.metric("Marked recycled", format_weight(recycled_weight))
    k4.metric("Awaiting recovery", format_weight(pending_weight))

    st.write("")
    left, right = st.columns([1.35, 1], gap="large")
    with left:
        st.markdown('<div class="section-kicker">THE LATEST</div>', unsafe_allow_html=True)
        st.subheader("Recent material activity")
        if df.empty:
            render_empty_state("↗", "Your workspace starts here", "Register your first material in Material Passport. Your real entries will appear here automatically.")
            st.write("")
            if st.button("＋ Register first material", use_container_width=True):
                navigate("Material Passport")
        else:
            recent = df.tail(6).iloc[::-1].copy()
            recent["Weight (kg)"] = pd.to_numeric(recent["Weight (kg)"], errors="coerce").fillna(0).map(lambda x: f"{x:.2f}")
            st.dataframe(recent, use_container_width=True, hide_index=True, height=280)
    with right:
        st.markdown('<div class="section-kicker">MATERIAL MIX</div>', unsafe_allow_html=True)
        st.subheader("Tracked by material")
        if df.empty:
            render_empty_state("◉", "No material mix yet", "Once records are added, this chart will compare the weight recorded for each material type.")
        else:
            summary = df.groupby("Material")["Weight (kg)"].sum().sort_values(ascending=True)
            st.bar_chart(summary, color="#36D887", horizontal=True, height=280)

    st.write("")
    st.markdown('<div class="section-kicker">QUICK ACCESS</div>', unsafe_allow_html=True)
    st.subheader("Your workspace")
    c1, c2, c3 = st.columns(3, gap="medium")
    with c1:
        st.markdown('<div class="surface"><div class="surface-icon">◎</div><h3>Waste Scanner</h3><p>Upload a photo and prepare it for a genuine model prediction.</p><span class="status-chip">MODEL INTEGRATION</span></div>', unsafe_allow_html=True)
        st.write("")
        if st.button("Open scanner  →", key="go_scanner", use_container_width=True):
            navigate("Waste Scanner")
    with c2:
        st.markdown('<div class="surface"><div class="surface-icon">▤</div><h3>Material Passport</h3><p>Register materials and track each lifecycle status.</p><span class="status-chip">RECORD MANAGEMENT</span></div>', unsafe_allow_html=True)
        st.write("")
        if st.button("Manage materials  →", key="go_passport", use_container_width=True):
            navigate("Material Passport")
    with c3:
        st.markdown('<div class="surface"><div class="surface-icon">↗</div><h3>Impact Lab</h3><p>Explore recorded weights and measured recovery progress.</p><span class="status-chip">DATA-BASED METRICS</span></div>', unsafe_allow_html=True)
        st.write("")
        if st.button("Explore impact  →", key="go_impact", use_container_width=True):
            navigate("Impact Lab")

# ============================================================
# WASTE SCANNER
# ============================================================
elif selected_page == "Waste Scanner":
    page_heading("Waste Scanner", "AI-assisted material recognition with human confirmation and practical disposal guidance.")
    st.markdown(
        '<div class="hero scanner-hero"><div class="hero-pill">✦ &nbsp; GROQ VISION · AI-ASSISTED SORTING</div><h1 style="font-size:2.25rem;">See it. Sort it.<br>Give it a second life.</h1><p>Upload a clear image of one item. CIRCULO will analyse it, explain the result and suggest a responsible next step. Always confirm the result before saving.</p><div class="hero-pill">● &nbsp; Human-in-the-loop classification</div></div>',
        unsafe_allow_html=True,
    )
    upload_col, preview_col = st.columns([0.9, 1.1], gap="large")
    with upload_col:
        st.subheader("01 · Add a waste image")
        image_mode = st.radio(
            "Choose image source",
            ["📁 Upload a photo", "📷 Capture with camera"],
            horizontal=True,
            key="waste_image_mode",
            label_visibility="collapsed",
        )
        uploaded_file = None
        if image_mode == "📁 Upload a photo":
            uploaded_file = st.file_uploader(
                "Choose an image", type=["jpg", "jpeg", "png", "webp"],
                key="waste_image_upload", help="Use a well-lit photo with one main object."
            )
        else:
            uploaded_file = st.camera_input(
                "Take a live photo of the waste item",
                key="waste_camera_capture",
                help="Allow camera access when your browser asks. Point the camera at one waste item and capture it."
            )
            st.caption("Camera access requires browser permission. On phones, the rear camera is usually best for waste items.")
        st.caption("Supported: JPG, JPEG, PNG, WEBP · Avoid faces or private information.")
        api_ready = bool(os.environ.get("GROQ_API_KEY"))
        if api_ready:
            st.success("AI connection configured")
        else:
            st.warning("AI key not configured yet. Set GROQ_API_KEY in PowerShell before running the app.")
        run_scan = st.button("✦ Analyse with AI", type="primary", use_container_width=True, disabled=(uploaded_file is None or not api_ready), key="run_groq_scan")
    with preview_col:
        st.subheader("02 · Image preview")
        if uploaded_file is None:
            st.markdown('<div class="surface" style="min-height:250px;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;"><div style="font-size:3.2rem;">♻️</div><h3>Your scan preview appears here</h3><p>Upload a photo or capture one using your camera.</p><div class="hero-pill">CAMERA / IMAGE → AI ANALYSIS → ACTION</div></div>', unsafe_allow_html=True)
        else:
            try:
                preview = Image.open(uploaded_file).convert("RGB")
                st.image(preview, caption="Image ready for analysis", use_container_width=True)
                a, b = st.columns(2)
                a.metric("Width", f"{preview.width}px")
                b.metric("Height", f"{preview.height}px")
            except Exception:
                st.error("This image could not be opened. Please try another image.")

    if run_scan and uploaded_file is not None:
        with st.spinner("CIRCULO is analysing the image…"):
            try:
                image_name = getattr(uploaded_file, "name", "camera_capture.jpg") or "camera_capture.jpg"
                image_type = getattr(uploaded_file, "type", "image/jpeg") or "image/jpeg"
                result = scan_waste_bytes(uploaded_file.getvalue(), image_name, image_type)
                st.session_state.circulo_last_scan = result
                st.session_state.circulo_last_scan_filename = image_name
            except ScannerError as error:
                st.error(str(error))
            except Exception as error:
                st.error("The scan could not be completed. Check your connection and model configuration, then try again.")
                st.caption(f"Technical detail: {error}")

    result = st.session_state.get("circulo_last_scan")
    if result:
        st.divider()
        st.markdown('<div class="section-kicker">03 · AI SCAN RESULT</div>', unsafe_allow_html=True)
        r1, r2 = st.columns([1, 1.25], gap="large")
        with r1:
            st.markdown('<div class="surface"><div class="eyebrow">IDENTIFIED OBJECT</div><h2 style="margin:.3rem 0 1rem 0;">🔎 ' + html.escape(str(result.get("item", "Unknown item"))) + '</h2><div class="hero-pill">CATEGORY · ' + html.escape(str(result.get("category", "other")).upper()) + '</div><p style="margin-top:14px;">' + html.escape(str(result.get("reason", "The model did not provide an explanation."))) + '</p></div>', unsafe_allow_html=True)
        with r2:
            st.markdown('<div class="surface"><div class="eyebrow">YOUR NEXT STEP</div><h3>♻️ Disposal guidance</h3><p>' + html.escape(str(result.get("disposal_advice", "Check local recycling rules before disposal."))) + '</p><p class="mini-note">AI suggestions can be wrong. Confirm the material and follow your local waste-management rules.</p></div>', unsafe_allow_html=True)
        st.write("")
        st.markdown('<div class="section-kicker">04 · HUMAN CONFIRMATION</div>', unsafe_allow_html=True)
        st.subheader("Confirm before saving to Material Passport")
        st.caption("The AI suggestion is not saved automatically. Review the category and weight, then save a verified record.")
        default_material = str(result.get("category", "Other")).strip().title()
        normalised = {"Electronic Waste": "Electronic waste", "Organic": "Organic", "Other": "Other", "Cardboard": "Cardboard", "Paper": "Paper", "Plastic": "Plastic", "Metal": "Metal", "Glass": "Glass", "Textile": "Textile"}
        default_material = normalised.get(default_material, "Other")
        if default_material not in MATERIAL_TYPES:
            default_material = "Other"
        with st.form("save_ai_scan_record", clear_on_submit=False):
            c1, c2 = st.columns(2, gap="large")
            with c1:
                confirmed_material = st.selectbox("Confirmed material category", MATERIAL_TYPES, index=MATERIAL_TYPES.index(default_material), key="scan_confirm_material")
                confirmed_weight = st.number_input("Measured weight (kg)", min_value=0.01, value=1.0, step=0.1, format="%.2f", key="scan_confirm_weight")
            with c2:
                confirmed_status = st.selectbox("Initial lifecycle status", STATUSES, index=STATUSES.index("Collected"), key="scan_confirm_status")
                confirmed_notes = st.text_input("Source / notes", value="AI scan: " + str(st.session_state.get("circulo_last_scan_filename", "uploaded image")), key="scan_confirm_notes")
            save_scan = st.form_submit_button("✓ Save confirmed material", use_container_width=True)
        if save_scan:
            next_id = max([int(r.get("ID", 0)) for r in st.session_state.records] or [0]) + 1
            new_record = {"ID": next_id, "Date": datetime.now().strftime("%Y-%m-%d %H:%M"), "Material": confirmed_material, "Weight (kg)": float(confirmed_weight), "Status": confirmed_status, "Notes": confirmed_notes.strip()}
            insert_record(new_record)
            st.session_state.records = load_records()
            st.success(f"Confirmed AI-assisted material saved as record #{next_id}.")
            st.rerun()

    st.divider()
    st.markdown('<div class="section-kicker">THE CIRCULO LOOP</div>', unsafe_allow_html=True)
    st.subheader("From image to action")
    p1, p2, p3 = st.columns(3, gap="medium")
    with p1:
        st.markdown('<div class="surface"><div class="surface-icon">📷</div><h3>01 · Capture</h3><p>Upload a clear photo of a single waste item.</p><span class="status-chip">IMAGE INTAKE</span></div>', unsafe_allow_html=True)
    with p2:
        st.markdown('<div class="surface"><div class="surface-icon">✨</div><h3>02 · Understand</h3><p>AI returns an object label, category, explanation and disposal suggestion.</p><span class="status-chip">AI ASSISTED</span></div>', unsafe_allow_html=True)
    with p3:
        st.markdown('<div class="surface"><div class="surface-icon">🌱</div><h3>03 · Track</h3><p>Confirm the material and save it into the same traceable database.</p><span class="status-chip">HUMAN VERIFIED</span></div>', unsafe_allow_html=True)

# ============================================================
# MATERIAL PASSPORT
# ============================================================
elif selected_page == "Material Passport":
    page_heading("Material Passport", "Create traceable material records and keep lifecycle statuses up to date.")
    st.markdown(
        '<div class="hero" style="padding:22px 25px;margin-bottom:20px;"><div class="hero-pill">MATERIAL TRACEABILITY</div><h1 style="font-size:1.8rem;">Every material has a journey.</h1><p>Record what was collected, how much was weighed, and where it is in the recovery process.</p></div>',
        unsafe_allow_html=True,
    )
    with st.form("register_material", clear_on_submit=True):
        st.subheader("＋ Register material")
        col1, col2 = st.columns(2, gap="large")
        with col1:
            material = st.selectbox("Material type", MATERIAL_TYPES)
            weight = st.number_input("Weight (kg)", min_value=0.01, max_value=100000.0, value=1.0, step=0.1, format="%.2f")
            notes = st.text_input("Source / notes", placeholder="e.g. College canteen, classroom collection")
        with col2:
            status = st.selectbox("Current lifecycle status", STATUSES)
            st.markdown(
                '<div class="surface" style="margin-top:5px;"><div class="eyebrow">LIFECYCLE GUIDE</div><p style="margin:0;"><b>Collected</b> → <b>Sorted</b> → <b>Ready for recycling</b> → <b>Recycled</b></p><p style="margin:8px 0 0 0;">Reuse is recorded separately when the material is actually reused.</p></div>',
                unsafe_allow_html=True,
            )
        save_record = st.form_submit_button("Save material record", use_container_width=True)
        if save_record:
            next_id = max([int(r.get("ID", 0)) for r in st.session_state.records] or [0]) + 1
            new_record = {
                "ID": next_id,
                "Date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "Material": material,
                "Weight (kg)": float(weight),
                "Status": status,
                "Notes": notes.strip(),
            }
            insert_record(new_record)
            st.session_state.records = load_records()
            st.success(f"Material record #{next_id} saved.")
            st.rerun()

    st.write("")
    st.markdown('<div class="section-kicker">TRACEABILITY</div>', unsafe_allow_html=True)
    st.subheader("Manage lifecycle records")
    if df.empty:
        st.info("No material records yet. Use the form above to create your first passport.")
    else:
        for record in st.session_state.records:
            record_id = int(record.get("ID", 0))
            title = f"#{record_id}  ·  {record['Material']}  ·  {float(record['Weight (kg)']):.2f} kg  ·  {record['Status']}"
            with st.expander(title):
                details_col, edit_col = st.columns([1, 1], gap="large")
                with details_col:
                    st.write(f"**Logged:** {record['Date']}")
                    st.write(f"**Source / notes:** {record.get('Notes') or '—'}")
                with edit_col:
                    chosen_status = st.selectbox("Update lifecycle status", STATUSES, index=STATUSES.index(record["Status"]) if record["Status"] in STATUSES else 0, key=f"record_status_{record_id}")
                    if st.button("Save status", key=f"save_status_{record_id}", use_container_width=True):
                        update_record_status(record_id, chosen_status)
                        st.session_state.records = load_records()
                        st.success("Lifecycle status updated and saved to the local database.")
                        st.rerun()
                if st.button("Delete this record", key=f"delete_record_{record_id}", use_container_width=True):
                    delete_record(record_id)
                    st.session_state.records = load_records()
                    st.success(f"Record #{record_id} deleted.")
                    st.rerun()

# ============================================================
# EARN & RETURN | SIMULATED REWARD DEMO
# ============================================================
elif selected_page == "Earn & Return":
    page_heading("Earn & Return", "Turn sorted recyclables into estimated rewards. Demo credits only — no real money is paid.")
    st.markdown('<div class="hero"><div class="hero-pill">♻️ CIRCULAR ECONOMY</div><h1>Recycle it. Weigh it. Earn from it.</h1><p>Estimate the value of your recyclable waste and create a collection request. A real recycling partner would need to verify material and weight before any payment.</p></div>', unsafe_allow_html=True)
    # Illustrative rates for a hackathon demo, not live market prices.
    demo_rates = {"Plastic bottles": 10.0, "Paper": 8.0, "Cardboard": 6.0, "Aluminium cans": 90.0, "Metal scrap": 25.0, "Glass": 2.0}
    with sqlite3.connect(DB_PATH) as connection:
        reward_rows = connection.execute("SELECT id, date, material, weight, rate, amount, status, notes FROM reward_requests ORDER BY id DESC").fetchall()
    reward_total = sum(row[5] for row in reward_rows if row[6] == "Approved demo credit")
    pending_total = sum(row[5] for row in reward_rows if row[6] == "Pending verification")
    m1, m2, m3 = st.columns(3)
    m1.metric("Approved demo credits", f"₹{reward_total:.2f}")
    m2.metric("Pending estimate", f"₹{pending_total:.2f}")
    m3.metric("Requests submitted", str(len(reward_rows)))
    st.divider()
    st.subheader("Estimate your recycling reward")
    left, right = st.columns([1, 1], gap="large")
    with left:
        with st.form("earn_return_form"):
            material = st.selectbox("Recyclable material", list(demo_rates.keys()))
            weight = st.number_input("Weight (kg)", min_value=0.1, max_value=500.0, value=1.0, step=0.1)
            rate = st.number_input("Demo rate (₹ per kg)", min_value=0.0, max_value=10000.0, value=demo_rates[material], step=1.0, help="Illustrative demo rate only. Change it to demonstrate different material rates.")
            notes = st.text_input("Optional notes", placeholder="e.g. clean bottles, sorted paper")
            estimate = round(float(weight) * float(rate), 2)
            st.markdown(f"### Estimated reward: ₹{estimate:.2f}")
            submitted = st.form_submit_button("Submit demo collection request", use_container_width=True)
            if submitted:
                with sqlite3.connect(DB_PATH) as connection:
                    connection.execute("INSERT INTO reward_requests (date, material, weight, rate, amount, status, notes) VALUES (?, ?, ?, ?, ?, ?, ?)", (datetime.now().strftime("%Y-%m-%d %H:%M"), material, float(weight), float(rate), estimate, "Pending verification", notes.strip()))
                st.success("Demo request saved! The estimate is pending material and weight verification.")
                st.rerun()
    with right:
        st.markdown('<div class="surface"><div class="eyebrow">HOW IT WORKS</div><h3>Three simple steps</h3><p><b>01 · Sort</b><br>Separate clean recyclable materials.</p><p><b>02 · Weigh</b><br>Enter the weight and see an estimated value.</p><p><b>03 · Verify</b><br>A real partner would confirm the material and weight before payment.</p><hr><p class="mini-note">Demo transparency: all rates are sample values, all rewards are simulated, and no cash/UPI payout is connected.</p></div>', unsafe_allow_html=True)
    st.divider()
    st.subheader("Reward request history")
    if not reward_rows:
        render_empty_state("₹", "No reward requests yet", "Submit a demo collection request to see it recorded here.")
    else:
        reward_df = pd.DataFrame(reward_rows, columns=["ID", "Date", "Material", "Weight (kg)", "Demo rate (₹/kg)", "Estimated reward (₹)", "Status", "Notes"])
        st.dataframe(reward_df, use_container_width=True, hide_index=True)
        st.caption("Requests are stored in a separate table in circulo.db. Existing material records are not modified.")
        pending_ids = [row[0] for row in reward_rows if row[6] == "Pending verification"]
        if pending_ids:
            with st.expander("Judge demo controls · simulate partner verification"):
                chosen_id = st.selectbox("Choose a pending request", pending_ids, format_func=lambda rid: f"Request #{rid}")
                verify_action = st.radio("Demo action", ["Approve demo credit", "Reject request"], horizontal=True)
                if st.button("Apply demo verification", use_container_width=True):
                    new_status = "Approved demo credit" if verify_action == "Approve demo credit" else "Rejected"
                    with sqlite3.connect(DB_PATH) as connection:
                        connection.execute("UPDATE reward_requests SET status = ? WHERE id = ?", (new_status, int(chosen_id)))
                    st.success(f"Request #{chosen_id} marked: {new_status}. This is a simulation only.")
                    st.rerun()

# ============================================================
# IMPACT LAB
# ============================================================
elif selected_page == "Impact Lab":
    page_heading("Impact Lab", "A transparent view of material weight and recovery progress — no invented environmental savings.")
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Total tracked", format_weight(total_weight))
    k2.metric("Marked recycled", format_weight(recycled_weight))
    k3.metric("Marked reused", format_weight(reused_weight))
    k4.metric("Awaiting recovery", format_weight(pending_weight))

    st.write("")
    st.markdown('<div class="section-kicker">RECOVERY PROGRESS</div>', unsafe_allow_html=True)
    st.subheader("Processed material share")
    if total_weight > 0:
        st.progress(min(max(progress, 0.0), 1.0))
        st.markdown(f"**{progress * 100:.1f}%** of tracked weight is marked as recycled or reused.")
        st.caption(f"Recycled: {recycled_weight:.2f} kg · Reused: {reused_weight:.2f} kg · Awaiting recovery: {pending_weight:.2f} kg")
    else:
        st.info("Add material records to calculate the actual recovery share.")

    left, right = st.columns([1.1, 1], gap="large")
    with left:
        st.markdown('<div class="section-kicker">MATERIAL DISTRIBUTION</div>', unsafe_allow_html=True)
        st.subheader("Weight by material")
        if df.empty:
            render_empty_state("◉", "No measurements yet", "Your chart will use the weights recorded in Material Passport.")
        else:
            summary = df.groupby("Material")["Weight (kg)"].sum().sort_values(ascending=True)
            st.bar_chart(summary, color="#36D887", horizontal=True, height=320)
    with right:
        st.markdown('<div class="section-kicker">STATUS BREAKDOWN</div>', unsafe_allow_html=True)
        st.subheader("Where materials stand")
        if df.empty:
            render_empty_state("▤", "No statuses yet", "Status totals appear after you register materials.")
        else:
            status_summary = df.groupby("Status")["Weight (kg)"].sum().reindex(STATUSES, fill_value=0)
            st.bar_chart(status_summary, color="#C4F36A", height=320)

    st.divider()
    st.markdown(
        '<div class="surface"><div class="eyebrow">MEASUREMENT NOTE</div><p style="margin:0;">This prototype reports recorded weights and lifecycle labels only. Carbon, water, energy, landfill-diversion, or monetary benefits require validated material-specific factors and are intentionally not estimated here.</p></div>',
        unsafe_allow_html=True,
    )

# ============================================================
# RECORDS & EXPORT
# ============================================================
elif selected_page == "Records & Export":
    page_heading("Records & Export", "Review your current session's data and export it for analysis or submission.")
    if df.empty:
        render_empty_state("▣", "No records to export yet", "Register material in Material Passport. The saved records will be available here.")
        st.write("")
        if st.button("Go to Material Passport", use_container_width=True):
            navigate("Material Passport")
    else:
        a, b, c = st.columns(3)
        a.metric("Material records", f"{record_count:,}")
        b.metric("Total tracked", format_weight(total_weight))
        c.metric("Processed (recycled + reused)", format_weight(recycled_weight + reused_weight))
        st.dataframe(df, use_container_width=True, hide_index=True, height=420)
        csv_data = df.to_csv(index=False).encode("utf-8-sig")
        st.download_button("Download CSV", data=csv_data, file_name="circulo_material_records.csv", mime="text/csv", use_container_width=True)
        st.caption("Storage: records are saved in the local SQLite database file circulo.db, so they remain after app restarts on this computer. Download CSV for a backup or sharing.")
        st.divider()
        with st.expander("Danger zone · Clear session records"):
            st.warning("This permanently clears all records in the current app session.")
            confirm_clear = st.checkbox("I understand this cannot be undone.", key="confirm_clear_records")
            if st.button("Clear all records", disabled=not confirm_clear, type="secondary"):
                clear_database()
                st.session_state.records = []
                st.success("All material records were cleared from the local database.")
                st.rerun()

# -------------------------- FOOTER --------------------------
st.divider()
st.markdown('<div class="footer">CIRCULO · SMART RECYCLING ASSISTANT · CODE CLASH 2.0 PROTOTYPE</div>', unsafe_allow_html=True)