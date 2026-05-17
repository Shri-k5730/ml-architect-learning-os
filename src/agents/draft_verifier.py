from __future__ import annotations

import re
from typing import Any, Dict, List

from src.agents.topic_coaching_profiles import get_topic_coaching_profile
from src.schemas import ArchitectNote, Assessment, ConceptNote


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip().lower())


def _meaningful_words(text: str) -> List[str]:
    return [
        word.strip(".,;:()[]{}!?\"'").lower()
        for word in (text or "").split()
        if len(word.strip(".,;:()[]{}!?\"'").lower()) > 4
    ]


def _coverage_gap(expected_focus: List[str], answer: str) -> List[str]:
    answer_l = _normalize(answer)
    gaps: List[str] = []

    for focus in expected_focus or []:
        words = _meaningful_words(focus)
        if not words:
            continue
        hits = sum(1 for word in words if word in answer_l)
        required = 1 if len(words) <= 2 else 2
        if hits < required:
            gaps.append(focus)

    return gaps[:3]


def _profile_gap(topic_id: str, answer: str) -> List[Dict[str, str]]:
    answer_l = _normalize(answer)
    profile = get_topic_coaching_profile(topic_id)
    findings: List[Dict[str, str]] = []

    for item in profile.get("common_misconceptions", []) or []:
        patterns = item.get("pattern", [])
        if isinstance(patterns, str):
            patterns = [patterns]
        for pattern in patterns:
            if pattern and pattern.lower() in answer_l:
                findings.append(
                    {
                        "evidence": pattern,
                        "issue": str(item.get("issue", "Potential misconception detected.")),
                        "correction": str(item.get("correction", "Tighten the concept before final evaluation.")),
                    }
                )
                break

    return findings[:2]


def _type_gap(question_type: str, answer: str) -> List[str]:
    answer_l = _normalize(answer)
    gaps: List[str] = []
    word_count = len(answer.split())

    if word_count > 180:
        gaps.append("Too long. Cut repeated definitions and keep the answer to definition, example, production risk, and control.")
    elif word_count > 140 and question_type in {"teachback", "concept_check"}:
        gaps.append("Tighten the answer. This question needs clarity, not an essay.")

    if question_type == "tiny_hands_on":
        if not any(token in answer_l for token in ["metric", "rmse", "mae", "r2", "r²", "precision", "recall", "confusion", "calculate", "compare"]):
            gaps.append("Add a metric, calculation, or concrete comparison. Pure explanation is not enough.")
    if question_type == "failure_diagnosis":
        if not any(token in answer_l for token in ["because", "cause", "mechanism", "pipeline", "feature", "training", "drift", "distribution", "underfit", "overfit"]):
            gaps.append("Name the failure mechanism, not only the symptom.")
    if question_type == "architect_decision":
        if not any(token in answer_l for token in ["monitor", "threshold", "fallback", "alert", "validation", "drift", "owner", "trigger", "guardrail"]):
            gaps.append("Name the concrete controls you would design into the system.")
    if question_type == "teachback":
        if len(answer.split()) > 150:
            gaps.append("Shorten the explanation. Stakeholder teachback should be clear, not exhaustive.")
        if not any(token in answer_l for token in ["example", "manufacturing", "defect", "line", "quality", "stakeholder"]):
            gaps.append("Anchor the explanation in a concrete business example.")

    return gaps[:3]


def _vague_language_penalty(answer: str) -> int:
    answer_l = _normalize(answer)
    vague_terms = ["average", "good", "bad", "better outcome", "balance between", "properly", "accurately set"]
    return 1 if any(term in answer_l for term in vague_terms) else 0


def _readiness_score(answer: str, gap_count: int, misconception_count: int) -> int:
    """Conservative draft readiness score, not a star prediction.

    The previous verifier was too generous: directionally correct drafts were
    labelled strong, while final evaluation penalized missing practical and
    architect detail. This score intentionally under-promises.
    """
    word_count = len((answer or "").split())
    vague_penalty = _vague_language_penalty(answer)
    overlong_penalty = 1 if word_count > 180 else 0

    if word_count < 20:
        return 1
    if misconception_count >= 2:
        return 2
    if misconception_count == 1 and gap_count >= 1:
        return 2
    if gap_count >= 3:
        return 2
    if gap_count == 2:
        return 3
    if gap_count == 1:
        return 3 if (vague_penalty or overlong_penalty) else 4

    # No obvious gap does not mean 5-star readiness. Full evaluation is still
    # stricter and checks coherence across all answers. Overlong answers are
    # capped because they usually hide repetition instead of stronger reasoning.
    return 3 if overlong_penalty else 4


def _verdict(score: int) -> str:
    if score <= 2:
        return "Weak draft"
    if score == 3:
        return "Partial draft"
    return "Evaluable draft"


def _next_action(question_type: str, gaps: List[str], misconceptions: List[Dict[str, str]]) -> str:
    if misconceptions:
        return misconceptions[0]["correction"]
    if gaps:
        return gaps[0]
    if question_type == "architect_decision":
        return "Add one owner, threshold, or production guardrail to make it architecture-grade."
    if question_type == "tiny_hands_on":
        return "Add one number, metric, or comparison to make the reasoning concrete."
    return "Tighten wording and remove vague phrases before final evaluation."


def verify_draft_answers(
    concept_note: ConceptNote,
    architect_note: ArchitectNote,
    assessment: Assessment,
    answers_doc: Dict[str, Any],
) -> Dict[str, Any]:
    """Create copy-safe draft verification.

    This deliberately avoids full model answers. It tells the learner what is missing,
    but does not hand over a polished answer before the attempt is submitted.
    """
    by_question = {item.get("question_id"): item for item in answers_doc.get("answers", [])}
    items: List[Dict[str, Any]] = []
    profile = get_topic_coaching_profile(concept_note.topic_id)

    for question in assessment.questions:
        answer = str(by_question.get(question.question_id, {}).get("answer", "")).strip()
        expected_gaps = _coverage_gap(question.expected_focus, answer)
        concept_findings = _profile_gap(concept_note.topic_id, answer)
        type_gaps = _type_gap(question.type, answer)

        all_gaps = []
        for gap in [*expected_gaps, *type_gaps]:
            if gap not in all_gaps:
                all_gaps.append(gap)

        score = _readiness_score(answer, len(all_gaps), len(concept_findings))
        items.append(
            {
                "question_id": question.question_id,
                "question": question.question,
                "question_type": question.type,
                "verdict": _verdict(score),
                "readiness_score": score,
                "likely_score": score,  # backward-compatible UI key; not a star prediction
                "coverage_gaps": all_gaps[:4],
                "misconceptions": concept_findings,
                "next_improvement": _next_action(question.type, all_gaps, concept_findings),
                "copy_safe": True,
            }
        )

    weak_items = [item for item in items if item["readiness_score"] <= 2]
    partial_items = [item for item in items if item["readiness_score"] == 3]
    readiness_avg = round(sum(item["readiness_score"] for item in items) / len(items), 2) if items else 0
    four_star_ready = (not weak_items and not partial_items and readiness_avg >= 4)

    return {
        "topic_id": concept_note.topic_id,
        "topic_title": concept_note.title,
        "mode": "draft_verification_copy_safe_calibrated",
        "summary": {
            "readiness_average": readiness_avg,
            "likely_average": readiness_avg,  # backward compatibility; not a star prediction
            "weak_count": len(weak_items),
            "partial_count": len(partial_items),
            "four_star_ready": four_star_ready,
            "recommendation": (
                "Do not submit yet. Fix the weak drafts first."
                if weak_items
                else "Not 4-star ready yet. Improve the partial drafts before final submission."
                if partial_items
                else "Evaluable. This still does not guarantee 4 stars; final evaluation checks consistency across all answers."
            ),
        },
        "core_concepts_to_check": profile.get("core_concepts", [])[:5],
        "items": items,
        "note": "Verification gives hints only. Readiness is not a star prediction. Better answers are deliberately hidden until final evaluation is locked.",
    }
