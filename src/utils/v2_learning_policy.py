"""
MLOS V2.2 Learning Policy

This file is intentionally small and deterministic.  The rest of the app must
call this policy instead of hard-coding progression in Streamlit or SQL.

Rules:
- A normal ML lesson is mastered only when all core scores are >= 3.
- A failed redo/latest revise stays the repair target.  Do not jump to a stale
  awaiting run or a later topic.
- Capstone unlocks only after all mlf_* lessons and the architect checkpoint are
  mastered.
- DL/NN unlocks only after the capstone is mastered.
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
REPAIR_STATUSES = {"revise", "borderline", "fail_prereq"}
MASTERED_STATUS = "completed"
REPAIR_STATUS = "revise"
UNLOCKED_STATUS = "not_started"
LOCKED_STATUS = "locked"


def _to_int(value: Any, default: int = 0) -> int:
    try:
        if value is None or value == "":
            return default
        return int(float(value))
    except Exception:
        return default


def is_mlf_topic(topic_id: str) -> bool:
    return str(topic_id or "").startswith("mlf_")


def is_dl_topic(topic_id: str) -> bool:
    return str(topic_id or "").startswith("dl_")


def is_checkpoint_topic(topic_id: str) -> bool:
    return str(topic_id or "").startswith("checkpoint_")


def is_capstone_topic(topic_id: str) -> bool:
    return str(topic_id or "") == "capstone_ml_architect_001"


def min_core_score(progress_row: Dict[str, Any]) -> int:
    return min(_to_int(progress_row.get(k), 0) for k in CORE_SCORE_KEYS)


def min_run_score(scores: Dict[str, Any]) -> int:
    return min(_to_int(scores.get(k), 0) for k in RUN_SCORE_KEYS)


def has_core_scores(progress_row: Dict[str, Any]) -> bool:
    return any(str(progress_row.get(k) or "").strip() for k in CORE_SCORE_KEYS)


def is_mastered(progress_row: Dict[str, Any], min_score: int = 3) -> bool:
    return has_core_scores(progress_row) and min_core_score(progress_row) >= min_score


def _is_blank(value: Any) -> bool:
    text = str(value or "").strip().lower()
    return text in {"", "none", "nan", "null"}


def has_attempt(progress_row: Dict[str, Any]) -> bool:
    return _to_int(progress_row.get("attempt_count"), 0) > 0 or not _is_blank(progress_row.get("last_decision"))


def all_ml_lessons_mastered(progress_rows: Iterable[Dict[str, Any]]) -> bool:
    rows = [r for r in progress_rows if is_mlf_topic(str(r.get("topic_id", "")))]
    return bool(rows) and all(is_mastered(r) for r in rows)


def architect_checkpoint_mastered(progress_rows: Iterable[Dict[str, Any]]) -> bool:
    return any(
        str(r.get("topic_id")) == "checkpoint_ml_architect_001" and is_mastered(r)
        for r in progress_rows
    )


def foundations_checkpoint_mastered(progress_rows: Iterable[Dict[str, Any]]) -> bool:
    return any(
        str(r.get("topic_id")) == "checkpoint_ml_foundations_001" and is_mastered(r)
        for r in progress_rows
    )


def capstone_mastered(progress_rows: Iterable[Dict[str, Any]]) -> bool:
    rows = list(progress_rows)
    if not (all_ml_lessons_mastered(rows) and architect_checkpoint_mastered(rows)):
        return False
    return any(
        is_capstone_topic(str(r.get("topic_id", ""))) and is_mastered(r)
        for r in rows
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


def _prerequisites_mastered(row: Dict[str, Any], progress_by_topic: Dict[str, Dict[str, Any]]) -> bool:
    prereqs = row.get("prerequisites") or []
    if isinstance(prereqs, str):
        # Supabase CSV extracts can deserialize arrays as strings.  The app uses
        # real lists at runtime, but fail safe here.
        prereqs = [x.strip().strip('"') for x in prereqs.strip("[]").split(",") if x.strip()]
    for prereq in prereqs:
        prereq_row = progress_by_topic.get(str(prereq))
        if not prereq_row or not is_mastered(prereq_row):
            return False
    return True


def classify_progress_row(row: Dict[str, Any], progress_rows: List[Dict[str, Any]]) -> str:
    """Return only statuses understood by the existing app UI.

    Do not return custom states such as 'needs_attention' or 'unlocked'; those
    created the earlier mismatch.  Use 'revise' and 'not_started' because the
    current UI, schemas and selector already understand them.
    """
    topic_id = str(row.get("topic_id", ""))
    by_topic = {str(r.get("topic_id")): r for r in progress_rows}

    if is_mlf_topic(topic_id):
        if is_mastered(row):
            return MASTERED_STATUS
        if has_attempt(row):
            return REPAIR_STATUS
        return UNLOCKED_STATUS if topic_id == "mlf_001" else LOCKED_STATUS

    if topic_id == "checkpoint_ml_foundations_001":
        first_ten = [r for r in progress_rows if str(r.get("topic_id", "")).startswith("mlf_") and _to_int(r.get("sequence_no"), 9999) <= 10]
        if not first_ten or not all(is_mastered(r) for r in first_ten):
            return LOCKED_STATUS
        if is_mastered(row):
            return MASTERED_STATUS
        if has_attempt(row):
            return REPAIR_STATUS
        return UNLOCKED_STATUS

    if topic_id == "checkpoint_ml_architect_001":
        if not (all_ml_lessons_mastered(progress_rows) and foundations_checkpoint_mastered(progress_rows)):
            return LOCKED_STATUS
        if is_mastered(row):
            return MASTERED_STATUS
        if has_attempt(row):
            return REPAIR_STATUS
        return UNLOCKED_STATUS

    if is_capstone_topic(topic_id):
        if not (all_ml_lessons_mastered(progress_rows) and architect_checkpoint_mastered(progress_rows)):
            return LOCKED_STATUS
        if is_mastered(row):
            return MASTERED_STATUS
        if has_attempt(row):
            return REPAIR_STATUS
        return UNLOCKED_STATUS

    if is_dl_topic(topic_id):
        if not capstone_mastered(progress_rows):
            return LOCKED_STATUS
        if is_mastered(row):
            return MASTERED_STATUS
        if has_attempt(row):
            return REPAIR_STATUS
        return UNLOCKED_STATUS if _prerequisites_mastered(row, by_topic) else LOCKED_STATUS

    if _prerequisites_mastered(row, by_topic):
        if is_mastered(row):
            return MASTERED_STATUS
        if has_attempt(row):
            return REPAIR_STATUS
        return UNLOCKED_STATUS
    return LOCKED_STATUS


def select_active_topic(progress_rows: List[Dict[str, Any]], latest_evaluation: Optional[Dict[str, Any]] = None) -> Optional[str]:
    """Choose the next repair/start target.

    Highest priority is the latest failed evaluation because a redo failure must
    stay focused instead of jumping to an older active run.
    """
    if latest_evaluation:
        topic_id = latest_evaluation.get("topic_id")
        status = str(latest_evaluation.get("status") or latest_evaluation.get("decision") or "").lower()
        next_action = str(latest_evaluation.get("next_action") or "").lower()
        if topic_id and (status in REPAIR_STATUSES or next_action == "retry_same_topic"):
            return str(topic_id)

    def seq(row: Dict[str, Any]) -> int:
        return _to_int(row.get("sequence_no"), 10_000)

    for status in (REPAIR_STATUS, UNLOCKED_STATUS):
        candidates = sorted(
            [r for r in progress_rows if str(r.get("status") or "") == status and str(r.get("prerequisites_unlocked") or "").lower() == "true"],
            key=seq,
        )
        if candidates:
            return str(candidates[0].get("topic_id"))
    return None


def normal_lesson_contract() -> Dict[str, int]:
    return {"mcq_count": 10, "written_evidence_tasks": 2, "minimum_core_score": 3}
