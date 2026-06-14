"""
MLOS V2 Learning Design Renderer Helpers

These helpers convert the V2 JSON learning_design shape into simple blocks your
Streamlit app can render. They are intentionally UI-light so they can plug into
an existing app.py without forcing a new layout.
"""
from __future__ import annotations

from typing import Any, Dict, List


def get_concept_steps(learning_design: Dict[str, Any]) -> List[Dict[str, str]]:
    return [
        {"heading": str(step.get("heading", "")), "body": str(step.get("body", ""))}
        for step in learning_design.get("concept_steps", [])
        if isinstance(step, dict)
    ]


def get_mcqs(learning_design: Dict[str, Any]) -> List[Dict[str, Any]]:
    return [q for q in learning_design.get("knowledge_checks", []) if isinstance(q, dict)]


def get_evidence_tasks(learning_design: Dict[str, Any]) -> List[Dict[str, Any]]:
    return [q for q in learning_design.get("evidence_tasks", []) if isinstance(q, dict)]


def render_text_block(title: str, body: str) -> str:
    title = title.strip()
    body = body.strip()
    return f"### {title}

{body}" if title else body


def build_tutor_markdown(learning_design: Dict[str, Any]) -> str:
    """Builds a complete markdown tutor view for the Learn tab."""
    chunks: List[str] = []
    title = str(learning_design.get("title") or "Lesson")
    objective = str(learning_design.get("learning_objective") or "")
    bridge = str(learning_design.get("prerequisite_bridge") or "")

    chunks.append(f"## {title}")
    if objective:
        chunks.append(render_text_block("By the end", objective))
    if bridge:
        chunks.append(render_text_block("Before this concept", bridge))

    for step in get_concept_steps(learning_design):
        chunks.append(render_text_block(step["heading"], step["body"]))

    worked = learning_design.get("worked_example") or {}
    if isinstance(worked, dict) and worked:
        scenario = str(worked.get("scenario") or "")
        takeaway = str(worked.get("takeaway") or "")
        chunks.append(render_text_block("Worked example", f"{scenario}

**Takeaway:** {takeaway}"))

    bar = learning_design.get("answer_quality_bar") or {}
    if isinstance(bar, dict) and bar:
        chunks.append(render_text_block(
            "Answer quality bar",
            "
".join([
                f"**3-star:** {bar.get('three_star', '')}",
                f"**4-star:** {bar.get('four_star', '')}",
                f"**5-star:** {bar.get('five_star', '')}",
            ]),
        ))

    return "

".join([c for c in chunks if c.strip()])
