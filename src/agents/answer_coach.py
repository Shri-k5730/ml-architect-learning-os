from __future__ import annotations

import json
from typing import Any, Callable, Dict, List

from src.schemas import (
    ArchitectNote,
    Assessment,
    ConceptNote,
    EvaluationResult,
    UserAnswer,
)


ANSWER_COACH_SYSTEM_PROMPT = """
You are an Answer Coach in a private ML Architect learning system.

Your job is to help the learner improve after evaluation.

For each question:
1. Read the question.
2. Read the learner's answer.
3. Identify what was missing.
4. Write a better answer in clear, direct language.
5. Explain why the better answer is stronger.
6. Add one ML Architect-level upgrade.

Do not flatter.
Do not be vague.
Do not write long essays.
Do not repeat generic theory.
Make the better answer interview-ready and system-relevant.

Output strict JSON only.

Output schema:
{
  "topic_id": "string",
  "coaching": [
    {
      "question_id": "string",
      "question": "string",
      "your_answer": "string",
      "answer_quality": "strong|partial|weak",
      "what_was_missing": ["string", "string"],
      "better_answer": "string",
      "why_this_is_better": "string",
      "architect_upgrade": "string"
    }
  ]
}
""".strip()


class AnswerCoachError(Exception):
    """Raised when answer coaching generation fails."""


def extract_json_text(raw: str) -> Dict[str, Any]:
    if not raw or not raw.strip():
        raise AnswerCoachError("Answer coach returned an empty response.")

    cleaned = raw.strip()

    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        if len(lines) >= 3:
            cleaned = "\n".join(lines[1:-1]).strip()

    start = cleaned.find("{")
    end = cleaned.rfind("}")

    if start == -1 or end == -1 or end <= start:
        raise AnswerCoachError(f"Could not find JSON object in answer coach output:\n{raw}")

    parsed = json.loads(cleaned[start:end + 1])

    if not isinstance(parsed, dict):
        raise AnswerCoachError("Answer coach response must be a JSON object.")

    return parsed


def generate_answer_coaching(
    concept_note: ConceptNote,
    architect_note: ArchitectNote,
    assessment: Assessment,
    user_answers: List[UserAnswer],
    evaluation: EvaluationResult,
    llm_callable: Callable[[str, str], str],
) -> Dict[str, Any]:
    answer_map = {answer.question_id: answer.answer for answer in user_answers}

    payload = {
        "topic_id": concept_note.topic_id,
        "concept_note": concept_note.to_dict(),
        "architect_note": architect_note.to_dict(),
        "assessment": assessment.to_dict(),
        "user_answers": [answer.to_dict() for answer in user_answers],
        "evaluation": evaluation.to_dict(),
        "instruction": (
            "For every assessment question, provide a better answer that the learner "
            "can study and reuse as an interview-quality response."
        ),
    }

    raw = llm_callable(
        ANSWER_COACH_SYSTEM_PROMPT,
        json.dumps(payload, indent=2),
    )
    parsed = extract_json_text(raw)

    if parsed.get("topic_id") != concept_note.topic_id:
        parsed["topic_id"] = concept_note.topic_id

    coaching = parsed.get("coaching", [])
    if not isinstance(coaching, list):
        raise AnswerCoachError("Answer coach response must contain a coaching list.")

    for item in coaching:
        qid = item.get("question_id")
        if qid in answer_map:
            item["your_answer"] = answer_map[qid]

    return parsed