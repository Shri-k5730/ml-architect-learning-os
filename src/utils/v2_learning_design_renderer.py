"""MLOS V2.1 Learning Design Renderer Helpers."""
from __future__ import annotations

from typing import Any, Dict, List


def get_concept_steps(learning_design: Dict[str, Any]) -> List[Dict[str, str]]:
    return [
        {"heading": str(step.get("heading", "")).strip(), "body": str(step.get("body", "")).strip()}
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
    if not title:
        return body
    return f"### {title}\n\n{body}"


def build_tutor_markdown(learning_design: Dict[str, Any]) -> str:
    chunks: List[str] = []
    title = str(learning_design.get("title") or "Lesson").strip()
    objective = str(learning_design.get("learning_objective") or "").strip()
    bridge = str(learning_design.get("prerequisite_bridge") or "").strip()

    chunks.append(f"## {title}")
    if objective:
        chunks.append(render_text_block("By the end", objective))
    if bridge:
        chunks.append(render_text_block("Before this concept", bridge))

    for step in get_concept_steps(learning_design):
        chunks.append(render_text_block(step["heading"], step["body"]))

    worked_examples = learning_design.get("worked_examples") or []
    if worked_examples:
        for item in worked_examples:
            if not isinstance(item, dict):
                continue
            label = str(item.get("label") or "Worked example")
            scenario = str(item.get("scenario") or "")
            reasoning = str(item.get("reasoning") or "")
            chunks.append(render_text_block(label, f"{scenario}\n\n**Reasoning:** {reasoning}"))
    else:
        worked = learning_design.get("worked_example") or {}
        if isinstance(worked, dict) and worked:
            scenario = str(worked.get("scenario") or "")
            takeaway = str(worked.get("takeaway") or "")
            chunks.append(render_text_block("Worked example", f"{scenario}\n\n**Takeaway:** {takeaway}"))

    quality = learning_design.get("answer_quality_bar") or {}
    if isinstance(quality, dict) and quality:
        body = "\n".join([
            f"**3-star:** {quality.get('three_star', '')}",
            f"**4-star:** {quality.get('four_star', '')}",
            f"**5-star:** {quality.get('five_star', '')}",
        ])
        chunks.append(render_text_block("Answer quality bar", body))

    return "\n\n".join([c for c in chunks if c.strip()])
