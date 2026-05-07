from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
RUNS_DIR = PROJECT_ROOT / "runs"
ASSESSMENTS_DIR = PROJECT_ROOT / "assessments"
NOTES_DIR = PROJECT_ROOT / "notes"
PROGRESS_TRACKER_PATH = DATA_DIR / "progress_tracker.csv"
REWARDS_STATE_PATH = DATA_DIR / "rewards_state.json"
RUN_HISTORY_PATH = DATA_DIR / "run_history.jsonl"
WEAK_SPOTS_LOG_PATH = DATA_DIR / "weak_spots_log.csv"
TOPIC_UNLOCK_RULES_PATH = PROJECT_ROOT / "topics" / "topic_unlock_rules.json"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def ensure_runtime_dirs() -> None:
    for path in [
        DATA_DIR,
        RUNS_DIR,
        ASSESSMENTS_DIR / "answers",
        ASSESSMENTS_DIR / "questions",
        ASSESSMENTS_DIR / "evaluations",
        NOTES_DIR / "concepts",
        NOTES_DIR / "architect_lens",
        NOTES_DIR / "refined",
    ]:
        path.mkdir(parents=True, exist_ok=True)

    if not RUN_HISTORY_PATH.exists():
        RUN_HISTORY_PATH.write_text("", encoding="utf-8")
    if not WEAK_SPOTS_LOG_PATH.exists():
        WEAK_SPOTS_LOG_PATH.write_text("topic_id,run_id,weak_spot,created_at\n", encoding="utf-8")


def _read_csv_rows(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def _write_csv_rows(path: Path, rows: List[Dict[str, str]]) -> None:
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0].keys())
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _load_unlock_sequence() -> List[str]:
    try:
        data = json.loads(TOPIC_UNLOCK_RULES_PATH.read_text(encoding="utf-8"))
        seq = data.get("sequence", [])
        if isinstance(seq, list) and seq:
            return [str(item) for item in seq]
    except Exception:
        pass
    return [f"mlf_{i:03d}" for i in range(1, 11)]


def normalize_progress_rows(rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """Force V1 progress into strict linear unlock order.

    This prevents branch/random unlocks after Streamlit restarts or after old runs.
    """
    if not rows:
        return rows

    by_id = {row.get("topic_id", ""): dict(row) for row in rows}
    sequence = _load_unlock_sequence()
    output: List[Dict[str, str]] = []
    prior_complete = True

    for topic_id in sequence:
        row = by_id.get(topic_id)
        if row is None:
            continue

        status = (row.get("status") or "locked").strip()
        is_complete = status == "completed"

        if is_complete:
            row["prerequisites_unlocked"] = "true"
            prior_complete = True
        elif prior_complete:
            row["prerequisites_unlocked"] = "true"
            if status == "locked":
                row["status"] = "not_started"
            prior_complete = False
        else:
            row["prerequisites_unlocked"] = "false"
            if status != "locked":
                row["status"] = "locked"
            prior_complete = False

        output.append(row)

    # Preserve any unknown rows after known sequence, but lock them.
    known = {row.get("topic_id") for row in output}
    for row in rows:
        if row.get("topic_id") not in known:
            row = dict(row)
            row["prerequisites_unlocked"] = "false"
            row["status"] = "locked"
            output.append(row)

    return output


def persist_progress_to_supabase(rows: Optional[List[Dict[str, str]]] = None) -> None:
    try:
        from src.utils.supabase_store import upsert_state

        if rows is None:
            rows = _read_csv_rows(PROGRESS_TRACKER_PATH)
        rows = normalize_progress_rows(rows)
        upsert_state("progress_tracker", {"rows": rows, "updated_at": utc_now_iso()})
    except Exception:
        return


def persist_rewards_to_supabase(state: Optional[Dict[str, Any]] = None) -> None:
    try:
        from src.utils.rewards import load_rewards_state, normalize_rewards_state
        from src.utils.supabase_store import upsert_state

        if state is None:
            state = load_rewards_state(prefer_cloud=False)
        state = normalize_rewards_state(state)
        upsert_state("rewards_state", state)
    except Exception:
        return


def hydrate_progress_from_supabase() -> bool:
    try:
        from src.utils.supabase_store import fetch_state

        state = fetch_state("progress_tracker")
        if not isinstance(state, dict):
            return False
        rows = state.get("rows")
        if not isinstance(rows, list) or not rows:
            return False
        normalized = normalize_progress_rows([dict(row) for row in rows if isinstance(row, dict)])
        _write_csv_rows(PROGRESS_TRACKER_PATH, normalized)
        # Persist normalized version back to cloud so old branch unlocks get cleaned.
        persist_progress_to_supabase(normalized)
        return True
    except Exception:
        return False


def hydrate_rewards_from_supabase() -> bool:
    try:
        from src.utils.rewards import normalize_rewards_state
        from src.utils.supabase_store import fetch_state

        state = fetch_state("rewards_state")
        if not isinstance(state, dict):
            return False
        normalized = normalize_rewards_state(state)
        REWARDS_STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
        REWARDS_STATE_PATH.write_text(json.dumps(normalized, indent=2, ensure_ascii=False), encoding="utf-8")
        persist_rewards_to_supabase(normalized)
        return True
    except Exception:
        return False


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text or "", encoding="utf-8")


def hydrate_run_from_supabase(run_id: str) -> bool:
    try:
        from src.utils.supabase_store import fetch_run, fetch_run_artifacts

        run_row = fetch_run(run_id)
        if not isinstance(run_row, dict):
            return False

        run_state = run_row.get("run_state") or {}
        if not isinstance(run_state, dict):
            return False

        run_dir = RUNS_DIR / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        _write_json(run_dir / "run_state.json", run_state)

        artifacts = fetch_run_artifacts(run_id)
        for item in artifacts:
            artifact_type = item.get("artifact_type")
            payload = item.get("payload")
            text_payload = item.get("text_payload")

            if artifact_type == "selected_topic":
                _write_json(run_dir / "selected_topic.json", payload)
            elif artifact_type == "concept_note":
                _write_json(run_dir / "concept_note.json", payload)
            elif artifact_type == "architect_note":
                _write_json(run_dir / "architect_note.json", payload)
            elif artifact_type == "assessment":
                _write_json(run_dir / "assessment.json", payload)
            elif artifact_type == "answer_template":
                answer_path = PROJECT_ROOT / run_state.get("artifacts", {}).get(
                    "answers", f"assessments/answers/{run_id}_answers.json"
                )
                _write_json(answer_path, payload)
            elif artifact_type == "answers":
                _write_json(run_dir / "answers.json", payload)
            elif artifact_type == "evaluation":
                _write_json(run_dir / "evaluation.json", payload)
            elif artifact_type == "answer_coaching":
                _write_json(run_dir / "answer_coaching.json", payload)
            elif artifact_type == "answer_coaching_error":
                _write_json(run_dir / "answer_coaching_error.json", payload)
            elif artifact_type == "rewards":
                _write_json(run_dir / "rewards.json", payload)
            elif artifact_type == "logs":
                _write_text(run_dir / "logs.txt", text_payload or json.dumps(payload or {}, indent=2))

        return True
    except Exception:
        return False


def hydrate_latest_runs_from_supabase() -> None:
    try:
        from src.utils.supabase_store import fetch_latest_run_by_phase

        for phase in ["awaiting_user_answers", "evaluation_complete"]:
            row = fetch_latest_run_by_phase(phase)
            if isinstance(row, dict) and row.get("run_id"):
                hydrate_run_from_supabase(str(row["run_id"]))
    except Exception:
        return


def bootstrap_cloud_state() -> Dict[str, Any]:
    """Hydrate local runtime from Supabase, then mirror local fallback to Supabase.

    Call once after authentication and before reading progress/rewards in the UI.
    """
    ensure_runtime_dirs()
    progress_loaded = hydrate_progress_from_supabase()
    rewards_loaded = hydrate_rewards_from_supabase()
    hydrate_latest_runs_from_supabase()

    if not progress_loaded and PROGRESS_TRACKER_PATH.exists():
        rows = normalize_progress_rows(_read_csv_rows(PROGRESS_TRACKER_PATH))
        _write_csv_rows(PROGRESS_TRACKER_PATH, rows)
        persist_progress_to_supabase(rows)

    if not rewards_loaded and REWARDS_STATE_PATH.exists():
        persist_rewards_to_supabase()

    return {
        "progress_from_cloud": progress_loaded,
        "rewards_from_cloud": rewards_loaded,
        "hydrated_at": utc_now_iso(),
    }
