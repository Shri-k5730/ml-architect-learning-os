from __future__ import annotations

import csv
import hashlib
import hmac
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from html import escape
from zoneinfo import ZoneInfo

import streamlit as st
import streamlit.components.v1 as components

from src.utils.curriculum_catalog import load_topic_catalog_source
from src.utils.rewards import get_topic_reward_state, load_rewards_state
from src.utils.tracker import read_progress_rows
from src.utils.cloud_state import repair_cloud_state_on_startup
from src.utils.code_runner import run_code_exercise
from src.agents.draft_verifier import verify_draft_answers
from src.agents.lesson_booster import build_lesson_booster
from src.agents.writing_assist import analyze_answer_text
from src.agents.tutor_narrative import get_tutor_narrative
from src.blueprints.learning_design import get_bundled_learning_design, runtime_task_for_question
from src.schemas import ArchitectNote, Assessment, ConceptNote
from src.utils.validator import build_dataclass
from src.utils.supabase_store import append_event, upsert_artifact, get_supabase_client, fetch_run_artifacts, fetch_topic_resources, fetch_topic_learning_design
from src.utils.cloud_run_cache import sync_active_run_from_supabase, sync_latest_evaluation_from_supabase
from src.utils.v23_mastery_policy import display_status as v23_display_status, needs_repair as v23_needs_repair, is_mastered as v23_is_mastered
from src.utils.v23_tutor_quality import enhance_learning_design


PROJECT_ROOT = Path(__file__).resolve().parent
RUNS_DIR = PROJECT_ROOT / "runs"
DATA_DIR = PROJECT_ROOT / "data"
TOPICS_DIR = PROJECT_ROOT / "topics"
NOTES_DIR = PROJECT_ROOT / "notes"
ASSESSMENTS_DIR = PROJECT_ROOT / "assessments"


# -----------------------------
# Basic loaders
# -----------------------------
def load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def load_progress_tracker() -> List[Dict[str, str]]:
    try:
        return read_progress_rows()
    except Exception:
        tracker_path = DATA_DIR / "progress_tracker.csv"
        if not tracker_path.exists():
            return []
        with tracker_path.open("r", encoding="utf-8", newline="") as f:
            return list(csv.DictReader(f))


def load_run_history() -> List[Dict[str, Any]]:
    history_path = DATA_DIR / "run_history.jsonl"
    if not history_path.exists():
        return []

    rows: List[Dict[str, Any]] = []
    with history_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except Exception:
                continue
    return rows


def get_secret_value(key: str, default: Any = None) -> Any:
    try:
        return st.secrets.get(key, default)
    except Exception:
        return default


def _render_session_heartbeat_status() -> None:
    """Render hosted-session heartbeat plus a real browser-side IST clock.

    Two separate things happen here:
    1. The Streamlit fragment reruns this function every 60 seconds, touching the
       Python backend while the browser tab and laptop are active.
    2. The embedded browser clock updates every second inside the page, so the
       visible clock behaves like an actual clock instead of waiting for the
       backend heartbeat.
    """
    now_ist = datetime.now(ZoneInfo("Asia/Kolkata"))
    backend_heartbeat_text = now_ist.strftime("%H:%M:%S IST")
    st.session_state["last_backend_heartbeat_ist"] = backend_heartbeat_text

    components.html(
        f"""
        <div class="heartbeat-shell">
          <div class="heartbeat-card">
            <span class="heartbeat-dot"></span>
            <span class="heartbeat-main">Session active</span>
            <span class="heartbeat-separator">·</span>
            <span>IST <span id="mlos-ist-clock">--:--:--</span></span>
            <span class="heartbeat-separator">·</span>
            <span class="heartbeat-muted">Backend ping {escape(backend_heartbeat_text)}</span>
          </div>
        </div>
        <style>
          html, body {{
            margin: 0;
            padding: 0;
            background: transparent;
            font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
          }}
          .heartbeat-shell {{
            display: flex;
            justify-content: flex-end;
            align-items: center;
            width: 100%;
            box-sizing: border-box;
            padding: 0 0 6px 0;
          }}
          .heartbeat-card {{
            display: inline-flex;
            align-items: center;
            gap: 0.45rem;
            border-radius: 999px;
            padding: 0.42rem 0.76rem;
            background: #eef3f8;
            border: 1px solid rgba(24, 128, 91, 0.28);
            box-shadow: 0 10px 24px rgba(32, 48, 70, 0.08);
            color: #34465b;
            font-size: 13px;
            font-weight: 750;
            white-space: nowrap;
          }}
          .heartbeat-dot {{
            width: 0.62rem;
            height: 0.62rem;
            border-radius: 999px;
            background: #22c55e;
            box-shadow: 0 0 0 rgba(34, 197, 94, 0.55);
            animation: heartbeatPulse 1.8s infinite;
          }}
          .heartbeat-main {{ color: #17684a; }}
          .heartbeat-muted {{ color: #586a80; font-weight: 650; }}
          .heartbeat-separator {{ color: #8391a5; }}
          #mlos-ist-clock {{
            color: #1e2b3d;
            font-variant-numeric: tabular-nums;
            letter-spacing: 0.02em;
          }}
          @keyframes heartbeatPulse {{
            0% {{ box-shadow: 0 0 0 0 rgba(34, 197, 94, 0.55); }}
            70% {{ box-shadow: 0 0 0 8px rgba(34, 197, 94, 0); }}
            100% {{ box-shadow: 0 0 0 0 rgba(34, 197, 94, 0); }}
          }}
          @media (max-width: 780px) {{
            .heartbeat-shell {{ justify-content: flex-start; }}
            .heartbeat-card {{ font-size: 12px; flex-wrap: wrap; border-radius: 16px; white-space: normal; }}
          }}
        </style>
        <script>
          const clockEl = document.getElementById("mlos-ist-clock");
          function updateISTClock() {{
            const now = new Date();
            const parts = new Intl.DateTimeFormat("en-IN", {{
              timeZone: "Asia/Kolkata",
              hour: "2-digit",
              minute: "2-digit",
              second: "2-digit",
              hour12: false
            }}).format(now);
            if (clockEl) {{ clockEl.textContent = parts; }}
          }}
          updateISTClock();
          setInterval(updateISTClock, 1000);
        </script>
        """,
        height=44,
        scrolling=False,
    )


if hasattr(st, "fragment"):
    @st.fragment(run_every="60s")
    def render_session_heartbeat() -> None:
        _render_session_heartbeat_status()
else:
    def render_session_heartbeat() -> None:
        _render_session_heartbeat_status()


# -----------------------------
# Auth
# -----------------------------
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def require_login() -> None:
    auth_enabled = bool(get_secret_value("APP_AUTH_ENABLED", True))
    if not auth_enabled:
        return

    expected_hash = str(get_secret_value("APP_PASSWORD_HASH", "")).strip()
    if not expected_hash:
        st.error("Security misconfiguration: APP_PASSWORD_HASH is missing.")
        st.stop()

    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if st.session_state.authenticated:
        with st.sidebar:
            st.success("Authenticated")
            if st.button("Logout"):
                st.session_state.authenticated = False
                st.rerun()
        return

    st.markdown("## 🔐 Private Learning OS")
    st.caption("Enter the app password to continue.")

    password = st.text_input("Password", type="password")
    if st.button("Unlock"):
        provided_hash = hash_password(password)
        if hmac.compare_digest(provided_hash, expected_hash):
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Invalid password.")

    st.stop()


# -----------------------------
# Theme
# -----------------------------
def inject_theme() -> None:
    st.markdown(
        """
        <style>
        :root {
            --bg: #e6ecf3;
            --panel: #f7f9fc;
            --panel-soft: #e5ebf3;
            --line: #c9d4e2;
            --text: #1d293b;
            --muted: #53657b;
            --primary: #245a92;
            --primary-soft: #dbe7f5;
            --teal: #116a68;
            --teal-soft: #dbeeea;
            --risk: #885416;
            --risk-soft: #f5ead8;
            --success: #17684a;
        }
        html { scroll-behavior: smooth; }
        #MainMenu, footer, div[data-testid="stDecoration"], div[data-testid="stStatusWidget"] { visibility: hidden; display: none; }
        header[data-testid="stHeader"] { height: 0rem; min-height: 0rem; background: transparent; }
        div[data-testid="stToolbar"] { visibility: hidden; height: 0rem; position: fixed; }
        body, .stApp, [data-testid="stAppViewContainer"] {
            background: linear-gradient(145deg, #e8eef5 0%, #e2e9f1 48%, #dae3ed 100%);
            color: var(--text);
        }
        .block-container { padding-top: 1.05rem; padding-bottom: 3rem; max-width: 1440px; }
        .main-title {
            font-size: 2.55rem; font-weight: 900; letter-spacing: -0.045em;
            color: #173b64; margin-bottom: 0.2rem;
        }
        .sub-title, .small-muted, .topic-subline { color: var(--muted); }
        .session-heartbeat { display:flex; justify-content:flex-end; align-items:center; gap:.55rem; margin:-.35rem 0 .75rem; color:var(--muted); font-size:.84rem; font-weight:700; }
        .session-heartbeat-card { display:inline-flex; align-items:center; gap:.5rem; border-radius:999px; padding:.42rem .72rem; background:#eef3f8; border:1px solid #c6ddd5; box-shadow:0 6px 18px rgba(16, 42, 67, .07); }
        .heartbeat-dot { width:.62rem; height:.62rem; border-radius:999px; background:#22a06b; box-shadow:0 0 0 rgba(34,160,107,.45); animation:heartbeatPulse 1.8s infinite; }
        @keyframes heartbeatPulse { 0% { box-shadow:0 0 0 0 rgba(34,160,107,.42); } 70% { box-shadow:0 0 0 8px rgba(34,160,107,0); } 100% { box-shadow:0 0 0 0 rgba(34,160,107,0); } }
        div[data-testid="stMetric"] { background:var(--panel); border:1px solid var(--line); padding:1rem; border-radius:18px; box-shadow:0 8px 24px rgba(21, 42, 73, .06); }
        div[data-testid="stMetric"] label { color:var(--muted) !important; }
        div[data-testid="stMetricValue"] { color:var(--text) !important; font-weight:800; }
        /* Action buttons: Review, Redo, Save Answers, Verify Draft, Run Code, Submit */
        .stButton > button,
        div[data-testid="stButton"] > button,
        div[data-testid="stButton"] button,
        div[data-testid="stFormSubmitButton"] > button,
        div[data-testid="stFormSubmitButton"] button {
            border-radius:13px !important;
            border:1px solid #204e80 !important;
            background:#245a92 !important;
            color:#ffffff !important;
            font-weight:800 !important;
            padding:.68rem 1rem !important;
            box-shadow:0 6px 14px rgba(36,90,146,.18) !important;
            transition:all .16s ease !important;
        }
        .stButton > button:hover,
        div[data-testid="stButton"] > button:hover,
        div[data-testid="stButton"] button:hover,
        div[data-testid="stFormSubmitButton"] > button:hover,
        div[data-testid="stFormSubmitButton"] button:hover {
            transform:translateY(-1px);
            background:#1c486f !important;
            border-color:#1c486f !important;
            color:#ffffff !important;
            box-shadow:0 10px 18px rgba(36,90,146,.22) !important;
        }
        .stButton > button:active,
        div[data-testid="stButton"] > button:active,
        div[data-testid="stButton"] button:active,
        div[data-testid="stFormSubmitButton"] > button:active,
        div[data-testid="stFormSubmitButton"] button:active {
            background:#173b64 !important;
            border-color:#173b64 !important;
            color:#ffffff !important;
        }
        .stButton > button:focus,
        div[data-testid="stButton"] > button:focus,
        div[data-testid="stFormSubmitButton"] > button:focus {
            color:#ffffff !important;
            box-shadow:0 0 0 3px rgba(36,90,146,.22) !important;
        }
        .stButton > button p,
        .stButton > button span,
        div[data-testid="stButton"] button p,
        div[data-testid="stButton"] button span,
        div[data-testid="stFormSubmitButton"] button p,
        div[data-testid="stFormSubmitButton"] button span {
            color:#ffffff !important;
            font-weight:800 !important;
        }
        .stButton > button:disabled,
        div[data-testid="stButton"] > button:disabled,
        div[data-testid="stButton"] button:disabled,
        div[data-testid="stFormSubmitButton"] > button:disabled,
        div[data-testid="stFormSubmitButton"] button:disabled {
            background:#dde5ee !important;
            border-color:#c9d4e2 !important;
            color:#66768a !important;
            box-shadow:none !important;
            transform:none !important;
            opacity:1 !important;
        }
        .stButton > button:disabled p,
        .stButton > button:disabled span,
        div[data-testid="stButton"] button:disabled p,
        div[data-testid="stButton"] button:disabled span,
        div[data-testid="stFormSubmitButton"] button:disabled p,
        div[data-testid="stFormSubmitButton"] button:disabled span {
            color:#66768a !important;
            font-weight:750 !important;
        }
        div[data-testid="stTabs"] button { border-radius:999px; color:#4f6075; padding:.62rem 1rem; font-weight:700; }
        div[data-testid="stTabs"] button[aria-selected="true"] { background:var(--primary-soft); color:#1d4c7d; border:1px solid #b8cade; }
        div[data-testid="stTextArea"] textarea, div[data-baseweb="select"] > div, .stTextInput input { background:#f7f9fc; border:1px solid #bfccdc; color:var(--text); border-radius:14px; }
        div[data-testid="stTextArea"] textarea:focus { border-color:#6f98c6; box-shadow:0 0 0 3px rgba(36,90,146,.13); }
        .level-card { border-radius:20px; padding:1rem; min-height:205px; background:var(--panel); border:1px solid var(--line); box-shadow:0 8px 22px rgba(21,42,73,.07); transition:all .16s ease; }
        .level-card:hover { transform:translateY(-2px); border-color:#9eb5d0; box-shadow:0 12px 28px rgba(21,42,73,.11); }
        .level-card-selected { border-color:#678fbc; box-shadow:0 10px 26px rgba(36,90,146,.13); }
        .level-id, .topic-kicker { color:#275884; font-size:.78rem; font-weight:850; text-transform:uppercase; letter-spacing:.10em; margin-bottom:.45rem; }
        .level-title { font-size:1.07rem; line-height:1.3; font-weight:850; color:var(--text); margin-bottom:.8rem; }
        .level-status { display:inline-flex; border-radius:999px; padding:.28rem .62rem; font-size:.82rem; font-weight:750; color:#145b67; background:#ddecef; border:1px solid #bed6dd; margin-bottom:.75rem; }
        .level-stars { font-size:1.2rem; letter-spacing:.06em; color:#ae7418; margin-bottom:.65rem; }
        .level-badge { color:var(--muted); font-size:.92rem; font-weight:650; }
        .app-header-row { display:flex; align-items:flex-start; justify-content:space-between; gap:1rem; margin-bottom:1rem; }
        .status-strip { display:flex; flex-wrap:wrap; gap:.55rem; margin:.75rem 0 1.2rem; }
        .status-pill { display:inline-flex; align-items:center; gap:.35rem; border-radius:999px; padding:.42rem .72rem; background:var(--panel); border:1px solid var(--line); color:var(--muted); font-size:.84rem; font-weight:700; }
        .current-topic-hero { border-radius:22px; padding:1.15rem 1.22rem; margin-bottom:1rem; background:linear-gradient(135deg, #f7f9fc, #e8eef6); border:1px solid #c6d4e5; box-shadow:0 10px 28px rgba(21,42,73,.06); }
        .topic-heading { color:var(--text); font-size:1.68rem; line-height:1.18; font-weight:900; letter-spacing:-.03em; margin-bottom:.45rem; }
        .workflow-strip { display:flex; gap:.5rem; flex-wrap:wrap; margin:.75rem 0 0; }
        .workflow-step { border-radius:999px; padding:.4rem .68rem; background:#e1eaf5; border:1px solid #bfd0e4; color:#234f7d; font-size:.82rem; font-weight:760; }
        .section-card { border-radius:18px; padding:.92rem 1rem; margin-bottom:.78rem; background:var(--panel); border:1px solid var(--line); box-shadow:0 5px 17px rgba(21,42,73,.06); }
        .section-card h4 { margin:0 0 .42rem; color:var(--text); font-size:1rem; font-weight:850; }
        .section-card p, .section-card li { color:#35465b; line-height:1.54; font-size:.95rem; }
        .section-card ul { margin:.42rem 0 0 1.05rem; padding:0; }
        .two-card-grid { display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:.8rem; margin-bottom:.2rem; }
        .callout-good { border-color:#adcec6; background:var(--teal-soft); }
        .callout-risk { border-color:#dfbf8f; background:var(--risk-soft); }
        .mission-card { border-radius:16px; padding:.9rem 1rem; margin:.85rem 0 .6rem; background:var(--panel); border:1px solid var(--line); }
        .mission-card-title { color:var(--text); font-size:.97rem; font-weight:850; margin-bottom:.35rem; }
        .mission-question { color:#35465b; line-height:1.48; }
        .save-panel { border-radius:18px; padding:1rem; background:#e1eaf5; border:1px solid #c1d1e3; margin-bottom:1rem; }
        .stAlert { border-radius:15px; } hr { border-color:#cbd6e3; }
        @media (max-width: 900px) { .two-card-grid { grid-template-columns:1fr; } .topic-heading { font-size:1.3rem; } .main-title { font-size:2rem; } }
        </style>
        """,
        unsafe_allow_html=True,
    )


# -----------------------------
# Run discovery
# -----------------------------
def find_latest_run(phase: Optional[str] = None) -> Optional[Path]:
    if not RUNS_DIR.exists():
        return None

    candidates = []
    for run_dir in RUNS_DIR.iterdir():
        if not run_dir.is_dir():
            continue

        state_path = run_dir / "run_state.json"
        if not state_path.exists():
            continue

        try:
            state = load_json(state_path)
        except Exception:
            continue

        if phase is None or state.get("phase") == phase:
            candidates.append(run_dir)

    if not candidates:
        return None

    return sorted(candidates, key=lambda p: p.name)[-1]


def topic_status_map(progress_rows: List[Dict[str, str]]) -> Dict[str, str]:
    return {str(row.get("topic_id", "")): str(row.get("status", "")) for row in progress_rows}


def is_stale_awaiting_run(
    run_dir: Optional[Path],
    progress_rows: List[Dict[str, str]],
    rewards_state: Optional[Dict[str, Any]] = None,
) -> bool:
    """Ignore active run cache when durable mastery says the topic is already done.

    V2.3 rule: best mastery wins. A stale local awaiting run for a topic that
    already has best_stars >= 3 must not hijack the Current Level screen.
    A genuine active repair for a topic below mastery is still allowed.
    """
    if run_dir is None:
        return False
    try:
        state = load_json(run_dir / "run_state.json")
    except Exception:
        return False
    topic_id = str(state.get("topic_id") or "")
    phase = str(state.get("phase") or "")
    if phase != "awaiting_user_answers" or not topic_id:
        return False

    row = next((r for r in progress_rows if str(r.get("topic_id") or "") == topic_id), None)
    if row and v23_is_mastered(row, rewards_state):
        return True

    # Older logic fallback for legacy rows without best_stars/reward state.
    return topic_status_map(progress_rows).get(topic_id) == "completed"


def get_latest_evaluation_run() -> Optional[Path]:
    local_run = find_latest_run("evaluation_complete")
    if local_run is not None:
        return local_run
    return sync_latest_evaluation_from_supabase()


def get_history_entry_for_run(run_id: str) -> Optional[Dict[str, Any]]:
    history = load_run_history()
    matches = [row for row in history if row.get("run_id") == run_id]
    if not matches:
        return None
    return matches[-1]


# -----------------------------
# Runtime execution
# -----------------------------
def run_module(
    module_name: str,
    args: Optional[List[str]] = None,
    env_extra: Optional[Dict[str, str]] = None,
) -> tuple[bool, str]:
    cmd = [sys.executable, "-m", module_name]
    if args:
        cmd.extend(args)

    env = os.environ.copy()
    openai_key = get_secret_value("OPENAI_API_KEY", None)
    if openai_key and "OPENAI_API_KEY" not in env:
        env["OPENAI_API_KEY"] = str(openai_key)
    if env_extra:
        env.update(env_extra)

    result = subprocess.run(
        cmd,
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=env,
    )
    ok = result.returncode == 0
    output = (result.stdout or "") + ("\n" + result.stderr if result.stderr else "")
    return ok, output.strip()


def start_lesson_for_topic(topic_id: Optional[str] = None, allow_completed_restart: bool = False) -> tuple[bool, str]:
    env_extra = None
    if allow_completed_restart:
        env_extra = {
            "ML_OS_ALLOW_RESTART_COMPLETED": "true",
            "ML_OS_REDO_MODE": "true",
        }
    if topic_id:
        return run_module("src.start_lesson", args=["--topic_id", topic_id], env_extra=env_extra)
    return run_module("src.start_lesson", env_extra=env_extra)


def save_answers(answer_path: Path, data: Dict[str, Any]) -> None:
    answer_path.parent.mkdir(parents=True, exist_ok=True)
    answer_path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


# -----------------------------
# Review / Redo helpers
# -----------------------------
def fetch_topic_runs_for_review(topic_id: str, limit: int = 30) -> List[Dict[str, Any]]:
    """Fetch run history for a topic from Supabase, with local runtime fallback."""
    rows: List[Dict[str, Any]] = []
    try:
        client = get_supabase_client()
        if client is not None:
            result = (
                client.table("mlos_runs")
                .select("run_id, topic_id, topic_title, phase, status, created_at, updated_at")
                .eq("topic_id", topic_id)
                .order("created_at", desc=True)
                .limit(limit)
                .execute()
            )
            rows = getattr(result, "data", None) or []
    except Exception:
        rows = []

    seen = {row.get("run_id") for row in rows}
    if RUNS_DIR.exists():
        local_rows: List[Dict[str, Any]] = []
        for run_dir in RUNS_DIR.iterdir():
            state_path = run_dir / "run_state.json"
            if not state_path.exists():
                continue
            try:
                state = load_json(state_path)
            except Exception:
                continue
            if state.get("topic_id") != topic_id:
                continue
            run_id = state.get("run_id") or run_dir.name
            if run_id in seen:
                continue
            local_rows.append(
                {
                    "run_id": run_id,
                    "topic_id": topic_id,
                    "topic_title": state.get("topic_name") or topic_id,
                    "phase": state.get("phase"),
                    "status": state.get("status"),
                    "created_at": None,
                    "updated_at": None,
                    "source": "local_runtime",
                }
            )
        rows.extend(sorted(local_rows, key=lambda item: str(item.get("run_id") or ""), reverse=True))

    return rows


def _artifact_payload_map_from_supabase(run_id: str) -> Dict[str, Any]:
    try:
        rows = fetch_run_artifacts(run_id)
    except Exception:
        rows = []
    payloads: Dict[str, Any] = {}
    for row in rows or []:
        artifact_type = row.get("artifact_type")
        if not artifact_type:
            continue
        payloads[artifact_type] = row.get("payload") if row.get("payload") is not None else row.get("text_payload")
    return payloads


def _artifact_payload_map_from_local(run_id: str) -> Dict[str, Any]:
    run_dir = RUNS_DIR / run_id
    payloads: Dict[str, Any] = {}
    if not run_dir.exists():
        return payloads

    local_files = {
        "run_state": run_dir / "run_state.json",
        "selected_topic": run_dir / "selected_topic.json",
        "concept_note": run_dir / "concept_note.json",
        "architect_note": run_dir / "architect_note.json",
        "assessment": run_dir / "assessment.json",
        "evaluation": run_dir / "evaluation.json",
        "answer_coaching": run_dir / "answer_coaching.json",
        "practice_result": run_dir / "practice_result.json",
        "capstone_deliverables": run_dir / "capstone_deliverables.json",
    }
    for artifact_type, file_path in local_files.items():
        if file_path.exists():
            try:
                payloads[artifact_type] = load_json(file_path)
            except Exception:
                pass

    state = payloads.get("run_state") or {}
    answer_rel = ((state.get("artifacts") or {}).get("answers"))
    if answer_rel:
        answer_path = PROJECT_ROOT / answer_rel
        if answer_path.exists():
            try:
                payloads["answers"] = load_json(answer_path)
            except Exception:
                pass
    return payloads


def load_review_payloads(run_id: str) -> Dict[str, Any]:
    payloads = _artifact_payload_map_from_supabase(run_id)
    local_payloads = _artifact_payload_map_from_local(run_id)
    for key, value in local_payloads.items():
        payloads.setdefault(key, value)
    return payloads


def _score_average(scores: Dict[str, Any]) -> Optional[float]:
    vals = []
    for key in ["conceptual_clarity", "practical_reasoning", "architect_reasoning", "communication", "coding_correctness"]:
        value = scores.get(key)
        if value is None:
            continue
        try:
            vals.append(float(value))
        except Exception:
            continue
    if not vals:
        return None
    return sum(vals) / len(vals)


def _format_run_option(row: Dict[str, Any]) -> str:
    run_id = str(row.get("run_id") or "-")
    phase = str(row.get("phase") or "-")
    status = str(row.get("status") or "-")
    created = str(row.get("created_at") or "local")
    return f"{created} · {status} · {phase} · {run_id}"


def render_review_payloads(payloads: Dict[str, Any]) -> None:
    evaluation = payloads.get("evaluation") or {}
    answers_doc = payloads.get("answers") or payloads.get("answer_template") or {}
    coaching_doc = payloads.get("answer_coaching") or {}
    concept_note = payloads.get("concept_note") or {}
    architect_note = payloads.get("architect_note") or {}

    if evaluation:
        st.markdown("### Evaluation")
        decision = str(evaluation.get("decision", "-")).upper()
        avg = _score_average(evaluation.get("scores", {}) or {})
        if avg is not None:
            st.caption(f"Decision: {decision} · Average score: {avg:.2f}")
        else:
            st.caption(f"Decision: {decision}")
        render_score_cards(evaluation)

        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Strengths**")
            for item in evaluation.get("strengths", []) or []:
                st.markdown(f"- {item}")
        with c2:
            st.markdown("**Weak spots**")
            for item in evaluation.get("weak_spots", []) or []:
                st.markdown(f"- {item}")

        if evaluation.get("refined_architect_summary"):
            st.markdown("**Refined architect summary**")
            st.info(evaluation.get("refined_architect_summary"))
    else:
        st.info("No final evaluation found for this run yet.")

    st.divider()
    st.markdown("### Answers + Coaching")
    answers_by_q = {item.get("question_id"): item for item in answers_doc.get("answers", []) or []}
    coaching_items = (coaching_doc.get("coaching") or []) if isinstance(coaching_doc, dict) else []
    coaching_by_q = {item.get("question_id"): item for item in coaching_items if isinstance(item, dict)}

    if not answers_by_q and not coaching_by_q:
        st.info("No answer/coaching artifacts found for this run.")
    else:
        qids = sorted(set(answers_by_q) | set(coaching_by_q))
        for qid in qids:
            answer_item = answers_by_q.get(qid, {})
            coaching = coaching_by_q.get(qid, {})
            question = answer_item.get("question") or coaching.get("question") or qid
            with st.expander(f"{qid} · {question}", expanded=False):
                answer = answer_item.get("answer") or coaching.get("your_answer") or ""
                st.markdown("**Your answer**")
                st.write(answer if answer else "-")

                if coaching:
                    quality = coaching.get("answer_quality") or coaching.get("quality_label") or "-"
                    st.markdown(f"**Coaching verdict:** {str(quality).upper()}")
                    missing = coaching.get("what_was_missing") or coaching.get("missing") or []
                    if missing:
                        st.markdown("**What was missing**")
                        for item in missing:
                            st.markdown(f"- {item}")
                    better = coaching.get("better_answer") or coaching.get("stronger_answer")
                    if better:
                        st.markdown("**Stronger sample answer**")
                        st.info(str(better))
                    upgrade = coaching.get("architect_upgrade")
                    if upgrade:
                        st.markdown("**Architect upgrade**")
                        st.write(str(upgrade))

    st.divider()
    capstone_pack = payloads.get("capstone_deliverables") or {}
    if capstone_pack:
        st.divider()
        st.markdown("### Capstone Artifact Pack")
        st.caption(
            f"Sections completed: {capstone_pack.get('sections_completed', 0)}/{capstone_pack.get('sections_required', 5)}"
        )
        for section_name, section_text in (capstone_pack.get("sections") or {}).items():
            with st.expander(section_name.replace("_", " ").title(), expanded=False):
                st.write(section_text or "-")
        st.markdown("**Required deliverables represented by this pack**")
        for artifact in capstone_pack.get("required_artifacts", []) or []:
            st.markdown(f"- {artifact}")

    with st.expander("Lesson artifacts", expanded=False):
        if concept_note:
            st.markdown("**Concept note**")
            st.json(concept_note)
        if architect_note:
            st.markdown("**Architect note**")
            st.json(architect_note)


def render_review_redo_tab(progress_rows: List[Dict[str, str]], awaiting_run: Optional[Path], rewards_state: Dict[str, Any]) -> None:
    st.subheader("Review / Redo")
    st.caption("Review completed attempts or deliberately start a new attempt for a completed topic. Redo never erases history and rewards keep the best completed attempt.")

    if not progress_rows:
        st.info("No topics available.")
        return

    completed_rows = [
        row for row in progress_rows
        if row.get("topic_id") and v23_display_status(row, rewards_state) in {"completed", "needs_attention"}
    ]
    if not completed_rows:
        st.info("No reviewed or repairable lessons are available yet.")
        return

    topic_options = [row.get("topic_id") for row in completed_rows if row.get("topic_id")]
    default_topic = st.session_state.get("review_topic_id") or (topic_options[0] if topic_options else None)
    if default_topic not in topic_options and topic_options:
        default_topic = topic_options[0]

    topic_label_map = {
        row.get("topic_id"): f"{row.get('topic_id')} · {row.get('title')} · {v23_display_status(row, rewards_state)}"
        for row in completed_rows
        if row.get("topic_id")
    }
    selected_topic_id = st.selectbox(
        "Topic",
        options=topic_options,
        index=topic_options.index(default_topic) if default_topic in topic_options else 0,
        format_func=lambda tid: topic_label_map.get(tid, tid),
    )
    st.session_state.review_topic_id = selected_topic_id

    topic_row = next((row for row in completed_rows if row.get("topic_id") == selected_topic_id), {})
    status = v23_display_status(topic_row, rewards_state)
    topic_reward = get_topic_reward_state(rewards_state, selected_topic_id)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Status", status or "-")
    c2.metric("Attempts", topic_row.get("attempt_count", "-"))
    c3.metric("Best Stars", topic_reward.get("best_stars", 0))
    c4.metric("Latest Stars", topic_reward.get("latest_stars", topic_reward.get("best_stars", 0)))

    st.markdown("### Start a redo attempt")
    if awaiting_run is not None:
        active_state = load_json(awaiting_run / "run_state.json")
        st.warning(f"Finish the active lesson first: {active_state.get('topic_id')} · {active_state.get('run_id')}")
    elif status == "needs_attention":
        st.caption("This starts a repair attempt for a topic below mastery. It does not erase history.")
        if st.button(f"Start Repair Attempt · {selected_topic_id}", use_container_width=True, type="primary"):
            with st.spinner(f"Starting repair attempt for {selected_topic_id}..."):
                ok, output = start_lesson_for_topic(selected_topic_id, allow_completed_restart=False)
            record_action_result("Start Repair Attempt", ok, output)
            if ok:
                st.rerun()
    else:
        st.caption("This creates a fresh run for the same topic. It does not erase the old attempt. XP/rewards only improve if the new completed attempt beats the previous best.")
        if st.button(f"Start Redo Attempt · {selected_topic_id}", use_container_width=True, type="secondary"):
            with st.spinner(f"Starting redo attempt for {selected_topic_id}..."):
                ok, output = start_lesson_for_topic(selected_topic_id, allow_completed_restart=True)
            record_action_result("Start Redo Attempt", ok, output)
            if ok:
                st.rerun()

    st.divider()
    st.markdown("### Attempt history")
    topic_runs = fetch_topic_runs_for_review(selected_topic_id)
    if not topic_runs:
        st.info("No runs found for this topic yet.")
        return

    run_ids = [row.get("run_id") for row in topic_runs if row.get("run_id")]
    selected_run_id = st.selectbox(
        "Run",
        options=run_ids,
        format_func=lambda rid: _format_run_option(next((row for row in topic_runs if row.get("run_id") == rid), {"run_id": rid})),
    )
    payloads = load_review_payloads(selected_run_id)
    render_review_payloads(payloads)


def persist_mission_draft_to_supabase(run_state: Dict[str, Any], topic_id: str, answers_doc: Dict[str, Any]) -> None:
    """Persist draft answers durably so Streamlit sleep does not wipe work."""
    try:
        upsert_artifact(
            run_id=run_state["run_id"],
            artifact_type="answers",
            topic_id=topic_id,
            payload=answers_doc,
        )
        append_event(
            event_type="answers_saved",
            run_id=run_state["run_id"],
            topic_id=topic_id,
            payload={"answer_count": len(answers_doc.get("answers", [])), "source": "mission_tab_save"},
        )
    except Exception:
        pass




def persist_practice_submission_to_supabase(
    run_state: Dict[str, Any],
    topic_id: str,
    practice_submission: Dict[str, Any],
    practice_result: Optional[Dict[str, Any]] = None,
) -> None:
    """Persist Code Lab work durably so Streamlit sleep does not wipe it."""
    try:
        upsert_artifact(
            run_id=run_state["run_id"],
            artifact_type="practice_submission",
            topic_id=topic_id,
            payload=practice_submission,
        )
        if practice_result is not None:
            upsert_artifact(
                run_id=run_state["run_id"],
                artifact_type="practice_result",
                topic_id=topic_id,
                payload=practice_result,
            )
        append_event(
            event_type="practice_submission_saved",
            run_id=run_state["run_id"],
            topic_id=topic_id,
            payload={
                "exercise_id": practice_submission.get("exercise_id"),
                "has_result": practice_result is not None,
            },
        )
    except Exception:
        pass

def _runtime_task_meta(learning_design: Optional[Dict[str, Any]], item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    return runtime_task_for_question(
        learning_design,
        str(item.get("question_id", "")),
        str(item.get("question", "")),
    )


def render_answer_pressure(question_type: str, answer_text: str, task_meta: Optional[Dict[str, Any]] = None) -> None:
    words = len((answer_text or "").split())
    minimum = int((task_meta or {}).get("target_min_words", 45))
    maximum = int((task_meta or {}).get("target_max_words", 105))
    shape = str((task_meta or {}).get("response_shape", "Answer the exact question directly and show your reasoning."))
    if words == 0:
        st.caption(f"Response shape: {shape} Target: {minimum}-{maximum} words.")
        return
    if words > maximum + 30:
        st.warning(f"{words} words. The evidence needed here should fit in {minimum}-{maximum} words. Cut repetition.")
    elif words > maximum:
        st.caption(f"{words} words. Slightly long for this evidence task; tighten repeated explanation.")
    elif words < minimum:
        st.caption(f"{words} words. Check that you demonstrated: {shape}")
    else:
        st.caption(f"{words} words. Within the range for this evidence task.")


def render_writing_assist_panel(question_type: str, answer_text: str, task_meta: Optional[Dict[str, Any]] = None) -> None:
    """Low-risk language assist. It must not become a hidden scoring rubric."""
    analysis = analyze_answer_text(answer_text, question_type)
    if not answer_text:
        return

    minimum = int((task_meta or {}).get("target_min_words", analysis.get("target_min", 45)))
    maximum = int((task_meta or {}).get("target_max_words", analysis.get("target_max", 105)))
    word_count = analysis.get("word_count", 0)

    with st.expander("Writing assist . language and technical precision", expanded=analysis.get("has_language_noise", False)):
        if minimum <= word_count <= maximum:
            st.success(f"Length: {word_count} words. Suggested range for this task: {minimum}-{maximum}.")
        elif word_count > maximum:
            st.warning(f"Length: {word_count} words. Suggested range for this task: {minimum}-{maximum}. Remove repeated explanation, not necessary evidence.")
        else:
            st.info(f"Length: {word_count} words. Suggested range for this task: {minimum}-{maximum}. Check whether the required reasoning is present.")

        suggestions = analysis.get("spelling_suggestions", []) or []
        if suggestions:
            st.markdown("**Possible spelling fixes**")
            for item in suggestions:
                st.markdown(f"- `{item.get('original')}` → `{item.get('suggestion')}`")
        else:
            st.caption("No common spelling hints detected.")

        hints = analysis.get("technical_precision_hints", []) or []
        if hints:
            st.markdown("**Technical wording hints**")
            for hint in hints:
                st.info(str(hint))

        st.caption("Length is guidance only. Evaluation should score the reasoning demonstrated for this task, not vocabulary or essay size.")


def load_relative_json_or_none(relative_path: Optional[str]) -> Optional[Dict[str, Any]]:
    if not relative_path:
        return None
    path = PROJECT_ROOT / relative_path
    if not path.exists():
        return None
    try:
        data = load_json(path)
        return data if isinstance(data, dict) else None
    except Exception:
        return None


def render_practice_result_summary(result: Dict[str, Any]) -> None:
    summary = result.get("summary", {}) or {}
    if summary.get("passed"):
        st.success(
            f"Code tests passed: {summary.get('total_passed', 0)}/{summary.get('total_tests', 0)}."
        )
    else:
        st.error(
            f"Code tests not cleared: {summary.get('total_passed', 0)}/{summary.get('total_tests', 0)}."
        )
        if result.get("error"):
            st.code(result.get("error"))

    diagnostics = result.get("diagnostics", {}) or {}
    failed_categories = diagnostics.get("failed_categories", []) or []
    diagnostic_hints = diagnostics.get("hints", []) or []
    if failed_categories:
        st.markdown("**Failed skill areas**")
        for category in failed_categories:
            st.warning(str(category))
    if diagnostic_hints:
        st.markdown("**Debug hints**")
        for hint in diagnostic_hints:
            st.info(str(hint))

    visible_rows = []
    for item in result.get("visible_tests", []) or []:
        row = {
            "test": item.get("name"),
            "passed": item.get("passed"),
            "scenario": item.get("scenario") or item.get("reason"),
            "skill": item.get("concept_tag") or item.get("failure_category"),
            "hint_if_failed": "" if item.get("passed") else item.get("failure_hint", ""),
        }
        if item.get("show_expected", True):
            row["expected"] = item.get("expected")
        if item.get("show_actual", True):
            row["actual"] = item.get("actual")
        if not item.get("passed") and item.get("error"):
            row["error"] = item.get("error")
        visible_rows.append(row)

    if visible_rows:
        st.markdown("**Visible test results**")
        st.dataframe(visible_rows, use_container_width=True)

    hidden_total = summary.get("hidden_total", 0)
    if hidden_total:
        hidden_rows = []
        for idx, item in enumerate(result.get("hidden_tests", []) or [], start=1):
            hidden_rows.append(
                {
                    "hidden_test": idx,
                    "passed": item.get("passed"),
                    "failed_skill": "" if item.get("passed") else (item.get("failure_category") or item.get("concept_tag")),
                    "diagnostic_hint": "" if item.get("passed") else item.get("failure_hint", ""),
                }
            )
        st.markdown("**Hidden diagnostic results**")
        st.caption(
            "Hidden tests do not reveal inputs, expected outputs, or final answers. They show the failed skill area only."
        )
        st.dataframe(hidden_rows, use_container_width=True)

    interpretation = result.get("interpretation", {}) or {}
    st.markdown("**Interpretation check**")
    st.write(f"Score: {interpretation.get('score', '-')}/5")
    missing = interpretation.get("missing_focus", []) or []
    if missing:
        st.warning("Missing interpretation focus: " + ", ".join(str(item) for item in missing))


# -----------------------------
# Action output and run diagnostics
# -----------------------------
def record_action_result(action: str, ok: bool, output: str) -> None:
    st.session_state["last_action"] = action
    st.session_state["last_action_ok"] = ok
    st.session_state["last_action_output"] = output or "No output returned."


def render_last_action_result() -> None:
    if "last_action_output" not in st.session_state:
        return

    ok = bool(st.session_state.get("last_action_ok", False))
    action = st.session_state.get("last_action", "Last action")
    output = st.session_state.get("last_action_output", "")

    with st.expander(f"Last Action Output . {action}", expanded=not ok):
        if ok:
            st.success(f"{action} completed.")
        else:
            st.error(f"{action} failed.")
        st.code(output)


def list_run_dirs() -> List[Path]:
    if not RUNS_DIR.exists():
        return []
    return sorted(
        [p for p in RUNS_DIR.iterdir() if p.is_dir() and (p / "run_state.json").exists()],
        key=lambda p: p.name,
        reverse=True,
    )


def load_json_or_none(path: Path) -> Optional[Dict[str, Any]]:
    if not path.exists():
        return None
    try:
        return load_json(path)
    except Exception:
        return None


def load_text_or_empty(path: Path) -> str:
    if not path.exists():
        return ""
    try:
        return load_text(path)
    except Exception as exc:
        return f"Could not read {path.name}: {exc}"


def render_json_file(label: str, path: Path) -> None:
    data = load_json_or_none(path)
    with st.expander(label, expanded=False):
        if data is None:
            st.info(f"Missing or unreadable: {path}")
        else:
            st.json(data)


def render_text_file(label: str, path: Path) -> None:
    text = load_text_or_empty(path)
    with st.expander(label, expanded=False):
        if not text:
            st.info(f"Missing or empty: {path}")
        else:
            st.code(text)


def render_run_details() -> None:
    run_dirs = list_run_dirs()
    if not run_dirs:
        st.info("No run directories found yet.")
        return

    options = [p.name for p in run_dirs]
    selected_name = st.selectbox("Select run", options=options, index=0)
    run_dir = RUNS_DIR / selected_name

    state = load_json_or_none(run_dir / "run_state.json") or {}
    phase = state.get("phase", "unknown")
    status = state.get("status", "unknown")
    topic = state.get("topic_id", "unknown")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Run", selected_name)
    c2.metric("Topic", topic)
    c3.metric("Phase", phase)
    c4.metric("Status", status)

    st.markdown("### Run Files")
    render_json_file("run_state.json", run_dir / "run_state.json")
    render_text_file("logs.txt", run_dir / "logs.txt")
    render_json_file("selected_topic.json", run_dir / "selected_topic.json")
    render_json_file("concept_note.json", run_dir / "concept_note.json")
    render_json_file("architect_note.json", run_dir / "architect_note.json")
    render_json_file("assessment.json", run_dir / "assessment.json")
    render_json_file("answers.json", run_dir / "answers.json")
    render_json_file("evaluation.json", run_dir / "evaluation.json")
    render_json_file("answer_coaching.json", run_dir / "answer_coaching.json")
    render_json_file("rewards.json", run_dir / "rewards.json")



# -----------------------------
# Metrics and gamification
# -----------------------------
def to_int(value: Any) -> Optional[int]:
    try:
        if value is None or str(value).strip() == "":
            return None
        return int(value)
    except Exception:
        return None


def compute_topic_average_score(row: Dict[str, str]) -> Optional[float]:
    score_fields = [
        "last_score_conceptual",
        "last_score_practical",
        "last_score_architect",
        "last_score_communication",
    ]
    values = [to_int(row.get(field)) for field in score_fields]
    values = [v for v in values if v is not None]

    if not values:
        return None

    return sum(values) / len(values)


def star_string(avg_score: Optional[float]) -> str:
    if avg_score is None:
        return "☆☆☆☆☆"

    filled = max(0, min(5, round(avg_score)))
    return "★" * filled + "☆" * (5 - filled)


def status_chip(status: str) -> str:
    mapping = {
        "locked": "🔒 Locked",
        "not_started": "🟦 Unlocked",
        "unlocked": "🟦 Unlocked",
        "needs_attention": "🟥 Needs Attention",
        "in_progress": "🟨 In Progress",
        "completed": "🟩 Mastered",
        "borderline": "🟧 Borderline",
        "revise": "🟥 Revise",
    }
    return mapping.get(status, status)


def _int_or_none(value: Any) -> Optional[int]:
    value = str(value or "").strip()
    if not value:
        return None
    try:
        return int(value)
    except Exception:
        return None


def topic_needs_attention(row: Dict[str, str], rewards_state: Optional[Dict[str, Any]] = None) -> bool:
    """Flag completed or revised topics where the learner should revisit the skill.

    Needs Attention should not mean only current status='revise'. A completed
    2-star/borderline lesson with practical=2 still needs attention.
    """
    status = v23_display_status(row, rewards_state)
    if status == "needs_attention":
        return True
    if status not in {"completed", "borderline"}:
        return False

    score_fields = [
        "last_score_conceptual",
        "last_score_practical",
        "last_score_architect",
        "last_score_communication",
        "last_score_coding",
    ]
    scores = [_int_or_none(row.get(field)) for field in score_fields]
    present_scores = [score for score in scores if score is not None]
    if any(score < 3 for score in present_scores):
        return True

    if rewards_state:
        topic_reward = get_topic_reward_state(rewards_state, row.get("topic_id", ""))
        best_stars = topic_reward.get("best_stars")
        if isinstance(best_stars, int) and 0 < best_stars < 3:
            return True

    return False


def compute_overall_metrics(progress_rows: List[Dict[str, str]], rewards_state: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    completed = sum(1 for row in progress_rows if v23_display_status(row, rewards_state) == "completed")
    borderline = sum(1 for row in progress_rows if v23_display_status(row, rewards_state) == "borderline")
    revise = sum(1 for row in progress_rows if v23_display_status(row, rewards_state) in {"revise", "needs_attention"})
    needs_attention_rows = [row for row in progress_rows if topic_needs_attention(row, rewards_state)]
    unlocked = sum(
        1
        for row in progress_rows
        if row.get("prerequisites_unlocked", "").lower() == "true"
        and v23_display_status(row, rewards_state) != "completed"
    )
    locked = sum(1 for row in progress_rows if v23_display_status(row, rewards_state) == "locked")

    all_scores = []
    for row in progress_rows:
        avg = compute_topic_average_score(row)
        if avg is not None:
            all_scores.append(avg)

    overall_avg = round(sum(all_scores) / len(all_scores), 2) if all_scores else None

    return {
        "completed": completed,
        "borderline": borderline,
        "revise": revise,
        "needs_attention": len(needs_attention_rows),
        "needs_attention_topics": [row.get("topic_id") for row in needs_attention_rows],
        "unlocked": unlocked,
        "locked": locked,
        "overall_avg": overall_avg,
    }

def compute_display_stars(row: Dict[str, str], rewards_state: Dict[str, Any]) -> str:
    topic_reward = get_topic_reward_state(rewards_state, row["topic_id"])
    best_stars = topic_reward.get("best_stars")
    if isinstance(best_stars, int) and best_stars > 0:
        return "★" * best_stars + "☆" * (5 - best_stars)

    avg_score = compute_topic_average_score(row)
    return star_string(avg_score)


def badge_label_for_topic(row: Dict[str, str], rewards_state: Dict[str, Any]) -> str:
    topic_reward = get_topic_reward_state(rewards_state, row["topic_id"])
    last_badges = topic_reward.get("last_badges", [])

    if row["status"] == "locked":
        return "🔒 Locked"
    if last_badges:
        return f"🏅 {last_badges[-1]}"

    avg_score = compute_topic_average_score(row)
    if avg_score is None:
        return "🟦 Available"
    if avg_score >= 4.5:
        return "💎 Diamond"
    if avg_score >= 4.0:
        return "🥇 Gold"
    if avg_score >= 3.0:
        return "🥈 Silver"
    if avg_score >= 2.0:
        return "🥉 Bronze"
    return "🪨 Starter"


def badge_to_label(badge: Any) -> str:
    if isinstance(badge, dict):
        return str(badge.get("label") or badge.get("id") or "").strip()
    return str(badge or "").strip()


def badge_to_description(badge: Any) -> str:
    if isinstance(badge, dict):
        return str(badge.get("description") or "").strip()
    return ""


def flatten_badges(badges: Any) -> str:
    if not badges:
        return ""
    if isinstance(badges, dict):
        badges = [badges]
    if not isinstance(badges, list):
        return str(badges)
    labels = [badge_to_label(item) for item in badges]
    return ", ".join(label for label in labels if label)


def reward_history_display_rows(reward_history: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for item in reward_history:
        rows.append(
            {
                "run_id": item.get("run_id"),
                "topic_id": item.get("topic_id"),
                "topic_title": item.get("topic_title"),
                "decision": item.get("decision"),
                "completed": item.get("completed", item.get("decision") in {"pass", "borderline"}),
                "xp_earned": item.get("xp_earned"),
                "total_xp": item.get("total_xp"),
                "stars_earned": item.get("stars_earned"),
                "best_stars": item.get("best_stars"),
                "badges_awarded": flatten_badges(item.get("badges_awarded", [])),
                "current_streak": item.get("current_completion_streak"),
                "best_streak": item.get("best_completion_streak"),
            }
        )
    return rows


# -----------------------------
# Notes lookup
# -----------------------------
def find_note_file(folder: Path, topic_id: str) -> Optional[Path]:
    if not folder.exists():
        return None

    candidates = sorted(folder.glob(f"{topic_id}*"))
    return candidates[0] if candidates else None


# -----------------------------
# UI render helpers
# -----------------------------
def render_score_cards(evaluation: Dict[str, Any]) -> None:
    scores = evaluation.get("scores", {})
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Conceptual", scores.get("conceptual_clarity", "-"))
    c2.metric("Practical", scores.get("practical_reasoning", "-"))
    c3.metric("Architect", scores.get("architect_reasoning", "-"))
    c4.metric("Communication", scores.get("communication", "-"))

def render_answer_coaching_panel(run_dir: Path) -> None:
    coaching_path = run_dir / "answer_coaching.json"

    if not coaching_path.exists():
        st.info("No question-level answer coaching found for this run. Re-evaluate a lesson to generate it.")
        return

    answer_coaching = load_json(coaching_path)
    coaching_items = answer_coaching.get("coaching", [])

    if not coaching_items:
        st.info("No answer coaching entries found.")
        return

    st.markdown("### Coaching by Question")
    st.caption("Better answers are shown only after final evaluation. They are samples for learning, not text to resubmit unchanged.")

    for item in coaching_items:
        qid = item.get("question_id", "")
        question = item.get("question", "")
        quality = item.get("answer_quality", "partial")

        with st.expander(f"{qid} . {quality.upper()} . {question}", expanded=False):
            st.markdown("**Your Answer**")
            st.write(item.get("your_answer", ""))

            findings = item.get("evidence_bound_findings", []) or []
            if findings:
                st.markdown("**Evidence-bound Findings**")
                for finding in findings:
                    st.warning(
                        f"Evidence: `{finding.get('evidence', '')}`  \n"
                        f"Issue: {finding.get('issue', '')}  \n"
                        f"Correction: {finding.get('correction', '')}"
                    )

            st.markdown("**What Was Missing**")
            missing_items = item.get("what_was_missing", [])
            if missing_items:
                for missing in missing_items:
                    st.markdown(f"- {missing}")
            else:
                st.write("-")

            with st.expander("Show stronger sample answer", expanded=False):
                st.success(item.get("better_answer", ""))

            st.markdown("**Why This Is Better**")
            st.write(item.get("why_this_is_better", ""))

            st.markdown("**Architect Upgrade**")
            st.info(item.get("architect_upgrade", ""))


def render_draft_verification_panel(verification: Dict[str, Any]) -> None:
    summary = verification.get("summary", {})
    is_guardrail = str(verification.get("mode", "")).startswith("evidence_guardrail")

    st.markdown("### Draft Guardrail" if is_guardrail else "### Draft Verification")
    if is_guardrail:
        st.caption("This checks for empty responses and known technical/unsafe claims. It does not predict stars or reward keywords.")
        c1, c2 = st.columns(2)
        c1.metric("Blocking Issues", summary.get("weak_count", 0))
        c2.metric("Responses Checked", len(verification.get("items", []) or []))
    else:
        st.caption("This is copy-safe guidance. It gives gaps and next actions, not final answers.")
        c1, c2, c3 = st.columns(3)
        c1.metric("Readiness Avg", summary.get("readiness_average", summary.get("likely_average", "-")))
        c2.metric("Weak Drafts", summary.get("weak_count", "-"))
        c3.metric("Partial Drafts", summary.get("partial_count", "-"))
        st.caption("Readiness Avg is not a star prediction. Final scoring may be stricter after full evaluation.")

    recommendation = summary.get("recommendation", "")
    if summary.get("weak_count", 0):
        st.error(recommendation)
    elif is_guardrail:
        st.success(recommendation)
    elif summary.get("partial_count", 0):
        st.warning(recommendation)
    else:
        st.success(recommendation)

    for item in verification.get("items", []) or []:
        task = item.get("evidence_task", {}) or {}
        title = task.get("label", item.get("question_id", ""))
        issue_count = len(item.get("misconceptions", []) or []) + len(item.get("coverage_gaps", []) or [])
        exp_label = f"{item.get('question_id', '')} . {title}" + (f" . {issue_count} issue(s)" if issue_count else " . no blocking issue detected")
        with st.expander(exp_label, expanded=issue_count > 0):
            st.markdown("**Question**")
            st.write(item.get("question", ""))
            if task.get("response_shape"):
                st.caption("Evidence shape: " + str(task.get("response_shape")))

            misconceptions = item.get("misconceptions", []) or []
            if misconceptions:
                st.markdown("**Technical or unsafe claim to fix**")
                for finding in misconceptions:
                    st.warning(
                        f"Evidence: `{finding.get('evidence', '')}`  \n"
                        f"Issue: {finding.get('issue', '')}  \n"
                        f"Correction: {finding.get('correction', '')}"
                    )

            gaps = item.get("coverage_gaps", []) or []
            if gaps:
                st.markdown("**Action needed**")
                for gap in gaps:
                    st.markdown(f"- {gap}")

            writing = item.get("writing_assist", {}) or {}
            suggestions = writing.get("spelling_suggestions", []) or []
            hints = writing.get("technical_precision_hints", []) or []
            if suggestions or hints:
                st.markdown("**Language and precision assist**")
                for sug in suggestions[:5]:
                    st.markdown(f"- `{sug.get('original')}` → `{sug.get('suggestion')}`")
                for hint in hints[:3]:
                    st.info(str(hint))

            if not is_guardrail:
                st.markdown("**Next improvement**")
                st.info(item.get("next_improvement", ""))





def html_text(value: Any) -> str:
    return escape(str(value or ""))


def html_list(items: Any) -> str:
    if not items:
        return ""
    if not isinstance(items, list):
        items = [items]
    lis = "".join(f"<li>{html_text(item)}</li>" for item in items if str(item or "").strip())
    return f"<ul>{lis}</ul>" if lis else ""


def render_static_card(title: str, body: Any, css_class: str = "") -> None:
    content = ""
    if isinstance(body, list):
        content = html_list(body)
    else:
        content = f"<p>{html_text(body)}</p>" if str(body or "").strip() else "<p class='small-muted'>Not available.</p>"
    st.markdown(
        f"""
        <div class="section-card {css_class}">
            <h4>{html_text(title)}</h4>
            {content}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_topic_hero(run_state: Dict[str, Any], concept_note: Dict[str, Any], mission_types: List[str]) -> None:
    mission_chips = "".join(
        f"<span class='status-pill'>{html_text(item.replace('_', ' ').title())}</span>"
        for item in mission_types
    )
    st.markdown(
        f"""
        <div class="current-topic-hero">
            <div class="topic-kicker">{html_text(run_state.get('topic_id'))} . Current Level</div>
            <div class="topic-heading">{html_text(concept_note.get('title'))}</div>
            <div class="topic-subline">Complete the flow left to right: learn, bridge the concept to missions, check understanding, write and verify drafts, run practical work, then submit.</div>
            <div class="workflow-strip">
                <span class="workflow-step">1 Learn</span>
                <span class="workflow-step">2 Check It</span>
                <span class="workflow-step">3 MCQs</span>
                <span class="workflow-step">4 Evidence + Verify</span>
                <span class="workflow-step">5 Code Lab</span>
                <span class="workflow-step">6 Submit</span>
            </div>
            <div class="status-strip">{mission_chips}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_learning_brief(concept_note: Dict[str, Any], architect_note: Dict[str, Any]) -> None:
    st.markdown("### Learning Brief")
    st.caption("Read this first. The mission answers should reuse the logic, not copy the wording.")

    c1, c2 = st.columns(2)
    with c1:
        render_static_card("Concept", concept_note.get("simple_explanation", ""))
    with c2:
        render_static_card("Tiny Example", concept_note.get("tiny_example", ""))

    c1, c2 = st.columns(2)
    with c1:
        render_static_card("Wrong Mental Model", concept_note.get("wrong_mental_model", ""), "callout-risk")
    with c2:
        render_static_card("Correct Mental Model", concept_note.get("correct_mental_model", ""), "callout-good")

    c1, c2 = st.columns(2)
    with c1:
        render_static_card("Why It Matters", concept_note.get("why_it_matters", ""))
    with c2:
        render_static_card("Edge Case", concept_note.get("edge_case", ""))

    render_static_card("Three Takeaways", concept_note.get("three_takeaways", []))

    st.markdown("### Architect Lens")
    render_static_card("Architect Summary", architect_note.get("architect_summary", ""))
    c1, c2 = st.columns(2)
    with c1:
        render_static_card("Design Implications", architect_note.get("design_implications", []))
    with c2:
        render_static_card("Production Risks", architect_note.get("production_risks", []), "callout-risk")
    c1, c2 = st.columns(2)
    with c1:
        render_static_card("Common Mistakes", architect_note.get("common_mistakes", []))
    with c2:
        render_static_card("Interview Framing", architect_note.get("interview_framing", ""))



def render_topic_resources_panel(topic_id: str) -> None:
    """Show optional, Supabase-managed learning resources without making them assessment prerequisites."""
    resources = fetch_topic_resources(topic_id)
    if not resources:
        return

    with st.expander("Learn Further . Optional resources", expanded=False):
        st.caption("Use these when the in-app explanation is not enough. These links are optional and are not hidden assessment requirements.")
        for item in resources:
            rtype = str(item.get("resource_type", "resource")).replace("_", " ").title()
            primary = " · Recommended first" if item.get("is_primary") else ""
            minutes = item.get("estimated_minutes")
            time_note = f" · approx. {minutes} min" if minutes else ""
            st.markdown(f"**{rtype}{primary}**{time_note}")
            st.markdown(f"[{item.get('title', 'Open resource')}]({item.get('url', '')}) · {item.get('provider', '')}")
            if item.get("purpose"):
                st.caption(str(item.get("purpose")))
            st.divider()



def load_topic_learning_design(topic_id: str) -> Optional[Dict[str, Any]]:
    """Supabase-authored design first; bundled design is a deploy-safe fallback.

    V2.3 enhances shallow designs at runtime so tutor depth matches assessment depth.
    """
    return enhance_learning_design(fetch_topic_learning_design(topic_id) or get_bundled_learning_design(topic_id))


def render_learning_design_panel(topic_id: str) -> bool:
    design = load_topic_learning_design(topic_id)
    if not design:
        return False

    st.markdown("### Learn")
    st.caption("Built from the learning objective first. Assessment asks only for the evidence taught here.")
    render_static_card("By the end of this lesson, you should be able to", design.get("learning_objective", ""), "callout-good")

    prerequisite = str(design.get("prerequisite_bridge", "")).strip()
    if prerequisite:
        with st.expander("Before this concept . quick bridge", expanded=False):
            st.write(prerequisite)

    st.markdown("#### Build the idea")
    for idx, step in enumerate(design.get("concept_steps", []) or [], start=1):
        render_static_card(f"{idx}. {step.get('heading', 'Step')}", step.get("body", ""))

    concept_map = design.get("concept_map", []) or []
    if concept_map:
        st.markdown("#### Concept map")
        st.caption("Use this to separate terms that are easy to confuse.")
        st.dataframe(concept_map, use_container_width=True, hide_index=True)

    example = design.get("worked_example", {}) or {}
    if example:
        st.markdown("#### Worked example")
        render_static_card("Scenario", example.get("scenario", ""), "callout-good")
        rows = example.get("rows", []) or []
        if rows:
            st.dataframe(rows, use_container_width=True, hide_index=True)
        if example.get("takeaway"):
            st.info(str(example.get("takeaway")))

    more_examples = design.get("worked_examples", []) or []
    if more_examples:
        st.markdown("#### Work through it")
        for example_idx, extra in enumerate(more_examples, start=1):
            title = extra.get('title') or extra.get('label') or 'Reasoning steps'
            with st.expander(f"Worked example {example_idx}: {title}", expanded=example_idx == 1):
                steps = extra.get("steps", []) or []
                if steps:
                    for step_idx, step in enumerate(steps, start=1):
                        st.markdown(f"**{step_idx}.** {step}")
                elif extra.get("body"):
                    st.write(extra.get("body"))

    code_bridge = design.get("code_bridge", {}) or {}
    if code_bridge:
        with st.expander("Code Lab bridge . read before coding", expanded=True):
            if code_bridge.get("idea"):
                render_static_card("What the code represents", code_bridge.get("idea"), "callout-good")
            algorithm = code_bridge.get("algorithm", []) or []
            if algorithm:
                st.markdown("**Algorithm in plain English**")
                for idx, item in enumerate(algorithm, start=1):
                    st.markdown(f"{idx}. {item}")
            if code_bridge.get("common_bug"):
                render_static_card("Common implementation bug", code_bridge.get("common_bug"), "callout-risk")

    repair_prompts = design.get("mastery_repair_prompts", []) or []
    if repair_prompts:
        with st.expander("If this still feels weak . repair prompts", expanded=False):
            for prompt in repair_prompts:
                st.markdown(f"- {prompt}")

    with st.expander("Common trap and architect extension", expanded=False):
        if design.get("misconception"):
            render_static_card("Do not conclude this", design.get("misconception"), "callout-risk")
        if design.get("architect_extension"):
            render_static_card("Architect extension", design.get("architect_extension"), "callout-good")
    return True


def render_evidence_task_overview(learning_design: Optional[Dict[str, Any]], assessment_doc: Dict[str, Any]) -> None:
    if not learning_design:
        return
    st.markdown("### Evidence tasks")
    st.caption("These are different proofs of understanding. They are not five copies of the same essay template.")
    questions = assessment_doc.get("questions", []) or []
    for idx, question in enumerate(questions, start=1):
        meta = runtime_task_for_question(learning_design, str(question.get("question_id", "")), str(question.get("question", "")))
        if not meta:
            continue
        with st.expander(f"Task {idx} . {meta.get('label', question.get('type', 'Evidence'))}", expanded=False):
            st.write(meta.get("purpose", ""))
            st.markdown(f"**Response shape:** {meta.get('response_shape', 'Answer directly.')}  ")
            st.caption(f"Suggested length: {meta.get('target_min_words', 45)}-{meta.get('target_max_words', 105)} words. Length is guidance, not the scoring rule.")
            focus = meta.get("expected_focus", []) or []
            if focus:
                st.markdown("**Evidence this task should reveal:** " + " · ".join(str(x) for x in focus))
            if meta.get("sample_answer"):
                with st.expander("See a 3-star sample answer after trying", expanded=False):
                    st.write(meta.get("sample_answer"))
            if meta.get("common_weak_answer"):
                st.caption("Common weak pattern: " + str(meta.get("common_weak_answer")))
    st.info(str(learning_design.get("assessment_principle", "")))


def render_tutor_narrative_panel(topic_id: str) -> bool:
    """Render one coherent lesson, while moving scoring detail out of the teaching flow."""
    narrative = get_tutor_narrative(topic_id)
    if not narrative:
        return False

    st.markdown("### Expert Tutor Lesson")
    st.caption("Learn the idea here once. Application and mission requirements are separated into their own tabs.")

    sections = narrative.get("sections", []) or []
    section_map = {str(section.get("heading", "")): section for section in sections}
    for heading in ["Start Here: The Intuition", "Slow Walkthrough: What Actually Changes", "Worked Example, Step by Step"]:
        section = section_map.get(heading)
        if section:
            style = str(section.get("style", "normal"))
            css_class = "callout-good" if style == "good" else "callout-risk" if style == "risk" else ""
            render_static_card(section.get("heading", "Section"), section.get("body", ""), css_class)

    quick_check = section_map.get("Pause and Check Yourself")
    if quick_check:
        render_static_card("Stop and Test Your Understanding", quick_check.get("body", ""), "callout-good")

    deeper_headings = [
        "Precise Definition",
        "Why This Concept Exists",
        "Unsafe vs Safe Pattern",
        "Nuances You Should Not Miss",
        "Common Traps",
        "Architect Translation",
        "System Design Controls",
    ]
    available_deeper = [section_map[h] for h in deeper_headings if h in section_map]
    if available_deeper:
        with st.expander("Architect depth and guardrails . Optional before missions", expanded=False):
            for section in available_deeper:
                style = str(section.get("style", "normal"))
                css_class = "callout-good" if style == "good" else "callout-risk" if style == "risk" else ""
                render_static_card(section.get("heading", "Section"), section.get("body", ""), css_class)
    return True


def render_booster_walkthrough(booster: Dict[str, Any]) -> None:
    learning_design = booster.get("learning_design") if isinstance(booster, dict) else None
    st.markdown("### Check It")
    st.caption("One diagnostic check before assessment. Use it to see whether the central idea has clicked.")

    prompt = booster.get("application_prompt", "")
    reveal = booster.get("application_reveal", "")
    if prompt:
        render_static_card("Think before revealing", prompt, "callout-good")
        with st.expander("Reveal the reasoning", expanded=False):
            st.write(reveal)
    else:
        render_static_card("Think before proceeding", booster.get("production_trap", ""), "callout-risk")

    if learning_design:
        st.caption("This check is not scored. The assessed evidence is shown only in the Missions tab.")
    else:
        with st.expander("Response scaffold . open only if stuck", expanded=False):
            answer_frame = booster.get("answer_frame", []) or []
            if answer_frame:
                render_static_card("Use this structure", answer_frame)


def render_mission_bridge(booster: Dict[str, Any], assessment_doc: Dict[str, Any]) -> None:
    learning_design = booster.get("learning_design") if isinstance(booster, dict) else None
    if learning_design:
        render_evidence_task_overview(learning_design, assessment_doc)
        return

    bridge_items = booster.get("mission_bridge", []) or []
    questions = assessment_doc.get("questions", []) or []
    if not bridge_items and not questions:
        return
    st.markdown("### Mission Requirements")
    st.caption("Open the requirement for the mission you are answering.")
    bridge_by_type = {str(item.get("mission_type", "")): item for item in bridge_items if isinstance(item, dict)}
    for idx, question in enumerate(questions, start=1):
        qtype = str(question.get("type", "mission"))
        bridge = bridge_by_type.get(qtype, {})
        with st.expander(f"Mission {idx} . {qtype.replace('_', ' ').title()}", expanded=False):
            st.write(bridge.get("tested_skill") or "Apply the concept to the exact scenario.")
            expected = question.get("expected_focus", []) or []
            if expected:
                st.markdown("**Evidence expected:** " + " · ".join(str(item) for item in expected[:4]))


def run_draft_verification_action(
    *,
    awaiting_run: Path,
    run_state: Dict[str, Any],
    topic_id: str,
    concept_note: Dict[str, Any],
    architect_note: Dict[str, Any],
    assessment_doc: Dict[str, Any],
    answer_path: Path,
    updated_answers: Dict[str, Any],
) -> None:
    save_answers(answer_path, updated_answers)
    persist_mission_draft_to_supabase(run_state, topic_id, updated_answers)
    verification = verify_draft_answers(
        concept_note=build_dataclass(concept_note, ConceptNote),
        architect_note=build_dataclass(architect_note, ArchitectNote),
        assessment=build_dataclass(assessment_doc, Assessment),
        answers_doc=updated_answers,
    )
    save_answers(awaiting_run / "draft_verification.json", verification)
    try:
        upsert_artifact(
            run_id=run_state["run_id"],
            artifact_type="draft_verification",
            topic_id=topic_id,
            payload=verification,
        )
        append_event(
            event_type="draft_verified",
            run_id=run_state["run_id"],
            topic_id=topic_id,
            payload=verification.get("summary", {}),
        )
    except Exception:
        pass
    st.session_state["draft_verification_run_id"] = run_state["run_id"]
    st.session_state["draft_verification"] = verification


def get_draft_verification_to_show(awaiting_run: Path, run_id: str) -> Optional[Dict[str, Any]]:
    if st.session_state.get("draft_verification_run_id") == run_id:
        return st.session_state.get("draft_verification")
    if (awaiting_run / "draft_verification.json").exists():
        return load_json(awaiting_run / "draft_verification.json")
    return None


def _format_mcq_title(kind: str, idx: int, question: str) -> str:
    kind = str(kind or "Check").strip()
    prefix = f"Check {idx}" if kind.lower() == "check" else f"{kind} Check {idx}"
    return f"{prefix}. {question}"


def render_pre_mission_mcqs(topic_id: str, booster: Dict[str, Any]) -> None:
    mcqs = booster.get("mcqs", []) or []
    st.markdown("### Pre-mission MCQs")
    st.caption("Learning checks only. They do not affect score, XP, or unlocks. These should test judgment, not memory alone.")
    if not mcqs:
        st.info("No MCQs configured for this lesson yet.")
        return

    for idx, item in enumerate(mcqs, start=1):
        qkey = f"{topic_id}_mcq_{idx}"
        kind = str(item.get("kind", "Check"))
        title = _format_mcq_title(kind, idx, str(item.get("question", "")))
        with st.expander(title, expanded=(idx == 1)):
            options = item.get("options", []) or []
            if not options:
                st.info("No options configured.")
                continue
            selected = st.radio(
                label=f"Select answer for check {idx}",
                options=list(range(len(options))),
                format_func=lambda i, opts=options: opts[i],
                key=qkey,
                label_visibility="collapsed",
            )
            correct_index = int(item.get("answer_index", -1))
            option_explanations = item.get("option_explanations", []) or []
            if st.button(f"Check answer {idx}", key=f"{qkey}_btn", use_container_width=True):
                if selected == correct_index:
                    st.success("Correct. " + str(item.get("explanation", "")))
                else:
                    st.error("Not quite.")
                    if selected < len(option_explanations) and option_explanations[selected]:
                        st.warning(str(option_explanations[selected]))
                    else:
                        st.caption("This option misses the topic-specific mechanism. Re-read the tutor narrative and try again.")
                    st.caption("The correct option is intentionally not shown. Fix the reasoning, not the guess.")

def render_lesson_booster_panel(topic_id: str, concept_note: Dict[str, Any], architect_note: Dict[str, Any], assessment_doc: Dict[str, Any]) -> None:
    booster = build_lesson_booster(topic_id, concept_note, architect_note, assessment_doc)

    st.markdown("### Study Booster")
    st.caption("Use this before mission responses. It is a warm-up, not a final answer bank.")

    with st.expander("Tutor walkthrough", expanded=True):
        st.markdown("**In one line**")
        st.info(booster.get("plain_language", ""))

        st.markdown("**Worked example**")
        st.write(booster.get("worked_example", ""))

        st.markdown("**Common production trap**")
        st.warning(booster.get("production_trap", ""))

        st.markdown("**How to approach the missions**")
        st.success(booster.get("mission_hint", ""))

        focus = booster.get("mission_focus", []) or []
        if focus:
            st.markdown("**What the evaluator will look for**")
            for item in focus:
                st.markdown(f"- {item}")

    mcqs = booster.get("mcqs", []) or []
    if mcqs:
        with st.expander("Pre-mission multiple choice checks", expanded=True):
            st.caption("These checks are for learning only. They do not affect score or unlocks.")
            for idx, item in enumerate(mcqs, start=1):
                qkey = f"{topic_id}_mcq_{idx}"
                st.markdown(f"**{_format_mcq_title('Check', idx, str(item.get('question', '')))}**")
                options = item.get("options", []) or []
                if not options:
                    continue
                selected = st.radio(
                    label=f"Select answer for check {idx}",
                    options=list(range(len(options))),
                    format_func=lambda i, opts=options: opts[i],
                    key=qkey,
                    label_visibility="collapsed",
                )
                correct_index = int(item.get("answer_index", -1))
                if st.button(f"Check answer {idx}", key=f"{qkey}_btn"):
                    if selected == correct_index:
                        st.success("Correct. " + str(item.get("explanation", "")))
                    else:
                        st.error("Not quite. " + str(item.get("explanation", "")))
                        st.caption("Review the Study Booster, then try again. The correct option is intentionally not shown here.")
                st.divider()

def render_practice_coaching_panel(run_dir: Path) -> None:
    result_path = run_dir / "practice_result.json"
    coaching_path = run_dir / "practice_coaching.json"

    if not result_path.exists() and not coaching_path.exists():
        return

    st.markdown("### Practical Code Lab Result")

    if result_path.exists():
        result = load_json(result_path)
        render_practice_result_summary(result)

    if coaching_path.exists():
        coaching = load_json(coaching_path)
        with st.expander("Practical coaching", expanded=False):
            st.markdown("**What to fix next**")
            st.write(coaching.get("next_step", ""))

            failed_categories = coaching.get("failed_categories", []) or []
            if failed_categories:
                st.markdown("**Failed code skill areas**")
                for item in failed_categories:
                    st.markdown(f"- {item}")

            diagnostic_hints = coaching.get("diagnostic_hints", []) or []
            if diagnostic_hints:
                st.markdown("**Debug hints without hidden answers**")
                for item in diagnostic_hints:
                    st.info(str(item))

            missing = coaching.get("missing_interpretation_focus", []) or []
            if missing:
                st.markdown("**Missing interpretation focus**")
                for item in missing:
                    st.markdown(f"- {item}")

            st.markdown("**Better code**")
            st.code(coaching.get("better_code", ""), language="python")

            st.markdown("**Better interpretation**")
            st.info(coaching.get("better_interpretation", ""))


def render_level_card(
    row: Dict[str, str],
    selected_topic_id: Optional[str],
    rewards_state: Dict[str, Any],
) -> None:
    topic_id = row["topic_id"]
    title = row["title"]
    status = v23_display_status(row, rewards_state)
    stars = compute_display_stars(row, rewards_state)
    badge = badge_label_for_topic(row, rewards_state)
    selected = topic_id == selected_topic_id

    selected_class = " level-card-selected" if selected else ""

    st.markdown(
        f"""
        <div class="level-card{selected_class}">
            <div class="level-id">{topic_id}</div>
            <div class="level-title">{title}</div>
            <div class="level-status">{status_chip(status)}</div>
            <div class="level-stars">{stars}</div>
            <div class="level-badge">{badge}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_latest_evaluation_panel() -> None:
    eval_run = get_latest_evaluation_run()
    if eval_run is None:
        st.info("No completed evaluation yet.")
        return

    state = load_json(eval_run / "run_state.json")
    evaluation_path = eval_run / "evaluation.json"
    if not evaluation_path.exists():
        st.warning("Latest evaluation run exists, but evaluation.json is missing.")
        return

    evaluation = load_json(evaluation_path)
    history_entry = get_history_entry_for_run(state["run_id"])
    reward_summary = (history_entry or {}).get("reward_summary", {})

    decision = evaluation.get("decision", "unknown")
    if decision == "pass":
        st.success(f"Latest Result: PASS . {state['topic_id']} . {state['topic_name']}")
    elif decision == "borderline":
        st.warning(f"Latest Result: BORDERLINE . {state['topic_id']} . {state['topic_name']}")
    else:
        st.error(f"Latest Result: {decision.upper()} . {state['topic_id']} . {state['topic_name']}")

    render_score_cards(evaluation)

    reward_c1, reward_c2, reward_c3 = st.columns(3)
    reward_c1.metric("Stars Earned", reward_summary.get("stars_earned", "-"))
    reward_c2.metric("XP Earned", reward_summary.get("xp_earned", "-"))
    reward_c3.metric("Total XP", reward_summary.get("total_xp", "-"))

    badges = reward_summary.get("badges_awarded", []) or []
    if badges:
        st.markdown("**Badges Awarded**")
        for badge in badges:
            st.markdown(f"- {badge['label']} . {badge['description']}")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Strengths**")
        for item in evaluation.get("strengths", []):
            st.markdown(f"- {item}")

    with col2:
        st.markdown("**Weak Spots**")
        for item in evaluation.get("weak_spots", []):
            st.markdown(f"- {item}")

    render_answer_coaching_panel(eval_run)
    render_practice_coaching_panel(eval_run)

    st.markdown("**Decision Reason**")
    st.write(evaluation.get("decision_reason", ""))

    st.markdown("**Refined Explanation**")
    st.write(evaluation.get("refined_explanation", ""))

    st.markdown("**Refined Architect Summary**")
    st.write(evaluation.get("refined_architect_summary", ""))

    unlocked_topics = []
    if history_entry:
        unlocked_topics = history_entry.get("unlocked_topics", []) or []

    if unlocked_topics:
        st.markdown("**Unlocked Next**")
        st.write(", ".join(unlocked_topics))

    st.markdown("**Next Action**")
    st.write(evaluation.get("next_action", "-"))


def is_playable_status(status: str) -> bool:
    return status in {"not_started", "unlocked", "needs_attention", "in_progress", "borderline", "revise", "completed"}


# -----------------------------
# Streamlit page
# -----------------------------
st.set_page_config(page_title="ML Architect Learning OS", layout="wide")
inject_theme()
require_login()

st.markdown('<div class="main-title">ML Architect Learning OS</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-title">Level up topic by topic. Track mastery, weak spots, rewards, and architect readiness.</div>',
    unsafe_allow_html=True,
)
render_session_heartbeat()

cloud_repair_summary = repair_cloud_state_on_startup()
if cloud_repair_summary.get("error"):
    st.warning(f"Cloud state repair warning: {cloud_repair_summary['error']}")

progress_rows = load_progress_tracker()
rewards_state = load_rewards_state()
catalog_source, catalog_count = load_topic_catalog_source()
metrics = compute_overall_metrics(progress_rows, rewards_state)

# Supabase is the system of record. Streamlit Cloud local files are only cache.
# Rehydrate active/evaluation runs before local run discovery so sleep/redeploy
# does not make the app forget an in-progress lesson.
sync_active_run_from_supabase(progress_rows)
sync_latest_evaluation_from_supabase()

awaiting_run = find_latest_run("awaiting_user_answers")
stale_awaiting_run = None
if is_stale_awaiting_run(awaiting_run, progress_rows, rewards_state):
    stale_awaiting_run = awaiting_run
    awaiting_run = None

latest_eval_run = get_latest_evaluation_run()
latest_run = find_latest_run()
if stale_awaiting_run is not None and latest_run == stale_awaiting_run and latest_eval_run is not None:
    latest_run = latest_eval_run

if "selected_topic_id" not in st.session_state:
    st.session_state.selected_topic_id = None

top_c1, top_c2, top_c3, top_c4, top_c5, top_c6 = st.columns(6)
top_c1.metric("Completed Levels", metrics["completed"])
top_c2.metric("Unlocked", metrics["unlocked"])
top_c3.metric("Needs Attention", metrics["needs_attention"])
top_c4.metric("Avg Score", metrics["overall_avg"] if metrics["overall_avg"] is not None else "-")
top_c5.metric("Total XP", rewards_state.get("total_xp", 0))
top_c6.metric("Badges", len(rewards_state.get("badges_unlocked", [])))

if awaiting_run is not None:
    active_state = load_json(awaiting_run / "run_state.json")
    st.warning(f"Active lesson in progress . {active_state['topic_id']} . Finish active lesson first.")
elif stale_awaiting_run is not None:
    stale_state = load_json(stale_awaiting_run / "run_state.json")
    st.info(
        f"Ignored stale active run for mastered topic . {stale_state.get('topic_id')} . "
        "V2.3 will continue from the real repair queue."
    )

action_c1, action_c2 = st.columns([1, 1])

with action_c1:
    if st.button(
        "Start Next Lesson",
        use_container_width=True,
        disabled=awaiting_run is not None,
    ):
        with st.spinner("Starting next lesson..."):
            ok, output = start_lesson_for_topic(None)
        record_action_result("Start Next Lesson", ok, output)
        if ok:
            st.rerun()

with action_c2:
    if st.button("Evaluate Current Lesson", use_container_width=True):
        if awaiting_run is None:
            st.warning("No lesson is currently awaiting answers.")
        else:
            with st.spinner("Evaluating current lesson. This can take a little time..."):
                ok, output = run_module("src.evaluate_lesson")
            record_action_result("Evaluate Current Lesson", ok, output)
            if ok:
                st.rerun()

if latest_run:
    state = load_json(latest_run / "run_state.json")
    st.caption(
        f"Latest run: {state.get('run_id')} | topic: {state.get('topic_id')} | phase: {state.get('phase')} | status: {state.get('status')}"
    )
st.caption(f"Curriculum source: {catalog_source} . topics: {catalog_count}")

render_last_action_result()

tabs = st.tabs(
    [
        "🏠 Home",
        "🎮 Current Level",
        "📊 Last Evaluation",
        "📈 Trajectory",
        "📚 Notes Vault",
        "🧾 Run Details",
        "🏆 Rewards",
        "🔁 Review / Redo",
    ]
)

# -----------------------------
# HOME TAB
# -----------------------------
with tabs[0]:
    st.subheader("Level Map")
    st.caption("V2.3 flow: repair every ML topic below 3-star mastery, then checkpoint → capstone → DL/NN. Mastered topics support Review/Redo; weak topics show Repair.")

    if not progress_rows:
        st.warning("No progress tracker found.")
    else:
        cols_per_row = 3
        for i in range(0, len(progress_rows), cols_per_row):
            cols = st.columns(cols_per_row)
            for j, row in enumerate(progress_rows[i:i + cols_per_row]):
                with cols[j]:
                    render_level_card(row, st.session_state.selected_topic_id, rewards_state)
                    topic_id = row.get("topic_id", "")
                    status = v23_display_status(row, rewards_state)
                    if status == "completed":
                        action_cols = st.columns(2)
                        with action_cols[0]:
                            if st.button("Review", key=f"review_{topic_id}", use_container_width=True, disabled=not topic_id):
                                st.session_state.review_topic_id = topic_id
                                st.info("Open the Review / Redo tab to inspect this completed topic.")
                        with action_cols[1]:
                            redo_disabled = awaiting_run is not None
                            if st.button("Redo", key=f"redo_{topic_id}", use_container_width=True, disabled=redo_disabled):
                                with st.spinner(f"Starting redo attempt for {topic_id}..."):
                                    ok, output = start_lesson_for_topic(topic_id, allow_completed_restart=True)
                                record_action_result("Start Redo Attempt", ok, output)
                                if ok:
                                    st.rerun()
                    else:
                        unlocked = str(row.get("prerequisites_unlocked") or "").strip().lower() == "true"
                        if status in {"needs_attention", "revise", "borderline", "unlocked", "not_started"} and unlocked:
                            button_label = "Repair" if status in {"needs_attention", "revise", "borderline"} else "Start"
                            if st.button(button_label, key=f"repair_{topic_id}", use_container_width=True, disabled=awaiting_run is not None):
                                with st.spinner(f"Starting {button_label.lower()} attempt for {topic_id}..."):
                                    ok, output = start_lesson_for_topic(topic_id, allow_completed_restart=False)
                                record_action_result(f"Start {button_label} Attempt", ok, output)
                                if ok:
                                    st.rerun()
                        else:
                            st.caption("Locked until prerequisite mastery gate is met.")

    st.divider()
    st.subheader("Latest Result")
    render_latest_evaluation_panel()

# -----------------------------
# CURRENT LEVEL TAB
# -----------------------------
with tabs[1]:
    if awaiting_run is None:
        st.info("No active lesson. Start the next available level from Home.")
    else:
        run_state = load_json(awaiting_run / "run_state.json")
        topic_id = run_state["topic_id"]

        concept_note = load_json(awaiting_run / "concept_note.json")
        architect_note = load_json(awaiting_run / "architect_note.json")
        assessment_doc = load_json(awaiting_run / "assessment.json")

        answer_path = PROJECT_ROOT / run_state["artifacts"]["answers"]
        answers_doc = load_json(answer_path)

        mission_types = sorted({item["type"] for item in answers_doc["answers"]})
        render_topic_hero(run_state, concept_note, mission_types)

        learning_design = load_topic_learning_design(topic_id)
        booster = build_lesson_booster(topic_id, concept_note, architect_note, assessment_doc)

        artifacts = run_state.get("artifacts", {}) or {}
        practice_exercise = load_relative_json_or_none(artifacts.get("practice_exercise"))
        practice_submission_path = None
        practice_submission = None
        updated_practice_submission = None

        current_tabs = ["① Learn", "② Check It", "③ MCQs", "④ Evidence + Verify"]
        if practice_exercise is not None:
            current_tabs.append("⑤ Code Lab")
            submit_tab_label = "⑥ Submit"
        else:
            submit_tab_label = "⑤ Submit"
        current_tabs.append(submit_tab_label)
        lesson_tabs = st.tabs(current_tabs)

        with lesson_tabs[0]:
            if not render_learning_design_panel(topic_id):
                if not render_tutor_narrative_panel(topic_id):
                    render_learning_brief(concept_note, architect_note)
            render_topic_resources_panel(topic_id)

        with lesson_tabs[1]:
            render_booster_walkthrough(booster)

        with lesson_tabs[2]:
            render_pre_mission_mcqs(topic_id, booster)

        updated_answers = {
            "topic_id": answers_doc["topic_id"],
            "status": "pending_user_answers",
            "answers": [],
        }

        with lesson_tabs[3]:
            st.markdown("### Evidence Responses")
            st.caption("Answer only what each task asks. Normal lessons use different evidence tasks, not a repeated essay formula.")
            render_mission_bridge(booster, assessment_doc)
            st.divider()

            for i, item in enumerate(answers_doc["answers"], start=1):
                task_meta = _runtime_task_meta(learning_design, item)
                mission_type = (task_meta or {}).get("label") or item.get("type", "evidence").replace("_", " ").title()
                st.markdown(
                    f"""
                    <div class="mission-card">
                        <div class="mission-card-title">Task {i} . {html_text(mission_type)}</div>
                        <div class="mission-question">{html_text(item['question'])}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                if task_meta and task_meta.get("purpose"):
                    st.caption(str(task_meta.get("purpose")))
                max_words = int((task_meta or {}).get("target_max_words", 105))
                answer_text = st.text_area(
                    label=f"Answer for {item['question_id']}",
                    value=item.get("answer", ""),
                    height=105 if max_words <= 100 else 135,
                    key=f"{run_state['run_id']}_{item['question_id']}",
                    label_visibility="collapsed",
                )
                render_answer_pressure(item.get("type", "mission"), answer_text, task_meta)
                render_writing_assist_panel(item.get("type", "mission"), answer_text, task_meta)
                updated_answers["answers"].append(
                    {
                        "question_id": item["question_id"],
                        "type": item["type"],
                        "question": item["question"],
                        "answer": answer_text,
                    }
                )

            st.markdown("### Save + Verify Evidence")
            st.caption("Save and Verify stay here so your response work is protected before final evaluation.")
            action_c1, action_c2 = st.columns([1, 1])
            with action_c1:
                if st.button("Save Answers", use_container_width=True):
                    save_answers(answer_path, updated_answers)
                    persist_mission_draft_to_supabase(run_state, topic_id, updated_answers)
                    st.success("Mission answers saved locally and to Supabase.")
            with action_c2:
                if st.button("Verify Draft", use_container_width=True):
                    try:
                        run_draft_verification_action(
                            awaiting_run=awaiting_run,
                            run_state=run_state,
                            topic_id=topic_id,
                            concept_note=concept_note,
                            architect_note=architect_note,
                            assessment_doc=assessment_doc,
                            answer_path=answer_path,
                            updated_answers=updated_answers,
                        )
                        st.success("Draft verified. No stronger sample answers shown before final evaluation.")
                    except Exception as exc:
                        st.error(f"Draft verification failed: {exc}")

            verification_to_show = get_draft_verification_to_show(awaiting_run, run_state["run_id"])
            if verification_to_show:
                st.divider()
                render_draft_verification_panel(verification_to_show)

        if practice_exercise is not None:
            practice_tab_index = 4
            submit_tab_index = 5
            with lesson_tabs[practice_tab_index]:
                practice_submission_rel = artifacts.get("practice_submission")
                practice_submission_path = PROJECT_ROOT / practice_submission_rel if practice_submission_rel else awaiting_run / "practice_submission.json"
                practice_submission = load_relative_json_or_none(practice_submission_rel) or {
                    "topic_id": practice_exercise.get("topic_id"),
                    "exercise_id": practice_exercise.get("exercise_id"),
                    "status": "pending_user_submission",
                    "code": practice_exercise.get("starter_code", ""),
                    "interpretation": "",
                }

                st.markdown("### Code Lab")
                st.caption("First understand what the function represents. Then write the code and explain the result.")
                concept_bridge = practice_exercise.get("concept_bridge", "")
                if concept_bridge:
                    render_static_card("Why This Function Exists", concept_bridge, "callout-good")
                worked_code_example = practice_exercise.get("worked_code_example", "")
                if worked_code_example:
                    with st.expander("Small example before coding", expanded=True):
                        st.write(worked_code_example)
                render_static_card(practice_exercise.get("title", "Practice Exercise"), practice_exercise.get("prompt", ""))

                code_text = st.text_area(
                    "Code submission",
                    value=practice_submission.get("code", practice_exercise.get("starter_code", "")),
                    height=260,
                    key=f"{run_state['run_id']}_practice_code",
                )
                st.markdown("#### Practical interpretation")
                st.caption(practice_exercise.get("interpretation_prompt", "Explain what the result means."))
                interpretation_focus = practice_exercise.get("expected_interpretation_focus", []) or []
                if interpretation_focus:
                    st.markdown("**Your explanation must cover:** " + " · ".join(str(item) for item in interpretation_focus))
                interpretation_text = st.text_area(
                    "Practical interpretation response",
                    value=practice_submission.get("interpretation", ""),
                    height=135,
                    key=f"{run_state['run_id']}_practice_interpretation",
                    label_visibility="collapsed",
                )

                updated_practice_submission = {
                    "topic_id": practice_exercise.get("topic_id"),
                    "exercise_id": practice_exercise.get("exercise_id"),
                    "status": "pending_evaluation",
                    "code": code_text,
                    "interpretation": interpretation_text,
                }

                if st.button("Run Code Exercise", use_container_width=True):
                    save_answers(practice_submission_path, updated_practice_submission)
                    result = run_code_exercise(practice_exercise, updated_practice_submission)
                    persist_practice_submission_to_supabase(run_state, topic_id, updated_practice_submission, result)
                    render_practice_result_summary(result)
        else:
            submit_tab_index = 4

        with lesson_tabs[submit_tab_index]:
            st.markdown("### Submit Final Attempt")
            st.markdown(
                """
                <div class="save-panel">
                    <div class="mission-card-title">Final submission</div>
                    <div class="small-muted">Save and Verify Draft are in the Missions tab. Use this only when you are ready to lock the attempt for evaluation.</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            if practice_exercise is not None:
                st.info("Code Lab, if present, is separate practical evidence and is included in final evaluation. Run it before submitting.")

            if st.button("Save + Evaluate", use_container_width=True):
                save_answers(answer_path, updated_answers)
                persist_mission_draft_to_supabase(run_state, topic_id, updated_answers)
                if updated_practice_submission is not None and practice_submission_path is not None:
                    save_answers(practice_submission_path, updated_practice_submission)
                    persist_practice_submission_to_supabase(run_state, topic_id, updated_practice_submission)
                with st.spinner("Saving answers, running practical checks, and evaluating mission responses. This finalizes this attempt..."):
                    ok, output = run_module("src.evaluate_lesson")
                record_action_result("Save + Evaluate", ok, output)
                if ok:
                    st.session_state.pop("draft_verification", None)
                    st.session_state.pop("draft_verification_run_id", None)
                    st.rerun()

            verification_to_show = get_draft_verification_to_show(awaiting_run, run_state["run_id"])
            if verification_to_show:
                st.divider()
                st.caption("Latest draft verification from Missions tab")
                render_draft_verification_panel(verification_to_show)



# -----------------------------
# LAST EVALUATION TAB
# -----------------------------
with tabs[2]:
    st.subheader("Last Evaluation")
    if latest_eval_run is None:
        st.info("No completed evaluation yet.")
    else:
        render_latest_evaluation_panel()


# -----------------------------
# TRAJECTORY TAB
# -----------------------------
with tabs[3]:
    st.subheader("Trajectory")

    history = load_run_history()
    eval_history = [row for row in history if row.get("phase") == "evaluation_complete"]

    if not eval_history:
        st.info("No evaluation history yet.")
    else:
        summary_rows = []
        for row in progress_rows:
            avg_score = compute_topic_average_score(row)
            topic_reward = get_topic_reward_state(rewards_state, row["topic_id"])
            summary_rows.append(
                {
                    "topic_id": row["topic_id"],
                    "title": row["title"],
                    "status": row["status"],
                    "stars": compute_display_stars(row, rewards_state),
                    "attempts": row["attempt_count"],
                    "latest_avg_score": round(avg_score, 2) if avg_score is not None else None,
                    "best_stars": topic_reward.get("best_stars", 0),
                    "last_badges": ", ".join(topic_reward.get("last_badges", [])),
                }
            )

        st.markdown("### Topic Progress")
        st.dataframe(summary_rows, use_container_width=True)

        latest_five = eval_history[-5:]
        st.markdown("### Recent Evaluation Trail")
        st.dataframe(latest_five, use_container_width=True)

# -----------------------------
# NOTES VAULT TAB
# -----------------------------
with tabs[4]:
    st.subheader("Notes Vault")

    selected_topic_id = st.session_state.selected_topic_id
    if not selected_topic_id:
        if latest_eval_run is not None:
            selected_topic_id = load_json(latest_eval_run / "run_state.json")["topic_id"]
        elif awaiting_run is not None:
            selected_topic_id = load_json(awaiting_run / "run_state.json")["topic_id"]

    if not selected_topic_id:
        st.info("No topic selected yet.")
    else:
        st.caption(f"Selected topic: {selected_topic_id}")

        concept_file = find_note_file(NOTES_DIR / "concepts", selected_topic_id)
        architect_file = find_note_file(NOTES_DIR / "architect_lens", selected_topic_id)
        refined_file = find_note_file(NOTES_DIR / "refined", selected_topic_id)
        eval_file = find_note_file(ASSESSMENTS_DIR / "evaluations", selected_topic_id)
        coaching_file = find_note_file(ASSESSMENTS_DIR / "evaluations", f"{selected_topic_id}_answer_coaching")

        sub_tabs = st.tabs(["Concept", "Architect", "Refined", "Evaluation", "Answer Coaching"])

        with sub_tabs[0]:
            if concept_file:
                st.markdown(load_text(concept_file))
            else:
                st.info("No concept note found.")

        with sub_tabs[1]:
            if architect_file:
                st.markdown(load_text(architect_file))
            else:
                st.info("No architect note found.")

        with sub_tabs[2]:
            if refined_file:
                st.markdown(load_text(refined_file))
            else:
                st.info("No refined note found.")

        with sub_tabs[3]:
            if eval_file:
                st.markdown(load_text(eval_file))
            else:
                st.info("No evaluation note found.")
        
        with sub_tabs[4]:
            if coaching_file:
                st.markdown(load_text(coaching_file))
            else:
                st.info("No answer coaching note found.")

# -----------------------------
# RUN DETAILS TAB
# -----------------------------
with tabs[5]:
    st.subheader("Run Details")
    st.caption("Use this tab to inspect what happened after hosted Streamlit actions. These files live in the app runtime, not automatically in GitHub.")
    render_last_action_result()
    render_run_details()


# -----------------------------
# REWARDS TAB
# -----------------------------
with tabs[6]:
    st.subheader("Rewards")
    st.caption("XP now uses best completed attempt per topic. Revise/fail attempts earn 0 XP. Retry XP is added only if the retry beats the previous best completed attempt.")

    streaks = rewards_state.get("streaks", {})
    c1, c2, c3 = st.columns(3)
    c1.metric("Total XP", rewards_state.get("total_xp", 0))
    c2.metric("Current Streak", streaks.get("current_completion_streak", 0))
    c3.metric("Best Streak", streaks.get("best_completion_streak", 0))

    badges = rewards_state.get("badges_unlocked", [])
    st.markdown("### Badge Cabinet")
    if not badges:
        st.info("No badges unlocked yet.")
    else:
        for badge in badges:
            label = badge_to_label(badge)
            description = badge_to_description(badge)
            if description:
                st.markdown(f"- **{label}** . {description}")
            else:
                st.markdown(f"- **{label}**")

    reward_history = rewards_state.get("history", [])
    st.markdown("### Recent Rewards")
    if not reward_history:
        st.info("No reward history yet.")
    else:
        st.dataframe(reward_history_display_rows(reward_history[-10:]), use_container_width=True)


# -----------------------------
# REVIEW / REDO TAB
# -----------------------------
with tabs[7]:
    render_review_redo_tab(progress_rows, awaiting_run, rewards_state)
