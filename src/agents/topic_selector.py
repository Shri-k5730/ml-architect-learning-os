from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Dict, List, Optional

from src.schemas import SelectedTopic, Topic
from src.utils.curriculum_catalog import load_topic_catalog_dicts
from src.utils.tracker import read_progress_rows


PROJECT_ROOT = Path(__file__).resolve().parents[2]
TOPIC_CATALOG_PATH = PROJECT_ROOT / "topics" / "topic_catalog.json"
PROGRESS_TRACKER_PATH = PROJECT_ROOT / "data" / "progress_tracker.csv"


class TopicSelectorError(Exception):
    """Raised when topic selection fails."""


def _allow_completed_restart() -> bool:
    return str(os.getenv("ML_OS_ALLOW_RESTART_COMPLETED", "false")).strip().lower() in {"1", "true", "yes", "y"}


def _redo_mode() -> bool:
    return str(os.getenv("ML_OS_REDO_MODE", "false")).strip().lower() in {"1", "true", "yes", "y"}


def _read_topic_catalog() -> List[Topic]:
    data = load_topic_catalog_dicts(prefer_supabase=True)
    if not data:
        raise TopicSelectorError("No topic catalog found. Check Supabase mlos_topic_catalog or local topics/topic_catalog.json.")
    return [Topic(**item) for item in data]


def _read_progress_rows() -> List[Dict[str, str]]:
    rows = read_progress_rows()
    if not rows:
        raise TopicSelectorError("Progress tracker is empty. Check Supabase mlos_learner_progress or mlos_state.")
    return rows


def _get_topic_by_id(topic_catalog: List[Topic], topic_id: str) -> Topic:
    for topic in topic_catalog:
        if topic.topic_id == topic_id:
            return topic
    raise TopicSelectorError(f"Topic not found in catalog: {topic_id}")


def _get_progress_row(rows: List[Dict[str, str]], topic_id: str) -> Dict[str, str]:
    for row in rows:
        if row["topic_id"] == topic_id:
            return row
    raise TopicSelectorError(f"Topic not found in progress tracker: {topic_id}")


def _select_requested_topic(
    requested_topic_id: str,
    topic_catalog: List[Topic],
    progress_rows: List[Dict[str, str]],
) -> SelectedTopic:
    topic = _get_topic_by_id(topic_catalog, requested_topic_id)
    row = _get_progress_row(progress_rows, requested_topic_id)

    unlocked = row.get("prerequisites_unlocked", "").lower() == "true"
    status = row.get("status", "")

    is_redo = _redo_mode()

    if is_redo and status != "completed":
        raise TopicSelectorError(
            f"Redo is allowed only for completed topics. Requested topic '{requested_topic_id}' has status '{status}'."
        )

    if status == "locked" or not unlocked:
        raise TopicSelectorError(
            f"Requested topic '{requested_topic_id}' is locked and cannot be started yet."
        )

    if status == "completed" and not _allow_completed_restart():
        raise TopicSelectorError(
            f"Requested topic '{requested_topic_id}' is already completed. "
            "Set ML_OS_ALLOW_RESTART_COMPLETED=true only for deliberate replay/testing."
        )

    return SelectedTopic(
        selected_topic_id=topic.topic_id,
        reason=(
            f"Redo selected completed topic '{topic.topic_id}'."
            if is_redo else f"Manually selected topic '{topic.topic_id}' with current status '{status}'."
        ),
        selection_mode="retry" if is_redo else "manual_selected",
        prerequisite_gap=None,
    )


def _latest_evaluation_state() -> Optional[Dict[str, str]]:
    try:
        from src.utils.supabase_store import fetch_state, supabase_enabled
        if not supabase_enabled():
            return None
        state = fetch_state("latest_evaluation")
        return state if isinstance(state, dict) else None
    except Exception:
        return None


def select_topic(requested_topic_id: Optional[str] = None) -> SelectedTopic:
    """Select the next topic using the V2.2 learning policy.

    The old selector simply picked the first unlocked incomplete row.  That made
    redo failures and stale active runs fight each other.  V2.2 delegates the
    repair target to select_active_topic: latest failed redo first, then earliest
    weak lesson, then first unlocked new lesson.
    """
    topic_catalog = _read_topic_catalog()
    progress_rows = _read_progress_rows()

    if requested_topic_id:
        return _select_requested_topic(
            requested_topic_id=requested_topic_id,
            topic_catalog=topic_catalog,
            progress_rows=progress_rows,
        )

    try:
        from src.utils.v2_learning_policy import select_active_topic
        active_topic_id = select_active_topic(progress_rows, latest_evaluation=_latest_evaluation_state())
        if active_topic_id:
            topic = _get_topic_by_id(topic_catalog, active_topic_id)
            return SelectedTopic(
                selected_topic_id=topic.topic_id,
                reason=f"Selected V2.2 active repair/start target '{topic.topic_id}'.",
                selection_mode="next_unlocked",
                prerequisite_gap=None,
            )
    except Exception:
        pass

    for row in progress_rows:
        status = row.get("status", "")
        unlocked = row.get("prerequisites_unlocked", "").lower() == "true"
        if status == "completed":
            continue
        if unlocked and status in {"not_started", "in_progress", "revise", "borderline"}:
            topic = _get_topic_by_id(topic_catalog, row["topic_id"])
            return SelectedTopic(
                selected_topic_id=topic.topic_id,
                reason=f"Selected next unlocked curriculum item '{topic.topic_id}'.",
                selection_mode="next_unlocked",
                prerequisite_gap=None,
            )

    completed_count = sum(1 for row in progress_rows if row.get("status") == "completed")
    if completed_count == len(progress_rows):
        raise TopicSelectorError("All topics are completed. No next topic to select.")

    raise TopicSelectorError(
        "No topic could be selected. Check progress tracker statuses and unlock flags."
    )


def select_next_topic() -> SelectedTopic:
    return select_topic(requested_topic_id=None)


if __name__ == "__main__":
    selected = select_next_topic()
    print(json.dumps(selected.to_dict(), indent=2))
