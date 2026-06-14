"""V2.3 mastery policy.

Separates best mastery from latest attempt status.
A later failed redo must not erase an earlier 3-star/mastered attempt.
"""
from __future__ import annotations

from typing import Any, Dict, Iterable, Optional

CORE_FIELDS = (
    "last_score_conceptual",
    "last_score_practical",
    "last_score_architect",
    "last_score_communication",
)


def to_int(value: Any, default: int = 0) -> int:
    try:
        if value is None or value == "":
            return default
        return int(float(value))
    except Exception:
        return default


def min_core_score(row: Dict[str, Any]) -> int:
    values = [to_int(row.get(field), 0) for field in CORE_FIELDS]
    return min(values) if values else 0


def topic_best_stars(row: Dict[str, Any], rewards_state: Optional[Dict[str, Any]] = None) -> int:
    topic_id = str(row.get("topic_id") or "")
    if rewards_state:
        by_topic = rewards_state.get("topic_states", {}) or rewards_state.get("topics", {}) or {}
        item = by_topic.get(topic_id, {}) if isinstance(by_topic, dict) else {}
        if isinstance(item, dict):
            stars = to_int(item.get("best_stars"), 0)
            if stars:
                return stars
    # Fall back to current row scores when rewards state is unavailable.
    return min_core_score(row)


def is_mastered(row: Dict[str, Any], rewards_state: Optional[Dict[str, Any]] = None, min_star: int = 3) -> bool:
    topic_id = str(row.get("topic_id") or "")
    if topic_id.startswith("dl_"):
        return topic_best_stars(row, rewards_state) >= min_star
    if topic_id.startswith("checkpoint_") or topic_id.startswith("capstone_"):
        return topic_best_stars(row, rewards_state) >= min_star or min_core_score(row) >= min_star
    return topic_best_stars(row, rewards_state) >= min_star or min_core_score(row) >= min_star


def has_attempt(row: Dict[str, Any]) -> bool:
    return to_int(row.get("attempt_count"), 0) > 0 or bool(str(row.get("last_decision") or "").strip())


def display_status(row: Dict[str, Any], rewards_state: Optional[Dict[str, Any]] = None) -> str:
    raw = str(row.get("status") or "locked").strip().lower()
    topic_id = str(row.get("topic_id") or "")

    if raw == "locked":
        return "locked"
    if topic_id.startswith("mlf_") and is_mastered(row, rewards_state):
        return "completed"
    if raw in {"revise", "needs_attention"}:
        return "needs_attention"
    if has_attempt(row) and not is_mastered(row, rewards_state):
        return "needs_attention"
    if raw in {"not_started", "unlocked"}:
        return "unlocked"
    return raw


def needs_repair(row: Dict[str, Any], rewards_state: Optional[Dict[str, Any]] = None) -> bool:
    return display_status(row, rewards_state) == "needs_attention"


def mastered_ml_count(rows: Iterable[Dict[str, Any]], rewards_state: Optional[Dict[str, Any]] = None) -> int:
    return sum(1 for row in rows if str(row.get("topic_id") or "").startswith("mlf_") and is_mastered(row, rewards_state))
