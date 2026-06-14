"""MLOS V2.1 Progress Rebuilder."""
from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional, Tuple

from src.utils.v2_learning_policy import classify_progress_row, select_active_topic


def _to_int(value: Any, default: int = 10_000) -> int:
    try:
        if value is None or value == "":
            return default
        return int(float(value))
    except Exception:
        return default


def merge_catalog_and_progress(
    topic_catalog_rows: Iterable[Dict[str, Any]],
    progress_rows: Iterable[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    progress_by_topic = {str(r.get("topic_id")): dict(r) for r in progress_rows}
    merged: List[Dict[str, Any]] = []

    for topic in topic_catalog_rows:
        topic_id = str(topic.get("topic_id"))
        row = dict(topic)
        row.update(progress_by_topic.get(topic_id, {}))
        row.setdefault("topic_id", topic_id)
        row.setdefault("status", "locked")
        row.setdefault("attempt_count", 0)
        merged.append(row)

    return sorted(merged, key=lambda r: _to_int(r.get("sequence_no")))


def rebuild_v2_progress_state(
    topic_catalog_rows: Iterable[Dict[str, Any]],
    progress_rows: Iterable[Dict[str, Any]],
    latest_evaluation: Optional[Dict[str, Any]] = None,
) -> Tuple[List[Dict[str, Any]], Optional[str]]:
    merged = merge_catalog_and_progress(topic_catalog_rows, progress_rows)
    classified: List[Dict[str, Any]] = []
    for row in merged:
        new_row = dict(row)
        new_row["status"] = classify_progress_row(new_row, merged)
        classified.append(new_row)
    active_topic_id = select_active_topic(classified, latest_evaluation=latest_evaluation)
    return classified, active_topic_id
