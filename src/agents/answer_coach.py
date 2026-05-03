from __future__ import annotations

from typing import Any, Callable, Dict, List

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


def _question_quality(question_id: str, answer: str, evaluation: EvaluationResult) -> str:
    answer_len = len((answer or "").strip())
    weak_text = " ".join(evaluation.weak_spots or []).lower()
    q_patterns = [question_id.lower(), question_id.lower().replace("q", "question ")]

    if any(pattern in weak_text for pattern in q_patterns):
        return "partial" if answer_len >= 40 else "weak"
    if answer_len < 30:
        return "weak"
    if answer_len < 90:
        return "partial"
    return "strong"


def _missing_points(expected_focus: List[str], answer: str, question_type: str) -> List[str]:
    answer_l = (answer or "").lower()
    missing: List[str] = []

    for item in expected_focus:
        # Small heuristic: if less than two meaningful words from the focus appear, call it missing.
        words = [w.strip(".,;:()[]{}!?\"'").lower() for w in item.split() if len(w) > 4]
        hits = sum(1 for w in words if w and w in answer_l)
        if hits < min(2, max(1, len(words))):
            missing.append(item)

    if question_type == "tiny_hands_on" and not any(w in answer_l for w in ["because", "therefore", "beyond", "outside", "range", "fail"]):
        missing.append("Show the reasoning path, not only the final observation.")
    if question_type == "failure_diagnosis" and not any(w in answer_l for w in ["training", "unseen", "drift", "distribution", "edge", "failure"]):
        missing.append("Name the concrete failure mechanism, such as unseen inputs, missing failure examples, or distribution shift.")
    if question_type == "architect_decision" and not any(w in answer_l for w in ["monitor", "fallback", "threshold", "alert", "drift", "validation", "guardrail"]):
        missing.append("Name concrete design controls such as monitoring, drift checks, fallback, thresholding, or validation gates.")

    # Keep it useful, not noisy.
    deduped: List[str] = []
    for item in missing:
        if item not in deduped:
            deduped.append(item)
    return deduped[:4] if deduped else ["The answer is directionally correct, but could be sharper and more specific."]


def _better_answer(
    question_type: str,
    question: str,
    expected_focus: List[str],
    concept_note: ConceptNote,
    architect_note: ArchitectNote,
) -> str:
    focus_sentence = " ".join(expected_focus)

    if question_type == "concept_check":
        return (
            f"A stronger answer: {concept_note.title} is about learning useful patterns from data, not discovering absolute truth. "
            f"The model learns relationships between inputs and outputs from historical examples, then uses those relationships on new data. "
            f"The key limit is that the model does not understand why the relationship exists, so its reliability depends on whether new data still resembles the training data."
        )

    if question_type == "tiny_hands_on":
        return (
            f"A stronger answer: I would first identify the pattern in the given data, then state the risk outside the observed range. "
            f"Here the expected reasoning is: {focus_sentence} "
            f"The important point is not only the observed relationship, but the boundary of the data. A model trained only on this range may extrapolate badly when the input moves beyond what it has seen."
        )

    if question_type == "failure_diagnosis":
        return (
            f"A stronger answer: The likely failure is that the training data did not contain the condition that later appeared in production. "
            f"The model learned normal-pattern behavior and treated abnormal cases as if they were normal. "
            f"This is a generalization and distribution-shift problem, not just a model-accuracy problem. The fix is to include representative failure cases, stress-test edge cases, and monitor production drift."
        )

    if question_type == "architect_decision":
        return (
            f"A stronger answer: As an ML Architect, I would design the system with explicit production guardrails: validation data that resembles deployment, drift monitoring, confidence or anomaly thresholds, alerts, fallback rules, and periodic retraining triggers. "
            f"I would also define what action the business should take when the model sees inputs outside its training distribution. "
            f"That turns the model from an offline predictor into a controlled production system."
        )

    if question_type == "teachback":
        return (
            f"A stronger answer: I would explain it this way: the model learns from examples, like learning from past operating history. "
            f"It can make useful predictions when future cases look similar to past cases, but it does not understand the real cause like a human expert. "
            f"That is why system design must include monitoring, validation, and fallback when conditions change."
        )

    return (
        f"A stronger answer should directly address the mission, include the expected focus points, and connect the concept to system behavior. "
        f"For this question, cover: {focus_sentence}"
    )


def _why_better(question_type: str) -> str:
    if question_type == "tiny_hands_on":
        return "It separates the observed pattern from the extrapolation risk, which is the actual practical reasoning being tested."
    if question_type == "failure_diagnosis":
        return "It names the failure mechanism instead of only saying the model failed. That is closer to how an ML Architect diagnoses production issues."
    if question_type == "architect_decision":
        return "It moves from broad intent to concrete design controls, which is what architecture interviews and production reviews expect."
    if question_type == "teachback":
        return "It keeps the explanation simple while still preserving the production implication."
    return "It is more specific, connects the concept to model behavior, and avoids vague explanation."


def _architect_upgrade(question_type: str, architect_note: ArchitectNote) -> str:
    if question_type == "architect_decision":
        return "Upgrade the answer by naming the exact controls: drift monitor, out-of-distribution check, fallback policy, alert threshold, retraining trigger, and owner for response."
    if question_type == "failure_diagnosis":
        return "Upgrade the answer by separating data coverage failure, distribution shift, and monitoring failure. Those are different architecture problems."
    if question_type == "tiny_hands_on":
        return "Upgrade the answer by stating the data boundary and what decision you would make before trusting predictions outside that boundary."
    return architect_note.interview_framing or "Upgrade the answer by tying the concept to evaluation, deployment risk, and monitoring decisions."


def generate_answer_coaching(
    concept_note: ConceptNote,
    architect_note: ArchitectNote,
    assessment: Assessment,
    user_answers: List[UserAnswer],
    evaluation: EvaluationResult,
    llm_callable: Callable[[str, str], str] | None = None,
) -> Dict[str, Any]:
    """Generate deterministic per-question coaching.

    V1 deliberately avoids an LLM call here because malformed JSON from the answer-coach
    was blocking learning visibility. The evaluator can still be LLM-backed; coaching must
    always be available.
    """
    answers = _answer_map(user_answers)
    coaching: List[Dict[str, Any]] = []

    for question in assessment.questions:
        answer = answers.get(question.question_id, "")
        quality = _question_quality(question.question_id, answer, evaluation)
        missing = _missing_points(question.expected_focus, answer, question.type)

        coaching.append(
            {
                "question_id": question.question_id,
                "question": question.question,
                "your_answer": answer,
                "answer_quality": quality,
                "what_was_missing": missing,
                "better_answer": _better_answer(
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
        "coaching": coaching,
    }
