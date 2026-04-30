from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Dict, List, Optional

from src.schemas import SelectedTopic, Topic


PROJECT_ROOT = Path(__file__).resolve().parents[2]
TOPIC_CATALOG_PATH = PROJECT_ROOT / "topics" / "topic_catalog.json"
TOPIC_UNLOCK_RULES_PATH = PROJECT_ROOT / "topics" / "topic_unlock_rules.json"
PROGRESS_TRACKER_PATH = PROJECT_ROOT / "data" / "progress_tracker.csv"


class TopicSelectorError(Exception):
    """Raised when topic selection fails."""


def _read_topic_catalog() -> List[Topic]:
    if not TOPIC_CATALOG_PATH.exists():
        raise TopicSelectorError(f"Topic catalog not found: {TOPIC_CATALOG_PATH}")

    data = json.loads(TOPIC_CATALOG_PATH.read_text(encoding="utf-8"))
    return [Topic(**item) for item in data]


def _read_unlock_rules() -> Dict:
    if not TOPIC_UNLOCK_RULES_PATH.exists():
        raise TopicSelectorError(f"Unlock rules not found: {TOPIC_UNLOCK_RULES_PATH}")

    return json.loads(TOPIC_UNLOCK_RULES_PATH.read_text(encoding="utf-8"))


def _read_progress_rows() -> List[Dict[str, str]]:
    if not PROGRESS_TRACKER_PATH.exists():
        raise TopicSelectorError(f"Progress tracker not found: {PROGRESS_TRACKER_PATH}")

    with PROGRESS_TRACKER_PATH.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


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


def _sort_by_last_attempt(rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    return sorted(rows, key=lambda row: row.get("last_attempted_at", "") or "", reverse=True)


def _find_retry_topic(rows: List[Dict[str, str]]) -> Optional[Dict[str, str]]:
    revise_rows = [row for row in rows if row.get("status") == "revise"]
    if not revise_rows:
        return None
    return _sort_by_last_attempt(revise_rows)[0]


def _find_borderline_topic(rows: List[Dict[str, str]]) -> Optional[Dict[str, str]]:
    borderline_rows = [row for row in rows if row.get("status") == "borderline"]
    if not borderline_rows:
        return None
    return _sort_by_last_attempt(borderline_rows)[0]


def _find_next_unlocked_topic(rows: List[Dict[str, str]]) -> Optional[Dict[str, str]]:
    eligible_statuses = {"not_started", "in_progress"}
    for row in rows:
        unlocked = row.get("prerequisites_unlocked", "").lower() == "true"
        status = row.get("status", "")
        if unlocked and status in eligible_statuses:
            return row
    return None


def _should_fallback_to_prerequisite(row: Dict[str, str], rules: Dict) -> bool:
    retry_limit = rules.get("retry_rules", {}).get("revise_retries_before_prereq_fallback", 2)
    attempt_count = int(row.get("attempt_count") or 0)
    return attempt_count >= retry_limit


def _select_requested_topic(
    requested_topic_id: str,
    topic_catalog: List[Topic],
    progress_rows: List[Dict[str, str]],
) -> SelectedTopic:
    topic = _get_topic_by_id(topic_catalog, requested_topic_id)
    row = _get_progress_row(progress_rows, requested_topic_id)

    unlocked = row.get("prerequisites_unlocked", "").lower() == "true"
    status = row.get("status", "")

    if status == "locked" or not unlocked:
        raise TopicSelectorError(
            f"Requested topic '{requested_topic_id}' is locked and cannot be started yet."
        )

    return SelectedTopic(
        selected_topic_id=topic.topic_id,
        reason=f"Manually selected topic '{topic.topic_id}' with current status '{status}'.",
        selection_mode="manual_selected",
        prerequisite_gap=None,
    )


def select_topic(requested_topic_id: Optional[str] = None) -> SelectedTopic:
    topic_catalog = _read_topic_catalog()
    unlock_rules = _read_unlock_rules()
    progress_rows = _read_progress_rows()

    if requested_topic_id:
        return _select_requested_topic(
            requested_topic_id=requested_topic_id,
            topic_catalog=topic_catalog,
            progress_rows=progress_rows,
        )

    retry_row = _find_retry_topic(progress_rows)
    if retry_row is not None:
        retry_topic = _get_topic_by_id(topic_catalog, retry_row["topic_id"])

        if _should_fallback_to_prerequisite(retry_row, unlock_rules) and retry_topic.prerequisites:
            prerequisite_id = retry_topic.prerequisites[0]
            return SelectedTopic(
                selected_topic_id=prerequisite_id,
                reason=(
                    f"Topic '{retry_topic.topic_id}' hit the retry limit. "
                    f"Routing to prerequisite '{prerequisite_id}'."
                ),
                selection_mode="prerequisite_recovery",
                prerequisite_gap=prerequisite_id,
            )

        return SelectedTopic(
            selected_topic_id=retry_topic.topic_id,
            reason=f"Retrying topic '{retry_topic.topic_id}' because the last result was revise.",
            selection_mode="retry",
            prerequisite_gap=None,
        )

    borderline_row = _find_borderline_topic(progress_rows)
    if borderline_row is not None:
        borderline_topic = _get_topic_by_id(topic_catalog, borderline_row["topic_id"])
        return SelectedTopic(
            selected_topic_id=borderline_topic.topic_id,
            reason=f"Revisiting borderline topic '{borderline_topic.topic_id}' before moving forward.",
            selection_mode="retry",
            prerequisite_gap=None,
        )

    next_row = _find_next_unlocked_topic(progress_rows)
    if next_row is not None:
        next_topic = _get_topic_by_id(topic_catalog, next_row["topic_id"])
        return SelectedTopic(
            selected_topic_id=next_topic.topic_id,
            reason=f"Selected next unlocked topic '{next_topic.topic_id}'.",
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