from __future__ import annotations

import json
from typing import Any, Callable, Dict, List, Optional

from src.prompts import TEACHER_SYSTEM_PROMPT, make_teacher_user_prompt
from src.schemas import ConceptNote, Topic
from src.utils.validator import ValidationError, build_dataclass


class TeacherAgentError(Exception):
    """Raised when concept note generation fails."""


def build_teacher_payload(
    selected_topic: Topic,
    learner_profile: Dict[str, Any],
    weak_spots: Optional[List[str]] = None,
) -> Dict[str, Any]:
        return {
        "selected_topic": {
            "topic_id": selected_topic.topic_id,
            "title": selected_topic.title,
            "domain": selected_topic.domain,
            "difficulty": selected_topic.difficulty,
            "prerequisites": selected_topic.prerequisites,
            "architect_relevance": selected_topic.architect_relevance,
            "tags": selected_topic.tags,
        },
        "prerequisites": selected_topic.prerequisites,
        "weak_spots": weak_spots or [],
        "target_level": learner_profile.get("explanation_preferences", {}).get(
            "style", "simple_precise"
        ),
        "learning_goal": learner_profile.get("learning_goal", ""),
        "target_role": learner_profile.get("target_role", "ML Architect"),
        "priority_contexts": learner_profile.get("priority_contexts", []),
        "known_gaps": learner_profile.get("known_gaps", []),
        "teaching_goal": (
            "Teach this concept so the learner can explain it clearly in an ML Architect interview, "
            "connect it to ML system behavior, and avoid generic textbook wording."
        ),
        "must_emphasize": [
            "what the model is actually learning",
            "why the wrong mental model causes bad system decisions",
            "one concrete implication for evaluation, monitoring, or deployment"
        ],
        "forbidden_patterns": [
            "cats vs dogs examples",
            "generic blog-style explanations",
            "vague warnings like costly mistakes",
            "broad claims about real-world settings without a concrete consequence",
            "empty statements like data quality is important"
        ]
    }


def _extract_json(text: str) -> Dict[str, Any]:
    if not text or not text.strip():
        raise TeacherAgentError("Teacher agent returned an empty response.")

    cleaned = text.strip()

    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        if len(lines) >= 3:
            cleaned = "\n".join(lines[1:-1]).strip()

    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise TeacherAgentError(f"Teacher agent did not return valid JSON. Error: {exc}") from exc

    if not isinstance(parsed, dict):
        raise TeacherAgentError("Teacher agent response must be a JSON object.")

    return parsed


def generate_concept_note(
    payload: Dict[str, Any],
    llm_callable: Callable[[str, str], str],
) -> ConceptNote:
    if not callable(llm_callable):
        raise TeacherAgentError("llm_callable must be a callable that accepts system and user prompts.")

    user_prompt = make_teacher_user_prompt(payload)
    raw_response = llm_callable(TEACHER_SYSTEM_PROMPT, user_prompt)
    parsed = _extract_json(raw_response)

    try:
        return build_dataclass(parsed, ConceptNote)
    except ValidationError as exc:
        raise TeacherAgentError(f"Teacher agent response failed schema validation: {exc}") from exc


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

    sample_profile = {
        "target_role": "ML Architect",
        "learning_goal": "Build strong ML foundations and architect-level reasoning.",
        "priority_contexts": ["manufacturing_ai", "predictive_quality"],
        "known_gaps": ["deep_ml_foundations"],
        "explanation_preferences": {"style": "simple_precise"},
    }

    sample_payload = build_teacher_payload(
        selected_topic=sample_topic,
        learner_profile=sample_profile,
        weak_spots=["confuses learning with understanding"],
    )

    print(json.dumps(sample_payload, indent=2))