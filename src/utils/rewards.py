from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional


PROJECT_ROOT = Path(__file__).resolve().parents[2]
REWARDS_STATE_PATH = PROJECT_ROOT / "data" / "rewards_state.json"

CLEAR_DECISIONS = {"pass", "borderline"}


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


def _as_int(value: Any, default: int = 0) -> int:
    try:
        if value is None or str(value).strip() == "":
            return default
        return int(value)
    except Exception:
        return default


def _is_clear(decision: str, completed: Optional[bool] = None, status: Optional[str] = None) -> bool:
    if completed is not None:
        return bool(completed)
    if status == "completed":
        return True
    return str(decision or "").strip().lower() in CLEAR_DECISIONS


def _badge_dict(badge: Any) -> Optional[Dict[str, str]]:
    if isinstance(badge, dict):
        badge_id = str(badge.get("id") or badge.get("label") or "").strip()
        label = str(badge.get("label") or badge_id or "Badge").strip()
        description = str(badge.get("description") or "").strip()
        if not badge_id:
            return None
        return {"id": badge_id, "label": label, "description": description}

    if isinstance(badge, str) and badge.strip():
        label = badge.strip()
        return {"id": label.lower().replace(" ", "_"), "label": label, "description": ""}

    return None


def _award_badge(
    state: Dict[str, Any],
    badge_id: str,
    label: str,
    description: str,
    awarded: List[Dict[str, str]],
) -> None:
    cleaned_badges: List[Dict[str, str]] = []
    seen_ids = set()

    for existing in state.get("badges_unlocked", []):
        cleaned = _badge_dict(existing)
        if cleaned and cleaned["id"] not in seen_ids:
            cleaned_badges.append(cleaned)
            seen_ids.add(cleaned["id"])

    state["badges_unlocked"] = cleaned_badges

    if badge_id in seen_ids:
        return

    badge = {"id": badge_id, "label": label, "description": description}
    state["badges_unlocked"].append(badge)
    awarded.append(badge)


def compute_average_from_scores(scores: Dict[str, int]) -> float:
    values = [
        _as_int(scores.get("conceptual_clarity"), 1),
        _as_int(scores.get("practical_reasoning"), 1),
        _as_int(scores.get("architect_reasoning"), 1),
        _as_int(scores.get("communication"), 1),
    ]
    return sum(values) / len(values)


def compute_stars_from_scores(scores: Dict[str, int]) -> int:
    avg = compute_average_from_scores(scores)
    return max(1, min(5, round(avg)))


def normalize_rewards_state(state: Dict[str, Any]) -> Dict[str, Any]:
    """Clean old reward rows and recompute streaks from existing history.

    This fixes earlier V1 rows where borderline clears were stored with streak 0,
    and it prevents Streamlit from rendering badge objects as [object Object].
    """
    if not isinstance(state, dict):
        state = _default_state()

    default = _default_state()
    for key, value in default.items():
        state.setdefault(key, value)

    state.setdefault("streaks", default["streaks"])
    state.setdefault("topics", {})
    state.setdefault("history", [])
    state.setdefault("badges_unlocked", [])

    # Clean global badges.
    cleaned_global: List[Dict[str, str]] = []
    seen_badges = set()
    for badge in state.get("badges_unlocked", []):
        cleaned = _badge_dict(badge)
        if cleaned and cleaned["id"] not in seen_badges:
            cleaned_global.append(cleaned)
            seen_badges.add(cleaned["id"])
    state["badges_unlocked"] = cleaned_global

    # Clean history rows and recompute streaks.
    current_streak = 0
    best_streak = 0
    completed_topics = set()
    total_xp_from_history = 0

    for row in state.get("history", []):
        if not isinstance(row, dict):
            continue

        decision = str(row.get("decision") or "").strip().lower()
        status = str(row.get("status") or "").strip().lower()
        topic_id = str(row.get("topic_id") or "").strip()
        topic_title = str(row.get("topic_title") or topic_id).strip()
        stars = _as_int(row.get("stars_earned"), _as_int(row.get("best_stars"), 0))
        xp = _as_int(row.get("xp_earned"), 0)
        total_xp_from_history += xp

        clear = _is_clear(decision=decision, status=status)
        row["completed"] = clear

        raw_badges = row.get("badges_awarded", []) or []
        if isinstance(raw_badges, dict):
            raw_badges = [raw_badges]
        cleaned_row_badges: List[Dict[str, str]] = []
        for badge in raw_badges:
            cleaned = _badge_dict(badge)
            if cleaned:
                cleaned_row_badges.append(cleaned)
        row["badges_awarded"] = cleaned_row_badges
        row["badge_labels"] = ", ".join(b["label"] for b in cleaned_row_badges)

        if topic_id:
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
            topic_state["title"] = topic_title
            topic_state["attempts"] = max(_as_int(topic_state.get("attempts"), 0), 1)
            topic_state["latest_stars"] = stars or _as_int(topic_state.get("latest_stars"), 0)
            topic_state["best_stars"] = max(_as_int(topic_state.get("best_stars"), 0), stars)
            topic_state["last_decision"] = decision
            if clear:
                topic_state["completed"] = True
                completed_topics.add(topic_id)
            if cleaned_row_badges:
                topic_state["last_badges"] = [b["label"] for b in cleaned_row_badges]

        if clear:
            current_streak += 1
            best_streak = max(best_streak, current_streak)
        else:
            current_streak = 0

    state["streaks"]["current_completion_streak"] = current_streak
    state["streaks"]["best_completion_streak"] = max(
        _as_int(state["streaks"].get("best_completion_streak"), 0),
        best_streak,
    )

    # Preserve existing total if it is higher, otherwise rebuild from history.
    state["total_xp"] = max(_as_int(state.get("total_xp"), 0), total_xp_from_history)

    # Backfill durable per-level badges for completed topics.
    awarded_dummy: List[Dict[str, str]] = []
    for topic_id in sorted(completed_topics):
        topic_title = state["topics"].get(topic_id, {}).get("title", topic_id)
        _award_badge(
            state,
            f"level_clear_{topic_id}",
            f"Level Clear: {topic_id}",
            f"Completed {topic_title}.",
            awarded_dummy,
        )

    if completed_topics:
        _award_badge(
            state,
            "first_clear",
            "First Clear",
            "Completed the first level.",
            awarded_dummy,
        )

    return state


def load_rewards_state() -> Dict[str, Any]:
    if not REWARDS_STATE_PATH.exists():
        return _default_state()

    try:
        with REWARDS_STATE_PATH.open("r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            return _default_state()
        state = normalize_rewards_state(data)
        # Persist cleanup locally so repeated app reloads stay clean.
        save_rewards_state(state)
        return state
    except Exception:
        return _default_state()


def save_rewards_state(state: Dict[str, Any]) -> None:
    REWARDS_STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    REWARDS_STATE_PATH.write_text(
        json.dumps(normalize_rewards_state(state), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def get_topic_reward_state(state: Dict[str, Any], topic_id: str) -> Dict[str, Any]:
    return state.get("topics", {}).get(topic_id, {})


def apply_evaluation_rewards(
    run_id: str,
    topic_id: str,
    topic_title: str,
    scores: Dict[str, int],
    decision: str,
    completed: Optional[bool] = None,
) -> Dict[str, Any]:
    state = load_rewards_state()

    decision_norm = str(decision or "").strip().lower()
    stars = compute_stars_from_scores(scores)
    clear = _is_clear(decision=decision_norm, completed=completed)

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

    completed_before = bool(topic_state.get("completed", False))

    topic_state["title"] = topic_title
    topic_state["attempts"] = _as_int(topic_state.get("attempts"), 0) + 1
    topic_state["latest_stars"] = stars
    topic_state["best_stars"] = max(_as_int(topic_state.get("best_stars"), 0), stars)
    topic_state["last_decision"] = decision_norm

    if decision_norm == "pass":
        xp_earned = 60 + stars * 10
    elif decision_norm == "borderline":
        xp_earned = 25 + stars * 5
    else:
        xp_earned = 10 + stars * 2

    if clear:
        topic_state["completed"] = True
        state["streaks"]["current_completion_streak"] = _as_int(
            state["streaks"].get("current_completion_streak"), 0
        ) + 1
    else:
        state["streaks"]["current_completion_streak"] = 0

    state["streaks"]["best_completion_streak"] = max(
        _as_int(state["streaks"].get("best_completion_streak"), 0),
        _as_int(state["streaks"].get("current_completion_streak"), 0),
    )

    state["total_xp"] = _as_int(state.get("total_xp"), 0) + xp_earned

    badges_awarded: List[Dict[str, str]] = []

    if clear and not completed_before:
        _award_badge(
            state,
            f"level_clear_{topic_id}",
            f"Level Clear: {topic_id}",
            f"Completed {topic_title}.",
            badges_awarded,
        )

        completed_topics_after = sum(
            1 for item in state.get("topics", {}).values() if item.get("completed")
        )
        if completed_topics_after == 1:
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

    if _as_int(scores.get("architect_reasoning"), 0) >= 4:
        _award_badge(
            state,
            "architect_eye",
            "Architect Eye",
            "Reached strong architect reasoning on a lesson.",
            badges_awarded,
        )

    if _as_int(state["streaks"].get("current_completion_streak"), 0) >= 3:
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
        "decision": decision_norm,
        "completed": clear,
        "xp_earned": xp_earned,
        "total_xp": state["total_xp"],
        "stars_earned": stars,
        "best_stars": topic_state["best_stars"],
        "badges_awarded": badges_awarded,
        "badge_labels": ", ".join(badge["label"] for badge in badges_awarded),
        "current_completion_streak": state["streaks"]["current_completion_streak"],
        "best_completion_streak": state["streaks"]["best_completion_streak"],
    }

    state["history"].append(summary)
    save_rewards_state(state)
    return summary
