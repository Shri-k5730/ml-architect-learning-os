from __future__ import annotations

import json
from typing import Any, Callable, Dict, List

from src.prompts import (
    EVALUATOR_REFINER_SYSTEM_PROMPT,
    make_evaluator_refiner_user_prompt,
)
from src.schemas import (
    ArchitectNote,
    Assessment,
    ConceptNote,
    EvaluationResult,
    UserAnswer,
)
from src.utils.validator import ValidationError, build_dataclass
from src.blueprints.advanced_ml import blueprint_context
from src.blueprints.learning_design import runtime_task_for_question
from src.utils.learning_design_registry import resolve_learning_design
from src.agents.writing_assist import analyze_answer_text


class EvaluatorRefinerAgentError(Exception):
    """Raised when evaluation or refinement fails."""


def build_evaluator_refiner_payload(
    concept_note: ConceptNote,
    architect_note: ArchitectNote,
    assessment: Assessment,
    user_answers: List[UserAnswer],
    scoring_rubric: Dict[str, Any],
    learner_profile: Dict[str, Any],
    practice_exercise: Dict[str, Any] | None = None,
    practice_submission: Dict[str, Any] | None = None,
    practice_result: Dict[str, Any] | None = None,
    mcq_result: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    payload = {
        "topic_id": concept_note.topic_id,
        "concept_note": concept_note.to_dict(),
        "architect_note": architect_note.to_dict(),
        "assessment": assessment.to_dict(),
        "user_answers": [answer.to_dict() for answer in user_answers],
        "language_precision_audit": [
            {
                "question_id": answer.question_id,
                "writing_assist": analyze_answer_text(answer.answer),
            }
            for answer in user_answers
        ],
        "language_policy": {
            "typos_are_language_noise": True,
            "typos_must_not_be_called_terminology_confusion": True,
            "typos_must_not_reduce_content_scores_when_meaning_is_clear": True,
            "wrong_technical_terms_are_content_issues": [
                "feature_vs_parameter_vs_hyperparameter",
                "precision_vs_recall",
                "normalization_vs_standardization",
                "score_vs_threshold_decision",
            ],
        },
        "scoring_rubric": scoring_rubric,
        "target_role": learner_profile.get("target_role", "ML Architect"),
        "learning_goal": learner_profile.get("learning_goal", ""),
        "priority_contexts": learner_profile.get("priority_contexts", []),
    }
    learning_design = resolve_learning_design(concept_note.topic_id)
    if learning_design:
        runtime_design = dict(learning_design)
        runtime_design["evidence_tasks"] = [
            runtime_task_for_question(learning_design, question.question_id, question.question) or {
                "question_id": question.question_id, "type": question.type, "question": question.question,
                "purpose": "Demonstrate reasoning for the published task.", "response_shape": "Answer the exact question directly.",
                "expected_focus": question.expected_focus,
            }
            for question in assessment.questions
        ]
        payload["topic_learning_design"] = runtime_design
        payload["evaluation_instruction"] = (
            "Evaluate each response against the corresponding published evidence task in topic_learning_design. "
            "Score demonstrated reasoning and technically valid conclusions, not preferred terms, keyword presence, or essay length. "
            "Do not demand a generic production-risk/control structure when the task asks for calculation, comparison, diagnosis, or plain-language explanation. "
            "Do not introduce any criterion absent from the lesson or task. Penalize genuinely false or unsafe technical claims. "
            "Normal lessons intentionally use focused evidence tasks; checkpoints and capstone are deeper gates."
        )
    else:
        blueprint = blueprint_context(concept_note.topic_id)
        if blueprint:
            payload["expert_tutor_blueprint"] = blueprint
            payload["evaluation_instruction"] = (
                "Evaluate against expert_tutor_blueprint and its visible teaching_contract. Penalize technically unsafe claims even when phrased confidently. "
                "Do not penalize a learner for controls, calculations, metrics, or workflow detail that the teaching_contract and mission did not require. "
                "For scenario-only tiny_hands_on questions with no numeric inputs, judge valid conclusion, invalid conclusion, evidence check, and safe action; do not invent a numeric-comparison requirement. "
                "For architect_decision questions, require trigger/evidence/owner/approval/action/monitoring only when that chain is shown in the teaching_contract before submission."
            )
    if practice_exercise is not None:
        payload["practice_exercise"] = practice_exercise
    if practice_submission is not None:
        payload["practice_submission"] = practice_submission
    if practice_result is not None:
        payload["practice_result"] = practice_result
    if mcq_result is not None:
        payload["mcq_result"] = mcq_result
        payload["evaluation_instruction"] = (
            payload.get("evaluation_instruction", "")
            + " V3 assessment contract: normal lessons are MCQ-first. The MCQ result tests breadth; "
              "the written response tests concise reasoning. Do not expect five essays in normal lessons. "
              "Do not penalize the learner for omitting separate essay responses that V3 deliberately removed."
        ).strip()
    return payload


def _extract_json(text: str) -> Dict[str, Any]:
    if not text or not text.strip():
        raise EvaluatorRefinerAgentError("Evaluator Refiner agent returned an empty response.")

    cleaned = text.strip()

    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        if len(lines) >= 3:
            cleaned = "\n".join(lines[1:-1]).strip()

    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise EvaluatorRefinerAgentError(
            f"Evaluator Refiner agent did not return valid JSON. Error: {exc}"
        ) from exc

    if not isinstance(parsed, dict):
        raise EvaluatorRefinerAgentError(
            "Evaluator Refiner agent response must be a JSON object."
        )

    return parsed


def evaluate_and_refine(
    payload: Dict[str, Any],
    llm_callable: Callable[[str, str], str],
) -> EvaluationResult:
    if not callable(llm_callable):
        raise EvaluatorRefinerAgentError(
            "llm_callable must be a callable that accepts system and user prompts."
        )

    user_prompt = make_evaluator_refiner_user_prompt(payload)
    raw_response = llm_callable(EVALUATOR_REFINER_SYSTEM_PROMPT, user_prompt)
    parsed = _extract_json(raw_response)

    try:
        return build_dataclass(parsed, EvaluationResult)
    except ValidationError as exc:
        raise EvaluatorRefinerAgentError(
            f"Evaluator Refiner agent response failed schema validation: {exc}"
        ) from exc


if __name__ == "__main__":
    sample_concept_note = ConceptNote(
        topic_id="mlf_001",
        title="What machine learning is actually learning",
        simple_explanation=(
            "Machine learning finds statistical relationships in data and uses them "
            "to make predictions."
        ),
        wrong_mental_model=(
            "The model understands the world like a person understands it."
        ),
        correct_mental_model=(
            "The model learns patterns from historical examples, not human meaning."
        ),
        tiny_example=(
            "A house price model learns relationships between features like size and "
            "past sale prices."
        ),
        why_it_matters=(
            "If the input data changes, the model can fail even if it sounds confident."
        ),
        edge_case=(
            "A model can look strong in evaluation but fail in production when data shifts."
        ),
        three_takeaways=[
            "ML learns patterns, not meaning.",
            "Model behavior depends on training data.",
            "Confidence is not understanding.",
        ],
    )

    sample_architect_note = ArchitectNote(
        topic_id="mlf_001",
        architect_summary=(
            "An ML Architect must design around data dependence, generalization limits, "
            "and production monitoring."
        ),
        design_implications=[
            "Control the quality and boundaries of training data.",
            "Monitor drift and production behavior after deployment.",
        ],
        common_mistakes=[
            "Assuming good offline performance means real understanding.",
            "Ignoring how distribution changes break production behavior.",
        ],
        production_risks=[
            "Silent degradation after deployment.",
            "Overconfident outputs on unfamiliar inputs.",
        ],
        interview_framing=(
            "I would explain that models learn statistical relationships from past data, "
            "so architecture decisions must focus on data quality, generalization, and monitoring."
        ),
        use_case_mapping=[],
    )

    sample_assessment = Assessment(
        topic_id="mlf_001",
        questions=[]
    )

    sample_user_answers = [
        UserAnswer(
            question_id="q1",
            answer=(
                "Machine learning learns patterns from past data. "
                "It does not actually understand meaning like a person."
            ),
        )
    ]

    sample_rubric = {
        "dimensions": {
            "conceptual_clarity": {"min": 1, "max": 5},
            "practical_reasoning": {"min": 1, "max": 5},
            "architect_reasoning": {"min": 1, "max": 5},
            "communication": {"min": 1, "max": 5},
        }
    }

    sample_profile = {
        "target_role": "ML Architect",
        "learning_goal": "Build strong ML foundations and architect-level reasoning.",
        "priority_contexts": ["manufacturing_ai", "predictive_quality"],
    }

    sample_payload = build_evaluator_refiner_payload(
        concept_note=sample_concept_note,
        architect_note=sample_architect_note,
        assessment=sample_assessment,
        user_answers=sample_user_answers,
        scoring_rubric=sample_rubric,
        learner_profile=sample_profile,
    )

    print(json.dumps(sample_payload, indent=2))