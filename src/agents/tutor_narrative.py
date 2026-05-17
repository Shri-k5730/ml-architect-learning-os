
from __future__ import annotations

from typing import Any, Dict, List, Optional

from src.blueprints.advanced_ml import get_blueprint


def _as_list(value: Any) -> List[str]:
    if not value:
        return []
    if isinstance(value, list):
        return [str(item) for item in value if str(item or "").strip()]
    return [str(value)]


def get_tutor_narrative(topic_id: str) -> Optional[Dict[str, Any]]:
    """Build a teacher-like narrative from the expert blueprint.

    The blueprint is the source of truth. This renderer turns it into a lesson
    flow that explains before it asks, instead of dumping fields as reference
    text.
    """
    bp = get_blueprint(topic_id)
    if not bp:
        return None

    missions = bp.get("missions", []) or []
    mission_prep = []
    for mission in missions:
        qid = mission.get("question_id", "")
        qtype = str(mission.get("type", "mission")).replace("_", " ").title()
        expected = mission.get("expected_focus", []) or []
        mission_prep.append(
            {
                "title": f"{qid.upper()} . {qtype}",
                "question": mission.get("question", ""),
                "what_it_tests": "; ".join(expected[:4]) if expected else "Apply the mechanism to the scenario.",
                "how_to_answer": _mission_answer_guidance(str(mission.get("type", "")), bp),
            }
        )

    return {
        "topic_id": bp["topic_id"],
        "title": bp["title"],
        "sections": [
            {
                "heading": "Start Here: The Intuition",
                "body": bp.get("plain_intuition", ""),
                "style": "good",
            },
            {
                "heading": "Precise Definition",
                "body": bp.get("definition", ""),
                "style": "normal",
            },
            {
                "heading": "Why This Concept Exists",
                "body": bp.get("why_it_exists", ""),
                "style": "normal",
            },
            {
                "heading": "Slow Walkthrough: What Actually Changes",
                "body": bp.get("core_mechanism", ""),
                "style": "good",
            },
            {
                "heading": "Worked Example, Step by Step",
                "body": bp.get("worked_example", ""),
                "style": "normal",
            },
            {
                "heading": "Where This Matters Most",
                "body": bp.get("when_matters", ""),
                "style": "normal",
            },
            {
                "heading": "Where This Matters Less",
                "body": bp.get("when_less", ""),
                "style": "normal",
            },
            {
                "heading": "Nuances You Should Not Miss",
                "body": _as_list(bp.get("nuances", [])),
                "style": "good",
            },
            {
                "heading": "Common Traps",
                "body": _as_list(bp.get("common_confusions", [])),
                "style": "risk",
            },
            {
                "heading": "Architect Translation",
                "body": _as_list(bp.get("architect_implications", [])),
                "style": "good",
            },
            {
                "heading": "System Design Controls",
                "body": _as_list(bp.get("system_design_controls", [])),
                "style": "normal",
            },
            {
                "heading": "Mission Answer Frame",
                "body": _as_list(bp.get("mission_answer_frame", [])),
                "style": "normal",
            },
            {
                "heading": "Do Not Waste Words On This",
                "body": _as_list(bp.get("do_not_waste_words", [])),
                "style": "risk",
            },
        ],
        "mission_prep": mission_prep,
    }


def _mission_answer_guidance(question_type: str, bp: Dict[str, Any]) -> str:
    if question_type == "concept_check":
        return "Use one precise definition, one mechanism, and one consequence. Do not write a history lesson."
    if question_type == "tiny_hands_on":
        return "Use the numbers or scenario first, then interpret. Do not hide behind theory."
    if question_type == "failure_diagnosis":
        return "Write symptom → mechanism → evidence → prevention. Avoid generic 'model failed in production' wording."
    if question_type == "architect_decision":
        controls = ", ".join((bp.get("system_design_controls") or [])[:4])
        return f"Name the controls and ownership. Useful controls here include: {controls}."
    if question_type == "teachback":
        return "Explain simply, use one business example, and finish with the practical control."
    return "Use definition, example, failure mode, and control."
