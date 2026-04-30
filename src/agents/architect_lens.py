from __future__ import annotations

import json
from typing import Any, Callable, Dict, List

from src.prompts import ARCHITECT_LENS_SYSTEM_PROMPT, make_architect_lens_user_prompt
from src.schemas import ArchitectNote, ConceptNote, Topic
from src.utils.validator import ValidationError, build_dataclass


class ArchitectLensAgentError(Exception):
    """Raised when architect lens generation fails."""


def build_architect_lens_payload(
    selected_topic: Topic,
    concept_note: ConceptNote,
    learner_profile: Dict[str, Any],
) -> Dict[str, Any]:
    return {
        "topic_id": selected_topic.topic_id,
        "title": selected_topic.title,
        "domain": selected_topic.domain,
        "concept_note": concept_note.to_dict(),
        "target_role": learner_profile.get("target_role", "ML Architect"),
        "priority_contexts": learner_profile.get("priority_contexts", []),
        "focus_areas": learner_profile.get("focus_areas", []),
        "known_gaps": learner_profile.get("known_gaps", []),
        "learning_goal": learner_profile.get("learning_goal", ""),
    }


def _extract_json(text: str) -> Dict[str, Any]:
    if not text or not text.strip():
        raise ArchitectLensAgentError("Architect Lens agent returned an empty response.")

    cleaned = text.strip()

    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        if len(lines) >= 3:
            cleaned = "\n".join(lines[1:-1]).strip()

    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise ArchitectLensAgentError(
            f"Architect Lens agent did not return valid JSON. Error: {exc}"
        ) from exc

    if not isinstance(parsed, dict):
        raise ArchitectLensAgentError("Architect Lens agent response must be a JSON object.")

    return parsed


def generate_architect_note(
    payload: Dict[str, Any],
    llm_callable: Callable[[str, str], str],
) -> ArchitectNote:
    if not callable(llm_callable):
        raise ArchitectLensAgentError(
            "llm_callable must be a callable that accepts system and user prompts."
        )

    user_prompt = make_architect_lens_user_prompt(payload)
    raw_response = llm_callable(ARCHITECT_LENS_SYSTEM_PROMPT, user_prompt)
    parsed = _extract_json(raw_response)

    try:
        return build_dataclass(parsed, ArchitectNote)
    except ValidationError as exc:
        raise ArchitectLensAgentError(
            f"Architect Lens agent response failed schema validation: {exc}"
        ) from exc


if __name__ == "__main__":
    sample_topic = Topic(
        topic_id="mlf_001",
        title="What machine learning is actually learning",
        domain="machine_learning_fundamentals",
        difficulty=1,
        prerequisites=[],
        architect_relevance=["generalization", "data_dependency", "model_risk"],
        tags=["learning", "patterns", "prediction", "generalization"],
    )

    sample_concept_note = ConceptNote(
        topic_id="mlf_001",
        title="What machine learning is actually learning",
        simple_explanation=(
            "Machine learning does not understand the world like a person. "
            "It finds statistical relationships between inputs and outcomes."
        ),
        wrong_mental_model=(
            "The model understands meaning the same way a human does."
        ),
        correct_mental_model=(
            "The model learns patterns from past data and uses them to make predictions."
        ),
        tiny_example=(
            "A house price model does not understand houses. "
            "It learns which combinations of numbers often matched certain prices."
        ),
        why_it_matters=(
            "If the data changes, the model can fail even when it sounds confident."
        ),
        edge_case=(
            "A model can perform well in training and still fail in production if the input distribution changes."
        ),
        three_takeaways=[
            "ML learns patterns, not human meaning.",
            "Predictions depend on past data quality.",
            "Confidence is not the same as understanding.",
        ],
    )

    sample_profile = {
        "target_role": "ML Architect",
        "learning_goal": "Build strong ML foundations and architect-level reasoning.",
        "priority_contexts": ["manufacturing_ai", "predictive_quality"],
        "focus_areas": ["machine_learning_fundamentals", "system_design"],
        "known_gaps": ["deep_ml_foundations"],
    }

    sample_payload = build_architect_lens_payload(
        selected_topic=sample_topic,
        concept_note=sample_concept_note,
        learner_profile=sample_profile,
    )

    print(json.dumps(sample_payload, indent=2))