from __future__ import annotations

"""V3 assessment policy for MLOS.

This module deliberately separates:
- learning checks / MCQs for breadth;
- one focused written response for reasoning;
- checkpoints/capstone for deeper architecture evidence.

Normal lessons should not behave like five-essay exams.
"""

from copy import deepcopy
from typing import Any, Dict, Iterable, List, Optional


NORMAL_MCQ_TARGET_ITEMS = 10
NORMAL_MCQ_PASS_PCT = 70.0
NORMAL_WRITTEN_TASKS = 1
CHECKPOINT_WRITTEN_TASKS = 2
CAPSTONE_WRITTEN_TASKS = 4


ONION_PREFIXES = ("aia_", "genai_", "rag_", "llm_", "trf_")
NORMAL_PREFIXES = ("mlf_", "dl_") + ONION_PREFIXES


def topic_id(value: Any) -> str:
    return str(value or "").strip()


def is_checkpoint_topic(tid: str) -> bool:
    return topic_id(tid).startswith("checkpoint_")


def is_capstone_topic(tid: str) -> bool:
    return topic_id(tid).startswith("capstone_")


def is_onion_topic(tid: str) -> bool:
    return topic_id(tid).startswith(ONION_PREFIXES)


def is_normal_lesson_topic(tid: str) -> bool:
    tid = topic_id(tid)
    return tid.startswith(NORMAL_PREFIXES) and not is_checkpoint_topic(tid) and not is_capstone_topic(tid)


def written_task_limit(tid: str) -> int:
    tid = topic_id(tid)
    if is_capstone_topic(tid):
        return CAPSTONE_WRITTEN_TASKS
    if is_checkpoint_topic(tid):
        return CHECKPOINT_WRITTEN_TASKS
    return NORMAL_WRITTEN_TASKS


def filter_written_answer_items(tid: str, answer_items: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Return answer items visible/evaluated under V3.

    Existing active runs may have 4-5 old essay tasks. V3 keeps capstones deep,
    checkpoints moderate, and normal lessons to one focused written answer.
    """
    items = [deepcopy(item) for item in (answer_items or []) if isinstance(item, dict)]
    limit = written_task_limit(tid)
    return items[:limit]


def filter_assessment_questions(tid: str, questions: Iterable[Any]) -> List[Any]:
    questions = list(questions or [])
    return questions[: written_task_limit(tid)]


def normalize_mcq_items(mcqs: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    for idx, raw in enumerate(mcqs or [], start=1):
        if not isinstance(raw, dict):
            continue
        options = list(raw.get("options") or [])
        if not options:
            continue
        try:
            answer_index = int(raw.get("answer_index"))
        except Exception:
            continue
        if answer_index < 0 or answer_index >= len(options):
            continue
        item = deepcopy(raw)
        item["id"] = str(item.get("id") or item.get("question_id") or f"mcq_{idx:02d}")
        item["kind"] = str(item.get("kind") or ("Critical" if idx <= 3 else "Scenario"))
        item["is_critical"] = bool(item.get("is_critical", idx <= 3))
        item["answer_index"] = answer_index
        items.append(item)
    return items


def build_mcq_submission_payload(
    *,
    topic_id: str,
    run_id: str,
    mcqs: Iterable[Dict[str, Any]],
    selections: Dict[str, Any],
) -> Dict[str, Any]:
    items = normalize_mcq_items(mcqs)
    normalized_selections: Dict[str, Optional[int]] = {}
    for item in items:
        qid = str(item["id"])
        raw = selections.get(qid)
        try:
            normalized_selections[qid] = int(raw) if raw is not None and raw != "" else None
        except Exception:
            normalized_selections[qid] = None

    result = score_mcq_submission(topic_id=topic_id, mcqs=items, selections=normalized_selections)
    return {
        "topic_id": topic_id,
        "run_id": run_id,
        "assessment_mode": "v3_mcq_first",
        "selections": normalized_selections,
        "result": result,
        "items": [
            {
                "id": item["id"],
                "question": item.get("question", ""),
                "options": item.get("options", []),
                "answer_index": item.get("answer_index"),
                "is_critical": item.get("is_critical", False),
                "kind": item.get("kind", "Check"),
            }
            for item in items
        ],
    }


def score_mcq_submission(
    *,
    topic_id: str,
    mcqs: Iterable[Dict[str, Any]],
    selections: Dict[str, Any],
) -> Dict[str, Any]:
    items = normalize_mcq_items(mcqs)
    total = len(items)
    answered = 0
    correct = 0
    wrong: List[Dict[str, Any]] = []
    critical_failed: List[str] = []

    for item in items:
        qid = str(item["id"])
        selected = selections.get(qid)
        try:
            selected_int = int(selected) if selected is not None and selected != "" else None
        except Exception:
            selected_int = None

        if selected_int is None:
            wrong.append({"id": qid, "reason": "unanswered"})
            if item.get("is_critical"):
                critical_failed.append(qid)
            continue

        answered += 1
        if selected_int == int(item["answer_index"]):
            correct += 1
        else:
            wrong.append({"id": qid, "selected": selected_int, "correct": int(item["answer_index"])})
            if item.get("is_critical"):
                critical_failed.append(qid)

    pct = round((correct / total) * 100, 2) if total else 0.0
    min_pct = NORMAL_MCQ_PASS_PCT if is_normal_lesson_topic(topic_id) else 75.0
    # V3.2 Option B: score against the MCQs actually rendered for this run.
    # The curriculum target remains 10+ MCQs, but early/legacy runs may only
    # contain 1-9 items. A learner must answer every available item, meet the
    # percentage threshold, and clear critical checks. Do not convert 1/1 into
    # 1/10.
    if is_normal_lesson_topic(topic_id):
        has_enough_items = total > 0
        required_items = total
    else:
        has_enough_items = total > 0
        required_items = total

    passed = has_enough_items and answered == total and pct >= min_pct and not critical_failed

    return {
        "topic_id": topic_id,
        "total": total,
        "answered": answered,
        "correct": correct,
        "score_pct": pct,
        "minimum_pct": min_pct,
        "minimum_items": required_items,
        "target_items": NORMAL_MCQ_TARGET_ITEMS if is_normal_lesson_topic(topic_id) else None,
        "has_enough_items": has_enough_items,
        "critical_failed": critical_failed,
        "wrong": wrong,
        "passed": passed,
        "policy": "Normal lessons score all available MCQs for the run, target 10+, require >=70%, all critical checks correct, plus one short written answer.",
    }


def explain_contract(tid: str) -> Dict[str, Any]:
    tid = topic_id(tid)
    if is_capstone_topic(tid):
        return {
            "mode": "capstone_case",
            "mcq_required": False,
            "written_tasks": CAPSTONE_WRITTEN_TASKS,
            "summary": "Capstone is a case-study architecture decision. MCQs do not replace architecture evidence.",
        }
    if is_checkpoint_topic(tid):
        return {
            "mode": "checkpoint_mixed",
            "mcq_required": True,
            "mcq_minimum_pct": 75.0,
            "written_tasks": CHECKPOINT_WRITTEN_TASKS,
            "summary": "Checkpoint uses scenario MCQs plus two architecture responses.",
        }
    return {
        "mode": "normal_mcq_first",
        "mcq_required": True,
        "mcq_minimum_pct": NORMAL_MCQ_PASS_PCT,
        "mcq_minimum_items": "available",
        "mcq_target_items": NORMAL_MCQ_TARGET_ITEMS,
        "written_tasks": NORMAL_WRITTEN_TASKS,
        "summary": "Normal lessons use MCQs for breadth and one short written answer for reasoning.",
    }


def apply_mcq_gate_to_evaluation(evaluation: Any, mcq_result: Optional[Dict[str, Any]], topic_id: str) -> Any:
    """Mutate an EvaluationResult with the V3 MCQ gate.

    The LLM evaluates the written answer. This deterministic gate handles breadth.
    """
    if is_capstone_topic(topic_id):
        return evaluation

    if not is_normal_lesson_topic(topic_id) and not is_checkpoint_topic(topic_id):
        return evaluation

    if not mcq_result:
        evaluation.decision = "revise"
        evaluation.next_action = "retry_same_topic"
        evaluation.scores.conceptual_clarity = min(int(evaluation.scores.conceptual_clarity or 1), 2)
        evaluation.scores.practical_reasoning = min(int(evaluation.scores.practical_reasoning or 1), 2)
        msg = "V3 MCQ gate: no saved scored MCQ submission was found."
        if msg not in evaluation.weak_spots:
            evaluation.weak_spots.append(msg)
        evaluation.decision_reason = (evaluation.decision_reason + " " + msg).strip()
        return evaluation

    if not bool(mcq_result.get("passed")):
        evaluation.decision = "revise"
        evaluation.next_action = "retry_same_topic"
        evaluation.scores.conceptual_clarity = min(int(evaluation.scores.conceptual_clarity or 1), 2)
        evaluation.scores.practical_reasoning = min(int(evaluation.scores.practical_reasoning or 1), 2)
        msg = (
            f"V3 MCQ gate: scored MCQs not passed "
            f"({mcq_result.get('correct', 0)}/{mcq_result.get('total', 0)}, "
            f"{mcq_result.get('score_pct', 0)}%). Complete all MCQs, reach the threshold, and clear critical checks."
        )
        if msg not in evaluation.weak_spots:
            evaluation.weak_spots.append(msg)
        evaluation.decision_reason = (evaluation.decision_reason + " " + msg).strip()
        return evaluation

    strength = (
        f"V3 MCQ gate passed: {mcq_result.get('correct', 0)}/{mcq_result.get('total', 0)} "
        f"({mcq_result.get('score_pct', 0)}%)."
    )
    if strength not in evaluation.strengths:
        evaluation.strengths.append(strength)
    return evaluation
