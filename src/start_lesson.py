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
from src.schemas import (
    ArchitectNote,
    Assessment,
    AssessmentQuestion,
    ConceptNote,
    RunArtifacts,
    RunScores,
    RunState,
    Topic,
    UseCaseMapping,
)
from src.utils.llm_client import build_llm_callable
from src.utils.repo_writer import append_jsonl, write_json, write_markdown
from src.utils.supabase_store import append_event, upsert_artifact, upsert_run
from src.practice.exercise_bank import build_practice_submission_template, get_exercise_for_topic


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



# -----------------------------
# Deterministic fallbacks
# -----------------------------
def build_fallback_concept_note(topic: Topic) -> ConceptNote:
    title_lower = topic.title.lower()
    return ConceptNote(
        topic_id=topic.topic_id,
        title=topic.title,
        simple_explanation=(
            f"{topic.title} is a core ML concept that helps decide whether a model is learning useful patterns "
            "or merely looking good in a narrow test setup. For V1, treat this as a practical system-design idea, "
            "not a textbook definition."
        ),
        wrong_mental_model=(
            f"A weak mental model is to treat {title_lower} as a theory term that only matters during model training."
        ),
        correct_mental_model=(
            f"A stronger mental model is to use {title_lower} as a decision tool for model design, validation, "
            "monitoring, and production risk control."
        ),
        tiny_example=(
            "In a manufacturing defect model, a metric or design choice may look acceptable offline, but the model can still "
            "fail when production conditions shift. The concept helps identify that gap before deployment."
        ),
        why_it_matters=(
            "If this concept is misunderstood, the team may ship a model that appears acceptable in evaluation but fails "
            "when data, process behavior, or operating conditions change."
        ),
        edge_case=(
            "A production line receives unseen input patterns after a machine setting changes, and the model continues making "
            "confident predictions without triggering a monitoring or fallback path."
        ),
        three_takeaways=[
            f"{topic.title} should be understood through system behavior, not memorized as a definition.",
            "A model can look useful offline and still fail when production conditions differ.",
            "Architect-level reasoning connects the concept to validation, monitoring, and fallback design.",
        ],
    )


def build_fallback_architect_note(topic: Topic, concept_note: ConceptNote, learner_profile: Dict[str, Any]) -> ArchitectNote:
    priority_contexts = learner_profile.get("priority_contexts", []) or ["manufacturing_ai"]
    return ArchitectNote(
        topic_id=topic.topic_id,
        architect_summary=(
            f"For an ML Architect, {topic.title} matters because it influences how the model is evaluated, monitored, "
            "and trusted after deployment. The concept should translate into concrete controls, not just explanation."
        ),
        design_implications=[
            "Define the validation setup so it reflects the way the model will be used in production.",
            "Add monitoring and fallback behavior for cases where model inputs or outputs move outside expected patterns.",
        ],
        common_mistakes=[
            "Treating a good offline result as proof that the model is safe for production use.",
            "Failing to connect the concept to concrete checks, alerts, thresholds, or review actions.",
        ],
        production_risks=[
            "The system may silently make poor predictions when production data changes.",
            "Teams may over-invest in model complexity without proving that it improves the operational decision.",
        ],
        interview_framing=(
            f"I would explain {topic.title} by linking it to model reliability: how we validate the model, how we monitor it, "
            "and what guardrails exist when production behavior differs from training or test assumptions."
        ),
        use_case_mapping=[
            UseCaseMapping(
                context=str(priority_contexts[0]),
                relevance=(
                    f"In {priority_contexts[0]}, this concept helps decide whether model behavior is reliable enough "
                    "for operational use and what controls are needed around it."
                ),
            )
        ],
    )


def build_fallback_assessment(topic: Topic, concept_note: ConceptNote, architect_note: ArchitectNote) -> Assessment:
    return Assessment(
        topic_id=topic.topic_id,
        questions=[
            AssessmentQuestion(
                question_id="q1",
                type="concept_check",
                question=f"Explain {topic.title} in simple words without using a textbook definition.",
                expected_focus=[
                    "Clear explanation in plain language.",
                    "Connection to model behavior or evaluation.",
                ],
            ),
            AssessmentQuestion(
                question_id="q2",
                type="tiny_hands_on",
                question=(
                    "A defect prediction model performs well on historical data but starts missing defects after a machine "
                    "setting changes. Use this scenario to explain how the concept applies."
                ),
                expected_focus=[
                    "Identifies the gap between historical evaluation and production behavior.",
                    "Explains what should be checked or redesigned.",
                ],
            ),
            AssessmentQuestion(
                question_id="q3",
                type="failure_diagnosis",
                question=(
                    "What specific failure could happen in production if this concept is misunderstood by the ML team?"
                ),
                expected_focus=[
                    "Names a concrete failure mechanism.",
                    "Connects the failure to data, evaluation, monitoring, or deployment assumptions.",
                ],
            ),
            AssessmentQuestion(
                question_id="q4",
                type="architect_decision",
                question=(
                    "As an ML Architect, what design decision or guardrail would you add because of this concept?"
                ),
                expected_focus=[
                    "Specific design action such as monitoring, fallback, validation split, or threshold.",
                    "Reason for why that action reduces production risk.",
                ],
            ),
            AssessmentQuestion(
                question_id="q5",
                type="teachback",
                question=(
                    "Explain this concept to a non-technical stakeholder and include why it matters before deployment."
                ),
                expected_focus=[
                    "Stakeholder-friendly language.",
                    "Clear business or operational consequence.",
                ],
            ),
        ],
    )


def persist_lesson_start_to_supabase(
    run_id: str,
    topic: Topic,
    final_run_state: RunState,
    selected,
    concept_note,
    architect_note,
    assessment,
    answer_template: dict,
    practice_exercise: dict | None = None,
    practice_submission_template: dict | None = None,
) -> None:
    run_state_payload = final_run_state.to_dict()
    upsert_run(
        run_id=run_id,
        topic_id=topic.topic_id,
        topic_title=topic.title,
        phase=run_state_payload["phase"],
        status=run_state_payload["status"],
        run_state=run_state_payload,
    )
    upsert_artifact(run_id, "selected_topic", topic.topic_id, payload=selected.to_dict())
    upsert_artifact(run_id, "concept_note", topic.topic_id, payload=concept_note.to_dict())
    upsert_artifact(run_id, "architect_note", topic.topic_id, payload=architect_note.to_dict())
    upsert_artifact(run_id, "assessment", topic.topic_id, payload=assessment.to_dict())
    upsert_artifact(run_id, "answer_template", topic.topic_id, payload=answer_template)
    if practice_exercise is not None:
        upsert_artifact(run_id, "practice_exercise", topic.topic_id, payload=practice_exercise)
    if practice_submission_template is not None:
        upsert_artifact(run_id, "practice_submission_template", topic.topic_id, payload=practice_submission_template)
    append_event(
        event_type="lesson_started",
        run_id=run_id,
        topic_id=topic.topic_id,
        payload={
            "selection_mode": selected.selection_mode,
            "phase": run_state_payload["phase"],
            "status": run_state_payload["status"],
        },
    )

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
    try:
        concept_note, teacher_diagnostics = generate_teacher_note_with_quality_loop(
            teacher_payload,
            teacher_llm_callable,
        )
    except Exception as exc:
        concept_note = build_fallback_concept_note(topic)
        teacher_diagnostics = {
            "status": "fallback_used",
            "error": str(exc),
            "message": "Teacher generation failed. Deterministic fallback note was used so the lesson could continue.",
        }
        write_log(run_id, f"Teacher generation failed. Fallback concept note used: {exc}")

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
    try:
        architect_note = generate_architect_note(architect_payload, architect_llm_callable)
    except Exception as exc:
        architect_note = build_fallback_architect_note(topic, concept_note, learner_profile)
        write_log(run_id, f"Architect lens generation failed. Fallback architect note used: {exc}")

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
    try:
        assessment = generate_assessment(assessor_payload, assessor_llm_callable)
    except Exception as exc:
        assessment = build_fallback_assessment(topic, concept_note, architect_note)
        write_log(run_id, f"Assessment generation failed. Fallback mission set used: {exc}")

    write_json(f"runs/{run_id}/assessment.json", assessment)

    question_md_path = f"assessments/questions/{run_id}_questions.md"
    answer_md_path = f"assessments/answers/{run_id}_answers.md"
    answer_json_path = f"assessments/answers/{run_id}_answers.json"

    write_markdown(question_md_path, assessment_to_markdown(assessment))
    write_markdown(answer_md_path, answer_template_to_markdown(assessment))
    answer_template_payload = answer_template_to_json(assessment)
    write_json(answer_json_path, answer_template_payload)

    practice_exercise = get_exercise_for_topic(topic.topic_id)
    practice_submission_template = build_practice_submission_template(topic.topic_id)
    practice_exercise_path = None
    practice_submission_path = None
    if practice_exercise is not None and practice_submission_template is not None:
        practice_exercise_path = f"runs/{run_id}/practice_exercise.json"
        practice_submission_path = f"assessments/answers/{run_id}_practice_submission.json"
        write_json(practice_exercise_path, practice_exercise)
        write_json(practice_submission_path, practice_submission_template)
        write_log(run_id, f"Practice coding exercise attached: {practice_exercise['exercise_id']}")

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
            practice_exercise=practice_exercise_path,
            practice_submission=practice_submission_path,
        ),
        scores=RunScores(),
        next_action="await_user_answers",
    )

    write_json(f"runs/{run_id}/run_state.json", final_run_state)

    try:
        persist_lesson_start_to_supabase(
            run_id=run_id,
            topic=topic,
            final_run_state=final_run_state,
            selected=selected,
            concept_note=concept_note,
            architect_note=architect_note,
            assessment=assessment,
            answer_template=answer_template_payload,
            practice_exercise=practice_exercise,
            practice_submission_template=practice_submission_template,
        )
        write_log(run_id, "Supabase persistence completed for lesson start.")
    except Exception as exc:
        write_log(run_id, f"Supabase lesson-start persistence failed but local lesson remains available: {exc}")

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