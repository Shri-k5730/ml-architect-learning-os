from __future__ import annotations

import csv
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional


PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROGRESS_TRACKER_PATH = PROJECT_ROOT / "data" / "progress_tracker.csv"
WEAK_SPOTS_LOG_PATH = PROJECT_ROOT / "data" / "weak_spots_log.csv"


class TrackerError(Exception):
    """Raised when tracker operations fail."""


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _read_csv_rows(file_path: Path) -> list[Dict[str, str]]:
    if not file_path.exists():
        raise TrackerError(f"CSV file not found: {file_path}")

    with file_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        return list(reader)


def _write_csv_rows(file_path: Path, rows: list[Dict[str, str]], fieldnames: list[str]) -> None:
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with file_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _persist_progress_to_supabase(rows: list[Dict[str, str]]) -> None:
    try:
        from src.utils.supabase_store import upsert_state

        upsert_state("progress_tracker", {"rows": rows, "updated_at": utc_now_iso()})
    except Exception:
        return


def hydrate_progress_from_supabase_if_available() -> bool:
    """Pull persisted progress from Supabase into local CSV if available.

    This protects Streamlit Cloud from losing progress after redeploys. It is safe and
    non-blocking; if Supabase is disabled or unavailable, local CSV remains the source.
    """
    try:
        from src.utils.supabase_store import fetch_state

        state = fetch_state("progress_tracker")
        if not isinstance(state, dict):
            return False
        rows = state.get("rows")
        if not isinstance(rows, list) or not rows:
            return False
        fieldnames = list(rows[0].keys())
        _write_csv_rows(PROGRESS_TRACKER_PATH, rows, fieldnames)
        return True
    except Exception:
        return False


def read_progress_rows() -> list[Dict[str, str]]:
    return _read_csv_rows(PROGRESS_TRACKER_PATH)


def write_progress_rows(rows: list[Dict[str, str]]) -> None:
    if not rows:
        raise TrackerError("Progress tracker rows are empty.")
    fieldnames = list(rows[0].keys())
    _write_csv_rows(PROGRESS_TRACKER_PATH, rows, fieldnames)
    _persist_progress_to_supabase(rows)


def get_progress_row(topic_id: str) -> Optional[Dict[str, str]]:
    rows = _read_csv_rows(PROGRESS_TRACKER_PATH)
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
    decision: Optional[str] = None,
    prerequisites_unlocked: Optional[bool] = None,
    completed: bool = False,
) -> None:
    rows = _read_csv_rows(PROGRESS_TRACKER_PATH)
    if not rows:
        raise TrackerError("Progress tracker is empty.")

    found = False

    for row in rows:
        if row["topic_id"] != topic_id:
            continue

        found = True
        row["status"] = status

        if attempt_increment:
            current_attempts = int(row["attempt_count"] or 0)
            row["attempt_count"] = str(current_attempts + 1)

        if conceptual_score is not None:
            row["last_score_conceptual"] = str(conceptual_score)

        if practical_score is not None:
            row["last_score_practical"] = str(practical_score)

        if architect_score is not None:
            row["last_score_architect"] = str(architect_score)

        if communication_score is not None:
            row["last_score_communication"] = str(communication_score)

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
    rows = _read_csv_rows(PROGRESS_TRACKER_PATH)
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
    rows = _read_csv_rows(PROGRESS_TRACKER_PATH)
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
    """V1 unlock logic: only unlock the immediate next topic in CSV order."""
    rows = _read_csv_rows(PROGRESS_TRACKER_PATH)
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
            elif row["status"] in {"not_started", "in_progress", "revise", "borderline"}:
                unlocked.append(row["topic_id"])
            continue

        if idx > next_index:
            row["prerequisites_unlocked"] = "false"
            row["status"] = "locked"

    write_progress_rows(rows)
    # Return only one topic for clean V1 behavior.
    return unlocked[:1]


def normalize_linear_progression() -> None:
    """Repair accidental branch unlocks for V1.

    V1 is strict linear: completed prefix, first incomplete unlocked, all later locked.
    If a later topic was marked completed while an earlier topic is incomplete, downgrade
    the later topic back to locked because that state came from stale/branching data.
    """
    rows = _read_csv_rows(PROGRESS_TRACKER_PATH)
    if not rows:
        return

    first_incomplete_seen = False
    changed = False

    for row in rows:
        status = row.get("status")

        if status == "completed" and not first_incomplete_seen:
            if row.get("prerequisites_unlocked") != "true":
                row["prerequisites_unlocked"] = "true"
                changed = True
            continue

        if status == "completed" and first_incomplete_seen:
            row["status"] = "locked"
            row["completed_at"] = ""
            changed = True

        if not first_incomplete_seen:
            first_incomplete_seen = True
            if row.get("prerequisites_unlocked") != "true":
                row["prerequisites_unlocked"] = "true"
                changed = True
            if row.get("status") == "locked":
                row["status"] = "not_started"
                changed = True
        else:
            if row.get("prerequisites_unlocked") != "false":
                row["prerequisites_unlocked"] = "false"
                changed = True
            if row.get("status") != "locked":
                row["status"] = "locked"
                changed = True

    if changed:
        write_progress_rows(rows)

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
