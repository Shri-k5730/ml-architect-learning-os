from __future__ import annotations

import csv
import hashlib
import hmac
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import streamlit as st

from src.utils.rewards import get_topic_reward_state, load_rewards_state


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
    answer_path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


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


def needs_attention(row: Dict[str, str]) -> bool:
    last_decision = (row.get("last_decision") or "").lower()
    status = (row.get("status") or "").lower()
    return last_decision in {"borderline", "revise", "fail_prereq"} or status in {"borderline", "revise"}


def display_status_chip(row: Dict[str, str]) -> str:
    status = row.get("status", "")
    last_decision = (row.get("last_decision") or "").lower()

    if status == "completed" and last_decision == "borderline":
        return "🟧 Cleared · Improve"
    if status == "completed" and last_decision == "revise":
        return "🟥 Replay Recommended"
    return status_chip(status)


def compute_overall_metrics(progress_rows: List[Dict[str, str]]) -> Dict[str, Any]:
    completed = sum(1 for row in progress_rows if row.get("status") == "completed")
    borderline = sum(
        1
        for row in progress_rows
        if (row.get("last_decision") or "").lower() == "borderline"
        or row.get("status") == "borderline"
    )
    revise = sum(
        1
        for row in progress_rows
        if (row.get("last_decision") or "").lower() in {"revise", "fail_prereq"}
        or row.get("status") == "revise"
    )
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
    if needs_attention(row):
        return "🎯 Cleared · Improve for more stars"
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

    st.markdown("### Better Answers by Question")

    for item in coaching_items:
        qid = item.get("question_id", "")
        question = item.get("question", "")
        quality = item.get("answer_quality", "partial")

        with st.expander(f"{qid} . {quality.upper()} . {question}", expanded=False):
            st.markdown("**Your Answer**")
            st.write(item.get("your_answer", ""))

            st.markdown("**What Was Missing**")
            missing_items = item.get("what_was_missing", [])
            if missing_items:
                for missing in missing_items:
                    st.markdown(f"- {missing}")
            else:
                st.write("-")

            st.markdown("**Better Answer**")
            st.success(item.get("better_answer", ""))

            st.markdown("**Why This Is Better**")
            st.write(item.get("why_this_is_better", ""))

            st.markdown("**Architect Upgrade**")
            st.info(item.get("architect_upgrade", ""))

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
            <div class="level-status">{display_status_chip(row)}</div>
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

progress_rows = load_progress_tracker()
rewards_state = load_rewards_state()
metrics = compute_overall_metrics(progress_rows)

awaiting_run = find_latest_run("awaiting_user_answers")
latest_run = find_latest_run()
latest_eval_run = get_latest_evaluation_run()

if "selected_topic_id" not in st.session_state:
    st.session_state.selected_topic_id = None

top_c1, top_c2, top_c3, top_c4, top_c5, top_c6 = st.columns(6)
top_c1.metric("Completed Levels", metrics["completed"])
top_c2.metric("Unlocked", metrics["unlocked"])
top_c3.metric("Needs Attention", metrics["borderline"] + metrics["revise"])
top_c4.metric("Avg Score", metrics["overall_avg"] if metrics["overall_avg"] is not None else "-")
top_c5.metric("Total XP", rewards_state.get("total_xp", 0))
top_c6.metric("Badges", len(rewards_state.get("badges_unlocked", [])))

if awaiting_run is not None:
    active_state = load_json(awaiting_run / "run_state.json")
    st.warning(f"Active lesson in progress . {active_state['topic_id']} . Finish active lesson first.")

action_c1, action_c2 = st.columns([1, 1])

with action_c1:
    if st.button(
        "Start Next Lesson",
        use_container_width=True,
        disabled=awaiting_run is not None,
    ):
        ok, output = start_lesson_for_topic(None)
        if ok:
            st.success("New lesson created.")
        else:
            st.error("Failed to start lesson.")
        st.code(output)
        st.rerun()

with action_c2:
    if st.button("Evaluate Current Lesson", use_container_width=True):
        if awaiting_run is None:
            st.warning("No lesson is currently awaiting answers.")
        else:
            ok, output = run_module("src.evaluate_lesson")
            if ok:
                st.success("Lesson evaluated.")
            else:
                st.error("Lesson evaluation failed.")
            st.code(output)
            st.rerun()

if latest_run:
    state = load_json(latest_run / "run_state.json")
    st.caption(
        f"Latest run: {state.get('run_id')} | topic: {state.get('topic_id')} | phase: {state.get('phase')} | status: {state.get('status')}"
    )

tabs = st.tabs(
    [
        "🏠 Home",
        "🎮 Current Level",
        "📊 Last Evaluation",
        "📈 Trajectory",
        "📚 Notes Vault",
        "🏆 Rewards",
    ]
)

# -----------------------------
# HOME TAB
# -----------------------------
with tabs[0]:
    st.subheader("Level Map")

    if not progress_rows:
        st.warning("No progress tracker found.")
    else:
        cols_per_row = 3
        for i in range(0, len(progress_rows), cols_per_row):
            cols = st.columns(cols_per_row)
            for j, row in enumerate(progress_rows[i:i + cols_per_row]):
                topic_id = row["topic_id"]
                with cols[j]:
                    render_level_card(row, st.session_state.selected_topic_id, rewards_state)

                    button_cols = st.columns(2)
                    with button_cols[0]:
                        if st.button(f"Inspect {topic_id}", key=f"inspect_{topic_id}"):
                            st.session_state.selected_topic_id = topic_id
                            st.rerun()

                    with button_cols[1]:
                        playable = is_playable_status(row["status"])
                        if st.button(
                            f"Play {topic_id}",
                            key=f"play_{topic_id}",
                            disabled=(not playable) or (awaiting_run is not None),
                        ):
                            ok, output = start_lesson_for_topic(topic_id)
                            if ok:
                                st.success(f"Started {topic_id}.")
                            else:
                                st.error(f"Failed to start {topic_id}.")
                            st.code(output)
                            st.rerun()

    st.divider()
    st.subheader("Latest Result")
    render_latest_evaluation_panel()

# -----------------------------
# CURRENT LEVEL TAB
# -----------------------------
with tabs[1]:
    if awaiting_run is None:
        st.info("No active lesson. Start or replay a level from Home.")
    else:
        run_state = load_json(awaiting_run / "run_state.json")
        topic_id = run_state["topic_id"]

        concept_note = load_json(awaiting_run / "concept_note.json")
        architect_note = load_json(awaiting_run / "architect_note.json")

        answer_path = PROJECT_ROOT / run_state["artifacts"]["answers"]
        answers_doc = load_json(answer_path)

        st.subheader(f"Current Level . {concept_note['title']}")
        mission_types = sorted({item["type"] for item in answers_doc["answers"]})
        st.caption(f"Mission types: {', '.join(mission_types)}")

        left, right = st.columns([1.05, 0.95])

        with left:
            st.markdown("### Concept")
            st.write(concept_note["simple_explanation"])

            st.markdown("### Wrong Mental Model")
            st.write(concept_note["wrong_mental_model"])

            st.markdown("### Correct Mental Model")
            st.write(concept_note["correct_mental_model"])

            st.markdown("### Tiny Example")
            st.write(concept_note["tiny_example"])

            st.markdown("### Why It Matters")
            st.write(concept_note["why_it_matters"])

            st.markdown("### Edge Case")
            st.write(concept_note["edge_case"])

            st.markdown("### Three Takeaways")
            for item in concept_note["three_takeaways"]:
                st.markdown(f"- {item}")

            st.divider()

            st.markdown("### Architect Lens")
            st.write(architect_note["architect_summary"])

            st.markdown("**Design Implications**")
            for item in architect_note["design_implications"]:
                st.markdown(f"- {item}")

            st.markdown("**Common Mistakes**")
            for item in architect_note["common_mistakes"]:
                st.markdown(f"- {item}")

            st.markdown("**Production Risks**")
            for item in architect_note["production_risks"]:
                st.markdown(f"- {item}")

            st.markdown("**Interview Framing**")
            st.write(architect_note["interview_framing"])

        with right:
            st.subheader("Mission Response")

            updated_answers = {
                "topic_id": answers_doc["topic_id"],
                "status": "pending_user_answers",
                "answers": [],
            }

            for i, item in enumerate(answers_doc["answers"], start=1):
                mission_type = item.get("type", "mission").replace("_", " ").title()
                st.markdown(f"**Mission {i} · {mission_type}**")
                st.markdown(item["question"])
                answer_text = st.text_area(
                    label=f"Answer for {item['question_id']}",
                    value=item.get("answer", ""),
                    height=110,
                    key=f"{run_state['run_id']}_{item['question_id']}",
                    label_visibility="collapsed",
                )
                updated_answers["answers"].append(
                    {
                        "question_id": item["question_id"],
                        "type": item["type"],
                        "question": item["question"],
                        "answer": answer_text,
                    }
                )

            save_c1, save_c2 = st.columns([1, 1])

            with save_c1:
                if st.button("Save Answers", use_container_width=True):
                    save_answers(answer_path, updated_answers)
                    st.success("Answers saved.")

            with save_c2:
                if st.button("Save + Evaluate", use_container_width=True):
                    save_answers(answer_path, updated_answers)
                    ok, output = run_module("src.evaluate_lesson")
                    if ok:
                        st.success("Lesson evaluated.")
                    else:
                        st.error("Lesson evaluation failed.")
                    st.code(output)
                    st.rerun()



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
# REWARDS TAB
# -----------------------------
with tabs[5]:
    st.subheader("Rewards")

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
            st.markdown(f"- **{badge['label']}** . {badge['description']}")

    reward_history = rewards_state.get("history", [])
    st.markdown("### Recent Rewards")
    if not reward_history:
        st.info("No reward history yet.")
    else:
        st.dataframe(reward_history[-10:], use_container_width=True)
