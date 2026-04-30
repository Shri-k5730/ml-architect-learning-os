from __future__ import annotations

import json
from typing import Any, Callable, Dict, List, Tuple

from src.agents.teacher import generate_concept_note
from src.schemas import ConceptNote
from src.utils.quality_gate import check_teacher_note_quality
from src.utils.validator import build_dataclass


REVIEW_SYSTEM_PROMPT = """
You are a strict reviewer for a private Machine Learning Architect learning pipeline.

Your job is to evaluate a generated teaching note and reject it if it is generic, vague, blog-like, or weakly connected to ML system behavior.

Critical rules:
1. Do not infer strengths that are not explicitly present in the note.
2. Every strength and every problem must be supported by short quoted evidence from the note.
3. If the note does not clearly contain a strength, do not invent one.
4. Focus on whether the note is useful for a learner becoming an ML Architect.

Reject notes that:
- use vague filler
- sound like public beginner content
- fail to connect to evaluation, monitoring, deployment, drift, production, or system design
- use shallow examples
- describe edge cases without a concrete failure mode

Return strict JSON only.

Output schema:
{
  "decision": "pass|revise",
  "scores": {
    "sharpness": 1,
    "concreteness": 1,
    "architect_relevance": 1,
    "clarity": 1
  },
  "strengths": [
    {
      "point": "string",
      "evidence": "string"
    }
  ],
  "problems": [
    {
      "point": "string",
      "evidence": "string"
    }
  ],
  "rewrite_instructions": ["string", "string", "string"],
  "one_line_verdict": "string"
}
""".strip()


REVISION_SYSTEM_PROMPT = """
You are a strict reviser for a private Machine Learning Architect learning pipeline.

Your task is to rewrite a teaching note using reviewer feedback and deterministic quality gate failures.

Hard rules:
1. Preserve the original topic_id and title.
2. Keep the note compact and sharp.
3. Use simple words, but do not sound childish or blog-like.
4. Remove vague filler completely.
5. Make "why_it_matters" concrete for evaluation, monitoring, deployment, design, drift, or production.
6. Make "edge_case" one precise failure mode, not a mixed blob.
7. If the quality gate says edge_case is weak, rewrite edge_case so it explicitly contains a system or failure anchor such as:
   - production
   - deployment
   - drift
   - unseen inputs
   - distribution shift
   - failure
   - break
8. You MUST fix every exact failure listed in the quality gate result.
9. Do not replace one vague phrase with another vague phrase.
10. Keep exactly the same JSON schema.
11. Return strict JSON only.

Writing standard:
- private tutor note
- ML Architect trajectory
- concrete downstream implication
- one precise example
- one precise failure mode
- no stock filler
- no abstract wording that sounds intelligent but says little
""".strip()


class TeacherQualityError(Exception):
    """Raised when teacher note quality is unacceptable."""

    def __init__(self, message: str, diagnostics: Dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.diagnostics = diagnostics or {}


def extract_json_text(raw: str) -> Dict[str, Any]:
    if not raw or not raw.strip():
        raise TeacherQualityError("Model returned an empty response.")

    cleaned = raw.strip()

    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        if len(lines) >= 3:
            cleaned = "\n".join(lines[1:-1]).strip()

    start = cleaned.find("{")
    end = cleaned.rfind("}")

    if start == -1 or end == -1 or end <= start:
        raise TeacherQualityError(f"Could not find a JSON object in model output:\n{raw}")

    return json.loads(cleaned[start:end + 1])


def review_teacher_note(
    note: Dict[str, Any],
    llm_callable: Callable[[str, str], str],
) -> Dict[str, Any]:
    user_prompt = f"""
Review this teacher note for quality.

Target:
- private tutor note
- learner is becoming an ML Architect
- simple words
- sharp thinking
- concrete downstream consequences
- no blog-style filler

Teacher note:
{json.dumps(note, indent=2)}
""".strip()

    raw = llm_callable(REVIEW_SYSTEM_PROMPT, user_prompt)
    return extract_json_text(raw)


def revise_teacher_note(
    note: Dict[str, Any],
    review: Dict[str, Any],
    quality_gate_result: Dict[str, Any],
    llm_callable: Callable[[str, str], str],
    revision_round: int,
) -> Dict[str, Any]:
    quality_problems = quality_gate_result.get("problems", [])
    review_problems = review.get("problems", [])
    rewrite_instructions = review.get("rewrite_instructions", [])

    user_prompt = f"""
Rewrite this teacher note.

Revision round: {revision_round}

You must fix these exact deterministic quality failures:
{json.dumps(quality_problems, indent=2)}

You must also address these reviewer problems:
{json.dumps(review_problems, indent=2)}

You must follow these rewrite instructions:
{json.dumps(rewrite_instructions, indent=2)}

Current teacher note:
{json.dumps(note, indent=2)}
""".strip()

    raw = llm_callable(REVISION_SYSTEM_PROMPT, user_prompt)
    return extract_json_text(raw)


def evaluate_teacher_note(
    note: Dict[str, Any],
    llm_callable: Callable[[str, str], str],
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    review = review_teacher_note(note, llm_callable)
    quality_gate = check_teacher_note_quality(note)
    return review, quality_gate


def _accepted(review: Dict[str, Any], quality_gate: Dict[str, Any]) -> bool:
    return review.get("decision") == "pass" and quality_gate.get("decision") == "pass"


def generate_teacher_note_with_quality_loop(
    payload: Dict[str, Any],
    llm_callable: Callable[[str, str], str],
    max_revision_rounds: int = 3,
) -> Tuple[ConceptNote, Dict[str, Any]]:
    current_note = generate_concept_note(payload, llm_callable).to_dict()
    attempt_history: List[Dict[str, Any]] = []

    review, quality_gate = evaluate_teacher_note(current_note, llm_callable)
    attempt_history.append(
        {
            "round": 0,
            "note": current_note,
            "review": review,
            "quality_gate": quality_gate,
        }
    )

    if _accepted(review, quality_gate):
        final_note = build_dataclass(current_note, ConceptNote)
        diagnostics = {
            "status": "accepted_initial",
            "attempt_history": attempt_history,
            "review": review,
            "initial_quality_gate": quality_gate,
            "revised_quality_gate": None,
        }
        return final_note, diagnostics

    for revision_round in range(1, max_revision_rounds + 1):
        current_note = revise_teacher_note(
            note=current_note,
            review=review,
            quality_gate_result=quality_gate,
            llm_callable=llm_callable,
            revision_round=revision_round,
        )

        review, quality_gate = evaluate_teacher_note(current_note, llm_callable)
        attempt_history.append(
            {
                "round": revision_round,
                "note": current_note,
                "review": review,
                "quality_gate": quality_gate,
            }
        )

        if _accepted(review, quality_gate):
            final_note = build_dataclass(current_note, ConceptNote)
            diagnostics = {
                "status": "accepted_after_revision",
                "attempt_history": attempt_history,
                "review": review,
                "initial_quality_gate": attempt_history[0]["quality_gate"],
                "revised_quality_gate": quality_gate,
            }
            return final_note, diagnostics

    raise TeacherQualityError(
        "Teacher note failed quality gate after maximum revision rounds.",
        diagnostics={
            "status": "failed_after_max_revisions",
            "attempt_history": attempt_history,
            "final_review": review,
            "final_quality_gate": quality_gate,
        },
    )