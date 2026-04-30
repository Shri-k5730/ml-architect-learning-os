from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List
from src.agents.answer_coach import generate_answer_coaching

import yaml

from src.agents.evaluator_refiner import (
    build_evaluator_refiner_payload,
    evaluate_and_refine,
)
from src.schemas import (
    ArchitectNote,
    Assessment,
    ConceptNote,
    EvaluationResult,
    Topic,
    UserAnswer,
)
from src.utils.llm_client import build_llm_callable
from src.utils.repo_writer import append_jsonl, write_json, write_markdown
from src.utils.rewards import apply_evaluation_rewards
from src.utils.tracker import get_progress_row, unlock_topic, update_topic_status
from src.utils.validator import build_dataclass


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONFIG_DIR = PROJECT_ROOT / "config"
TOPICS_DIR = PROJECT_ROOT / "topics"


class EvaluateLessonError(Exception):
    """Raised when lesson evaluation fails."""


def load_yaml(file_path: Path) -> Dict[str, Any]:
    if not file_path.exists():
        raise EvaluateLessonError(f"YAML file not found: {file_path}")

    with file_path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    if not isinstance(data, dict):
        raise EvaluateLessonError(f"Expected top-level object in YAML: {file_path}")

    return data


def load_json(file_path: Path) -> Any:
    if not file_path.exists():
        raise EvaluateLessonError(f"JSON file not found: {file_path}")

    with file_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def write_log(run_id: str, message: str) -> None:
    log_path = PROJECT_ROOT / "runs" / run_id / "logs.txt"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as f:
        f.write(f"[{utc_now_iso()}] {message}\n")


def get_latest_awaiting_run() -> str:
    runs_dir = PROJECT_ROOT / "runs"
    if not runs_dir.exists():
        raise EvaluateLessonError("runs directory does not exist.")

    candidate_runs: List[str] = []

    for run_dir in runs_dir.iterdir():
        if not run_dir.is_dir():
            continue

        run_state_path = run_dir / "run_state.json"
        if not run_state_path.exists():
            continue

        run_state = load_json(run_state_path)
        if (
            run_state.get("phase") == "awaiting_user_answers"
            and run_state.get("next_action") == "await_user_answers"
        ):
            candidate_runs.append(run_dir.name)

    if not candidate_runs:
        raise EvaluateLessonError("No run is currently awaiting user answers.")

    return sorted(candidate_runs)[-1]


def load_topic_catalog() -> List[Topic]:
    data = load_json(TOPICS_DIR / "topic_catalog.json")
    if not isinstance(data, list):
        raise EvaluateLessonError("topic_catalog.json must contain a list.")
    return [Topic(**item) for item in data]


def get_topic_by_id(topic_catalog: List[Topic], topic_id: str) -> Topic:
    for topic in topic_catalog:
        if topic.topic_id == topic_id:
            return topic
    raise EvaluateLessonError(f"Topic not found: {topic_id}")


def load_user_answers(answer_json_path: Path) -> List[UserAnswer]:
    data = load_json(answer_json_path)
    answers = data.get("answers", [])

    if not isinstance(answers, list):
        raise EvaluateLessonError("answers JSON must contain a list under 'answers'.")

    user_answers: List[UserAnswer] = []
    for item in answers:
        question_id = item.get("question_id", "").strip()
        answer_text = item.get("answer", "").strip()

        if not question_id:
            raise EvaluateLessonError("One answer object is missing question_id.")

        if not answer_text:
            raise EvaluateLessonError(f"Question '{question_id}' has an empty answer.")

        user_answers.append(
            UserAnswer(
                question_id=question_id,
                answer=answer_text,
            )
        )

    return user_answers

def answer_coaching_to_markdown(answer_coaching: Dict[str, Any]) -> str:
    lines = [
        f"---",
        f"topic_id: {answer_coaching.get('topic_id', '')}",
        f"---",
        "",
        "# Answer Coaching",
        "",
    ]

    for item in answer_coaching.get("coaching", []):
        lines.append(f"## {item.get('question_id', '')}")
        lines.append("")
        lines.append(f"**Question:** {item.get('question', '')}")
        lines.append("")
        lines.append("**Your Answer:**")
        lines.append("")
        lines.append(item.get("your_answer", ""))
        lines.append("")
        lines.append("**What Was Missing:**")
        for missing in item.get("what_was_missing", []):
            lines.append(f"- {missing}")
        lines.append("")
        lines.append("**Better Answer:**")
        lines.append("")
        lines.append(item.get("better_answer", ""))
        lines.append("")
        lines.append("**Why This Is Better:**")
        lines.append("")
        lines.append(item.get("why_this_is_better", ""))
        lines.append("")
        lines.append("**Architect Upgrade:**")
        lines.append("")
        lines.append(item.get("architect_upgrade", ""))
        lines.append("")

    return "\n".join(lines).strip() + "\n"

def evaluation_to_markdown(evaluation: EvaluationResult, rewards_summary: Dict[str, Any]) -> str:
    strengths = evaluation.strengths or []
    weak_spots = evaluation.weak_spots or []
    badges_awarded = rewards_summary.get("badges_awarded", [])

    strength_lines = "\n".join(f"- {item}" for item in strengths) if strengths else "- None"
    weak_lines = "\n".join(f"- {item}" for item in weak_spots) if weak_spots else "- None"
    badge_lines = (
        "\n".join(f"- {item['label']}: {item['description']}" for item in badges_awarded)
        if badges_awarded else "- None"
    )

    return f"""---
topic_id: {evaluation.topic_id}
decision: {evaluation.decision}
next_action: {evaluation.next_action}
---

# Scores

- Conceptual Clarity: {evaluation.scores.conceptual_clarity}
- Practical Reasoning: {evaluation.scores.practical_reasoning}
- Architect Reasoning: {evaluation.scores.architect_reasoning}
- Communication: {evaluation.scores.communication}

# Rewards

- Stars Earned: {rewards_summary.get('stars_earned', '-')}
- Best Stars: {rewards_summary.get('best_stars', '-')}
- XP Earned: {rewards_summary.get('xp_earned', '-')}
- Total XP: {rewards_summary.get('total_xp', '-')}

# Badges Awarded

{badge_lines}

# Strengths

{strength_lines}

# Weak Spots

{weak_lines}

# Decision Reason

{evaluation.decision_reason}

# Refined Explanation

{evaluation.refined_explanation}

# Refined Architect Summary

{evaluation.refined_architect_summary}
"""


def unlock_dependent_topics(topic_catalog: List[Topic], completed_topic_id: str) -> List[str]:
    unlocked: List[str] = []

    for topic in topic_catalog:
        if completed_topic_id not in topic.prerequisites:
            continue

        all_done = True
        for prereq in topic.prerequisites:
            row = get_progress_row(prereq)
            if not row or row.get("status") != "completed":
                all_done = False
                break

        if all_done:
            unlock_topic(topic.topic_id)
            unlocked.append(topic.topic_id)

    return unlocked


def main() -> None:
    learner_profile = load_yaml(CONFIG_DIR / "learner_profile.yaml")
    scoring_rubric = load_yaml(CONFIG_DIR / "scoring_rubric.yaml")
    topic_catalog = load_topic_catalog()

    run_id = get_latest_awaiting_run()
    run_dir = PROJECT_ROOT / "runs" / run_id

    run_state = load_json(run_dir / "run_state.json")
    topic_id = run_state["topic_id"]
    topic = get_topic_by_id(topic_catalog, topic_id)

    concept_note = build_dataclass(load_json(run_dir / "concept_note.json"), ConceptNote)
    architect_note = build_dataclass(load_json(run_dir / "architect_note.json"), ArchitectNote)
    assessment = build_dataclass(load_json(run_dir / "assessment.json"), Assessment)

    answers_relative_path = run_state["artifacts"]["answers"]
    answer_json_path = PROJECT_ROOT / answers_relative_path
    user_answers = load_user_answers(answer_json_path)

    evaluator_llm_callable = build_llm_callable("evaluator_refiner")

    evaluator_payload = build_evaluator_refiner_payload(
        concept_note=concept_note,
        architect_note=architect_note,
        assessment=assessment,
        user_answers=user_answers,
        scoring_rubric=scoring_rubric,
        learner_profile=learner_profile,
    )
    evaluation = evaluate_and_refine(evaluator_payload, evaluator_llm_callable)

    answer_coaching = generate_answer_coaching(
    concept_note=concept_note,
    architect_note=architect_note,
    assessment=assessment,
    user_answers=user_answers,
    evaluation=evaluation,
    llm_callable=evaluator_llm_callable,
)


    write_json(
        f"runs/{run_id}/answers.json",
        {
            "topic_id": topic_id,
            "answers": [a.to_dict() for a in user_answers],
        },
    )
    write_json(f"runs/{run_id}/evaluation.json", evaluation)

    write_json(f"runs/{run_id}/answer_coaching.json", answer_coaching)
    write_markdown(
        f"assessments/evaluations/{topic_id}_answer_coaching.md",
        answer_coaching_to_markdown(answer_coaching),
    )

    completed = evaluation.decision == "pass"
    new_status = "completed" if completed else evaluation.decision

    update_topic_status(
        topic_id=topic_id,
        status=new_status,
        attempt_increment=True,
        conceptual_score=evaluation.scores.conceptual_clarity,
        practical_score=evaluation.scores.practical_reasoning,
        architect_score=evaluation.scores.architect_reasoning,
        communication_score=evaluation.scores.communication,
        decision=evaluation.decision,
        prerequisites_unlocked=True,
        completed=completed,
    )

    unlocked_topics: List[str] = []
    if completed:
        unlocked_topics = unlock_dependent_topics(topic_catalog, topic_id)
        write_log(run_id, f"Unlocked dependent topics: {unlocked_topics}")

    rewards_summary = apply_evaluation_rewards(
        run_id=run_id,
        topic_id=topic_id,
        topic_title=topic.title,
        scores={
            "conceptual_clarity": evaluation.scores.conceptual_clarity,
            "practical_reasoning": evaluation.scores.practical_reasoning,
            "architect_reasoning": evaluation.scores.architect_reasoning,
            "communication": evaluation.scores.communication,
        },
        decision=evaluation.decision,
    )

    write_json(f"runs/{run_id}/rewards.json", rewards_summary)
    write_markdown(
        f"assessments/evaluations/{topic_id}_evaluation.md",
        evaluation_to_markdown(evaluation, rewards_summary),
    )
    write_markdown(
        f"notes/refined/{topic_id}_refined.md",
        f"""---
topic_id: {topic_id}
---

# Refined Explanation

{evaluation.refined_explanation}

# Refined Architect Summary

{evaluation.refined_architect_summary}
""",
    )
    write_log(run_id, f"Evaluation completed with decision: {evaluation.decision}")
    write_log(run_id, f"Rewards applied: {rewards_summary}")

    final_run_state = {
        "run_id": run_id,
        "topic_id": topic_id,
        "topic_name": topic.title,
        "phase": "evaluation_complete",
        "status": new_status,
        "prerequisites": topic.prerequisites,
        "artifacts": {
            "concept_note": f"runs/{run_id}/concept_note.json",
            "architect_note": f"runs/{run_id}/architect_note.json",
            "assessment": f"runs/{run_id}/assessment.json",
            "answers": f"runs/{run_id}/answers.json",
            "evaluation": f"runs/{run_id}/evaluation.json",
            "answer_coaching": f"runs/{run_id}/answer_coaching.json",
            "rewards": f"runs/{run_id}/rewards.json",
            "refined_note": f"notes/refined/{topic_id}_refined.md",
            
        },
        "scores": {
            "conceptual_clarity": evaluation.scores.conceptual_clarity,
            "practical_reasoning": evaluation.scores.practical_reasoning,
            "architect_reasoning": evaluation.scores.architect_reasoning,
            "communication": evaluation.scores.communication,
        },
        "next_action": evaluation.next_action,
    }

    write_json(f"runs/{run_id}/run_state.json", final_run_state)

    append_jsonl(
        "data/run_history.jsonl",
        {
            "run_id": run_id,
            "timestamp": utc_now_iso(),
            "topic_id": topic_id,
            "topic_title": topic.title,
            "phase": "evaluation_complete",
            "status": new_status,
            "decision": evaluation.decision,
            "next_action": evaluation.next_action,
            "unlocked_topics": unlocked_topics,
            "reward_summary": rewards_summary,
        },
    )

    print(
        json.dumps(
            {
                "run_id": run_id,
                "topic_id": topic_id,
                "decision": evaluation.decision,
                "next_action": evaluation.next_action,
                "unlocked_topics": unlocked_topics,
                "reward_summary": rewards_summary,
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