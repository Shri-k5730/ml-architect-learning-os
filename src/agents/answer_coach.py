from __future__ import annotations

import re
from typing import Any, Callable, Dict, List

from src.agents.topic_coaching_profiles import (
    get_topic_coaching_profile,
    profile_golden_answer,
)
from src.agents.expert_blueprints import get_topic_blueprint
from src.schemas import (
    ArchitectNote,
    Assessment,
    ConceptNote,
    EvaluationResult,
    UserAnswer,
)


class AnswerCoachError(Exception):
    """Raised when answer coaching generation fails."""


def _answer_map(user_answers: List[UserAnswer]) -> Dict[str, str]:
    return {answer.question_id: answer.answer for answer in user_answers}


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip().lower())


def _meaningful_words(text: str) -> List[str]:
    return [
        word.strip(".,;:()[]{}!?\"'").lower()
        for word in (text or "").split()
        if len(word.strip(".,;:()[]{}!?\"'").lower()) > 4
    ]


def _mentions_question(evaluation: EvaluationResult, question_id: str) -> bool:
    weak_text = " ".join(evaluation.weak_spots or []).lower()
    patterns = [question_id.lower(), question_id.lower().replace("q", "question ")]
    return any(pattern in weak_text for pattern in patterns)


def _expected_focus_gaps(expected_focus: List[str], answer: str) -> List[str]:
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


def _topic_misconceptions(topic_id: str, answer: str) -> List[Dict[str, str]]:
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

    return findings[:3]


def _type_specific_gaps(question_type: str, answer: str) -> List[str]:
    answer_l = _normalize(answer)
    gaps: List[str] = []

    if question_type == "tiny_hands_on":
        if not any(token in answer_l for token in ["compare", "calculate", "metric", "rmse", "mae", "r2", "r²", "precision", "recall", "confusion", "train", "validation"]):
            gaps.append("Add a concrete metric, calculation, or train-vs-validation comparison.")
    elif question_type == "failure_diagnosis":
        if not any(token in answer_l for token in ["cause", "because", "mechanism", "feature", "pipeline", "training", "distribution", "drift", "underfit", "overfit"]):
            gaps.append("Name the failure mechanism, not only the symptom.")
    elif question_type == "architect_decision":
        if not any(token in answer_l for token in ["monitor", "threshold", "fallback", "alert", "validation", "drift", "guardrail", "trigger", "owner"]):
            gaps.append("Name concrete controls such as monitoring, thresholds, fallback, validation gates, or retraining triggers.")
    elif question_type == "teachback":
        if not any(token in answer_l for token in ["manufacturing", "defect", "quality", "line", "stakeholder", "business", "production"]):
            gaps.append("Anchor the explanation in a business or production example.")

    return gaps[:2]


def _question_quality(
    question_id: str,
    answer: str,
    expected_gaps: List[str],
    misconception_hits: List[Dict[str, str]],
    evaluation: EvaluationResult,
) -> str:
    answer_len = len((answer or "").strip())
    if answer_len < 30:
        return "weak"
    if misconception_hits:
        return "partial"
    if _mentions_question(evaluation, question_id):
        return "partial"
    if len(expected_gaps) >= 3:
        return "weak"
    if expected_gaps:
        return "partial"
    return "strong"


def _missing_points(
    topic_id: str,
    expected_focus: List[str],
    answer: str,
    question_type: str,
) -> tuple[List[str], List[Dict[str, str]]]:
    missing: List[str] = []

    for gap in _expected_focus_gaps(expected_focus, answer):
        if gap not in missing:
            missing.append(gap)
    for gap in _type_specific_gaps(question_type, answer):
        if gap not in missing:
            missing.append(gap)

    misconceptions = _topic_misconceptions(topic_id, answer)
    for item in misconceptions:
        issue = item.get("issue", "Potential misconception detected.")
        if issue not in missing:
            missing.append(issue)

    if not missing:
        missing.append("The answer is directionally correct. To make it stronger, add a more concrete metric, failure mode, or production control.")

    return missing[:5], misconceptions


def _fallback_better_answer(
    question_type: str,
    question: str,
    expected_focus: List[str],
    concept_note: ConceptNote,
    architect_note: ArchitectNote,
) -> str:
    focus_sentence = "; ".join(expected_focus[:3]) if expected_focus else "the concept, practical behavior, and production implication"
    blueprint = get_topic_blueprint(concept_note.topic_id) or {}
    if blueprint:
        mechanism = str(blueprint.get("core_mechanism", ""))
        controls = ", ".join(str(item) for item in blueprint.get("system_controls", [])[:3])
        frame = " ".join(str(item) for item in blueprint.get("mission_answer_frame", [])[:3])
        if question_type == "concept_check":
            return (
                f"A stronger answer should define {concept_note.title}, then explain the specific mechanism: {mechanism} "
                f"Do not stop at generic production risk. Cover: {focus_sentence}."
            )
        if question_type == "tiny_hands_on":
            return (
                f"A stronger answer should use the scenario or calculation, then connect it to this mechanism: {mechanism} "
                f"Use the answer frame: {frame}"
            )
        if question_type == "failure_diagnosis":
            return (
                f"A stronger answer should separate symptom, mechanism, evidence, and prevention. "
                f"For this topic the mechanism is: {mechanism}"
            )
        if question_type == "architect_decision":
            return (
                f"A stronger answer should turn the mechanism into controls. Relevant controls include: {controls}. "
                f"Cover: {focus_sentence}."
            )
        if question_type == "teachback":
            return (
                f"A stronger answer should explain the concept simply, use one concrete business example, "
                f"and name one control such as: {controls}."
            )

    if question_type == "concept_check":
        return (
            f"A stronger answer should define {concept_note.title} directly, state why the wrong interpretation fails, "
            f"and connect the concept to model behavior. Cover: {focus_sentence}."
        )

    if question_type == "tiny_hands_on":
        return (
            "A stronger answer should use the numbers or scenario in the question, make a concrete comparison, "
            f"and state the practical decision. Cover: {focus_sentence}."
        )

    if question_type == "failure_diagnosis":
        return (
            "A stronger answer should separate symptom from cause: what was observed, what likely failed, "
            f"and what evidence would confirm it. Cover: {focus_sentence}."
        )

    if question_type == "architect_decision":
        return (
            "A stronger answer should name the design controls, the metric or threshold, the monitoring rule, "
            f"and the operational response. Cover: {focus_sentence}."
        )

    if question_type == "teachback":
        return (
            "A stronger answer should explain the idea in simple language, use a concrete business example, "
            f"and preserve the production implication. Cover: {focus_sentence}."
        )

    return f"A stronger answer should directly address the mission and cover: {focus_sentence}."


def _better_answer(
    topic_id: str,
    question_type: str,
    question: str,
    expected_focus: List[str],
    concept_note: ConceptNote,
    architect_note: ArchitectNote,
) -> str:
    golden = profile_golden_answer(topic_id, question_type)
    if golden:
        return f"A stronger answer: {golden}"
    return _fallback_better_answer(question_type, question, expected_focus, concept_note, architect_note)


def _why_better(question_type: str) -> str:
    if question_type == "tiny_hands_on":
        return "It uses observable behavior, metrics, or calculation instead of staying at theory level."
    if question_type == "failure_diagnosis":
        return "It names the likely mechanism and what evidence would confirm it, instead of only describing the symptom."
    if question_type == "architect_decision":
        return "It converts a broad intention into controls that can be implemented, monitored, and owned."
    if question_type == "teachback":
        return "It is simpler, business-facing, and still keeps the production consequence visible."
    return "It defines the concept precisely and connects it to model behavior rather than vague system language."


def _architect_upgrade(question_type: str, architect_note: ArchitectNote) -> str:
    if question_type == "architect_decision":
        return "Upgrade by naming the exact controls: validation gate, metric threshold, monitoring signal, fallback policy, retraining trigger, and response owner."
    if question_type == "failure_diagnosis":
        return "Upgrade by separating observed symptom, likely model failure, data/pipeline evidence, and production control fix."
    if question_type == "tiny_hands_on":
        return "Upgrade by adding the metric comparison or numerical check you would use before trusting the model."
    if question_type == "teachback":
        return "Upgrade by explaining the business consequence in one concrete manufacturing, monitoring, or quality example."
    return architect_note.interview_framing or "Upgrade the answer by tying the concept to evaluation, deployment risk, and monitoring decisions."


def generate_answer_coaching(
    concept_note: ConceptNote,
    architect_note: ArchitectNote,
    assessment: Assessment,
    user_answers: List[UserAnswer],
    evaluation: EvaluationResult,
    llm_callable: Callable[[str, str], str] | None = None,
) -> Dict[str, Any]:
    """Generate topic-grounded, evidence-bound per-question coaching.

    This is deterministic by design. The LLM can still evaluate the final attempt,
    but coaching must not hallucinate a generic answer or leak rubric text.
    """
    answers = _answer_map(user_answers)
    coaching: List[Dict[str, Any]] = []

    for question in assessment.questions:
        answer = answers.get(question.question_id, "")
        missing, misconception_hits = _missing_points(
            topic_id=concept_note.topic_id,
            expected_focus=question.expected_focus,
            answer=answer,
            question_type=question.type,
        )
        quality = _question_quality(question.question_id, answer, missing, misconception_hits, evaluation)

        coaching.append(
            {
                "question_id": question.question_id,
                "question": question.question,
                "your_answer": answer,
                "answer_quality": quality,
                "what_was_missing": missing,
                "evidence_bound_findings": misconception_hits,
                "better_answer": _better_answer(
                    topic_id=concept_note.topic_id,
                    question_type=question.type,
                    question=question.question,
                    expected_focus=question.expected_focus,
                    concept_note=concept_note,
                    architect_note=architect_note,
                ),
                "why_this_is_better": _why_better(question.type),
                "architect_upgrade": _architect_upgrade(question.type, architect_note),
            }
        )

    return {
        "topic_id": concept_note.topic_id,
        "mode": "topic_grounded_evidence_bound",
        "coaching": coaching,
    }
