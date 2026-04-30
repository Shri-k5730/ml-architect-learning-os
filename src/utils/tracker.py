from __future__ import annotations

import csv
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional


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
    with file_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


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

    fieldnames = list(rows[0].keys())
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

    _write_csv_rows(PROGRESS_TRACKER_PATH, rows, fieldnames)


def unlock_topic(topic_id: str) -> None:
    rows = _read_csv_rows(PROGRESS_TRACKER_PATH)
    if not rows:
        raise TrackerError("Progress tracker is empty.")

    fieldnames = list(rows[0].keys())
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

    _write_csv_rows(PROGRESS_TRACKER_PATH, rows, fieldnames)


def lock_topic(topic_id: str) -> None:
    rows = _read_csv_rows(PROGRESS_TRACKER_PATH)
    if not rows:
        raise TrackerError("Progress tracker is empty.")

    fieldnames = list(rows[0].keys())
    found = False

    for row in rows:
        if row["topic_id"] == topic_id:
            row["prerequisites_unlocked"] = "false"
            row["status"] = "locked"
            found = True
            break

    if not found:
        raise TrackerError(f"Topic not found in progress tracker: {topic_id}")

    _write_csv_rows(PROGRESS_TRACKER_PATH, rows, fieldnames)


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