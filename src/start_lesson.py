from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from src.agents.architect_lens import (
    build_architect_lens_payload,
    generate_architect_note,
)
from src.agents.assessor import build_assessor_payload, generate_assessment
from src.agents.teacher import build_teacher_payload
from src.agents.teacher_quality import generate_teacher_note_with_quality_loop
from src.agents.topic_selector import select_topic
from src.schemas import RunArtifacts, RunScores, RunState, Topic
from src.utils.llm_client import build_llm_callable
from src.utils.repo_writer import append_jsonl, write_json, write_markdown


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONFIG_DIR = PROJECT_ROOT / "config"
TOPICS_DIR = PROJECT_ROOT / "topics"
RUNS_DIR = PROJECT_ROOT / "runs"


class StartLessonError(Exception):
    """Raised when lesson generation fails."""


def load_yaml(file_path: Path) -> Dict[str, Any]:
    if not file_path.exists():
        raise StartLessonError(f"YAML file not found: {file_path}")

    with file_path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    if not isinstance(data, dict):
        raise StartLessonError(f"Expected top-level object in YAML: {file_path}")

    return data


def load_json(file_path: Path) -> Any:
    if not file_path.exists():
        raise StartLessonError(f"JSON file not found: {file_path}")

    with file_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_topic_catalog() -> List[Topic]:
    data = load_json(TOPICS_DIR / "topic_catalog.json")
    if not isinstance(data, list):
        raise StartLessonError("topic_catalog.json must contain a list.")
    return [Topic(**item) for item in data]


def get_topic_by_id(topic_catalog: List[Topic], topic_id: str) -> Topic:
    for topic in topic_catalog:
        if topic.topic_id == topic_id:
            return topic
    raise StartLessonError(f"Topic not found: {topic_id}")


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def generate_run_id(topic_id: str) -> str:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    return f"{timestamp}_{topic_id}"


def write_log(run_id: str, message: str) -> None:
    log_path = PROJECT_ROOT / "runs" / run_id / "logs.txt"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as f:
        f.write(f"[{utc_now_iso()}] {message}\n")


def concept_note_to_markdown(concept_note) -> str:
    return f"""---
topic_id: {concept_note.topic_id}
title: {concept_note.title}
---

# Simple Explanation

{concept_note.simple_explanation}

# Wrong Mental Model

{concept_note.wrong_mental_model}

# Correct Mental Model

{concept_note.correct_mental_model}

# Tiny Example

{concept_note.tiny_example}

# Why It Matters

{concept_note.why_it_matters}

# Edge Case

{concept_note.edge_case}

# Three Takeaways

- {concept_note.three_takeaways[0]}
- {concept_note.three_takeaways[1]}
- {concept_note.three_takeaways[2]}
"""


def architect_note_to_markdown(architect_note) -> str:
    use_case_lines = []
    for item in architect_note.use_case_mapping:
        use_case_lines.append(f"- **{item.context}**: {item.relevance}")

    return f"""---
topic_id: {architect_note.topic_id}
---

# Architect Summary

{architect_note.architect_summary}

# Design Implications

- {architect_note.design_implications[0]}
- {architect_note.design_implications[1]}

# Common Mistakes

- {architect_note.common_mistakes[0]}
- {architect_note.common_mistakes[1]}

# Production Risks

- {architect_note.production_risks[0]}
- {architect_note.production_risks[1]}

# Interview Framing

{architect_note.interview_framing}

# Use Case Mapping

{chr(10).join(use_case_lines) if use_case_lines else "- None"}
"""


def assessment_to_markdown(assessment) -> str:
    lines = [
        "---",
        f"topic_id: {assessment.topic_id}",
        "---",
        "",
        "# Assessment Questions",
        "",
    ]

    for q in assessment.questions:
        lines.append(f"## {q.question_id} [{q.type}]")
        lines.append("")
        lines.append(q.question)
        lines.append("")
        lines.append("Expected focus:")
        for item in q.expected_focus:
            lines.append(f"- {item}")
        lines.append("")

    return "\n".join(lines).strip() + "\n"


def answer_template_to_markdown(assessment) -> str:
    lines = [
        "---",
        f"topic_id: {assessment.topic_id}",
        "status: pending_user_answers",
        "---",
        "",
        "# Your Answers",
        "",
        "Write your answers below each question.",
        "",
    ]

    for q in assessment.questions:
        lines.append(f"## {q.question_id} [{q.type}]")
        lines.append("")
        lines.append(f"Question: {q.question}")
        lines.append("")
        lines.append("Answer:")
        lines.append("")
        lines.append("[Write your answer here]")
        lines.append("")

    return "\n".join(lines).strip() + "\n"


def answer_template_to_json(assessment) -> dict:
    return {
        "topic_id": assessment.topic_id,
        "status": "pending_user_answers",
        "answers": [
            {
                "question_id": q.question_id,
                "type": q.type,
                "question": q.question,
                "answer": "",
            }
            for q in assessment.questions
        ],
    }


def resolve_requested_topic_id() -> Optional[str]:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--topic_id", type=str, default=None)
    args, _ = parser.parse_known_args()

    return (
        args.topic_id
        or os.getenv("ML_OS_TOPIC_ID")
        or os.getenv("LEARNING_OS_TOPIC_ID")
    )


def find_active_awaiting_run() -> Optional[Path]:
    if not RUNS_DIR.exists():
        return None

    candidates: List[Path] = []
    for run_dir in RUNS_DIR.iterdir():
        if not run_dir.is_dir():
            continue

        state_path = run_dir / "run_state.json"
        if not state_path.exists():
            continue

        try:
            state = load_json(state_path)
        except Exception:
            continue

        if (
            state.get("phase") == "awaiting_user_answers"
            and state.get("next_action") == "await_user_answers"
        ):
            candidates.append(run_dir)

    if not candidates:
        return None

    return sorted(candidates)[-1]


def main() -> None:
    active_run = find_active_awaiting_run()
    if active_run is not None:
        active_state = load_json(active_run / "run_state.json")
        raise StartLessonError(
            f"Active lesson already exists: {active_state['run_id']} ({active_state['topic_id']}). "
            f"Finish active lesson first."
        )

    learner_profile = load_yaml(CONFIG_DIR / "learner_profile.yaml")
    topic_catalog = load_topic_catalog()

    requested_topic_id = resolve_requested_topic_id()
    selected = select_topic(requested_topic_id=requested_topic_id)
    topic = get_topic_by_id(topic_catalog, selected.selected_topic_id)
    run_id = generate_run_id(topic.topic_id)

    run_state = RunState(
        run_id=run_id,
        topic_id=topic.topic_id,
        topic_name=topic.title,
        phase="topic_selected",
        status="in_progress",
        prerequisites=topic.prerequisites,
        artifacts=RunArtifacts(),
        scores=RunScores(),
        next_action="generate_concept_note",
    )

    write_json(f"runs/{run_id}/selected_topic.json", selected)
    write_json(f"runs/{run_id}/run_state.json", run_state)
    write_log(run_id, f"Lesson started for {topic.topic_id}")
    write_log(run_id, f"Selection reason: {selected.reason}")

    teacher_llm_callable = build_llm_callable("teacher")
    architect_llm_callable = build_llm_callable("architect_lens")
    assessor_llm_callable = build_llm_callable("assessor")

    teacher_payload = build_teacher_payload(
        selected_topic=topic,
        learner_profile=learner_profile,
        weak_spots=[],
    )
    concept_note, teacher_diagnostics = generate_teacher_note_with_quality_loop(
        teacher_payload,
        teacher_llm_callable,
    )
    write_json(f"runs/{run_id}/concept_note.json", concept_note)
    write_json(f"runs/{run_id}/teacher_quality_diagnostics.json", teacher_diagnostics)
    write_markdown(
        f"notes/concepts/{topic.topic_id}_{topic.title.lower().replace(' ', '_')}.md",
        concept_note_to_markdown(concept_note),
    )
    write_log(
        run_id,
        f"Concept note generated with teacher quality status: {teacher_diagnostics['status']}",
    )

    architect_payload = build_architect_lens_payload(
        selected_topic=topic,
        concept_note=concept_note,
        learner_profile=learner_profile,
    )
    architect_note = generate_architect_note(architect_payload, architect_llm_callable)
    write_json(f"runs/{run_id}/architect_note.json", architect_note)
    write_markdown(
        f"notes/architect_lens/{topic.topic_id}_{topic.title.lower().replace(' ', '_')}_architect.md",
        architect_note_to_markdown(architect_note),
    )
    write_log(run_id, "Architect note generated")

    assessor_payload = build_assessor_payload(
        concept_note=concept_note,
        architect_note=architect_note,
        learner_profile=learner_profile,
        weak_spots=[],
    )
    assessment = generate_assessment(assessor_payload, assessor_llm_callable)
    write_json(f"runs/{run_id}/assessment.json", assessment)

    question_md_path = f"assessments/questions/{run_id}_questions.md"
    answer_md_path = f"assessments/answers/{run_id}_answers.md"
    answer_json_path = f"assessments/answers/{run_id}_answers.json"

    write_markdown(question_md_path, assessment_to_markdown(assessment))
    write_markdown(answer_md_path, answer_template_to_markdown(assessment))
    write_json(answer_json_path, answer_template_to_json(assessment))
    write_log(run_id, "Assessment and answer templates generated")

    final_run_state = RunState(
        run_id=run_id,
        topic_id=topic.topic_id,
        topic_name=topic.title,
        phase="awaiting_user_answers",
        status="in_progress",
        prerequisites=topic.prerequisites,
        artifacts=RunArtifacts(
            concept_note=f"runs/{run_id}/concept_note.json",
            architect_note=f"runs/{run_id}/architect_note.json",
            assessment=f"runs/{run_id}/assessment.json",
            answers=answer_json_path,
        ),
        scores=RunScores(),
        next_action="await_user_answers",
    )

    write_json(f"runs/{run_id}/run_state.json", final_run_state)

    append_jsonl(
        "data/run_history.jsonl",
        {
            "run_id": run_id,
            "timestamp": utc_now_iso(),
            "topic_id": topic.topic_id,
            "topic_title": topic.title,
            "selection_mode": selected.selection_mode,
            "phase": "awaiting_user_answers",
            "status": "in_progress",
            "next_action": "await_user_answers",
        },
    )

    print(
        json.dumps(
            {
                "run_id": run_id,
                "topic_id": topic.topic_id,
                "selection_mode": selected.selection_mode,
                "phase": "awaiting_user_answers",
                "next_action": "await_user_answers",
                "answer_template": answer_json_path,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)