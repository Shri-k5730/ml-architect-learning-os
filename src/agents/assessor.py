from __future__ import annotations

import json
from typing import Any, Callable, Dict, List

from src.prompts import ASSESSOR_SYSTEM_PROMPT, make_assessor_user_prompt
from src.schemas import ArchitectNote, Assessment, ConceptNote
from src.utils.validator import ValidationError, build_dataclass


class AssessorAgentError(Exception):
    """Raised when assessment generation fails."""


def build_assessor_payload(
    concept_note: ConceptNote,
    architect_note: ArchitectNote,
    learner_profile: Dict[str, Any],
    weak_spots: List[str] | None = None,
) -> Dict[str, Any]:
    return {
        "topic_id": concept_note.topic_id,
        "concept_note": concept_note.to_dict(),
        "architect_note": architect_note.to_dict(),
        "weak_spots": weak_spots or [],
        "assessment_preferences": learner_profile.get("assessment_preferences", {}),
        "target_role": learner_profile.get("target_role", "ML Architect"),
        "priority_contexts": learner_profile.get("priority_contexts", []),
        "learning_goal": learner_profile.get("learning_goal", ""),
    }


def _extract_json(text: str) -> Dict[str, Any]:
    if not text or not text.strip():
        raise AssessorAgentError("Assessor agent returned an empty response.")

    cleaned = text.strip()

    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        if len(lines) >= 3:
            cleaned = "\n".join(lines[1:-1]).strip()

    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise AssessorAgentError(
            f"Assessor agent did not return valid JSON. Error: {exc}"
        ) from exc

    if not isinstance(parsed, dict):
        raise AssessorAgentError("Assessor agent response must be a JSON object.")

    return parsed


def generate_assessment(
    payload: Dict[str, Any],
    llm_callable: Callable[[str, str], str],
) -> Assessment:
    if not callable(llm_callable):
        raise AssessorAgentError(
            "llm_callable must be a callable that accepts system and user prompts."
        )

    user_prompt = make_assessor_user_prompt(payload)
    raw_response = llm_callable(ASSESSOR_SYSTEM_PROMPT, user_prompt)
    parsed = _extract_json(raw_response)

    try:
        return build_dataclass(parsed, Assessment)
    except ValidationError as exc:
        raise AssessorAgentError(
            f"Assessor agent response failed schema validation: {exc}"
        ) from exc


if __name__ == "__main__":
    sample_concept_note = ConceptNote(
        topic_id="mlf_001",
        title="What machine learning is actually learning",
        simple_explanation=(
            "Machine learning finds statistical relationships in data. "
            "It does not understand the world like a person."
        ),
        wrong_mental_model=(
            "The model understands meaning and intent the same way humans do."
        ),
        correct_mental_model=(
            "The model learns patterns from examples and uses them to make predictions."
        ),
        tiny_example=(
            "A house price model uses past house features and prices to predict a new price."
        ),
        why_it_matters=(
            "If the data changes, the model can fail even if it seems confident."
        ),
        edge_case=(
            "A model may do well on training-like data and still break on new production inputs."
        ),
        three_takeaways=[
            "ML learns patterns, not human meaning.",
            "Predictions depend on training data quality.",
            "Confidence does not equal understanding.",
        ],
    )

    sample_architect_note = ArchitectNote(
        topic_id="mlf_001",
        architect_summary=(
            "An ML Architect must remember that models depend on historical data patterns, "
            "so production reliability depends on data quality, drift handling, and monitoring."
        ),
        design_implications=[
            "Define what data the model is allowed to learn from.",
            "Plan for drift and input changes before deployment."
        ],
        common_mistakes=[
            "Assuming a good offline score means the model understands the business problem.",
            "Ignoring how training data limitations shape production behavior."
        ],
        production_risks=[
            "Silent failure when the real-world input distribution shifts.",
            "Overconfidence in predictions that are outside the training pattern."
        ],
        interview_framing=(
            "I would explain that ML systems learn statistical relationships from historical data, "
            "so architecture decisions must control data quality, monitor drift, and validate "
            "generalization before trusting deployment."
        ),
        use_case_mapping=[],
    )

    sample_profile = {
        "target_role": "ML Architect",
        "learning_goal": "Build strong ML foundations and architect-level reasoning.",
        "priority_contexts": ["manufacturing_ai", "predictive_quality"],
        "assessment_preferences": {
            "question_types": ["concept", "scenario", "architect_reasoning", "teachback"],
            "mcq_allowed": False,
            "answer_style": "short_written",
        },
    }

    sample_payload = build_assessor_payload(
        concept_note=sample_concept_note,
        architect_note=sample_architect_note,
        learner_profile=sample_profile,
        weak_spots=["confuses confidence with understanding"],
    )

    print(json.dumps(sample_payload, indent=2))