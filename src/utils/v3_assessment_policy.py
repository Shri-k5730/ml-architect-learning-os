from __future__ import annotations

"""V3 assessment policy for MLOS.

This module deliberately separates:
- learning checks / MCQs for breadth;
- one focused written response for reasoning;
- checkpoints/capstone for deeper architecture evidence.

Normal lessons should not behave like five-essay exams.
"""

from copy import deepcopy
import hashlib
import json
import random
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


def _hash_int(value: str) -> int:
    return int(hashlib.sha256(value.encode("utf-8")).hexdigest()[:16], 16)


def _shuffle_indices(indices: List[int], seed_text: str) -> List[int]:
    shuffled = list(indices)
    rng = random.Random(_hash_int(seed_text))
    rng.shuffle(shuffled)
    return shuffled


def _balanced_target_position(question_number: int, option_count: int, seed_context: str) -> int:
    if option_count <= 1:
        return 0

    base = list(range(option_count))
    target_count = max(NORMAL_MCQ_TARGET_ITEMS, question_number)

    cycle: List[int] = []
    while len(cycle) < target_count:
        cycle.extend(base)

    cycle = cycle[:target_count]
    shuffled_cycle = _shuffle_indices(
        cycle,
        f"mcq-position-cycle|{seed_context}|{target_count}|{option_count}",
    )
    return shuffled_cycle[question_number - 1]


def _order_with_correct_at(
    *,
    option_count: int,
    correct_index: int,
    desired_correct_position: int,
    seed_text: str,
) -> List[int]:
    desired_correct_position = max(0, min(desired_correct_position, option_count - 1))

    distractors = [i for i in range(option_count) if i != correct_index]
    distractors = _shuffle_indices(distractors, seed_text + "|distractors")

    order: List[Optional[int]] = [None] * option_count
    order[desired_correct_position] = correct_index

    di = 0
    for pos in range(option_count):
        if order[pos] is None:
            order[pos] = distractors[di]
            di += 1

    return [int(x) for x in order]


def normalize_mcq_items(
    mcqs: Iterable[Dict[str, Any]],
    *,
    seed_context: str = "",
    balance_answer_positions: bool = True,
) -> List[Dict[str, Any]]:
    seed_context = str(seed_context or "global")
    items: List[Dict[str, Any]] = []

    for idx, raw in enumerate(mcqs or [], start=1):
        if not isinstance(raw, dict):
            continue

        item = deepcopy(raw)

        source_options = list(item.get("original_options") or item.get("options") or [])
        if not source_options:
            continue

        try:
            source_answer_index = int(item.get("original_answer_index", item.get("answer_index")))
        except Exception:
            continue

        if source_answer_index < 0 or source_answer_index >= len(source_options):
            continue

        item_id = str(item.get("id") or item.get("question_id") or f"mcq_{idx:02d}")
        option_count = len(source_options)

        if balance_answer_positions:
            desired_pos = _balanced_target_position(idx, option_count, seed_context)
        else:
            desired_pos = _hash_int(f"mcq-position|{seed_context}|{item_id}") % option_count

        order = _order_with_correct_at(
            option_count=option_count,
            correct_index=source_answer_index,
            desired_correct_position=desired_pos,
            seed_text=f"mcq-option-order|{seed_context}|{item_id}|{item.get('question', '')}",
        )

        option_explanations = list(
            item.get("original_option_explanations") or item.get("option_explanations") or []
        )

        if len(option_explanations) == len(source_options):
            shuffled_explanations = [option_explanations[i] for i in order]
        else:
            shuffled_explanations = []

        item["id"] = item_id
        item["original_options"] = source_options
        item["original_answer_index"] = source_answer_index

        if option_explanations:
            item["original_option_explanations"] = option_explanations

        item["options"] = [source_options[i] for i in order]
        item["option_ids"] = [f"opt_{i}" for i in order]
        item["correct_option_id"] = f"opt_{source_answer_index}"
        item["answer_index"] = order.index(source_answer_index)
        item["option_order"] = order
        item["option_explanations"] = shuffled_explanations
        item["kind"] = str(item.get("kind") or ("Critical" if idx <= 3 else "Scenario"))
        item["is_critical"] = bool(item.get("is_critical", idx <= 3))
        item["v3_normalized"] = True
        item["v3_seed_context"] = seed_context

        items.append(item)

    return items


def mcq_bank_fingerprint(mcqs: Iterable[Dict[str, Any]]) -> str:
    """Stable fingerprint of authored question content before per-run shuffling."""
    canonical: List[Dict[str, Any]] = []
    for idx, raw in enumerate(mcqs or [], start=1):
        if not isinstance(raw, dict):
            continue
        canonical.append(
            {
                "id": str(raw.get("id") or raw.get("question_id") or f"mcq_{idx:02d}"),
                "question": str(raw.get("question") or ""),
                "options": list(raw.get("original_options") or raw.get("options") or []),
                "answer_index": int(raw.get("original_answer_index", raw.get("answer_index", -1))),
                "is_critical": bool(raw.get("is_critical", idx <= 3)),
            }
        )
    payload = json.dumps(canonical, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def build_mcq_submission_payload(
    *,
    topic_id: str,
    run_id: str,
    mcqs: Iterable[Dict[str, Any]],
    selections: Dict[str, Any],
    seed_context: str = "",
) -> Dict[str, Any]:
    seed_context = str(seed_context or run_id or topic_id or "global")
    items = normalize_mcq_items(mcqs, seed_context=seed_context)
    normalized_selections: Dict[str, Optional[str]] = {}

    for item in items:
        qid = str(item["id"])
        raw = selections.get(qid)

        if raw is None or raw == "":
            normalized_selections[qid] = None
            continue

        if isinstance(raw, str) and raw.startswith("opt_"):
            normalized_selections[qid] = raw
            continue

        try:
            selected_index = int(raw)
            option_ids = list(item.get("option_ids") or [])
            normalized_selections[qid] = (
                option_ids[selected_index]
                if 0 <= selected_index < len(option_ids)
                else None
            )
        except Exception:
            normalized_selections[qid] = None

    result = score_mcq_submission(
        topic_id=topic_id,
        mcqs=items,
        selections=normalized_selections,
        seed_context=seed_context,
    )

    return {
        "topic_id": topic_id,
        "run_id": run_id,
        "assessment_mode": "v4_stable_mcq_bank",
        "bank_fingerprint": mcq_bank_fingerprint(mcqs),
        "seed_context": seed_context,
        "selections": normalized_selections,
        "result": result,
        "items": [
            {
                "id": item["id"],
                "question": item.get("question", ""),
                "options": item.get("options", []),
                "option_ids": item.get("option_ids", []),
                "correct_option_id": item.get("correct_option_id"),
                "answer_index": item.get("answer_index"),
                "original_options": item.get("original_options", []),
                "original_answer_index": item.get("original_answer_index"),
                "option_order": item.get("option_order", []),
                "is_critical": item.get("is_critical", False),
                "kind": item.get("kind", "Check"),
                "v3_normalized": True,
                "v3_seed_context": seed_context,
            }
            for item in items
        ],
    }


def score_mcq_submission(
    *,
    topic_id: str,
    mcqs: Iterable[Dict[str, Any]],
    selections: Dict[str, Any],
    seed_context: str = "",
) -> Dict[str, Any]:
    seed_context = str(seed_context or "global")
    items = normalize_mcq_items(mcqs, seed_context=seed_context)

    total = len(items)
    answered = 0
    correct = 0
    wrong: List[Dict[str, Any]] = []
    critical_failed: List[str] = []

    for item in items:
        qid = str(item["id"])
        selected_raw = selections.get(qid)
        selected_option_id: Optional[str] = None

        if selected_raw is None or selected_raw == "":
            selected_option_id = None
        elif isinstance(selected_raw, str) and selected_raw.startswith("opt_"):
            selected_option_id = selected_raw
        else:
            try:
                selected_index = int(selected_raw)
                option_ids = list(item.get("option_ids") or [])
                selected_option_id = (
                    option_ids[selected_index]
                    if 0 <= selected_index < len(option_ids)
                    else None
                )
            except Exception:
                selected_option_id = None

        correct_option_id = str(
            item.get("correct_option_id")
            or f"opt_{item.get('original_answer_index', item.get('answer_index', -1))}"
        )

        if selected_option_id is None:
            wrong.append({"id": qid, "reason": "unanswered"})
            if item.get("is_critical"):
                critical_failed.append(qid)
            continue

        answered += 1

        if selected_option_id == correct_option_id:
            correct += 1
        else:
            wrong.append(
                {
                    "id": qid,
                    "selected": selected_option_id,
                    "correct": correct_option_id,
                }
            )
            if item.get("is_critical"):
                critical_failed.append(qid)

    pct = round((correct / total) * 100, 2) if total else 0.0
    min_pct = NORMAL_MCQ_PASS_PCT if is_normal_lesson_topic(topic_id) else 75.0

    has_enough_items = total > 0
    required_items = total

    passed = (
        has_enough_items
        and answered == total
        and pct >= min_pct
        and not critical_failed
    )

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
        "policy": "V4: score stable option IDs from the displayed run order. Correct-answer positions are balanced per run and unanswered items cannot pass.",
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
        msg = "V4 MCQ gate: no saved scored MCQ submission was found."
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
            f"V4 MCQ gate: scored MCQs not passed "
            f"({mcq_result.get('correct', 0)}/{mcq_result.get('total', 0)}, "
            f"{mcq_result.get('score_pct', 0)}%). Complete all MCQs, reach the threshold, and clear critical checks."
        )
        if msg not in evaluation.weak_spots:
            evaluation.weak_spots.append(msg)
        evaluation.decision_reason = (evaluation.decision_reason + " " + msg).strip()
        return evaluation

    strength = (
        f"V4 MCQ gate passed: {mcq_result.get('correct', 0)}/{mcq_result.get('total', 0)} "
        f"({mcq_result.get('score_pct', 0)}%)."
    )
    if strength not in evaluation.strengths:
        evaluation.strengths.append(strength)
    return evaluation
