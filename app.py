"""
Multi-AI Agent ATS  ·  Streamlit UI
Run: streamlit run app.py
"""

import os
import time
import json
import threading
from pathlib import Path
from datetime import datetime
from typing import Optional

import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config as _cfg

# ── Page config (must be first Streamlit call) ─────────────────────────────────
st.set_page_config(
    page_title="AI Recruiter · ATS",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:ital,wght@0,400;0,700;1,400&family=DM+Sans:wght@300;400;500;600&display=swap');

/* ── Base ── */
html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
}

/* ── Sidebar ── */
section[data-testid="stSidebar"] {
    background: #0d0d0d;
    border-right: 1px solid #1e1e1e;
}
section[data-testid="stSidebar"] * {
    color: #e8e8e8 !important;
}
section[data-testid="stSidebar"] .stTextInput input,
section[data-testid="stSidebar"] .stTextArea textarea,
section[data-testid="stSidebar"] .stSelectbox select {
    background: #1a1a1a !important;
    border: 1px solid #333 !important;
    color: #e8e8e8 !important;
    border-radius: 6px !important;
}

/* ── Main bg ── */
.main .block-container {
    background: #f8f7f4;
    padding-top: 2rem;
}

/* ── Header ── */
.ats-header {
    font-family: 'Space Mono', monospace;
    font-size: 2rem;
    font-weight: 700;
    letter-spacing: -1px;
    color: #0d0d0d;
    line-height: 1.1;
}
.ats-sub {
    font-family: 'Space Mono', monospace;
    font-size: 0.75rem;
    color: #888;
    letter-spacing: 3px;
    text-transform: uppercase;
    margin-top: 4px;
}

/* ── Stat cards ── */
.stat-card {
    background: #0d0d0d;
    color: #f8f7f4;
    border-radius: 12px;
    padding: 20px 24px;
    text-align: center;
}
.stat-number {
    font-family: 'Space Mono', monospace;
    font-size: 2.4rem;
    font-weight: 700;
    line-height: 1;
}
.stat-label {
    font-size: 0.72rem;
    letter-spacing: 2px;
    text-transform: uppercase;
    color: #888;
    margin-top: 4px;
}
.stat-card.green { border-left: 4px solid #22c55e; }
.stat-card.red   { border-left: 4px solid #ef4444; }
.stat-card.blue  { border-left: 4px solid #3b82f6; }
.stat-card.amber { border-left: 4px solid #f59e0b; }

/* ── Candidate card ── */
.candidate-card {
    background: white;
    border: 1px solid #e5e5e5;
    border-radius: 12px;
    padding: 20px;
    margin-bottom: 12px;
    transition: box-shadow .2s;
}
.candidate-card:hover { box-shadow: 0 4px 20px rgba(0,0,0,.08); }
.candidate-card.accepted { border-left: 4px solid #22c55e; }
.candidate-card.rejected { border-left: 4px solid #ef4444; }
.candidate-card.pending  { border-left: 4px solid #f59e0b; }
.candidate-card.error    { border-left: 4px solid #6b7280; }

.cand-name {
    font-family: 'Space Mono', monospace;
    font-size: 1rem;
    font-weight: 700;
    color: #0d0d0d;
}
.cand-badge {
    display: inline-block;
    padding: 2px 10px;
    border-radius: 20px;
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 1px;
    text-transform: uppercase;
}
.badge-accepted { background: #dcfce7; color: #16a34a; }
.badge-rejected { background: #fee2e2; color: #dc2626; }
.badge-pending  { background: #fef3c7; color: #d97706; }
.badge-error    { background: #f3f4f6; color: #6b7280; }

.score-ring {
    font-family: 'Space Mono', monospace;
    font-size: 1.6rem;
    font-weight: 700;
}
.score-high  { color: #22c55e; }
.score-mid   { color: #f59e0b; }
.score-low   { color: #ef4444; }

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
    gap: 4px;
    background: transparent;
    border-bottom: 2px solid #e5e5e5;
}
.stTabs [data-baseweb="tab"] {
    font-family: 'Space Mono', monospace;
    font-size: 0.8rem;
    letter-spacing: 1px;
    border-radius: 6px 6px 0 0;
    padding: 8px 16px;
}
.stTabs [aria-selected="true"] {
    background: #0d0d0d !important;
    color: white !important;
}

/* ── Buttons ── */
.stButton > button {
    font-family: 'Space Mono', monospace !important;
    font-size: 0.8rem !important;
    letter-spacing: 1px !important;
    border-radius: 8px !important;
    border: 2px solid #0d0d0d !important;
    background: #0d0d0d !important;
    color: #ffffff !important;
    padding: 10px 24px !important;
    transition: all .2s !important;
}
.stButton > button:hover {
    background: #ffffff !important;
    color: #0d0d0d !important;
}
.stButton > button[kind="secondary"] {
    background: #ffffff !important;
    color: #0d0d0d !important;
}
/* Sidebar button specifically */
section[data-testid="stSidebar"] .stButton > button {
    background: #22c55e !important;
    color: #000000 !important;
    border: none !important;
    font-weight: 700 !important;
}
section[data-testid="stSidebar"] .stButton > button:hover {
    background: #16a34a !important;
    color: #ffffff !important;
}

/* ── Log terminal ── */
.log-box {
    background: #0d0d0d;
    color: #22c55e;
    font-family: 'Space Mono', monospace;
    font-size: 0.78rem;
    padding: 16px;
    border-radius: 10px;
    min-height: 120px;
    line-height: 1.8;
    overflow-y: auto;
    max-height: 300px;
}

/* ── Email box ── */
.email-box {
    background: #fafaf9;
    border: 1px solid #e5e5e5;
    border-radius: 8px;
    padding: 16px;
    font-size: 0.88rem;
    line-height: 1.7;
    white-space: pre-wrap;
    font-family: 'DM Sans', sans-serif;
}

/* ── Agent thought ── */
.thought-item {
    font-size: 0.8rem;
    color: #555;
    padding: 6px 10px;
    border-left: 2px solid #e5e5e5;
    margin-bottom: 4px;
    font-style: italic;
}

/* ── Section titles ── */
.section-title {
    font-family: 'Space Mono', monospace;
    font-size: 0.7rem;
    letter-spacing: 3px;
    text-transform: uppercase;
    color: #888;
    margin-bottom: 12px;
    padding-bottom: 6px;
    border-bottom: 1px solid #e5e5e5;
}

/* ── Upload zone ── */
[data-testid="stFileUploader"] {
    border: 2px dashed #ccc !important;
    border-radius: 12px !important;
    padding: 16px !important;
    background: white !important;
}
[data-testid="stFileUploader"]:hover {
    border-color: #0d0d0d !important;
}
</style>
""", unsafe_allow_html=True)


# ── Session state init ─────────────────────────────────────────────────────────
def _init_state():
    defaults = {
        "results":        [],          # list[CandidateResult]
        "agents_ready":   False,
        "processing":     False,
        "log_lines":      [],
        "letta_client":   None,
        "job_desc":       "",
        "company_name":   "YourCompany",
        "company_desc":   "",
        "required_skills": "",
        "active_tab":     0,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

_init_state()


# ── Helpers ────────────────────────────────────────────────────────────────────
def add_log(msg: str):
    ts  = datetime.now().strftime("%H:%M:%S")
    st.session_state.log_lines.append(f"[{ts}]  {msg}")

def score_class(score: int) -> str:
    if score >= 7: return "score-high"
    if score >= 4: return "score-mid"
    return "score-low"

def render_stats():
    results = st.session_state.results
    total    = len(results)
    accepted = sum(1 for r in results if r.decision == "accepted")
    rejected = sum(1 for r in results if r.decision == "rejected")
    avg_time = (
        round(sum(r.processing_time for r in results) / total, 1)
        if total else 0
    )

    c1, c2, c3, c4 = st.columns(4)
    for col, cls, num, label in [
        (c1, "blue",  total,    "Total Screened"),
        (c2, "green", accepted, "Accepted"),
        (c3, "red",   rejected, "Rejected"),
        (c4, "amber", avg_time, "Avg Time (s)"),
    ]:
        col.markdown(
            f'<div class="stat-card {cls}">'
            f'<div class="stat-number">{num}</div>'
            f'<div class="stat-label">{label}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

def render_candidate_card(result, index: int):
    badge_cls = f"badge-{result.decision}"
    score_cls = score_class(result.score)
    decision_label = result.decision.upper()

    with st.container():
        st.markdown(
            f'<div class="candidate-card {result.decision}">'
            f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px">'
            f'  <span class="cand-name">{result.name}</span>'
            f'  <span class="cand-badge {badge_cls}">{decision_label}</span>'
            f'</div>'
            f'<div style="display:flex;gap:24px;align-items:center;flex-wrap:wrap">'
            f'  <span class="score-ring {score_cls}">{result.score}<span style="font-size:.85rem;color:#999">/10</span></span>'
            f'  <span style="font-size:.82rem;color:#555;flex:1">{result.justification[:180]}{"…" if len(result.justification)>180 else ""}</span>'
            f'  <span style="font-size:.72rem;color:#aaa;white-space:nowrap">⏱ {result.processing_time}s</span>'
            f'</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

        with st.expander("View details", expanded=False):
            t1, t2, t3 = st.tabs(["📋 Full Justification", "✉️ Email Draft", "🧠 Agent Thoughts"])

            with t1:
                st.write(result.justification or "—")

            with t2:
                if result.email_draft:
                    email_label = "✅ Acceptance Email" if result.decision == "accepted" else "❌ Rejection Email"
                    st.caption(email_label)
                    st.markdown(
                        f'<div class="email-box">{result.email_draft}</div>',
                        unsafe_allow_html=True,
                    )
                    st.download_button(
                        "Download email",
                        data=result.email_draft,
                        file_name=f"email_{result.name.replace(' ', '_')}.txt",
                        mime="text/plain",
                        key=f"dl_email_{index}",
                    )
                else:
                    st.info("No email drafted yet.")

            with t3:
                if result.agent_thoughts:
                    for thought in result.agent_thoughts:
                        st.markdown(
                            f'<div class="thought-item">💭 {thought}</div>',
                            unsafe_allow_html=True,
                        )
                else:
                    st.caption("No internal monologue captured.")


# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(
        '<div style="font-family:Space Mono,monospace;font-size:1.1rem;font-weight:700;'
        'color:#e8e8e8;padding:8px 0 20px">⬡ ATS CONFIG</div>',
        unsafe_allow_html=True,
    )

    # ── LLM Model ──
    st.markdown('<div class="section-title" style="color:#666">LLM Model</div>', unsafe_allow_html=True)
    model_name = st.text_input(
        "Model name (as registered in Letta)",
        value=_cfg.LETTA_LLM_MODEL,
        placeholder="lmstudio_openai/qwen3-8b@q6_k",
        help="Must match the handle shown in /v1/models/",
    )
    batch_workers = st.slider(
        "Batch workers",
        min_value=1, max_value=4, value=2,
        help="Parallel candidates. Keep at 1-2 for local LLMs.",
    )
    st.session_state["batch_workers"] = batch_workers

    st.divider()

    # ── Company ──
    st.markdown('<div class="section-title" style="color:#666">Company</div>', unsafe_allow_html=True)
    company_name = st.text_input("Company name", value=_cfg.DEFAULT_COMPANY_NAME)
    company_desc = st.text_area(
        "About the company",
        value=_cfg.DEFAULT_COMPANY_DESC,
        height=80,
    )

    st.divider()

    # ── Job ──
    st.markdown('<div class="section-title" style="color:#666">Job</div>', unsafe_allow_html=True)
    position_title = st.text_input("Position title", value="Solo AI Builder / Full-Stack Engineer")
    job_desc = st.text_area(
        "Job description",
        value=(
            "Solo AI Builder / Full-Stack Engineer. "
            "Must ship AI-powered MVPs fast. "
            "Experience with LLMs, RAG pipelines, and Python backends required."
        ),
        height=100,
    )
    required_skills = st.text_input(
        "Required skills (comma-separated)",
        value="Python, LLMs, RAG, FastAPI, Docker",
    )

    st.divider()

    # ── Recruiter ──
    st.markdown('<div class="section-title" style="color:#666">Recruiter</div>', unsafe_allow_html=True)
    recruiter_name  = st.text_input("Your name",  value="Talent Team")
    recruiter_email = st.text_input("Your email", value="careers@yourcompany.com")

    st.divider()

    # ── Init agents ──
    if st.button("⚡ Initialize Agents", use_container_width=True):
        import config as _cfg
        _cfg.LETTA_LLM_MODEL = model_name

        with st.spinner("Spinning up agents…"):
            try:
                from agents.ats_agents import get_client, setup_agents
                client = get_client()
                setup_agents(
                    client, job_desc, company_name, company_desc, required_skills,
                    recruiter_name=recruiter_name,
                    recruiter_email=recruiter_email,
                    position_title=position_title,
                )
                st.session_state.letta_client    = client
                st.session_state.agents_ready    = True
                st.session_state.job_desc        = job_desc
                st.session_state.company_name    = company_name
                st.session_state.company_desc    = company_desc
                st.session_state.required_skills = required_skills
                add_log("✅ Agents initialized successfully")
                st.success("Agents ready!")
            except Exception as e:
                add_log(f"❌ Init failed: {e}")
                st.error(f"Failed to initialize: {e}")

    status_color = "#22c55e" if st.session_state.agents_ready else "#ef4444"
    status_text  = "AGENTS READY" if st.session_state.agents_ready else "NOT INITIALIZED"
    st.markdown(
        f'<div style="text-align:center;margin-top:8px;font-family:Space Mono,monospace;'
        f'font-size:0.7rem;letter-spacing:2px;color:{status_color}">'
        f'● {status_text}</div>',
        unsafe_allow_html=True,
    )


# ── Main area ──────────────────────────────────────────────────────────────────
st.markdown(
    '<div class="ats-header">Multi-AI Agent<br>Screening System</div>'
    '<div class="ats-sub">Powered by Letta · Local LLMs · 3-Agent Pipeline</div>',
    unsafe_allow_html=True,
)
st.markdown("<br>", unsafe_allow_html=True)

# Stats row
render_stats()
st.markdown("<br>", unsafe_allow_html=True)

# ── Tabs ───────────────────────────────────────────────────────────────────────
tab_screen, tab_results, tab_memory, tab_log = st.tabs(
    ["▶  Screen Candidates", "📊  Results", "🧠  Shared Memory", "🖥  Agent Log"]
)


# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — Screen
# ══════════════════════════════════════════════════════════════════════════════
import streamlit.components.v1 as _stc

def _render_html(html_str, ph=None, height=360):
    if ph:
        with ph:
            _stc.html(html_str, height=height)
    else:
        _stc.html(html_str, height=height)

def render_pipeline_ui(candidate_name, stage, results_so_far):
    stages = [
        ("upload",   "ti-file-upload",   "Resume received"),
        ("parse",    "ti-text-scan-2",   "Parsing content"),
        ("eval",     "ti-brain",         "AI evaluation"),
        ("memory",   "ti-database",      "Updating memory"),
        ("email",    "ti-mail-forward",  "Drafting email"),
        ("done",     "ti-circle-check",  "Complete"),
    ]
    stage_idx = {"upload":0,"parse":1,"eval":2,"memory":3,"email":4,"done":5}.get(stage, 0)

    cards_html = ""
    for r in results_so_far:
        color = "#22c55e" if r.decision=="accepted" else "#ef4444" if r.decision=="rejected" else "#f59e0b"
        icon  = "ti-circle-check" if r.decision=="accepted" else "ti-circle-x" if r.decision=="rejected" else "ti-help-circle"
        cards_html += f"""
        <div style="display:flex;align-items:center;gap:10px;padding:8px 12px;background:#fff;border:1px solid #e5e5e5;border-left:3px solid {color};border-radius:8px;margin-bottom:6px">
          <i class="ti {icon}" style="color:{color};font-size:16px"></i>
          <span style="font-family:monospace;font-size:13px;font-weight:600;color:#0d0d0d">{r.name}</span>
          <span style="font-size:12px;color:#888;margin-left:auto">{r.score}/10 · {r.processing_time}s</span>
        </div>"""

    steps_html = ""
    for si, (sid, icon, label) in enumerate(stages):
        if si < stage_idx:
            bg, col, border = "#f0fdf4", "#22c55e", "#bbf7d0"
            icon_col = "#22c55e"
            tick = '<i class="ti ti-check" style="font-size:11px;position:absolute;right:-3px;bottom:-3px;background:#22c55e;color:#fff;border-radius:50%;width:14px;height:14px;display:flex;align-items:center;justify-content:center;line-height:14px"></i>'
        elif si == stage_idx:
            bg, col, border = "#eff6ff", "#3b82f6", "#bfdbfe"
            icon_col = "#3b82f6"
            tick = '<div style="position:absolute;right:-3px;bottom:-3px;width:14px;height:14px;border-radius:50%;background:#3b82f6;display:flex;align-items:center;justify-content:center"><div style="width:6px;height:6px;border-radius:50%;background:#fff;animation:pulse 0.8s ease-in-out infinite"></div></div>'
        else:
            bg, col, border = "#f9f9f9", "#ccc", "#e5e5e5"
            icon_col = "#ccc"
            tick = ""

        connector = "" if si == len(stages)-1 else f'<div style="position:absolute;left:50%;top:58px;width:2px;height:24px;background:{"#22c55e" if si < stage_idx else "#e5e5e5"};transform:translateX(-50%)"></div>'

        steps_html += f"""
        <div style="display:flex;flex-direction:column;align-items:center;flex:1;position:relative">
          <div style="position:relative;width:44px;height:44px;border-radius:50%;background:{bg};border:2px solid {border};display:flex;align-items:center;justify-content:center;transition:all 0.3s">
            <i class="ti {icon}" style="font-size:18px;color:{icon_col}"></i>
            {tick}
          </div>
          {connector}
          <span style="font-size:11px;color:{col};margin-top:28px;text-align:center;font-weight:{'600' if si==stage_idx else '400'};width:72px;line-height:1.3">{label}</span>
        </div>"""

    html = f"""
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@tabler/icons-webfont@latest/dist/tabler-icons.min.css">
    <style>
      @keyframes pulse {{0%,100%{{transform:scale(1)}}50%{{transform:scale(1.4)}}}}
      @keyframes slideIn {{from{{opacity:0;transform:translateY(8px)}}to{{opacity:1;transform:translateY(0)}}}}
      .ats-wrap * {{ box-sizing:border-box; font-family: -apple-system, sans-serif; }}
    </style>
    <div class="ats-wrap" style="background:#f8f7f4;border-radius:14px;padding:20px 24px;border:1px solid #e5e5e5">
      <div style="font-family:monospace;font-size:11px;letter-spacing:2px;color:#888;text-transform:uppercase;margin-bottom:16px">
        Pipeline · Processing <strong style="color:#0d0d0d">{candidate_name}</strong>
      </div>

      <div style="display:flex;justify-content:space-between;align-items:flex-start;padding:0 4px;margin-bottom:28px">
        {steps_html}
      </div>

      {'<div style="margin-top:4px"><div style="font-family:monospace;font-size:10px;letter-spacing:2px;color:#aaa;text-transform:uppercase;margin-bottom:8px">Completed</div>' + cards_html + '</div>' if cards_html else ''}
    </div>"""
    return html

with tab_screen:
    col_upload, col_manual = st.columns([1, 1], gap="large")

    with col_upload:
        st.markdown('<div class="section-title">Upload Resumes (PDF / TXT)</div>', unsafe_allow_html=True)
        uploaded = st.file_uploader(
            "Drop files here",
            type=["pdf", "txt"],
            accept_multiple_files=True,
            label_visibility="collapsed",
        )
        if uploaded:
            st.caption(f"{len(uploaded)} file(s) ready")

    with col_manual:
        st.markdown('<div class="section-title">Or Enter Manually</div>', unsafe_allow_html=True)
        manual_name = st.text_input("Candidate name", placeholder="Jane Doe")
        manual_text = st.text_area("Paste resume text here", height=180, placeholder="Summary\n\nExperience\n…")

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Action buttons ──
    btn_col1, btn_col2, btn_col3 = st.columns([2, 1, 1])

    with btn_col1:
        run_btn = st.button(
            "🚀 Run Screening Pipeline",
            disabled=not st.session_state.agents_ready,
            use_container_width=True,
        )
    with btn_col2:
        clear_btn = st.button("🗑 Clear Results", use_container_width=True)
    with btn_col3:
        demo_btn = st.button("🎭 Load Demo Data", use_container_width=True)

    if clear_btn:
        st.session_state.results   = []
        st.session_state.log_lines = []
        add_log("Results cleared")
        st.rerun()

    DEMO_CANDIDATES = {
        "Alex Chen": (
            "Alex Chen | Senior Python Developer\n"
            "Skills: Python, FastAPI, LangChain, Docker, PostgreSQL, RAG pipelines, OpenAI API\n"
            "Experience: 5 years building ML services and LLM applications at fintech startups.\n"
            "Projects: Built a RAG-based document QA system serving 10k users daily.\n"
            "Education: BSc Computer Science, UC Berkeley."
        ),
        "Maria Santos": (
            "Maria Santos | Frontend Designer\n"
            "Skills: Figma, CSS, React, Tailwind. Limited backend experience.\n"
            "Experience: 3 years UX design at agencies. No AI/ML background.\n"
            "Education: BFA Graphic Design."
        ),
        "Reza Ahmadi": (
            "Reza Ahmadi | AI/ML Engineer\n"
            "Skills: Python, PyTorch, LLM fine-tuning, FAISS, Hugging Face, FastAPI, Docker, Linux.\n"
            "Experience: 4 years NLP research + production. Built RAG pipelines and deployed LLMs.\n"
            "Publications: 2 papers on NLP at international conferences.\n"
            "Education: MSc Artificial Intelligence."
        ),
    }

    if demo_btn:
        if not st.session_state.agents_ready:
            st.error("Initialize agents first (sidebar).")
        else:
            from agents.ats_agents import screen_candidate
            add_log("Demo pipeline started: Alex Chen, Maria Santos, Reza Ahmadi")
            demo_items       = list(DEMO_CANDIDATES.items())
            progress_bar     = st.progress(0, text="Starting demo…")
            demo_pipeline_ph = st.empty()
            for i, (name, resume_text) in enumerate(demo_items):
                pct = int((i / len(demo_items)) * 100)
                progress_bar.progress(pct, text=f"Processing {i+1}/{len(demo_items)}: {name}")
                add_log(f"🔍 Evaluating {name}…")
                with demo_pipeline_ph:
                    _stc.html(render_pipeline_ui(name, "upload", st.session_state.results), height=360)
                time.sleep(0.3)
                with demo_pipeline_ph:
                    _stc.html(render_pipeline_ui(name, "parse",  st.session_state.results), height=360)
                time.sleep(0.4)
                with demo_pipeline_ph:
                    _stc.html(render_pipeline_ui(name, "eval",   st.session_state.results), height=360)
                result = screen_candidate(st.session_state.letta_client, name, resume_text)
                with demo_pipeline_ph:
                    _stc.html(render_pipeline_ui(name, "memory", st.session_state.results), height=360)
                time.sleep(0.3)
                with demo_pipeline_ph:
                    _stc.html(render_pipeline_ui(name, "email",  st.session_state.results), height=360)
                time.sleep(0.3)
                st.session_state.results.append(result)
                with demo_pipeline_ph:
                    _stc.html(render_pipeline_ui(name, "done",   st.session_state.results), height=360)
                time.sleep(0.5)
                add_log(
                    f"{'✅' if result.decision == 'accepted' else '❌'} "
                    f"{name} → {result.decision.upper()} (score {result.score}/10, {result.processing_time}s)"
                )
                if result.error:
                    add_log(f"⚠️  Error: {result.error}")
            progress_bar.progress(100, text="Demo complete!")
            demo_pipeline_ph.empty()
            st.rerun()

    # ── Run pipeline ──
    if run_btn:
        if not st.session_state.agents_ready:
            st.error("Initialize agents first (sidebar).")
        else:
            from agents.ats_agents import screen_candidate, CandidateResult
            from utils.resume_parser import resume_from_uploaded_file

            # Collect candidates
            candidates: list[tuple[str, str]] = []

            # From uploaded files
            for uf in (uploaded or []):
                text = resume_from_uploaded_file(uf)
                # Use filename (without extension) as candidate name
                raw_name = Path(uf.name).stem.replace("_", " ").replace("-", " ").title()
                candidates.append((raw_name, text))

            # From manual entry
            if manual_name.strip() and manual_text.strip():
                candidates.append((manual_name.strip(), manual_text.strip()))

            # Check for demo resumes on disk
            if not candidates:
                demo_dir = Path("data/resumes")
                if demo_dir.exists():
                    for f in demo_dir.glob("*.txt"):
                        name = f.stem.replace("_", " ").title()
                        text = f.read_text(encoding="utf-8")
                        candidates.append((name, text))

            if not candidates:
                st.warning("No candidates to process. Upload files, enter manually, or load demo data.")
            else:
                add_log(f"Starting pipeline for {len(candidates)} candidate(s)…")
                progress_bar = st.progress(0, text="Initialising…")
                status_text  = st.empty()

                from agents.ats_agents import screen_candidate

                pipeline_placeholder = st.empty()


                for i, (name, resume_text) in enumerate(candidates):
                    pct = int((i / len(candidates)) * 100)
                    progress_bar.progress(pct, text=f"Processing {i+1}/{len(candidates)}: {name}")
                    add_log(f"🔍 Evaluating {name}…")

                    with pipeline_placeholder:
                        _stc.html(render_pipeline_ui(name, "upload", st.session_state.results), height=360)
                    time.sleep(0.3)
                    with pipeline_placeholder:
                        _stc.html(render_pipeline_ui(name, "parse", st.session_state.results), height=360)
                    time.sleep(0.4)
                    with pipeline_placeholder:
                        _stc.html(render_pipeline_ui(name, "eval", st.session_state.results), height=360)

                    result = screen_candidate(
                        st.session_state.letta_client,
                        name,
                        resume_text,
                    )

                    with pipeline_placeholder:
                        _stc.html(render_pipeline_ui(name, "memory", st.session_state.results), height=360)
                    time.sleep(0.3)
                    with pipeline_placeholder:
                        _stc.html(render_pipeline_ui(name, "email", st.session_state.results), height=360)
                    time.sleep(0.3)

                    st.session_state.results.append(result)

                    with pipeline_placeholder:
                        _stc.html(render_pipeline_ui(name, "done", st.session_state.results), height=360)
                    time.sleep(0.5)

                    add_log(
                        f"{'✅' if result.decision == 'accepted' else '❌'} "
                        f"{name} → {result.decision.upper()} (score {result.score}/10, {result.processing_time}s)"
                    )
                    if result.error:
                        add_log(f"⚠️  Error detail: {result.error}")

                pipeline_placeholder.empty()

                progress_bar.progress(100, text="Done!")
                status_text.success(f"✅ Screened {len(candidates)} candidate(s).")
                time.sleep(0.8)
                progress_bar.empty()
                status_text.empty()
                st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — Results
# ══════════════════════════════════════════════════════════════════════════════
with tab_results:
    results = st.session_state.results

    if not results:
        st.markdown(
            '<div style="text-align:center;padding:60px 0;color:#aaa;font-family:Space Mono,monospace;'
            'font-size:0.85rem">No results yet.<br>Run the screening pipeline first.</div>',
            unsafe_allow_html=True,
        )
    else:
        # Filter bar
        f1, f2, f3 = st.columns([1, 1, 2])
        with f1:
            filter_decision = st.selectbox("Filter", ["All", "Accepted", "Rejected", "Error"])
        with f2:
            sort_by = st.selectbox("Sort by", ["Name", "Score ↓", "Score ↑", "Time"])
        with f3:
            search = st.text_input("Search name", placeholder="Type to filter…")

        filtered = results.copy()
        if filter_decision != "All":
            filtered = [r for r in filtered if r.decision == filter_decision.lower()]
        if search:
            filtered = [r for r in filtered if search.lower() in r.name.lower()]
        if sort_by == "Score ↓":
            filtered.sort(key=lambda r: r.score, reverse=True)
        elif sort_by == "Score ↑":
            filtered.sort(key=lambda r: r.score)
        elif sort_by == "Name":
            filtered.sort(key=lambda r: r.name)
        elif sort_by == "Time":
            filtered.sort(key=lambda r: r.processing_time, reverse=True)

        st.caption(f"Showing {len(filtered)} of {len(results)} candidates")
        st.markdown("<br>", unsafe_allow_html=True)

        for i, result in enumerate(filtered):
            render_candidate_card(result, i)

        st.markdown("<br>", unsafe_allow_html=True)

        # ── Export ──
        st.markdown('<div class="section-title">Export</div>', unsafe_allow_html=True)
        ec1, ec2 = st.columns(2)

        with ec1:
            csv_lines = ["Name,Decision,Score,Time(s),Justification"]
            for r in results:
                j = r.justification.replace('"', "'")
                csv_lines.append(f'"{r.name}",{r.decision},{r.score},{r.processing_time},"{j}"')
            csv_data = "\n".join(csv_lines)
            st.download_button(
                "📥 Download CSV",
                data=csv_data,
                file_name="ats_results.csv",
                mime="text/csv",
                use_container_width=True,
            )

        with ec2:
            json_data = json.dumps(
                [
                    {
                        "name":             r.name,
                        "decision":         r.decision,
                        "score":            r.score,
                        "justification":    r.justification,
                        "email_draft":      r.email_draft,
                        "processing_time":  r.processing_time,
                    }
                    for r in results
                ],
                indent=2,
                ensure_ascii=False,
            )
            st.download_button(
                "📥 Download JSON",
                data=json_data,
                file_name="ats_results.json",
                mime="application/json",
                use_container_width=True,
            )


# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — Shared Memory
# ══════════════════════════════════════════════════════════════════════════════
with tab_memory:
    st.markdown('<div class="section-title">Agent Shared Memory Blocks</div>', unsafe_allow_html=True)
    st.caption("Live view of what agents remember across all screenings.")

    if st.session_state.agents_ready and st.session_state.letta_client:
        from agents.ats_agents import get_candidates_log, get_decisions_log

        mem_col1, mem_col2 = st.columns(2)

        with mem_col1:
            st.markdown("**📋 Candidates Screened**")
            candidates_log = get_candidates_log(st.session_state.letta_client)
            st.markdown(
                f'<div class="log-box" style="color:#60a5fa;min-height:200px">'
                f'{candidates_log.replace(chr(10), "<br>") if candidates_log else "Empty"}'
                f'</div>',
                unsafe_allow_html=True,
            )

        with mem_col2:
            st.markdown("**✅ Accepted Decisions**")
            decisions_log = get_decisions_log(st.session_state.letta_client)
            st.markdown(
                f'<div class="log-box" style="color:#22c55e;min-height:200px">'
                f'{decisions_log.replace(chr(10), "<br>") if decisions_log else "Empty"}'
                f'</div>',
                unsafe_allow_html=True,
            )

        if st.button("🔄 Refresh Memory View"):
            st.rerun()
    else:
        st.info("Initialize agents first to see shared memory.")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 4 — Log
# ══════════════════════════════════════════════════════════════════════════════
with tab_log:
    st.markdown('<div class="section-title">Agent Activity Log</div>', unsafe_allow_html=True)

    log_html = "<br>".join(
        f'<span style="color:#888">{line.split("]")[0]}]</span>'
        f'<span style="color:#22c55e">{"]".join(line.split("]")[1:])}</span>'
        for line in (st.session_state.log_lines or ["No activity yet…"])
    )
    st.markdown(
        f'<div class="log-box">{log_html}</div>',
        unsafe_allow_html=True,
    )

    if st.button("Clear log"):
        st.session_state.log_lines = []
        st.rerun()