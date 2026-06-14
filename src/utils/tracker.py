from __future__ import annotations

import csv
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.utils.curriculum_catalog import load_topic_catalog_dicts


PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROGRESS_TRACKER_PATH = PROJECT_ROOT / "data" / "progress_tracker.csv"
WEAK_SPOTS_LOG_PATH = PROJECT_ROOT / "data" / "weak_spots_log.csv"

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


class TrackerError(Exception):
    """Raised when tracker operations fail."""


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _read_csv_rows(file_path: Path) -> list[Dict[str, str]]:
    if not file_path.exists():
        raise TrackerError(f"CSV file not found: {file_path}")

    with file_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        return [_normalize_progress_row(row) for row in reader]


def _write_csv_rows(file_path: Path, rows: list[Dict[str, str]], fieldnames: Optional[list[str]] = None) -> None:
    file_path.parent.mkdir(parents=True, exist_ok=True)
    final_fieldnames = fieldnames or PROGRESS_FIELDS
    with file_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=final_fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in final_fieldnames})


def _normalize_progress_row(row: Dict[str, Any]) -> Dict[str, str]:
    normalized = {field: str(row.get(field, "") or "") for field in PROGRESS_FIELDS}
    if not normalized["attempt_count"]:
        normalized["attempt_count"] = "0"
    if not normalized["status"]:
        normalized["status"] = "locked"
    if not normalized["prerequisites_unlocked"]:
        normalized["prerequisites_unlocked"] = "false"
    return normalized


def _none_if_empty(value: str) -> Optional[str]:
    value = str(value or "").strip()
    return value or None


def _int_or_none(value: str) -> Optional[int]:
    value = str(value or "").strip()
    if not value:
        return None
    try:
        return int(value)
    except Exception:
        return None


def _progress_row_to_supabase(row: Dict[str, str]) -> Dict[str, Any]:
    return {
        "topic_id": row["topic_id"],
        "status": row.get("status") or "locked",
        "attempt_count": int(row.get("attempt_count") or 0),
        "last_run_id": None,
        "last_decision": _none_if_empty(row.get("last_decision", "")),
        "last_score_conceptual": _int_or_none(row.get("last_score_conceptual", "")),
        "last_score_practical": _int_or_none(row.get("last_score_practical", "")),
        "last_score_architect": _int_or_none(row.get("last_score_architect", "")),
        "last_score_communication": _int_or_none(row.get("last_score_communication", "")),
        "last_score_coding": _int_or_none(row.get("last_score_coding", "")),
        "completed_at": _none_if_empty(row.get("completed_at", "")),
        "last_attempted_at": _none_if_empty(row.get("last_attempted_at", "")),
        "updated_at": utc_now_iso(),
    }


def _completed_count(rows: list[Dict[str, str]]) -> int:
    return sum(1 for row in rows if str(row.get("status") or "").strip().lower() == "completed")


def _unlocked_incomplete_count(rows: list[Dict[str, str]]) -> int:
    count = 0
    for row in rows:
        status = str(row.get("status") or "").strip().lower()
        unlocked = str(row.get("prerequisites_unlocked") or "").strip().lower() == "true"
        if unlocked and status != "completed":
            count += 1
    return count


def _fetch_state_progress_rows() -> list[Dict[str, str]]:
    """Read the repaired progress snapshot from mlos_state.

    Patch 006 introduced mlos_learner_progress, but real hosted history already
    lives in mlos_state + artifacts. If the table is stale, this snapshot is the
    safer source because cloud_state rebuilds it from evaluation artifacts.
    """
    try:
        from src.utils.supabase_store import fetch_state, supabase_enabled

        if not supabase_enabled():
            return []
        state = fetch_state("progress_tracker")
        if not isinstance(state, dict):
            return []
        rows = state.get("rows")
        if not isinstance(rows, list) or not rows:
            return []
        return [_normalize_progress_row(row) for row in rows if isinstance(row, dict)]
    except Exception:
        return []


def _choose_best_progress_rows(
    table_rows: list[Dict[str, str]],
    state_rows: list[Dict[str, str]],
) -> list[Dict[str, str]]:
    """Choose the least stale progress source.

    A stale mlos_learner_progress table can regress the learner to mlf_001.
    Prefer whichever source has more completed lessons; if tied, prefer the
    table because it is the newer normalized V2 structure.
    """
    if not table_rows and not state_rows:
        return []
    if not table_rows:
        return state_rows
    if not state_rows:
        return table_rows

    table_completed = _completed_count(table_rows)
    state_completed = _completed_count(state_rows)

    if state_completed > table_completed:
        return state_rows
    if table_completed > state_completed:
        return table_rows

    # Tie-breaker: prefer the source with an unlocked incomplete item. If only
    # one source has a playable next item, use that one. Otherwise use table.
    table_unlocked = _unlocked_incomplete_count(table_rows)
    state_unlocked = _unlocked_incomplete_count(state_rows)
    if state_unlocked > table_unlocked:
        return state_rows
    return table_rows



def _score_from_run_state(run_state: Dict[str, Any], key: str) -> Optional[int]:
    try:
        value = (run_state.get("scores") or {}).get(key)
        if value is None or value == "":
            return None
        return int(float(value))
    except Exception:
        return None


def _fetch_evaluation_mastery_from_runs() -> Dict[str, Dict[str, Any]]:
    """Return latest and best scored evaluation per topic from durable run history.

    V2.3 distinction:
    - latest attempt is useful for coaching;
    - best mastered attempt controls progression.
    """
    try:
        from src.utils.supabase_store import fetch_latest_runs, supabase_enabled

        if not supabase_enabled():
            return {}
        runs = fetch_latest_runs(limit=1000)
    except Exception:
        return {}

    by_topic: Dict[str, Dict[str, Any]] = {}
    for run in runs:
        if str(run.get("phase") or "") != "evaluation_complete":
            continue
        topic_id = str(run.get("topic_id") or "").strip()
        if not topic_id:
            continue
        state = run.get("run_state") or {}
        if not isinstance(state, dict):
            continue
        scores = {
            "last_score_conceptual": _score_from_run_state(state, "conceptual_clarity"),
            "last_score_practical": _score_from_run_state(state, "practical_reasoning"),
            "last_score_architect": _score_from_run_state(state, "architect_reasoning"),
            "last_score_communication": _score_from_run_state(state, "communication"),
        }
        present = [v for v in scores.values() if v is not None]
        if len(present) < 4:
            continue
        min_core = min(present)
        avg_core = sum(present) / len(present)
        record = {
            "run_id": run.get("run_id"),
            "topic_id": topic_id,
            "status": run.get("status") or state.get("status"),
            "decision": state.get("status") or run.get("status"),
            "updated_at": run.get("updated_at") or run.get("created_at"),
            "scores": scores,
            "min_core": min_core,
            "avg_core": avg_core,
        }
        bucket = by_topic.setdefault(topic_id, {"latest": None, "best": None})
        # fetch_latest_runs is newest first, so first seen is latest.
        if bucket["latest"] is None:
            bucket["latest"] = record
        best = bucket.get("best")
        if best is None or (min_core, avg_core) > (best.get("min_core", 0), best.get("avg_core", 0)):
            bucket["best"] = record
    return by_topic


def _apply_v23_best_mastery(rows: list[Dict[str, str]]) -> list[Dict[str, str]]:
    mastery = _fetch_evaluation_mastery_from_runs()
    if not mastery:
        return rows

    for row in rows:
        topic_id = str(row.get("topic_id") or "")
        info = mastery.get(topic_id) or {}
        latest = info.get("latest") or {}
        best = info.get("best") or {}
        if not latest and not best:
            continue

        if latest.get("updated_at"):
            row["last_attempted_at"] = str(latest.get("updated_at") or "")
        if latest.get("run_id"):
            row["last_run_id"] = str(latest.get("run_id") or "")

        # Progression is controlled by best mastery, not the latest redo failure.
        if best.get("min_core", 0) >= 3:
            row["status"] = "completed"
            row["last_decision"] = "mastered_best_attempt"
            for key, value in (best.get("scores") or {}).items():
                if value is not None:
                    row[key] = str(value)
            if not row.get("completed_at"):
                row["completed_at"] = str(best.get("updated_at") or utc_now_iso())
            continue

        # No mastered attempt exists. Keep the latest scores and mark for repair.
        if latest:
            row["status"] = "needs_attention"
            row["last_decision"] = str(latest.get("status") or "revise")
            for key, value in (latest.get("scores") or {}).items():
                if value is not None:
                    row[key] = str(value)
            row["completed_at"] = ""
    return rows


def _apply_v23_repair_unlocks(rows: list[Dict[str, str]]) -> list[Dict[str, str]]:
    """Unlock repair queue while keeping checkpoints/capstone/DL gated.

    The learner is in mastery-repair mode. Blocking every later ML repair item
    behind the first weak lesson creates the false impression that only one item
    exists. V2.3 unlocks all ML repair cards and gates only checkpoints/capstone/DL.
    """
    def mastered(row: Dict[str, str]) -> bool:
        try:
            scores = [int(float(row.get(k) or 0)) for k in [
                "last_score_conceptual", "last_score_practical", "last_score_architect", "last_score_communication"
            ]]
            return str(row.get("status") or "") == "completed" and min(scores) >= 3
        except Exception:
            return str(row.get("status") or "") == "completed"

    ml_rows = [r for r in rows if str(r.get("topic_id") or "").startswith("mlf_")]
    all_ml_mastered = bool(ml_rows) and all(mastered(r) for r in ml_rows)
    checkpoint_arch = next((r for r in rows if r.get("topic_id") == "checkpoint_ml_architect_001"), None)
    checkpoint_arch_mastered = bool(checkpoint_arch and mastered(checkpoint_arch))
    capstone = next((r for r in rows if r.get("topic_id") == "capstone_ml_architect_001"), None)
    capstone_mastered = bool(capstone and mastered(capstone))

    for row in rows:
        topic_id = str(row.get("topic_id") or "")
        status = str(row.get("status") or "").strip().lower()
        if topic_id.startswith("mlf_"):
            row["prerequisites_unlocked"] = "true"
            if status in {"revise", "borderline"}:
                row["status"] = "needs_attention"
            elif not status:
                row["status"] = "not_started"
            continue

        if topic_id == "checkpoint_ml_foundations_001":
            row["prerequisites_unlocked"] = "true" if all(
                mastered(r) for r in ml_rows if int(str(r.get("topic_id") or "mlf_000").split("_")[1]) <= 10
            ) else "false"
            if row["prerequisites_unlocked"] == "false" and row.get("status") != "completed":
                row["status"] = "locked"
            continue

        if topic_id == "checkpoint_ml_architect_001":
            row["prerequisites_unlocked"] = "true" if all_ml_mastered else "false"
            if not all_ml_mastered and row.get("status") != "completed":
                row["status"] = "locked"
            continue

        if topic_id == "capstone_ml_architect_001":
            row["prerequisites_unlocked"] = "true" if (all_ml_mastered and checkpoint_arch_mastered) else "false"
            if row["prerequisites_unlocked"] == "false" and row.get("status") != "completed":
                row["status"] = "locked"
            continue

        if topic_id.startswith("dl_"):
            row["prerequisites_unlocked"] = "true" if capstone_mastered and topic_id == "dl_001" else "false"
            if not capstone_mastered and row.get("status") != "completed":
                row["status"] = "locked"
            continue
    return rows

def _compose_progress_from_supabase_tables() -> list[Dict[str, str]]:
    try:
        from src.utils.supabase_store import fetch_learner_progress_rows, supabase_enabled

        if not supabase_enabled():
            return []

        catalog = load_topic_catalog_dicts(prefer_supabase=True)
        if not catalog:
            return []

        progress_rows = fetch_learner_progress_rows()
        progress_by_topic = {str(row.get("topic_id")): row for row in progress_rows}

        rows: list[Dict[str, str]] = []
        for idx, topic in enumerate(catalog):
            progress = progress_by_topic.get(topic["topic_id"], {})
            default_unlocked = idx == 0
            row = {
                "topic_id": topic["topic_id"],
                "title": topic.get("title", ""),
                "domain": topic.get("domain", ""),
                "difficulty": str(topic.get("difficulty", "")),
                "status": str(progress.get("status") or ("not_started" if default_unlocked else "locked")),
                "attempt_count": str(progress.get("attempt_count") or 0),
                "last_score_conceptual": str(progress.get("last_score_conceptual") or ""),
                "last_score_practical": str(progress.get("last_score_practical") or ""),
                "last_score_architect": str(progress.get("last_score_architect") or ""),
                "last_score_communication": str(progress.get("last_score_communication") or ""),
                "last_score_coding": str(progress.get("last_score_coding") or ""),
                "last_decision": str(progress.get("last_decision") or ""),
                "prerequisites_unlocked": "true" if default_unlocked else "false",
                "last_attempted_at": str(progress.get("last_attempted_at") or ""),
                "completed_at": str(progress.get("completed_at") or ""),
            }
            if row["status"] == "completed":
                row["prerequisites_unlocked"] = "true"
            rows.append(_normalize_progress_row(row))

        rows = _apply_v23_best_mastery(rows)
        return _apply_v23_repair_unlocks(rows)
    except Exception:
        return []


def _persist_progress_to_supabase(rows: list[Dict[str, str]]) -> None:
    try:
        from src.utils.supabase_store import upsert_learner_progress_rows, upsert_state

        normalized_rows = [_normalize_progress_row(row) for row in rows]
        upsert_state("progress_tracker", {"rows": normalized_rows, "updated_at": utc_now_iso(), "source": "tracker_write"})
        upsert_learner_progress_rows([_progress_row_to_supabase(row) for row in normalized_rows])
    except Exception:
        return


def hydrate_progress_from_supabase_if_available() -> bool:
    """Pull the best persisted progress source from Supabase into CSV cache.

    Supabase has two progress representations during the V2 transition:
    - mlos_learner_progress: normalized table, but it can be stale after migration.
    - mlos_state.progress_tracker: repaired snapshot rebuilt from artifacts.

    The selector must never trust a stale table that sends the learner back to
    mlf_001 after ten completed lessons.
    """
    table_rows: list[Dict[str, str]] = []
    state_rows: list[Dict[str, str]] = []

    try:
        table_rows = _compose_progress_from_supabase_tables()
    except Exception:
        table_rows = []

    try:
        state_rows = _fetch_state_progress_rows()
    except Exception:
        state_rows = []

    rows = _choose_best_progress_rows(table_rows, state_rows)
    if not rows:
        return False

    normalized = _apply_v23_repair_unlocks(_apply_v23_best_mastery([_normalize_progress_row(row) for row in rows]))
    _write_csv_rows(PROGRESS_TRACKER_PATH, normalized, PROGRESS_FIELDS)

    # If the repaired state is ahead of the normalized table, backfill the table.
    # This makes the next app/subprocess read consistent.
    if _completed_count(normalized) > _completed_count(table_rows):
        _persist_progress_to_supabase(normalized)

    return True


def _enforce_strict_linear_rows(rows: list[Dict[str, str]]) -> list[Dict[str, str]]:
    first_incomplete_seen = False
    prior_gap = False

    for row in rows:
        status = str(row.get("status") or "").strip().lower()

        if status == "completed" and not prior_gap:
            row["status"] = "completed"
            row["prerequisites_unlocked"] = "true"
            continue

        if status == "completed" and prior_gap:
            row["completed_at"] = ""

        if not first_incomplete_seen:
            first_incomplete_seen = True
            prior_gap = True
            row["status"] = "not_started" if status == "locked" else (status or "not_started")
            row["prerequisites_unlocked"] = "true"
        else:
            prior_gap = True
            row["status"] = "locked"
            row["prerequisites_unlocked"] = "false"

    return rows


def read_progress_rows() -> list[Dict[str, str]]:
    # Supabase is the V2 source of truth. The CSV is a cache used by existing modules.
    try:
        from src.utils.supabase_store import supabase_enabled

        if supabase_enabled() and hydrate_progress_from_supabase_if_available():
            return _read_csv_rows(PROGRESS_TRACKER_PATH)
    except Exception:
        pass

    try:
        rows = _read_csv_rows(PROGRESS_TRACKER_PATH)
        if rows:
            return rows
    except Exception:
        pass

    catalog = load_topic_catalog_dicts(prefer_supabase=True)
    rows = []
    for idx, topic in enumerate(catalog):
        rows.append(
            _normalize_progress_row(
                {
                    "topic_id": topic["topic_id"],
                    "title": topic.get("title", ""),
                    "domain": topic.get("domain", ""),
                    "difficulty": str(topic.get("difficulty", "")),
                    "status": "not_started" if idx == 0 else "locked",
                    "attempt_count": "0",
                    "prerequisites_unlocked": "true" if idx == 0 else "false",
                }
            )
        )
    if rows:
        write_progress_rows(rows)
    return rows


def write_progress_rows(rows: list[Dict[str, str]]) -> None:
    if not rows:
        raise TrackerError("Progress tracker rows are empty.")
    normalized_rows = [_normalize_progress_row(row) for row in rows]
    _write_csv_rows(PROGRESS_TRACKER_PATH, normalized_rows, PROGRESS_FIELDS)
    _persist_progress_to_supabase(normalized_rows)


def get_progress_row(topic_id: str) -> Optional[Dict[str, str]]:
    rows = read_progress_rows()
    for row in rows:
        if row["topic_id"] == topic_id:
            return row
    return None


def update_topic_status(
    topic_id: str,
    status: str,
    attempt_increment: bool = False,
    conceptual_score: Optional[int] = None,
    practical_score: Optional[int] = None,
    architect_score: Optional[int] = None,
    communication_score: Optional[int] = None,
    coding_score: Optional[int] = None,
    decision: Optional[str] = None,
    prerequisites_unlocked: Optional[bool] = None,
    completed: bool = False,
) -> None:
    rows = read_progress_rows()
    if not rows:
        raise TrackerError("Progress tracker is empty.")

    found = False

    for row in rows:
        if row["topic_id"] != topic_id:
            continue

        found = True
        row["status"] = status

        if attempt_increment:
            current_attempts = int(row.get("attempt_count") or 0)
            row["attempt_count"] = str(current_attempts + 1)

        if conceptual_score is not None:
            row["last_score_conceptual"] = str(conceptual_score)
        if practical_score is not None:
            row["last_score_practical"] = str(practical_score)
        if architect_score is not None:
            row["last_score_architect"] = str(architect_score)
        if communication_score is not None:
            row["last_score_communication"] = str(communication_score)
        if coding_score is not None:
            row["last_score_coding"] = str(coding_score)
        if decision is not None:
            row["last_decision"] = decision
        if prerequisites_unlocked is not None:
            row["prerequisites_unlocked"] = "true" if prerequisites_unlocked else "false"

        row["last_attempted_at"] = utc_now_iso()
        if completed:
            row["completed_at"] = utc_now_iso()
        break

    if not found:
        raise TrackerError(f"Topic not found in progress tracker: {topic_id}")

    write_progress_rows(rows)


def unlock_topic(topic_id: str) -> None:
    rows = read_progress_rows()
    if not rows:
        raise TrackerError("Progress tracker is empty.")

    found = False
    for row in rows:
        if row["topic_id"] == topic_id:
            row["prerequisites_unlocked"] = "true"
            if row["status"] == "locked":
                row["status"] = "not_started"
            found = True
            break

    if not found:
        raise TrackerError(f"Topic not found in progress tracker: {topic_id}")

    write_progress_rows(rows)


def lock_topic(topic_id: str) -> None:
    rows = read_progress_rows()
    if not rows:
        raise TrackerError("Progress tracker is empty.")

    found = False
    for row in rows:
        if row["topic_id"] == topic_id:
            row["prerequisites_unlocked"] = "false"
            if row["status"] != "completed":
                row["status"] = "locked"
            found = True
            break

    if not found:
        raise TrackerError(f"Topic not found in progress tracker: {topic_id}")

    write_progress_rows(rows)


def unlock_next_sequential_topic(completed_topic_id: str) -> List[str]:
    rows = read_progress_rows()
    if not rows:
        raise TrackerError("Progress tracker is empty.")

    completed_index = None
    for idx, row in enumerate(rows):
        if row["topic_id"] == completed_topic_id:
            completed_index = idx
            break

    if completed_index is None:
        raise TrackerError(f"Topic not found in progress tracker: {completed_topic_id}")

    unlocked: List[str] = []
    next_index = completed_index + 1

    for idx, row in enumerate(rows):
        if row["status"] == "completed":
            row["prerequisites_unlocked"] = "true"
            continue

        if idx == next_index:
            row["prerequisites_unlocked"] = "true"
            if row["status"] == "locked":
                row["status"] = "not_started"
            unlocked.append(row["topic_id"])
            continue

        if idx > next_index:
            row["prerequisites_unlocked"] = "false"
            row["status"] = "locked"

    write_progress_rows(rows)
    return unlocked[:1]


def normalize_linear_progression() -> None:
    rows = read_progress_rows()
    if not rows:
        return
    repaired = _enforce_strict_linear_rows(rows)
    write_progress_rows(repaired)


def log_weak_spot(
    topic_id: str,
    title: str,
    weak_spot_category: str,
    weak_spot_detail: str,
    severity: str,
    detected_from: str,
    next_action: str,
    status: str = "open",
) -> None:
    file_exists = WEAK_SPOTS_LOG_PATH.exists()

    with WEAK_SPOTS_LOG_PATH.open("a", encoding="utf-8", newline="") as f:
        fieldnames = [
            "timestamp",
            "topic_id",
            "title",
            "weak_spot_category",
            "weak_spot_detail",
            "severity",
            "detected_from",
            "next_action",
            "status",
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)

        if not file_exists or WEAK_SPOTS_LOG_PATH.stat().st_size == 0:
            writer.writeheader()

        writer.writerow(
            {
                "timestamp": utc_now_iso(),
                "topic_id": topic_id,
                "title": title,
                "weak_spot_category": weak_spot_category,
                "weak_spot_detail": weak_spot_detail,
                "severity": severity,
                "detected_from": detected_from,
                "next_action": next_action,
                "status": status,
            }
        )
