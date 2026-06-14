"""
MLOS V2 Learning Policy
Drop-in policy module for the Streamlit app.

Purpose:
- Tutor/assessment alignment: normal lessons use 10 MCQs + 2 evidence tasks.
- Capstone lock: all mlf_* lessons must have all core scores >= 3.
- DL/NN lock: unlock only after capstone completion/mastery.
- Redo/review fix: a failed redo remains the active topic until repaired.

Wire this into the app's topic selector and progress rebuild logic.
"""
from __future__ import annotations

from dataclasses import dataclass
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

MASTERED_STATUSES = {"completed", "pass", "borderline"}
REPAIR_STATUSES = {"revise", "needs_attention"}


def _to_int(value: Any, default: int = 0) -> int:
    try:
        if value is None or value == "":
            return default
        return int(float(value))
    except Exception:
        return default


def min_core_score(progress_row: Dict[str, Any]) -> int:
    return min(_to_int(progress_row.get(k)) for k in CORE_SCORE_KEYS)


def min_run_score(run_scores: Dict[str, Any]) -> int:
    return min(_to_int(run_scores.get(k)) for k in RUN_SCORE_KEYS)


def is_mastered(progress_row: Dict[str, Any], min_score: int = 3) -> bool:
    return min_core_score(progress_row) >= min_score


def is_mlf_topic(topic_id: str) -> bool:
    return topic_id.startswith("mlf_")


def is_dl_topic(topic_id: str) -> bool:
    return topic_id.startswith("dl_")


def all_ml_lessons_mastered(progress_rows: Iterable[Dict[str, Any]]) -> bool:
    rows = [r for r in progress_rows if is_mlf_topic(str(r.get("topic_id", "")))]
    return bool(rows) and all(is_mastered(r) for r in rows)


def capstone_mastered(progress_rows: Iterable[Dict[str, Any]]) -> bool:
    for row in progress_rows:
        if row.get("topic_id") == "capstone_ml_architect_001":
            return is_mastered(row) or row.get("status") in {"completed", "pass"}
    return False


def should_complete_from_visible_gate(topic_id: str, scores: Dict[str, Any], code_passed: bool = True, interpretation_score: Optional[int] = None) -> bool:
    """The UI-visible gate is the source of truth. Hidden LLM decision text cannot override it."""
    if min_run_score(scores) < 3:
        return False
    if not code_passed:
        return False
    if interpretation_score is not None and _to_int(interpretation_score) < 3:
        return False
    return True


def classify_progress_row(row: Dict[str, Any], progress_rows: List[Dict[str, Any]]) -> str:
    topic_id = str(row.get("topic_id", ""))
    attempt_count = _to_int(row.get("attempt_count"))
    has_attempt = attempt_count > 0 or bool(row.get("last_decision"))

    if is_dl_topic(topic_id):
        if topic_id == "dl_001" and capstone_mastered(progress_rows):
            return "unlocked" if not is_mastered(row) else "completed"
        return "locked"

    if topic_id == "capstone_ml_architect_001":
        checkpoint_ok = any(r.get("topic_id") == "checkpoint_ml_architect_001" and is_mastered(r) for r in progress_rows)
        if all_ml_lessons_mastered(progress_rows) and checkpoint_ok:
            return "completed" if is_mastered(row) else "unlocked"
        return "locked"

    if is_mlf_topic(topic_id):
        if is_mastered(row):
            return "completed"
        if has_attempt:
            return "needs_attention"
        return "unlocked" if topic_id == "mlf_001" else "locked"

    if topic_id.startswith("checkpoint_"):
        return "completed" if is_mastered(row) else ("needs_attention" if has_attempt else "locked")

    return str(row.get("status") or "locked")


def select_active_topic(progress_rows: List[Dict[str, Any]], latest_evaluation: Optional[Dict[str, Any]] = None) -> Optional[str]:
    """Active-topic selection. This fixes the mlf_001 redo -> mlf_016 jump.

    Priority:
    1. latest failed redo/revise topic
    2. earliest needs_attention by sequence_no
    3. earliest unlocked topic by sequence_no
    """
    if latest_evaluation:
        status = str(latest_evaluation.get("status") or latest_evaluation.get("decision") or "").lower()
        topic_id = latest_evaluation.get("topic_id")
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


def normal_lesson_assessment_contract() -> Dict[str, int]:
    return {"mcq_count": 10, "written_evidence_tasks": 2, "min_core_score": 3}
