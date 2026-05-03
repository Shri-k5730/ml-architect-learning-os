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
        "processed_run_ids": [],
    }


def _fetch_supabase_rewards_state() -> Dict[str, Any] | None:
    try:
        from src.utils.supabase_store import fetch_state

        payload = fetch_state("rewards_state")
        if isinstance(payload, dict):
            return payload
    except Exception:
        return None
    return None


def _persist_supabase_rewards_state(state: Dict[str, Any]) -> None:
    try:
        from src.utils.supabase_store import upsert_state

        upsert_state("rewards_state", state)
    except Exception:
        return


def _merge_state_shape(state: Dict[str, Any]) -> Dict[str, Any]:
    base = _default_state()
    base.update(state or {})
    base.setdefault("streaks", _default_state()["streaks"])
    base["streaks"].setdefault("current_completion_streak", 0)
    base["streaks"].setdefault("best_completion_streak", 0)
    base.setdefault("topics", {})
    base.setdefault("history", [])
    base.setdefault("badges_unlocked", [])
    base.setdefault("processed_run_ids", [])
    base.setdefault("total_xp", 0)
    return base


def load_rewards_state() -> Dict[str, Any]:
    supabase_state = _fetch_supabase_rewards_state()
    if supabase_state:
        state = _merge_state_shape(supabase_state)
        _write_rewards_local(state)
        return state

    if not REWARDS_STATE_PATH.exists():
        return _default_state()

    try:
        with REWARDS_STATE_PATH.open("r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            return _default_state()
        return _merge_state_shape(data)
    except Exception:
        return _default_state()


def _write_rewards_local(state: Dict[str, Any]) -> None:
    REWARDS_STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    REWARDS_STATE_PATH.write_text(
        json.dumps(state, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def save_rewards_state(state: Dict[str, Any]) -> None:
    state = _merge_state_shape(state)
    _write_rewards_local(state)
    _persist_supabase_rewards_state(state)


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
    existing_ids = {item.get("id") for item in state.get("badges_unlocked", [])}
    badge = {
        "id": badge_id,
        "label": label,
        "description": description,
    }

    if badge_id not in existing_ids:
        state["badges_unlocked"].append(badge)

    # Per-run awarded list should show what was relevant this run even if badge already exists.
    if badge not in awarded:
        awarded.append(badge)


def get_topic_reward_state(state: Dict[str, Any], topic_id: str) -> Dict[str, Any]:
    return state.get("topics", {}).get(topic_id, {})


def apply_evaluation_rewards(
    run_id: str,
    topic_id: str,
    topic_title: str,
    scores: Dict[str, int],
    decision: str,
    completed: bool = False,
) -> Dict[str, Any]:
    state = load_rewards_state()

    if run_id in state.get("processed_run_ids", []):
        for item in reversed(state.get("history", [])):
            if item.get("run_id") == run_id:
                return item

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
    previous_best = int(topic_state.get("best_stars", 0) or 0)

    topic_state["title"] = topic_title
    topic_state["attempts"] = int(topic_state.get("attempts", 0)) + 1
    topic_state["latest_stars"] = stars
    topic_state["best_stars"] = max(previous_best, stars)
    topic_state["last_decision"] = decision

    if completed:
        topic_state["completed"] = True
        # Borderline completion counts as a clear for streak purposes in V1.
        state["streaks"]["current_completion_streak"] = int(
            state["streaks"].get("current_completion_streak", 0)
        ) + 1
        if decision == "pass":
            xp_earned = 60 + stars * 10
        else:
            xp_earned = 25 + stars * 5
    else:
        state["streaks"]["current_completion_streak"] = 0
        xp_earned = 10 + stars * 2

    state["streaks"]["best_completion_streak"] = max(
        int(state["streaks"].get("best_completion_streak", 0)),
        int(state["streaks"].get("current_completion_streak", 0)),
    )

    state["total_xp"] = int(state.get("total_xp", 0)) + xp_earned
    badges_awarded: List[Dict[str, str]] = []

    completed_topics_after = sum(
        1 for item in state["topics"].values() if item.get("completed")
    )

    if completed and not completed_before and completed_topics_after == 1:
        _award_badge(
            state,
            "first_clear",
            "First Clear",
            "Completed the first level.",
            badges_awarded,
        )

    if completed and not completed_before:
        _award_badge(
            state,
            f"level_clear_{topic_id}",
            f"Level Clear: {topic_id.upper()}",
            f"Completed {topic_title}.",
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

    if int(scores["practical_reasoning"]) >= 3:
        _award_badge(
            state,
            "hands_on_starter",
            "Hands-on Starter",
            "Handled a practical mission with acceptable reasoning.",
            badges_awarded,
        )

    if stars > previous_best and previous_best > 0:
        _award_badge(
            state,
            f"improved_{topic_id}",
            f"Improved: {topic_id.upper()}",
            f"Improved best stars for {topic_title} from {previous_best} to {stars}.",
            badges_awarded,
        )

    current_streak = int(state["streaks"].get("current_completion_streak", 0))
    if current_streak >= 3:
        _award_badge(
            state,
            "clear_streak_3",
            "Clear Streak x3",
            "Completed 3 lessons in a row.",
            badges_awarded,
        )

    if current_streak >= 5:
        _award_badge(
            state,
            "clear_streak_5",
            "Clear Streak x5",
            "Completed 5 lessons in a row.",
            badges_awarded,
        )

    topic_state["last_badges"] = [badge["label"] for badge in badges_awarded]

    summary = {
        "run_id": run_id,
        "topic_id": topic_id,
        "topic_title": topic_title,
        "decision": decision,
        "completed": completed,
        "xp_earned": xp_earned,
        "total_xp": state["total_xp"],
        "stars_earned": stars,
        "best_stars": topic_state["best_stars"],
        "badges_awarded": badges_awarded,
        "current_completion_streak": state["streaks"]["current_completion_streak"],
        "best_completion_streak": state["streaks"]["best_completion_streak"],
    }

    state["history"].append(summary)
    state["processed_run_ids"].append(run_id)
    save_rewards_state(state)
    return summary
