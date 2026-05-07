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
        return list(csv.DictReader(f))


def _write_csv_rows(file_path: Path, rows: list[Dict[str, str]], fieldnames: list[str]) -> None:
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with file_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _normalize(rows: list[Dict[str, str]]) -> list[Dict[str, str]]:
    try:
        from src.utils.cloud_state import normalize_progress_rows

        return normalize_progress_rows(rows)
    except Exception:
        return rows


def _persist_progress_to_supabase(rows: list[Dict[str, str]]) -> None:
    try:
        from src.utils.cloud_state import persist_progress_to_supabase

        persist_progress_to_supabase(rows)
    except Exception:
        return


def hydrate_progress_from_supabase_if_available() -> bool:
    try:
        from src.utils.cloud_state import hydrate_progress_from_supabase

        return hydrate_progress_from_supabase()
    except Exception:
        return False


def read_progress_rows() -> list[Dict[str, str]]:
    rows = _read_csv_rows(PROGRESS_TRACKER_PATH)
    rows = _normalize(rows)
    return rows


def write_progress_rows(rows: list[Dict[str, str]]) -> None:
    if not rows:
        raise TrackerError("Progress tracker rows are empty.")
    rows = _normalize(rows)
    fieldnames = list(rows[0].keys())
    _write_csv_rows(PROGRESS_TRACKER_PATH, rows, fieldnames)
    _persist_progress_to_supabase(rows)


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
    decision: Optional[str] = None,
    prerequisites_unlocked: Optional[bool] = None,
    completed: bool = False,
) -> None:
    rows = read_progress_rows()
    if not rows:
        raise TrackerError("Progress tracker is empty.")

    found = False
    now = utc_now_iso()

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
        if decision is not None:
            row["last_decision"] = decision
        if prerequisites_unlocked is not None:
            row["prerequisites_unlocked"] = "true" if prerequisites_unlocked else "false"

        row["last_attempted_at"] = now
        if completed:
            row["completed_at"] = now
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


def log_weak_spots(topic_id: str, run_id: str, weak_spots: List[str]) -> None:
    WEAK_SPOTS_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    file_exists = WEAK_SPOTS_LOG_PATH.exists()

    with WEAK_SPOTS_LOG_PATH.open("a", encoding="utf-8", newline="") as f:
        fieldnames = ["topic_id", "run_id", "weak_spot", "created_at"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        for weak_spot in weak_spots:
            writer.writerow(
                {
                    "topic_id": topic_id,
                    "run_id": run_id,
                    "weak_spot": weak_spot,
                    "created_at": utc_now_iso(),
                }
            )
