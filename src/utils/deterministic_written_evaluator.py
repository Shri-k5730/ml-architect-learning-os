from __future__ import annotations

"""Deterministic written-response evaluation for published normal-lesson rubrics.

The evaluator does not invent criteria. It checks only the rubric shipped with
the canonical learning design and returns the exact evidence it found.
"""

import re
from typing import Any, Dict, Iterable, List, Optional, Tuple

from src.schemas import EvaluationResult, Scores, UserAnswer


_NEGATING_PREFIXES = (
    "no ",
    "not ",
    "never ",
    "without ",
    "skip ",
    "bypass ",
    "ignore ",
    "remove ",
    "unrestricted ",
)


def normalize_text(text: str) -> str:
    value = (text or "").lower()
    value = value.replace("’", "'").replace("–", "-").replace("—", "-")
    value = re.sub(r"[^a-z0-9_+\-/' ]+", " ", value)
    value = re.sub(r"\s+", " ", value).strip()
    return value


def _sentences(text: str) -> List[str]:
    parts = re.split(r"(?<=[.!?])\s+|\n+", (text or "").strip())
    return [p.strip() for p in parts if p.strip()]


def _phrase_match(answer_l: str, phrase: str) -> bool:
    phrase_l = normalize_text(phrase)
    if not phrase_l:
        return False

    start = 0
    while True:
        idx = answer_l.find(phrase_l, start)
        if idx < 0:
            return False

        prefix = answer_l[max(0, idx - 18):idx]
        if not any(prefix.endswith(neg) for neg in _NEGATING_PREFIXES):
            return True
        start = idx + max(1, len(phrase_l))


def _group_match(answer_l: str, group: Iterable[str]) -> bool:
    tokens = [normalize_text(token) for token in group if normalize_text(token)]
    return bool(tokens) and all(token in answer_l for token in tokens)


def criterion_match(criterion: Dict[str, Any], answer: str) -> Dict[str, Any]:
    answer_l = normalize_text(answer)
    matched_signal: Optional[str] = None

    for phrase in criterion.get("phrases_any", []) or []:
        if _phrase_match(answer_l, str(phrase)):
            matched_signal = str(phrase)
            break

    if matched_signal is None:
        for group in criterion.get("token_groups_all", []) or []:
            if _group_match(answer_l, group):
                matched_signal = " + ".join(str(token) for token in group)
                break

    matched = matched_signal is not None
    evidence = ""

    if matched:
        signal_parts = [normalize_text(part) for part in re.split(r"\s*\+\s*", matched_signal or "") if normalize_text(part)]
        for sentence in _sentences(answer):
            sentence_l = normalize_text(sentence)
            if all(part in sentence_l for part in signal_parts[:2]):
                evidence = sentence
                break
        if not evidence:
            for sentence in _sentences(answer):
                sentence_l = normalize_text(sentence)
                if any(part in sentence_l for part in signal_parts):
                    evidence = sentence
                    break

    return {
        "id": str(criterion.get("id") or ""),
        "label": str(criterion.get("label") or criterion.get("id") or "criterion"),
        "description": str(criterion.get("description") or ""),
        "matched": matched,
        "matched_signal": matched_signal,
        "evidence": evidence,
    }


def evaluate_rubric_evidence(
    learning_design: Dict[str, Any],
    answer: str,
) -> Dict[str, Any]:
    rubric = dict(learning_design.get("written_rubric") or {})
    required = [criterion_match(item, answer) for item in rubric.get("required", []) or []]
    bonus = [criterion_match(item, answer) for item in rubric.get("bonus", []) or []]

    required_met = sum(1 for item in required if item["matched"])
    bonus_met = sum(1 for item in bonus if item["matched"])

    target = (learning_design.get("evidence_tasks") or [{}])[0]
    minimum = int(target.get("target_min_words", 80) or 80)
    maximum = int(target.get("target_max_words", 140) or 140)
    word_count = len((answer or "").split())

    return {
        "mode": "v4_deterministic_published_rubric",
        "topic_id": learning_design.get("topic_id"),
        "design_version": learning_design.get("design_version"),
        "required": required,
        "bonus": bonus,
        "required_met": required_met,
        "required_total": len(required),
        "bonus_met": bonus_met,
        "bonus_total": len(bonus),
        "all_required_met": bool(required) and required_met == len(required),
        "word_count": word_count,
        "target_min_words": minimum,
        "target_max_words": maximum,
        "length_within_target": minimum <= word_count <= maximum,
        "policy": (
            "Only the published written rubric is scored. A criterion is credited "
            "only when matching evidence is present in the learner response."
        ),
    }


def _score_communication(audit: Dict[str, Any]) -> int:
    count = int(audit.get("word_count", 0) or 0)
    minimum = int(audit.get("target_min_words", 80) or 80)
    maximum = int(audit.get("target_max_words", 140) or 140)

    if count < 30:
        return 1
    if count < 50 or count > max(280, maximum * 2):
        return 2
    if minimum <= count <= maximum:
        return 4
    return 3


def _required_map(audit: Dict[str, Any]) -> Dict[str, bool]:
    return {str(item.get("id")): bool(item.get("matched")) for item in audit.get("required", [])}


def build_deterministic_evaluation(
    *,
    learning_design: Dict[str, Any],
    user_answers: List[UserAnswer],
    mcq_result: Optional[Dict[str, Any]] = None,
) -> Tuple[EvaluationResult, Dict[str, Any]]:
    answer = user_answers[0].answer if user_answers else ""
    audit = evaluate_rubric_evidence(learning_design, answer)
    req = _required_map(audit)

    mechanism = req.get("mechanism", False)
    example = req.get("example", False)
    risk = req.get("risk", False)
    control = req.get("control", False)
    bonus_met = int(audit.get("bonus_met", 0) or 0)

    conceptual = 3 if mechanism else 2
    if mechanism and example and bool((mcq_result or {}).get("score_pct", 0) >= 90):
        conceptual = 4

    practical_components = sum([example, risk, control])
    if practical_components == 3:
        practical = 3 + (1 if bonus_met >= 1 else 0)
        if bonus_met >= 3:
            practical = 5
    elif practical_components == 2:
        practical = 2
    else:
        practical = 1

    if mechanism and control:
        architect = 3 + (1 if bonus_met >= 2 else 0)
        if bonus_met >= 3:
            architect = 5
    elif mechanism or control:
        architect = 2
    else:
        architect = 1

    communication = _score_communication(audit)

    all_required = bool(audit.get("all_required_met"))
    decision = "pass" if all_required else "revise"
    next_action = "next_topic" if all_required else "retry_same_topic"

    strengths: List[str] = []
    for item in audit.get("required", []):
        if item.get("matched"):
            evidence = str(item.get("evidence") or "").strip()
            label = str(item.get("label") or item.get("id"))
            strengths.append(
                f"{label} demonstrated"
                + (f": {evidence}" if evidence else ".")
            )
    strengths = strengths[:3]

    weak_spots: List[str] = []
    for item in audit.get("required", []):
        if not item.get("matched"):
            weak_spots.append(
                f"Missing published requirement: {item.get('label')}. {item.get('description')}"
            )

    met_labels = [str(item.get("label")) for item in audit.get("required", []) if item.get("matched")]
    missing_labels = [str(item.get("label")) for item in audit.get("required", []) if not item.get("matched")]

    if all_required:
        decision_reason = (
            "Published written rubric passed. Evidence was found for: "
            + ", ".join(met_labels)
            + ". No hidden criteria were applied."
        )
        refined = (
            "The response demonstrates the required mechanism, concrete example, "
            "specific risk and implementable control for this lesson."
        )
    else:
        decision_reason = (
            "Published written rubric not yet passed. Missing: "
            + ", ".join(missing_labels)
            + ". Present: "
            + (", ".join(met_labels) if met_labels else "none")
            + "."
        )
        refined = (
            "Keep the valid parts already demonstrated and add only the missing "
            "published requirement(s). No extra architecture vocabulary is required."
        )

    bonus_labels = [str(item.get("label")) for item in audit.get("bonus", []) if item.get("matched")]
    architect_summary = (
        "Architect evidence is grounded in the published rubric. "
        + ("Additional operating detail demonstrated: " + ", ".join(bonus_labels) + "." if bonus_labels else
           "A higher score would require only relevant optional operating detail from the published bonus criteria.")
    )

    evaluation = EvaluationResult(
        topic_id=str(learning_design.get("topic_id") or ""),
        scores=Scores(
            conceptual_clarity=max(1, min(5, conceptual)),
            practical_reasoning=max(1, min(5, practical)),
            architect_reasoning=max(1, min(5, architect)),
            communication=max(1, min(5, communication)),
        ),
        strengths=strengths,
        weak_spots=weak_spots,
        decision=decision,
        decision_reason=decision_reason,
        refined_explanation=refined,
        refined_architect_summary=architect_summary,
        next_action=next_action,
    )

    audit["scores_before_mcq_gate"] = evaluation.scores.to_dict()
    audit["decision_before_mcq_gate"] = evaluation.decision
    return evaluation, audit
