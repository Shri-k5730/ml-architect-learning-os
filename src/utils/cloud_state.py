from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from src.utils.curriculum_catalog import load_topic_catalog_dicts, seed_supabase_catalog_from_local_if_empty
from src.utils.rewards import normalize_rewards_state
from src.utils.supabase_store import get_supabase_client, supabase_enabled, upsert_learner_progress_rows, upsert_state


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
TOPICS_DIR = PROJECT_ROOT / "topics"
PROGRESS_TRACKER_PATH = DATA_DIR / "progress_tracker.csv"
REWARDS_STATE_PATH = DATA_DIR / "rewards_state.json"
RUN_HISTORY_PATH = DATA_DIR / "run_history.jsonl"

PROGRESS_FIELDS = [
    "topic_id",
    "title",
    "domain",
    "difficulty",
    "status",
    "attempt_count",
    "last_score_conceptual",
    "last_score_practical",
    "last_score_architect",
    "last_score_communication",
    "last_score_coding",
    "last_decision",
    "prerequisites_unlocked",
    "last_attempted_at",
    "completed_at",
]

CLEAR_DECISIONS = {"pass", "borderline"}


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _as_int(value: Any, default: int = 0) -> int:
    try:
        if value is None or str(value).strip() == "":
            return default
        return int(value)
    except Exception:
        return default


def _load_topic_catalog() -> List[Dict[str, Any]]:
    # Supabase is the V2 curriculum source of truth. Local JSON is only fallback.
    return load_topic_catalog_dicts(prefer_supabase=True)


def _default_progress_rows() -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    for idx, topic in enumerate(_load_topic_catalog()):
        rows.append(
            {
                "topic_id": str(topic.get("topic_id", "")),
                "title": str(topic.get("title", "")),
                "domain": str(topic.get("domain", "")),
                "difficulty": str(topic.get("difficulty", "")),
                "status": "not_started" if idx == 0 else "locked",
                "attempt_count": "0",
                "last_score_conceptual": "",
                "last_score_practical": "",
                "last_score_architect": "",
                "last_score_communication": "",
                "last_score_coding": "",
                "last_decision": "",
                "prerequisites_unlocked": "true" if idx == 0 else "false",
                "last_attempted_at": "",
                "completed_at": "",
            }
        )
    return rows


def _write_progress_rows(rows: List[Dict[str, str]]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with PROGRESS_TRACKER_PATH.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=PROGRESS_FIELDS, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in PROGRESS_FIELDS})




def _none_if_empty(value: Any) -> Optional[str]:
    value = str(value or "").strip()
    return value or None


def _int_or_none(value: Any) -> Optional[int]:
    value = str(value or "").strip()
    if not value:
        return None
    try:
        return int(value)
    except Exception:
        return None


def _persist_progress_rows_to_supabase_table(rows: List[Dict[str, str]]) -> None:
    payload = []
    for row in rows:
        payload.append(
            {
                "topic_id": row["topic_id"],
                "status": row.get("status") or "locked",
                "attempt_count": _as_int(row.get("attempt_count"), 0),
                "last_run_id": None,
                "last_decision": _none_if_empty(row.get("last_decision")),
                "last_score_conceptual": _int_or_none(row.get("last_score_conceptual")),
                "last_score_practical": _int_or_none(row.get("last_score_practical")),
                "last_score_architect": _int_or_none(row.get("last_score_architect")),
                "last_score_communication": _int_or_none(row.get("last_score_communication")),
                "last_score_coding": _int_or_none(row.get("last_score_coding")),
                "completed_at": _none_if_empty(row.get("completed_at")),
                "last_attempted_at": _none_if_empty(row.get("last_attempted_at")),
                "updated_at": utc_now_iso(),
            }
        )
    try:
        upsert_learner_progress_rows(payload)
    except Exception:
        # Table may not be created yet. mlos_state still preserves the JSON copy.
        return

def _write_rewards_state(state: Dict[str, Any]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    REWARDS_STATE_PATH.write_text(
        json.dumps(normalize_rewards_state(state), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def _fetch_artifacts_by_type(artifact_type: str) -> List[Dict[str, Any]]:
    if not supabase_enabled():
        return []

    client = get_supabase_client()
    if client is None:
        return []

    result = (
        client.table("mlos_artifacts")
        .select("run_id,topic_id,artifact_type,payload,created_at")
        .eq("artifact_type", artifact_type)
        .order("created_at", desc=False)
        .execute()
    )
    return getattr(result, "data", None) or []


def _fetch_runs() -> List[Dict[str, Any]]:
    if not supabase_enabled():
        return []

    client = get_supabase_client()
    if client is None:
        return []

    result = (
        client.table("mlos_runs")
        .select("run_id,topic_id,topic_title,phase,status,created_at,updated_at")
        .order("created_at", desc=False)
        .execute()
    )
    return getattr(result, "data", None) or []


def _rebuild_progress_from_evaluations() -> Tuple[List[Dict[str, str]], int]:
    rows = _default_progress_rows()
    if not rows:
        return rows, 0

    row_by_topic = {row["topic_id"]: row for row in rows}
    evaluation_artifacts = _fetch_artifacts_by_type("evaluation")
    run_status_by_id = {row.get("run_id"): row.get("status") for row in _fetch_runs()}

    processed = 0
    for artifact in evaluation_artifacts:
        topic_id = str(artifact.get("topic_id") or "").strip()
        if topic_id not in row_by_topic:
            continue

        payload = artifact.get("payload") or {}
        if not isinstance(payload, dict):
            continue

        row = row_by_topic[topic_id]
        decision = str(payload.get("decision") or "").strip().lower()
        run_status = str(run_status_by_id.get(artifact.get("run_id")) or "").strip().lower()
        scores = payload.get("scores") or {}
        created_at = str(artifact.get("created_at") or utc_now_iso())

        row["attempt_count"] = str(_as_int(row.get("attempt_count"), 0) + 1)
        row["last_decision"] = decision
        row["last_attempted_at"] = created_at
        row["last_score_conceptual"] = str(scores.get("conceptual_clarity", ""))
        row["last_score_practical"] = str(scores.get("practical_reasoning", ""))
        row["last_score_architect"] = str(scores.get("architect_reasoning", ""))
        row["last_score_communication"] = str(scores.get("communication", ""))

        if decision in CLEAR_DECISIONS or run_status == "completed":
            row["status"] = "completed"
            row["prerequisites_unlocked"] = "true"
            row["completed_at"] = created_at
        elif decision in {"revise", "fail_prereq"}:
            # Keep the failed/revise topic as the next playable level after linear repair.
            row["status"] = "not_started"

        processed += 1

    rows = _enforce_v1_linear_rows(rows)
    return rows, processed


def _enforce_v1_linear_rows(rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """Strict V1: completed prefix, first incomplete unlocked, all later locked.

    This repairs stale branch unlocks and old corrupted cloud state.
    """
    first_incomplete_seen = False
    prior_gap = False

    for row in rows:
        status = str(row.get("status") or "").strip().lower()

        if status == "completed" and not prior_gap:
            row["status"] = "completed"
            row["prerequisites_unlocked"] = "true"
            continue

        # If a later topic says completed despite an earlier gap, V1 must not keep it completed.
        if status == "completed" and prior_gap:
            row["completed_at"] = ""

        if not first_incomplete_seen:
            first_incomplete_seen = True
            prior_gap = True
            row["status"] = "not_started"
            row["prerequisites_unlocked"] = "true"
        else:
            prior_gap = True
            row["status"] = "locked"
            row["prerequisites_unlocked"] = "false"

    return rows


def _rebuild_rewards_from_artifacts(progress_rows: List[Dict[str, str]]) -> Tuple[Dict[str, Any], int]:
    reward_artifacts = _fetch_artifacts_by_type("rewards")
    history: List[Dict[str, Any]] = []

    for artifact in reward_artifacts:
        payload = artifact.get("payload") or {}
        if not isinstance(payload, dict):
            continue
        payload = dict(payload)
        payload.setdefault("run_id", artifact.get("run_id"))
        payload.setdefault("topic_id", artifact.get("topic_id"))
        payload.setdefault("created_at", artifact.get("created_at"))
        payload.setdefault("status", "completed" if payload.get("completed") else payload.get("decision"))
        history.append(payload)

    if history:
        latest_total = max(_as_int(row.get("total_xp"), 0) for row in history)
        state = {
            "total_xp": latest_total,
            "badges_unlocked": [],
            "streaks": {
                "current_completion_streak": 0,
                "best_completion_streak": 0,
            },
            "topics": {},
            "history": history,
        }
        return normalize_rewards_state(state), len(history)

    # Fallback if reward artifacts are absent: rebuild minimal rewards from progress.
    minimal_history: List[Dict[str, Any]] = []
    running_xp = 0
    for row in progress_rows:
        if row.get("status") != "completed":
            continue
        scores = {
            "conceptual_clarity": _as_int(row.get("last_score_conceptual"), 1),
            "practical_reasoning": _as_int(row.get("last_score_practical"), 1),
            "architect_reasoning": _as_int(row.get("last_score_architect"), 1),
            "communication": _as_int(row.get("last_score_communication"), 1),
        }
        avg = sum(scores.values()) / 4
        stars = max(1, min(5, round(avg)))
        xp = 25 + stars * 5
        running_xp += xp
        minimal_history.append(
            {
                "run_id": f"rebuilt_{row['topic_id']}",
                "topic_id": row["topic_id"],
                "topic_title": row.get("title", row["topic_id"]),
                "decision": row.get("last_decision") or "borderline",
                "status": "completed",
                "completed": True,
                "xp_earned": xp,
                "total_xp": running_xp,
                "stars_earned": stars,
                "best_stars": stars,
                "badges_awarded": [],
            }
        )

    state = {
        "total_xp": running_xp,
        "badges_unlocked": [],
        "streaks": {
            "current_completion_streak": 0,
            "best_completion_streak": 0,
        },
        "topics": {},
        "history": minimal_history,
    }
    return normalize_rewards_state(state), len(minimal_history)


def repair_cloud_state_on_startup(force: bool = True) -> Dict[str, Any]:
    """Rebuild durable V1 state from Supabase run artifacts.

    This prevents Streamlit Cloud sleep/restart from resetting progress and prevents
    stale local files from overwriting good cloud history.
    """
    summary: Dict[str, Any] = {
        "supabase_enabled": supabase_enabled(),
        "progress_rebuilt": False,
        "rewards_rebuilt": False,
        "evaluation_artifacts_used": 0,
        "reward_artifacts_used": 0,
        "catalog_seed": None,
        "error": None,
    }

    if not supabase_enabled():
        return summary

    try:
        summary["catalog_seed"] = seed_supabase_catalog_from_local_if_empty()

        progress_rows, eval_count = _rebuild_progress_from_evaluations()
        if progress_rows:
            _write_progress_rows(progress_rows)
            upsert_state("progress_tracker", {"rows": progress_rows, "updated_at": utc_now_iso(), "source": "rebuilt_from_evaluations"})
            _persist_progress_rows_to_supabase_table(progress_rows)
            summary["progress_rebuilt"] = True
            summary["evaluation_artifacts_used"] = eval_count

        rewards_state, reward_count = _rebuild_rewards_from_artifacts(progress_rows)
        _write_rewards_state(rewards_state)
        if reward_count > 0 or rewards_state.get("total_xp", 0) > 0:
            upsert_state("rewards_state", {**rewards_state, "updated_at": utc_now_iso(), "source": "rebuilt_from_reward_artifacts"})
        summary["rewards_rebuilt"] = True
        summary["reward_artifacts_used"] = reward_count

        # Keep a local empty run history file if it is missing.
        RUN_HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
        if not RUN_HISTORY_PATH.exists():
            RUN_HISTORY_PATH.write_text("", encoding="utf-8")

    except Exception as exc:
        summary["error"] = str(exc)

    return summary

# Backward-compatible alias for older app.py versions.
def bootstrap_cloud_state(force: bool = True):
    return repair_cloud_state_on_startup(force=force)
