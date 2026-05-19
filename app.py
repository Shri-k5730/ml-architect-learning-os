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

from src.utils.curriculum_catalog import load_topic_catalog_source
from src.utils.rewards import get_topic_reward_state, load_rewards_state
from src.utils.tracker import read_progress_rows
from src.utils.cloud_state import repair_cloud_state_on_startup
from src.utils.code_runner import run_code_exercise
from src.agents.draft_verifier import verify_draft_answers
from src.agents.lesson_booster import build_lesson_booster
from src.agents.writing_assist import analyze_answer_text
from src.agents.tutor_narrative import get_tutor_narrative
from src.schemas import ArchitectNote, Assessment, ConceptNote
from src.utils.validator import build_dataclass
from src.utils.supabase_store import append_event, upsert_artifact


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
    """Render a tiny hosted-session heartbeat in the app header.

    This is intentionally backend-driven. When wrapped in st.fragment(run_every),
    Streamlit touches the Python backend periodically while the browser tab and
    laptop are active. A pure JavaScript clock would only prove that the browser
    is alive and would not reliably keep the hosted Streamlit session warm.
    """
    now_ist = datetime.now(ZoneInfo("Asia/Kolkata"))
    heartbeat_text = now_ist.strftime("%H:%M:%S IST")
    st.session_state["last_backend_heartbeat_ist"] = heartbeat_text
    st.markdown(
        f"""
        <div class="session-heartbeat">
          <div class="session-heartbeat-card">
            <span class="heartbeat-dot"></span>
            <span>Backend heartbeat active · {escape(heartbeat_text)} · refresh every 60s</span>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
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
        html { scroll-behavior: smooth; }

        #MainMenu { visibility: hidden; }
        footer { visibility: hidden; }
        header[data-testid="stHeader"] {
            height: 0rem;
            min-height: 0rem;
            background: transparent;
        }
        div[data-testid="stToolbar"] {
            visibility: hidden;
            height: 0rem;
            position: fixed;
        }
        div[data-testid="stDecoration"] { display: none; }
        div[data-testid="stStatusWidget"] { display: none; }

        .session-heartbeat {
            display: flex;
            justify-content: flex-end;
            align-items: center;
            gap: 0.55rem;
            margin: -0.35rem 0 0.75rem 0;
            color: #cbd5e1;
            font-size: 0.84rem;
            font-weight: 750;
        }
        .session-heartbeat-card {
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            border-radius: 999px;
            padding: 0.42rem 0.72rem;
            background: rgba(15, 23, 42, 0.72);
            border: 1px solid rgba(34, 197, 94, 0.26);
            box-shadow: 0 14px 34px rgba(34, 197, 94, 0.08);
        }
        .heartbeat-dot {
            width: 0.62rem;
            height: 0.62rem;
            border-radius: 999px;
            background: #22c55e;
            box-shadow: 0 0 0 rgba(34, 197, 94, 0.55);
            animation: heartbeatPulse 1.8s infinite;
        }
        @keyframes heartbeatPulse {
            0% { box-shadow: 0 0 0 0 rgba(34, 197, 94, 0.55); }
            70% { box-shadow: 0 0 0 8px rgba(34, 197, 94, 0); }
            100% { box-shadow: 0 0 0 0 rgba(34, 197, 94, 0); }
        }

        body {
            background:
                radial-gradient(circle at top left, rgba(124, 58, 237, 0.18), transparent 34%),
                radial-gradient(circle at top right, rgba(14, 165, 233, 0.14), transparent 30%),
                linear-gradient(135deg, #020617 0%, #0f172a 45%, #111827 100%);
            color: #e5e7eb;
        }

        .stApp {
            background:
                radial-gradient(circle at 10% 0%, rgba(124, 58, 237, 0.18), transparent 28%),
                radial-gradient(circle at 90% 8%, rgba(56, 189, 248, 0.14), transparent 26%),
                linear-gradient(135deg, #020617 0%, #0f172a 50%, #111827 100%);
        }

        .block-container {
            padding-top: 1.25rem;
            padding-bottom: 3rem;
            max-width: 1480px;
        }

        .main-title {
            font-size: 2.75rem;
            font-weight: 900;
            letter-spacing: -0.045em;
            background: linear-gradient(90deg, #f8fafc 0%, #c4b5fd 45%, #7dd3fc 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 0.2rem;
        }

        .sub-title {
            color: #94a3b8;
            font-size: 1.02rem;
            margin-bottom: 1.25rem;
        }

        div[data-testid="stMetric"] {
            background: rgba(15, 23, 42, 0.72);
            border: 1px solid rgba(148, 163, 184, 0.18);
            padding: 1rem;
            border-radius: 18px;
            box-shadow: 0 18px 45px rgba(0, 0, 0, 0.25);
            backdrop-filter: blur(14px);
        }

        div[data-testid="stMetric"] label { color: #94a3b8 !important; }
        div[data-testid="stMetricValue"] { color: #f8fafc !important; font-weight: 800; }

        .stButton > button {
            border-radius: 14px;
            border: 1px solid rgba(167, 139, 250, 0.35);
            background: linear-gradient(135deg, rgba(124, 58, 237, 0.95), rgba(14, 165, 233, 0.85));
            color: #ffffff;
            font-weight: 750;
            letter-spacing: 0.01em;
            padding: 0.72rem 1rem;
            box-shadow: 0 14px 32px rgba(59, 130, 246, 0.22);
            transition: transform 0.18s ease, box-shadow 0.18s ease, border-color 0.18s ease;
        }

        .stButton > button:hover {
            transform: translateY(-1px);
            box-shadow: 0 18px 42px rgba(124, 58, 237, 0.36);
            border-color: rgba(221, 214, 254, 0.8);
        }

        .stButton > button:disabled {
            background: rgba(30, 41, 59, 0.75);
            border: 1px solid rgba(100, 116, 139, 0.24);
            color: #64748b;
            box-shadow: none;
            transform: none;
        }

        div[data-testid="stTabs"] button {
            border-radius: 999px;
            color: #cbd5e1;
            padding: 0.65rem 1.1rem;
            font-weight: 700;
        }

        div[data-testid="stTabs"] button[aria-selected="true"] {
            background: rgba(124, 58, 237, 0.25);
            color: #ffffff;
            border: 1px solid rgba(196, 181, 253, 0.35);
        }

        div[data-testid="stTextArea"] textarea {
            background: rgba(15, 23, 42, 0.78);
            border: 1px solid rgba(148, 163, 184, 0.24);
            color: #f8fafc;
            border-radius: 16px;
            box-shadow: inset 0 0 0 1px rgba(255,255,255,0.02);
        }

        div[data-testid="stTextArea"] textarea:focus {
            border-color: rgba(124, 58, 237, 0.8);
            box-shadow: 0 0 0 3px rgba(124, 58, 237, 0.18);
        }

        .level-card {
            border-radius: 22px;
            padding: 1rem;
            min-height: 205px;
            background:
                linear-gradient(145deg, rgba(15, 23, 42, 0.96), rgba(30, 41, 59, 0.78)),
                radial-gradient(circle at top right, rgba(124, 58, 237, 0.18), transparent 40%);
            border: 1px solid rgba(148, 163, 184, 0.18);
            box-shadow: 0 24px 70px rgba(0, 0, 0, 0.30);
            transition: transform 0.18s ease, border-color 0.18s ease, box-shadow 0.18s ease;
        }

        .level-card:hover {
            transform: translateY(-3px);
            border-color: rgba(167, 139, 250, 0.55);
            box-shadow: 0 28px 80px rgba(76, 29, 149, 0.32);
        }

        .level-card-selected {
            border-color: rgba(125, 211, 252, 0.70);
            box-shadow: 0 28px 80px rgba(14, 165, 233, 0.22);
        }

        .level-id {
            font-size: 0.78rem;
            color: #a78bfa;
            font-weight: 800;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            margin-bottom: 0.55rem;
        }

        .level-title {
            font-size: 1.08rem;
            line-height: 1.28;
            font-weight: 850;
            color: #f8fafc;
            margin-bottom: 0.85rem;
        }

        .level-status {
            display: inline-flex;
            align-items: center;
            border-radius: 999px;
            padding: 0.28rem 0.62rem;
            font-size: 0.82rem;
            font-weight: 750;
            color: #e0f2fe;
            background: rgba(14, 165, 233, 0.14);
            border: 1px solid rgba(125, 211, 252, 0.25);
            margin-bottom: 0.75rem;
        }

        .level-stars {
            font-size: 1.22rem;
            letter-spacing: 0.06em;
            color: #facc15;
            margin-bottom: 0.65rem;
            text-shadow: 0 0 24px rgba(250, 204, 21, 0.25);
        }

        .level-badge {
            color: #cbd5e1;
            font-size: 0.92rem;
            font-weight: 650;
        }



        .app-header-row {
            display: flex;
            align-items: flex-start;
            justify-content: space-between;
            gap: 1rem;
            margin-bottom: 1rem;
        }

        .status-strip {
            display: flex;
            flex-wrap: wrap;
            gap: 0.55rem;
            margin: 0.75rem 0 1.2rem 0;
        }

        .status-pill {
            display: inline-flex;
            align-items: center;
            gap: 0.35rem;
            border-radius: 999px;
            padding: 0.42rem 0.72rem;
            background: rgba(15, 23, 42, 0.72);
            border: 1px solid rgba(148, 163, 184, 0.18);
            color: #cbd5e1;
            font-size: 0.84rem;
            font-weight: 700;
        }

        .current-topic-hero {
            border-radius: 24px;
            padding: 1.2rem 1.25rem;
            margin-bottom: 1rem;
            background:
                linear-gradient(135deg, rgba(15, 23, 42, 0.96), rgba(30, 41, 59, 0.80)),
                radial-gradient(circle at top right, rgba(14, 165, 233, 0.16), transparent 36%);
            border: 1px solid rgba(148, 163, 184, 0.18);
            box-shadow: 0 24px 70px rgba(0, 0, 0, 0.26);
        }

        .topic-kicker {
            color: #7dd3fc;
            font-size: 0.78rem;
            font-weight: 850;
            text-transform: uppercase;
            letter-spacing: 0.11em;
            margin-bottom: 0.38rem;
        }

        .topic-heading {
            color: #f8fafc;
            font-size: 1.75rem;
            line-height: 1.15;
            font-weight: 900;
            letter-spacing: -0.03em;
            margin-bottom: 0.5rem;
        }

        .topic-subline {
            color: #94a3b8;
            font-size: 0.95rem;
            line-height: 1.45;
        }

        .workflow-strip {
            display: flex;
            gap: 0.5rem;
            flex-wrap: wrap;
            margin: 0.75rem 0 0 0;
        }

        .workflow-step {
            border-radius: 999px;
            padding: 0.42rem 0.72rem;
            background: rgba(124, 58, 237, 0.13);
            border: 1px solid rgba(167, 139, 250, 0.22);
            color: #ddd6fe;
            font-size: 0.82rem;
            font-weight: 760;
        }

        .section-card {
            border-radius: 22px;
            padding: 1rem 1.05rem;
            margin-bottom: 0.85rem;
            background: rgba(15, 23, 42, 0.70);
            border: 1px solid rgba(148, 163, 184, 0.16);
            box-shadow: 0 16px 42px rgba(0, 0, 0, 0.18);
        }

        .section-card h4 {
            margin: 0 0 0.45rem 0;
            color: #f8fafc;
            font-size: 1rem;
            font-weight: 860;
        }

        .section-card p, .section-card li {
            color: #cbd5e1;
            line-height: 1.55;
            font-size: 0.95rem;
        }

        .section-card ul {
            margin: 0.45rem 0 0 1.1rem;
            padding: 0;
        }

        .two-card-grid {
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 0.85rem;
            margin-bottom: 0.2rem;
        }

        .callout-good {
            border-color: rgba(34, 197, 94, 0.26);
            background: linear-gradient(135deg, rgba(20, 83, 45, 0.32), rgba(15, 23, 42, 0.72));
        }

        .callout-risk {
            border-color: rgba(251, 191, 36, 0.26);
            background: linear-gradient(135deg, rgba(113, 63, 18, 0.30), rgba(15, 23, 42, 0.72));
        }

        .mission-card {
            border-radius: 20px;
            padding: 0.95rem 1rem;
            margin-bottom: 0.95rem;
            background: rgba(2, 6, 23, 0.42);
            border: 1px solid rgba(148, 163, 184, 0.14);
        }

        .mission-card-title {
            color: #f8fafc;
            font-size: 0.98rem;
            font-weight: 850;
            margin-bottom: 0.35rem;
        }

        .mission-question {
            color: #cbd5e1;
            line-height: 1.48;
            margin-bottom: 0.7rem;
        }

        .save-panel {
            border-radius: 22px;
            padding: 1rem;
            background: rgba(15, 23, 42, 0.76);
            border: 1px solid rgba(125, 211, 252, 0.18);
            box-shadow: 0 18px 48px rgba(14, 165, 233, 0.10);
            margin-bottom: 1rem;
        }

        .small-muted {
            color: #94a3b8;
            font-size: 0.86rem;
            line-height: 1.45;
        }

        @media (max-width: 900px) {
            .two-card-grid { grid-template-columns: 1fr; }
            .topic-heading { font-size: 1.35rem; }
        }

        .stAlert { border-radius: 18px; }
        hr { border-color: rgba(148, 163, 184, 0.16); }
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


def is_stale_awaiting_run(run_dir: Optional[Path], progress_rows: List[Dict[str, str]]) -> bool:
    """Ignore accidental active runs for topics already completed.

    Patch 007 exposed a selector bug that could create a new awaiting run for
    mlf_001 even after it was completed. The dirty run should not block the next
    checkpoint once durable progress says that topic is completed.
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
    return topic_status_map(progress_rows).get(topic_id) == "completed"


def get_latest_evaluation_run() -> Optional[Path]:
    return find_latest_run("evaluation_complete")


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


def start_lesson_for_topic(topic_id: Optional[str] = None) -> tuple[bool, str]:
    if topic_id:
        return run_module("src.start_lesson", args=["--topic_id", topic_id])
    return run_module("src.start_lesson")


def save_answers(answer_path: Path, data: Dict[str, Any]) -> None:
    answer_path.parent.mkdir(parents=True, exist_ok=True)
    answer_path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


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


def render_answer_pressure(question_type: str, answer_text: str) -> None:
    words = len((answer_text or "").split())
    if words == 0:
        st.caption("Target: 80-140 words. Definition → example → production risk → control.")
        return
    if words > 180:
        st.warning(f"{words} words. Too long. Cut repetition and keep only the control/action.")
    elif words > 140:
        st.caption(f"{words} words. Acceptable, but tighten if you are repeating definitions.")
    elif words < 45 and question_type not in {"tiny_hands_on"}:
        st.caption(f"{words} words. Likely thin. Add one example and one production control.")
    else:
        st.caption(f"{words} words. Good length. Now make sure it has a concrete control.")




def render_writing_assist_panel(question_type: str, answer_text: str) -> None:
    """Low-risk writing assist: no rewrite, no answer generation, just noise signals."""
    analysis = analyze_answer_text(answer_text, question_type)
    if not answer_text:
        return

    status = analysis.get("length_status")
    word_count = analysis.get("word_count", 0)
    target_min = analysis.get("target_min", 80)
    target_max = analysis.get("target_max", 140)

    with st.expander("Writing assist . spelling, length, and precision", expanded=analysis.get("has_language_noise", False)):
        if status == "good":
            st.success(f"Length: {word_count} words. Target {target_min}-{target_max}. Good range.")
        elif status in {"long", "essay"}:
            st.warning(f"Length: {word_count} words. Target {target_min}-{target_max}. {analysis.get('length_hint')}")
        else:
            st.info(f"Length: {word_count} words. Target {target_min}-{target_max}. {analysis.get('length_hint')}")

        suggestions = analysis.get("spelling_suggestions", []) or []
        if suggestions:
            st.markdown("**Possible spelling fixes**")
            for item in suggestions:
                st.markdown(f"- `{item.get('original')}` → `{item.get('suggestion')}`")
        else:
            st.caption("No common spelling hints detected.")

        repeated = analysis.get("repeated_phrases", []) or []
        if repeated:
            st.markdown("**Repeated generic phrases**")
            for phrase in repeated:
                st.markdown(f"- `{phrase}` . Replace with the exact mechanism or control.")

        hints = analysis.get("technical_precision_hints", []) or []
        if hints:
            st.markdown("**Technical wording hints**")
            for hint in hints:
                st.info(str(hint))

        st.caption("This assist does not rewrite your answer or add concepts. It only flags language noise and precision risks before evaluation.")


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
        "in_progress": "🟨 In Progress",
        "completed": "🟩 Completed",
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
    status = str(row.get("status") or "").strip().lower()
    if status == "revise":
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
    completed = sum(1 for row in progress_rows if row.get("status") == "completed")
    borderline = sum(1 for row in progress_rows if row.get("status") == "borderline")
    revise = sum(1 for row in progress_rows if row.get("status") == "revise")
    needs_attention_rows = [row for row in progress_rows if topic_needs_attention(row, rewards_state)]
    unlocked = sum(
        1
        for row in progress_rows
        if row.get("prerequisites_unlocked", "").lower() == "true"
        and row.get("status") != "completed"
    )
    locked = sum(1 for row in progress_rows if row.get("status") == "locked")

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

    st.markdown("### Draft Verification")
    st.caption("This is copy-safe guidance. It gives gaps and next actions, not final answers.")

    c1, c2, c3 = st.columns(3)
    c1.metric("Readiness Avg", summary.get("readiness_average", summary.get("likely_average", "-")))
    c2.metric("Weak Drafts", summary.get("weak_count", "-"))
    c3.metric("Partial Drafts", summary.get("partial_count", "-"))
    st.caption("Readiness Avg is not a star prediction. Final scoring may be stricter after full evaluation.")

    recommendation = summary.get("recommendation", "")
    if summary.get("weak_count", 0):
        st.error(recommendation)
    elif summary.get("partial_count", 0):
        st.warning(recommendation)
    else:
        st.success(recommendation)

    concepts = verification.get("core_concepts_to_check", []) or []
    if concepts:
        with st.expander("Concepts to verify before final submission", expanded=False):
            for concept in concepts:
                st.markdown(f"- {concept}")

    for item in verification.get("items", []) or []:
        with st.expander(
            f"{item.get('question_id', '')} . {item.get('verdict', '')} . readiness {item.get('readiness_score', item.get('likely_score', '-'))}/5",
            expanded=item.get("readiness_score", item.get("likely_score", 5)) <= 3,
        ):
            st.markdown("**Question**")
            st.write(item.get("question", ""))

            misconceptions = item.get("misconceptions", []) or []
            if misconceptions:
                st.markdown("**Possible Misconception**")
                for finding in misconceptions:
                    st.warning(
                        f"Evidence: `{finding.get('evidence', '')}`  \n"
                        f"Issue: {finding.get('issue', '')}  \n"
                        f"Correction: {finding.get('correction', '')}"
                    )

            gaps = item.get("coverage_gaps", []) or []
            if gaps:
                st.markdown("**Gaps to fix**")
                for gap in gaps:
                    st.markdown(f"- {gap}")

            writing = item.get("writing_assist", {}) or {}
            if writing.get("has_language_noise"):
                st.markdown("**Writing assist**")
                st.caption(writing.get("length_hint", ""))
                for sug in writing.get("spelling_suggestions", [])[:5]:
                    st.markdown(f"- `{sug.get('original')}` → `{sug.get('suggestion')}`")
                for hint in writing.get("technical_precision_hints", [])[:3]:
                    st.info(str(hint))

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
                <span class="workflow-step">2 Booster</span>
                <span class="workflow-step">3 MCQs</span>
                <span class="workflow-step">4 Missions + Verify</span>
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




def render_tutor_narrative_panel(topic_id: str) -> bool:
    """Render expert-tutor narrative when a blueprint exists.

    Returns True when rendered so the caller can skip the older generic learning brief.
    """
    narrative = get_tutor_narrative(topic_id)
    if not narrative:
        return False

    st.markdown("### Expert Tutor Lesson")
    st.caption("This is not a reference card. Read it as the teacher walkthrough before missions.")

    sections = narrative.get("sections", []) or []
    for section in sections:
        style = str(section.get("style", "normal"))
        css_class = "callout-good" if style == "good" else "callout-risk" if style == "risk" else ""
        render_static_card(section.get("heading", "Section"), section.get("body", ""), css_class)

    mission_prep = narrative.get("mission_prep", []) or []
    if mission_prep:
        st.markdown("### Mission-by-Mission Prep")
        st.caption("This is the bridge between what was taught and what you are about to answer. It is visible by default because hidden prep is useless.")
        for item in mission_prep:
            with st.container(border=True):
                st.markdown(f"#### {item.get('title', 'Mission')}")
                question = item.get("question", "")
                if question:
                    st.markdown("**Question**")
                    st.write(question)

                tested_skill = item.get("tested_skill") or item.get("what_it_tests") or "Apply the topic mechanism to the mission scenario."
                st.markdown("**What this is really testing**")
                st.info(tested_skill)

                must_include = item.get("must_include", []) or []
                if must_include:
                    st.markdown("**Strong answer must include**")
                    for point in must_include:
                        st.markdown(f"- {point}")

                answer_shape = item.get("answer_shape", "")
                if answer_shape:
                    st.markdown("**Answer shape**")
                    st.success(answer_shape)

                avoid = item.get("avoid", "")
                if avoid:
                    st.markdown("**Do not waste words on**")
                    st.warning(avoid)

                how_to_answer = item.get("how_to_answer", "")
                if how_to_answer:
                    st.caption(how_to_answer)
    return True


def render_booster_walkthrough(booster: Dict[str, Any]) -> None:
    st.markdown("### Study Booster")
    st.caption("This bridges the gap between the concept note and mission-quality answers. It is not an answer bank.")

    c1, c2 = st.columns(2)
    with c1:
        render_static_card("In One Line", booster.get("plain_language", ""), "callout-good")
    with c2:
        render_static_card("Worked Example", booster.get("worked_example", ""))

    c1, c2 = st.columns(2)
    with c1:
        render_static_card("Common Production Trap", booster.get("production_trap", ""), "callout-risk")
    with c2:
        render_static_card("How To Approach Missions", booster.get("mission_hint", ""))

    key_distinctions = booster.get("key_distinctions", []) or []
    if key_distinctions:
        render_static_card("Key Distinctions You Must Know", key_distinctions, "callout-good")

    answer_frame = booster.get("answer_frame", []) or []
    if answer_frame:
        render_static_card("Mission Answer Frame", answer_frame)

    focus = booster.get("mission_focus", []) or []
    if focus:
        render_static_card("Evaluator Will Look For", focus)


def render_mission_bridge(booster: Dict[str, Any], assessment_doc: Dict[str, Any]) -> None:
    bridge_items = booster.get("mission_bridge", []) or []
    questions = assessment_doc.get("questions", []) or []
    if not bridge_items and not questions:
        return

    st.markdown("### Mission Readiness Map")
    st.caption("This is the contract between what was taught and what each mission expects. Use it to plan, not to copy.")

    bridge_by_type = {
        str(item.get("mission_type", "")): item
        for item in bridge_items
        if isinstance(item, dict)
    }

    for idx, question in enumerate(questions, start=1):
        qtype = str(question.get("type", "mission"))
        bridge = bridge_by_type.get(qtype, {})
        title = qtype.replace("_", " ").title()
        with st.expander(f"Mission {idx} . {title} . what this is testing", expanded=(idx == 1)):
            tested = bridge.get("tested_skill") or "Apply the concept to the exact scenario, then state the practical or architectural implication."
            taught = bridge.get("use_from_booster") or "Use the learning brief, study booster, and the mission scenario. Avoid generic definitions."
            st.markdown("**Tested skill**")
            st.write(tested)
            st.markdown("**Use from booster**")
            st.info(taught)
            expected = question.get("expected_focus", []) or []
            if expected:
                st.markdown("**Evaluator focus**")
                for item in expected[:4]:
                    st.markdown(f"- {item}")


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
    status = row["status"]
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
    return status in {"not_started", "in_progress", "borderline", "revise", "completed"}


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

awaiting_run = find_latest_run("awaiting_user_answers")
stale_awaiting_run = None
if is_stale_awaiting_run(awaiting_run, progress_rows):
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
        f"Ignored stale active run for completed topic . {stale_state.get('topic_id')} . "
        "Start Next Lesson will use repaired Supabase progress."
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
    ]
)

# -----------------------------
# HOME TAB
# -----------------------------
with tabs[0]:
    st.subheader("Level Map")
    st.caption("V1 flow is linear: Start Next Lesson → Current Level → Save + Evaluate. The cards are progress indicators, not launch buttons.")

    if not progress_rows:
        st.warning("No progress tracker found.")
    else:
        cols_per_row = 3
        for i in range(0, len(progress_rows), cols_per_row):
            cols = st.columns(cols_per_row)
            for j, row in enumerate(progress_rows[i:i + cols_per_row]):
                with cols[j]:
                    render_level_card(row, st.session_state.selected_topic_id, rewards_state)

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

        booster = build_lesson_booster(topic_id, concept_note, architect_note, assessment_doc)

        artifacts = run_state.get("artifacts", {}) or {}
        practice_exercise = load_relative_json_or_none(artifacts.get("practice_exercise"))
        practice_submission_path = None
        practice_submission = None
        updated_practice_submission = None

        current_tabs = ["① Learn", "② Study Booster", "③ MCQs", "④ Missions + Verify"]
        if practice_exercise is not None:
            current_tabs.append("⑤ Code Lab")
            submit_tab_label = "⑥ Submit"
        else:
            submit_tab_label = "⑤ Submit"
        current_tabs.append(submit_tab_label)
        lesson_tabs = st.tabs(current_tabs)

        with lesson_tabs[0]:
            if not render_tutor_narrative_panel(topic_id):
                render_learning_brief(concept_note, architect_note)

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
            st.markdown("### Mission Response")
            st.caption("Answer in your own words. Aim for 80-140 words: definition, example, production risk, control. Do not write essays.")
            render_mission_bridge(booster, assessment_doc)
            st.divider()

            for i, item in enumerate(answers_doc["answers"], start=1):
                mission_type = item.get("type", "mission").replace("_", " ").title()
                st.markdown(
                    f"""
                    <div class="mission-card">
                        <div class="mission-card-title">Mission {i} . {html_text(mission_type)}</div>
                        <div class="mission-question">{html_text(item['question'])}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                answer_text = st.text_area(
                    label=f"Answer for {item['question_id']}",
                    value=item.get("answer", ""),
                    height=135,
                    key=f"{run_state['run_id']}_{item['question_id']}",
                    label_visibility="collapsed",
                )
                render_answer_pressure(item.get("type", "mission"), answer_text)
                render_writing_assist_panel(item.get("type", "mission"), answer_text)
                updated_answers["answers"].append(
                    {
                        "question_id": item["question_id"],
                        "type": item["type"],
                        "question": item["question"],
                        "answer": answer_text,
                    }
                )

            st.markdown("### Save + Verify Draft")
            st.caption("Save and Verify live here because they are part of writing missions. Final submission is separate.")
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
                st.caption("Practical V2 exercise. Written answers alone are no longer enough.")
                render_static_card(practice_exercise.get("title", "Practice Exercise"), practice_exercise.get("prompt", ""), "callout-good")

                code_text = st.text_area(
                    "Code submission",
                    value=practice_submission.get("code", practice_exercise.get("starter_code", "")),
                    height=260,
                    key=f"{run_state['run_id']}_practice_code",
                )
                interpretation_text = st.text_area(
                    "Practical interpretation",
                    value=practice_submission.get("interpretation", ""),
                    height=135,
                    key=f"{run_state['run_id']}_practice_interpretation",
                    help=practice_exercise.get("interpretation_prompt", "Explain what the result means."),
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
                st.info("Code Lab, if present, is included in final evaluation. Run it before submitting.")

            if st.button("Save + Evaluate", use_container_width=True):
                save_answers(answer_path, updated_answers)
                persist_mission_draft_to_supabase(run_state, topic_id, updated_answers)
                if updated_practice_submission is not None and practice_submission_path is not None:
                    save_answers(practice_submission_path, updated_practice_submission)
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
