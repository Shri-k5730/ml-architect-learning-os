from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List


PROJECT_ROOT = Path(__file__).resolve().parents[2]
REWARDS_STATE_PATH = PROJECT_ROOT / "data" / "rewards_state.json"


def _default_state() -> Dict[str, Any]:
    return {
        "total_xp": 0,
        "badges_unlocked": [],
        "streaks": {
            "current_completion_streak": 0,
            "best_completion_streak": 0,
        },
        "topics": {},
        "history": [],
    }


def load_rewards_state() -> Dict[str, Any]:
    if not REWARDS_STATE_PATH.exists():
        return _default_state()

    try:
        with REWARDS_STATE_PATH.open("r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            return _default_state()
        return data
    except Exception:
        return _default_state()


def save_rewards_state(state: Dict[str, Any]) -> None:
    REWARDS_STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    REWARDS_STATE_PATH.write_text(
        json.dumps(state, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def compute_average_from_scores(scores: Dict[str, int]) -> float:
    values = [
        int(scores["conceptual_clarity"]),
        int(scores["practical_reasoning"]),
        int(scores["architect_reasoning"]),
        int(scores["communication"]),
    ]
    return sum(values) / len(values)


def compute_stars_from_scores(scores: Dict[str, int]) -> int:
    avg = compute_average_from_scores(scores)
    return max(1, min(5, round(avg)))


def _award_badge(
    state: Dict[str, Any],
    badge_id: str,
    label: str,
    description: str,
    awarded: List[Dict[str, str]],
) -> None:
    existing_ids = {item["id"] for item in state["badges_unlocked"]}
    if badge_id in existing_ids:
        return

    badge = {
        "id": badge_id,
        "label": label,
        "description": description,
    }
    state["badges_unlocked"].append(badge)
    awarded.append(badge)


def get_topic_reward_state(state: Dict[str, Any], topic_id: str) -> Dict[str, Any]:
    return state.get("topics", {}).get(topic_id, {})


def apply_evaluation_rewards(
    run_id: str,
    topic_id: str,
    topic_title: str,
    scores: Dict[str, int],
    decision: str,
) -> Dict[str, Any]:
    state = load_rewards_state()

    topic_state = state["topics"].setdefault(
        topic_id,
        {
            "title": topic_title,
            "attempts": 0,
            "completed": False,
            "latest_stars": 0,
            "best_stars": 0,
            "last_decision": None,
            "last_badges": [],
        },
    )

    stars = compute_stars_from_scores(scores)
    completed_before = bool(topic_state.get("completed", False))

    topic_state["attempts"] = int(topic_state.get("attempts", 0)) + 1
    topic_state["latest_stars"] = stars
    topic_state["best_stars"] = max(int(topic_state.get("best_stars", 0)), stars)
    topic_state["last_decision"] = decision

    if decision == "pass":
        xp_earned = 60 + stars * 10
        topic_state["completed"] = True
        state["streaks"]["current_completion_streak"] += 1
    elif decision == "borderline":
        xp_earned = 25 + stars * 5
        state["streaks"]["current_completion_streak"] = 0
    else:
        xp_earned = 10 + stars * 2
        state["streaks"]["current_completion_streak"] = 0

    state["streaks"]["best_completion_streak"] = max(
        state["streaks"]["best_completion_streak"],
        state["streaks"]["current_completion_streak"],
    )

    state["total_xp"] += xp_earned
    badges_awarded: List[Dict[str, str]] = []

    completed_topics_after = sum(
        1 for item in state["topics"].values() if item.get("completed")
    )

    if decision == "pass" and not completed_before and completed_topics_after == 1:
        _award_badge(
            state,
            "first_clear",
            "First Clear",
            "Completed the first level.",
            badges_awarded,
        )

    if stars >= 3:
        _award_badge(
            state,
            "three_star_scholar",
            "Three-Star Scholar",
            "Earned at least 3 stars on a level.",
            badges_awarded,
        )

    if stars >= 4:
        _award_badge(
            state,
            "four_star_architect",
            "Four-Star Architect",
            "Earned at least 4 stars on a level.",
            badges_awarded,
        )

    if stars == 5:
        _award_badge(
            state,
            "five_star_master",
            "Five-Star Master",
            "Earned 5 stars on a level.",
            badges_awarded,
        )

    if int(scores["architect_reasoning"]) >= 4:
        _award_badge(
            state,
            "architect_eye",
            "Architect Eye",
            "Reached strong architect reasoning on a lesson.",
            badges_awarded,
        )

    if state["streaks"]["current_completion_streak"] >= 3:
        _award_badge(
            state,
            "clear_streak_3",
            "Clear Streak x3",
            "Completed 3 lessons in a row.",
            badges_awarded,
        )

    topic_state["last_badges"] = [badge["label"] for badge in badges_awarded]

    summary = {
        "run_id": run_id,
        "topic_id": topic_id,
        "topic_title": topic_title,
        "decision": decision,
        "xp_earned": xp_earned,
        "total_xp": state["total_xp"],
        "stars_earned": stars,
        "best_stars": topic_state["best_stars"],
        "badges_awarded": badges_awarded,
        "current_completion_streak": state["streaks"]["current_completion_streak"],
        "best_completion_streak": state["streaks"]["best_completion_streak"],
    }

    state["history"].append(summary)
    save_rewards_state(state)
    return summary