"""MLOS V2.2 progress rebuilding helpers."""
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


def _as_list(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(x) for x in value]
    if isinstance(value, tuple):
        return [str(x) for x in value]
    text = str(value).strip()
    if not text or text.lower() == "nan":
        return []
    if text.startswith("[") and text.endswith("]"):
        return [x.strip().strip('"').strip("'") for x in text[1:-1].split(",") if x.strip()]
    return [text]


def merge_catalog_and_progress(
    topic_catalog_rows: Iterable[Dict[str, Any]],
    progress_rows: Iterable[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    progress_by_topic = {str(r.get("topic_id")): dict(r) for r in progress_rows if r.get("topic_id")}
    merged: List[Dict[str, Any]] = []

    for topic in topic_catalog_rows:
        topic_id = str(topic.get("topic_id"))
        row = dict(topic)
        row.update(progress_by_topic.get(topic_id, {}))
        row["topic_id"] = topic_id
        row["title"] = row.get("title") or topic.get("title") or topic_id
        row["domain"] = row.get("domain") or topic.get("domain") or ""
        row["difficulty"] = row.get("difficulty") or topic.get("difficulty") or ""
        row["sequence_no"] = row.get("sequence_no") or topic.get("sequence_no") or 10_000
        row["prerequisites"] = _as_list(topic.get("prerequisites") or row.get("prerequisites"))
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

    # First classify all rows using the merged score history.
    for row in merged:
        new_row = dict(row)
        new_row["status"] = classify_progress_row(new_row, merged)
        new_row["prerequisites_unlocked"] = "false" if new_row["status"] == "locked" else "true"
        classified.append(new_row)

    active_topic_id = select_active_topic(classified, latest_evaluation=latest_evaluation)
    if active_topic_id:
        for row in classified:
            if str(row.get("topic_id")) == active_topic_id and str(row.get("status")) != "completed":
                row["prerequisites_unlocked"] = "true"
                break

    return classified, active_topic_id
