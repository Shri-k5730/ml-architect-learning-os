"""
MLOS V2.1 Learning Policy

Fixes:
- stale in-progress runs must not override latest failed redo;
- capstone unlock requires every mlf_* lesson to reach min core score >= 3;
- DL/NN unlock requires capstone mastery;
- visible scoring gate beats hidden LLM decision text.
"""
from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional

CORE_SCORE_KEYS = (
    "last_score_conceptual",
    "last_score_practical",
    "last_score_architect",
    "last_score_communication",
)
RUN_SCORE_KEYS = (
    "conceptual_clarity",
    "practical_reasoning",
    "architect_reasoning",
    "communication",
)
REPAIR_STATUSES = {"revise", "needs_attention"}


def _to_int(value: Any, default: int = 0) -> int:
    try:
        if value is None or value == "":
            return default
        return int(float(value))
    except Exception:
        return default


def is_mlf_topic(topic_id: str) -> bool:
    return str(topic_id).startswith("mlf_")


def is_dl_topic(topic_id: str) -> bool:
    return str(topic_id).startswith("dl_")


def min_core_score(progress_row: Dict[str, Any]) -> int:
    return min(_to_int(progress_row.get(k), 0) for k in CORE_SCORE_KEYS)


def min_run_score(scores: Dict[str, Any]) -> int:
    return min(_to_int(scores.get(k), 0) for k in RUN_SCORE_KEYS)


def is_mastered(progress_row: Dict[str, Any], min_score: int = 3) -> bool:
    return min_core_score(progress_row) >= min_score


def has_attempt(progress_row: Dict[str, Any]) -> bool:
    return _to_int(progress_row.get("attempt_count"), 0) > 0 or bool(progress_row.get("last_decision"))


def all_ml_lessons_mastered(progress_rows: Iterable[Dict[str, Any]]) -> bool:
    rows = [r for r in progress_rows if is_mlf_topic(str(r.get("topic_id", "")))]
    return bool(rows) and all(is_mastered(r) for r in rows)


def checkpoint_architect_mastered(progress_rows: Iterable[Dict[str, Any]]) -> bool:
    return any(
        r.get("topic_id") == "checkpoint_ml_architect_001" and is_mastered(r)
        for r in progress_rows
    )


def capstone_mastered(progress_rows: Iterable[Dict[str, Any]]) -> bool:
    return any(
        r.get("topic_id") == "capstone_ml_architect_001" and is_mastered(r)
        for r in progress_rows
    )


def should_complete_from_visible_gate(
    topic_id: str,
    scores: Dict[str, Any],
    code_passed: bool = True,
    interpretation_score: Optional[int] = None,
) -> bool:
    if min_run_score(scores) < 3:
        return False
    if not code_passed:
        return False
    if interpretation_score is not None and _to_int(interpretation_score) < 3:
        return False
    return True


def classify_progress_row(row: Dict[str, Any], progress_rows: List[Dict[str, Any]]) -> str:
    topic_id = str(row.get("topic_id", ""))

    if is_dl_topic(topic_id):
        if not capstone_mastered(progress_rows):
            return "locked"
        return "completed" if is_mastered(row) else ("needs_attention" if has_attempt(row) else "unlocked" if topic_id == "dl_001" else "locked")

    if topic_id == "capstone_ml_architect_001":
        if not (all_ml_lessons_mastered(progress_rows) and checkpoint_architect_mastered(progress_rows)):
            return "locked"
        return "completed" if is_mastered(row) else ("needs_attention" if has_attempt(row) else "unlocked")

    if is_mlf_topic(topic_id):
        if is_mastered(row):
            return "completed"
        if has_attempt(row):
            return "needs_attention"
        return "unlocked" if topic_id == "mlf_001" else "locked"

    if topic_id.startswith("checkpoint_"):
        return "completed" if is_mastered(row) else ("needs_attention" if has_attempt(row) else "locked")

    return str(row.get("status") or "locked")


def select_active_topic(progress_rows: List[Dict[str, Any]], latest_evaluation: Optional[Dict[str, Any]] = None) -> Optional[str]:
    # Most important: failed redo stays active.
    if latest_evaluation:
        topic_id = latest_evaluation.get("topic_id")
        status = str(latest_evaluation.get("status") or latest_evaluation.get("decision") or "").lower()
        next_action = str(latest_evaluation.get("next_action") or "").lower()
        if topic_id and (status in REPAIR_STATUSES or next_action == "retry_same_topic"):
            return str(topic_id)

    def seq(row: Dict[str, Any]) -> int:
        return _to_int(row.get("sequence_no"), 10_000)

    for status in ("needs_attention", "unlocked"):
        candidates = sorted([r for r in progress_rows if r.get("status") == status], key=seq)
        if candidates:
            return str(candidates[0].get("topic_id"))
    return None


def normal_lesson_contract() -> Dict[str, int]:
    return {"mcq_count": 10, "written_evidence_tasks": 2, "minimum_core_score": 3}
