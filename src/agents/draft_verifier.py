from __future__ import annotations

import re
from typing import Any, Dict, List

from src.agents.topic_coaching_profiles import get_topic_coaching_profile
from src.agents.writing_assist import analyze_answer_text
from src.schemas import ArchitectNote, Assessment, ConceptNote


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip().lower())


def _contains_any(answer_l: str, tokens: List[str]) -> bool:
    return any(str(token).lower() in answer_l for token in tokens if str(token).strip())


SEMANTIC_COVERAGE: Dict[str, List[str]] = {
    # generic rubric phrases that learners often satisfy without exact wording
    "where/why errors": ["where", "why", "failure pocket", "error pattern", "wrong", "mistake", "slices mistakes", "supplier", "shift", "defect type"],
    "average metric limitation": ["hide", "overall", "average", "92%", "80%", "accuracy", "one supplier", "one shift", "one defect"],
    "segment slicing": ["slice", "supplier", "shift", "plant", "station", "product", "defect type", "feature range", "confidence band", "segment"],
    "evidence": ["inspect", "compare", "confusion matrix", "false negative", "feature distribution", "missing", "label", "sensor", "process", "evidence"],
    "data/process/label shift": ["process", "material", "measurement", "missing feature", "label", "training", "represented", "feature distribution", "supplier process"],
    "checks": ["inspect", "check", "compare", "review", "audit", "confusion matrix", "missing-value", "distribution"],
    "logged predictions": ["log every prediction", "timestamp", "model score", "prediction", "actual label", "confidence", "plant", "line", "station"],
    "simple explanation": ["like", "explain", "first", "model is wrong", "replacing", "checking", "defect", "where"],
    "targeted fix": ["targeted", "right action", "better data", "threshold change", "feature improvement", "retraining", "choose the right action", "fix backlog"],
    "business efficiency": ["business", "efficient", "waste", "without checking", "will not fix", "quality", "supplier-specific", "review"],
    "score-to-action": ["score", "action", "decision", "threshold", "decision point", "business policy"],
    "missed defects vs extra checks": ["missed defect", "extra inspection", "false negative", "false positive", "inspection", "business loss"],
    "owner": ["owner", "quality owner", "ml owner", "review", "approval", "responsible"],
    "monitoring": ["monitor", "dashboard", "track", "trigger", "alert", "weekly", "monthly"],
    "minority-class failure": ["minority", "defect", "recall", "false negative", "accuracy", "escape", "warranty"],
    "interpretation": ["bad model", "despite high accuracy", "0 recall", "catches none", "quality", "business loss"],
}


def _meaningful_words(text: str) -> List[str]:
    return [
        word.strip(".,;:()[]{}!?\"'").lower()
        for word in (text or "").split()
        if len(word.strip(".,;:()[]{}!?\"'").lower()) > 4
    ]


def _focus_is_covered(focus: str, answer_l: str) -> bool:
    focus_l = _normalize(focus)
    if not focus_l:
        return True
    if focus_l in answer_l:
        return True
    for key, tokens in SEMANTIC_COVERAGE.items():
        if key in focus_l and _contains_any(answer_l, tokens):
            return True
    words = _meaningful_words(focus_l)
    if not words:
        return True
    hits = sum(1 for word in words if word in answer_l)
    required = 1 if len(words) <= 2 else 2
    return hits >= required


def _coverage_gap(expected_focus: List[str], answer: str) -> List[str]:
    answer_l = _normalize(answer)
    gaps: List[str] = []
    for focus in expected_focus or []:
        if not _focus_is_covered(str(focus), answer_l):
            gaps.append(str(focus))
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

    if word_count > 190:
        gaps.append("Too long. Cut repeated definitions and keep the answer to mechanism, evidence, and control.")
    elif word_count > 155 and question_type in {"teachback", "concept_check"}:
        gaps.append("Tighten the answer. This question needs clarity, not an essay.")

    if question_type == "tiny_hands_on":
        if not any(token in answer_l for token in ["metric", "precision", "recall", "confusion", "calculate", "compare", "inspect", "false negative", "feature distribution", "segment"]):
            gaps.append("Use the number or scenario first, then interpret it.")
    if question_type == "failure_diagnosis":
        if not any(token in answer_l for token in ["cause", "because", "mechanism", "evidence", "inspect", "check", "distribution", "label", "feature", "threshold", "segment"]):
            gaps.append("Separate symptom, likely cause, evidence to inspect, and prevention.")
    if question_type == "architect_decision":
        has_control = any(token in answer_l for token in ["monitor", "threshold", "fallback", "alert", "validation", "owner", "trigger", "dashboard", "audit", "review"])
        if not has_control:
            gaps.append("Name the concrete controls, owner, trigger, or review path you would design into the system.")
    if question_type == "teachback":
        if len(answer.split()) > 150:
            gaps.append("Shorten the explanation. Stakeholder teachback should be clear, not exhaustive.")
        if not any(token in answer_l for token in ["like", "example", "manufacturing", "defect", "quality", "business", "supplier", "shift"]):
            gaps.append("Anchor the explanation in a simple analogy or business example.")

    return gaps[:3]


def _serious_technical_hints(writing_assist: Dict[str, Any]) -> List[str]:
    hints = writing_assist.get("technical_precision_hints", []) or []
    # These are concept precision risks, not spelling. Keep them separate from language noise.
    return [str(hint) for hint in hints if str(hint).strip()][:3]


def _readiness_score(answer: str, gap_count: int, misconception_count: int, serious_hint_count: int) -> int:
    word_count = len((answer or "").split())
    if word_count < 20:
        return 1
    if misconception_count >= 2 or serious_hint_count >= 2:
        return 2
    if misconception_count == 1 and gap_count >= 1:
        return 2
    if gap_count >= 3:
        return 2
    if gap_count == 2:
        return 3
    if gap_count == 1:
        return 4 if word_count >= 60 and serious_hint_count == 0 else 3
    return 4


def _verdict(score: int) -> str:
    if score <= 2:
        return "Weak draft"
    if score == 3:
        return "Partial draft"
    return "Submit-ready draft"


def _next_action(question_type: str, gaps: List[str], misconceptions: List[Dict[str, str]], serious_hints: List[str]) -> str:
    if serious_hints:
        return serious_hints[0]
    if misconceptions:
        return misconceptions[0]["correction"]
    if gaps:
        return gaps[0]
    if question_type == "architect_decision":
        return "To push from 4 to 5, add owner, trigger threshold, review cadence, and operational action."
    if question_type == "tiny_hands_on":
        return "To push from 4 to 5, add the concrete interpretation and the decision implication."
    if question_type == "teachback":
        return "To push from 4 to 5, add a simple analogy plus one business consequence."
    return "Submit-ready. To push higher, add one sharper mechanism or control."


def verify_draft_answers(
    concept_note: ConceptNote,
    architect_note: ArchitectNote,
    assessment: Assessment,
    answers_doc: Dict[str, Any],
) -> Dict[str, Any]:
    """Copy-safe draft verification calibrated against final-evaluation behavior.

    This verifier is semantic, not keyword-only. It should not call a strong answer weak
    merely because the answer used different wording from expected_focus.
    """
    by_question = {item.get("question_id"): item for item in answers_doc.get("answers", [])}
    items: List[Dict[str, Any]] = []
    profile = get_topic_coaching_profile(concept_note.topic_id)

    for question in assessment.questions:
        answer = str(by_question.get(question.question_id, {}).get("answer", "")).strip()
        expected_gaps = _coverage_gap(question.expected_focus, answer)
        concept_findings = _profile_gap(concept_note.topic_id, answer)
        type_gaps = _type_gap(question.type, answer)
        writing_assist = analyze_answer_text(answer, question.type)
        serious_hints = _serious_technical_hints(writing_assist)

        all_gaps: List[str] = []
        for gap in [*expected_gaps, *type_gaps]:
            if gap not in all_gaps:
                all_gaps.append(gap)

        # Do not count spelling suggestions as readiness blockers. They are language noise.
        score = _readiness_score(answer, len(all_gaps), len(concept_findings), len(serious_hints))
        items.append(
            {
                "question_id": question.question_id,
                "question": question.question,
                "question_type": question.type,
                "verdict": _verdict(score),
                "readiness_score": score,
                "likely_score": score,
                "coverage_gaps": all_gaps[:4],
                "misconceptions": concept_findings,
                "technical_precision_hints": serious_hints,
                "writing_assist": writing_assist,
                "language_noise_note": (
                    "Language noise detected. Clean it if possible, but it should not be treated as a concept gap."
                    if writing_assist.get("spelling_suggestions") else ""
                ),
                "next_improvement": _next_action(question.type, all_gaps, concept_findings, serious_hints),
                "copy_safe": True,
            }
        )

    weak_items = [item for item in items if item["readiness_score"] <= 2]
    partial_items = [item for item in items if item["readiness_score"] == 3]
    submit_ready_items = [item for item in items if item["readiness_score"] >= 4]
    readiness_avg = round(sum(item["readiness_score"] for item in items) / len(items), 2) if items else 0
    four_star_ready = (not weak_items and len(submit_ready_items) >= max(3, len(items) - 1) and readiness_avg >= 3.6)

    if weak_items:
        recommendation = "Do not submit yet. Fix the weak draft or technical precision issue first."
    elif four_star_ready:
        recommendation = "Submit-ready for a 4-star attempt. To chase 5, add sharper owner/trigger/action details where relevant."
    elif partial_items:
        recommendation = "Borderline submit-ready. Improve the partial drafts if you want a stronger score."
    else:
        recommendation = "Evaluable. Final evaluation checks cross-answer consistency and may still be stricter."

    return {
        "topic_id": concept_note.topic_id,
        "topic_title": concept_note.title,
        "mode": "draft_verification_semantic_calibrated_v2",
        "summary": {
            "readiness_average": readiness_avg,
            "likely_average": readiness_avg,
            "weak_count": len(weak_items),
            "partial_count": len(partial_items),
            "submit_ready_count": len(submit_ready_items),
            "four_star_ready": four_star_ready,
            "recommendation": recommendation,
        },
        "core_concepts_to_check": profile.get("core_concepts", [])[:5],
        "items": items,
        "note": "Verification uses semantic coverage. It gives hints only. Spelling is language noise; technical misuse is content feedback. Better answers remain hidden until final evaluation.",
    }
