from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional


PROJECT_ROOT = Path(__file__).resolve().parents[2]
REWARDS_STATE_PATH = PROJECT_ROOT / "data" / "rewards_state.json"

CLEAR_DECISIONS = {"pass", "borderline"}
LOW_VALUE_BADGE_PREFIXES = (
    "level_clear_",
)
LOW_VALUE_BADGE_IDS = {
    "first_clear",
    "three_star_scholar",
    "four_star_architect",
    "five_star_master",
}


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
        "xp_policy": "best_completed_attempt_per_topic",
        "badge_policy": "capability_badges_only",
    }


def _as_int(value: Any, default: int = 0) -> int:
    try:
        if value is None or str(value).strip() == "":
            return default
        return int(value)
    except Exception:
        return default


def _as_bool(value: Any) -> Optional[bool]:
    if isinstance(value, bool):
        return value
    if value is None:
        return None
    text = str(value).strip().lower()
    if text in {"true", "1", "yes", "y"}:
        return True
    if text in {"false", "0", "no", "n"}:
        return False
    return None


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


def _is_low_value_badge(badge_id: str) -> bool:
    """Return True for old attendance-style badges that should not remain in the cabinet.

    Older reward payloads stored badge labels as free text, for example:
    - "Level Clear: mlf_013 . Completed Encoding categorical variables safely."
    - "Three-Star Scholar"
    - "Clear Streak x3"

    Earlier filtering only caught normalized ids such as ``level_clear_mlf_013``.
    It missed the free-text labels because of punctuation. This broader filter
    keeps the cabinet focused on capability badges rather than attendance spam.
    """
    raw = str(badge_id or "").strip()
    text = raw.lower()
    normalized = (
        text.replace(":", " ")
        .replace(".", " ")
        .replace("-", "_")
        .replace(" ", "_")
    )

    if normalized in LOW_VALUE_BADGE_IDS or text in LOW_VALUE_BADGE_IDS:
        return True

    low_value_text_prefixes = (
        "level clear",
        "level_clear",
        "first clear",
        "first_clear",
        "three-star scholar",
        "three star scholar",
        "three_star_scholar",
        "four-star architect",
        "five-star master",
        "clear streak",
        "clear_streak",
    )
    if any(text.startswith(prefix) or normalized.startswith(prefix.replace(" ", "_")) for prefix in low_value_text_prefixes):
        return True

    return any(normalized.startswith(prefix) for prefix in LOW_VALUE_BADGE_PREFIXES)


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
        if cleaned and not _is_low_value_badge(cleaned["id"]) and cleaned["id"] not in seen_ids:
            cleaned_badges.append(cleaned)
            seen_ids.add(cleaned["id"])

    state["badges_unlocked"] = cleaned_badges

    if _is_low_value_badge(badge_id) or badge_id in seen_ids:
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
    coding = scores.get("coding_correctness") or scores.get("coding") or scores.get("code_lab")
    if coding not in (None, ""):
        values.append(_as_int(coding, 1))
    return sum(values) / len(values)


def compute_stars_from_scores(scores: Dict[str, int]) -> int:
    avg = compute_average_from_scores(scores)
    return max(1, min(5, round(avg)))


def _base_xp_for_clear(decision: str, stars: int) -> int:
    decision_norm = str(decision or "").strip().lower()
    if decision_norm == "pass":
        return 60 + stars * 10
    if decision_norm == "borderline":
        return 25 + stars * 5
    return 0


def _compact_score_signature(row: Dict[str, Any]) -> str:
    scores = row.get("scores") if isinstance(row.get("scores"), dict) else {}
    if not scores:
        return ""
    ordered = [
        f"concept={scores.get('conceptual_clarity', '-')}",
        f"practical={scores.get('practical_reasoning', '-')}",
        f"architect={scores.get('architect_reasoning', '-')}",
        f"communication={scores.get('communication', '-')}",
    ]
    coding = scores.get("coding_correctness") or scores.get("coding") or scores.get("code_lab")
    if coding not in (None, ""):
        ordered.append(f"coding={coding}")
    return ", ".join(ordered)


def _award_capability_badges(
    *,
    state: Dict[str, Any],
    topic_id: str,
    decision: str,
    clear: bool,
    scores: Dict[str, Any],
    stars: int,
    previous_topic_state: Dict[str, Any],
    awarded: List[Dict[str, str]],
) -> None:
    if not clear:
        return

    practical = _as_int(scores.get("practical_reasoning"), 0)
    architect = _as_int(scores.get("architect_reasoning"), 0)
    conceptual = _as_int(scores.get("conceptual_clarity"), 0)
    communication = _as_int(scores.get("communication"), 0)
    coding = _as_int(scores.get("coding_correctness") or scores.get("coding") or scores.get("code_lab"), 0)

    if str(topic_id).startswith("checkpoint_"):
        _award_badge(
            state,
            "module_checkpoint_clear",
            "Checkpoint Cleared",
            "Cleared a module checkpoint and unlocked the next block.",
            awarded,
        )

    if previous_topic_state.get("last_decision") not in (None, "", "pass", "borderline"):
        _award_badge(
            state,
            "recovery_clear",
            "Recovered After Revise",
            "Improved a revised attempt into a clear.",
            awarded,
        )

    if practical >= 3:
        _award_badge(
            state,
            "practical_reasoning_clear",
            "Practical Reasoning Clear",
            "Reached acceptable practical reasoning on a lesson.",
            awarded,
        )

    if architect >= 3:
        _award_badge(
            state,
            "production_controls_named",
            "Production Controls Named",
            "Named deployable controls such as validation, monitoring, thresholds, fallback, or retraining triggers.",
            awarded,
        )

    if conceptual >= 3 and practical >= 3 and architect >= 3 and communication >= 3:
        _award_badge(
            state,
            "balanced_ml_answer",
            "Balanced ML Answer",
            "Reached the minimum bar across concept, practical reasoning, architecture, and communication.",
            awarded,
        )

    if stars >= 4:
        _award_badge(
            state,
            "four_star_attempt",
            "Four-Star Attempt",
            "Produced a strong answer set with 4 or more stars.",
            awarded,
        )

    if coding >= 3:
        _award_badge(
            state,
            "code_lab_clear",
            "Code Lab Clear",
            "Cleared a practical coding exercise.",
            awarded,
        )

    if _as_int(state["streaks"].get("current_completion_streak"), 0) >= 3:
        _award_badge(
            state,
            "no_flunk_streak_3",
            "No-Flunk Streak x3",
            "Cleared 3 attempts in a row without a revise/fail reset.",
            awarded,
        )


def normalize_rewards_state(state: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize rewards using best-completed-attempt XP.

    Policy:
    - Revise/fail attempts earn 0 XP and reset the streak.
    - A topic contributes XP only from its best completed attempt.
    - A retry adds only the positive delta if it beats the previous best completed attempt.
    - Low-value badge spam such as per-level clear badges is filtered from the global cabinet.
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
    state["xp_policy"] = "best_completed_attempt_per_topic"
    state["badge_policy"] = "capability_badges_only"

    state["badges_unlocked"] = []
    state["topics"] = {}

    current_streak = 0
    best_streak = 0
    running_total_xp = 0
    best_base_xp_by_topic: Dict[str, int] = {}
    best_stars_by_topic: Dict[str, int] = {}

    cleaned_history: List[Dict[str, Any]] = []

    for raw_row in state.get("history", []):
        if not isinstance(raw_row, dict):
            continue
        row = dict(raw_row)

        decision = str(row.get("decision") or "").strip().lower()
        status = str(row.get("status") or "").strip().lower()
        topic_id = str(row.get("topic_id") or "").strip()
        topic_title = str(row.get("topic_title") or topic_id).strip()
        completed_flag = _as_bool(row.get("completed"))
        clear = _is_clear(decision=decision, completed=completed_flag, status=status)
        stars = _as_int(row.get("stars_earned"), _as_int(row.get("best_stars"), 0))
        base_xp = _base_xp_for_clear(decision, stars) if clear else 0

        previous_best_xp = best_base_xp_by_topic.get(topic_id, 0)
        xp_earned = max(0, base_xp - previous_best_xp) if topic_id else 0
        if clear and topic_id and base_xp > previous_best_xp:
            best_base_xp_by_topic[topic_id] = base_xp
            best_stars_by_topic[topic_id] = stars

        if not clear:
            xp_earned = 0

        running_total_xp += xp_earned
        row["completed"] = clear
        row["raw_xp_earned"] = _as_int(row.get("xp_earned"), 0)
        row["xp_earned"] = xp_earned
        row["total_xp"] = running_total_xp
        row["stars_earned"] = stars
        row["best_stars"] = max(best_stars_by_topic.get(topic_id, 0), stars if clear else 0)
        row["xp_policy"] = "best_completed_attempt_per_topic"
        row["score_signature"] = _compact_score_signature(row)

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
                "best_completed_xp": 0,
            },
        )
        previous_topic_state = dict(topic_state)
        topic_state["title"] = topic_title
        topic_state["attempts"] = _as_int(topic_state.get("attempts"), 0) + 1
        topic_state["latest_stars"] = stars
        topic_state["last_decision"] = decision
        if clear:
            topic_state["completed"] = True
            topic_state["best_stars"] = max(_as_int(topic_state.get("best_stars"), 0), stars)
            topic_state["best_completed_xp"] = max(_as_int(topic_state.get("best_completed_xp"), 0), base_xp)

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

        row_badges: List[Dict[str, str]] = []
        scores = row.get("scores") if isinstance(row.get("scores"), dict) else {}
        if clear:
            _award_capability_badges(
                state=state,
                topic_id=topic_id,
                decision=decision,
                clear=clear,
                scores=scores,
                stars=stars,
                previous_topic_state=previous_topic_state,
                awarded=row_badges,
            )
        row["badges_awarded"] = row_badges
        row["badge_labels"] = ", ".join(b["label"] for b in row_badges)
        if row_badges:
            topic_state["last_badges"] = [b["label"] for b in row_badges]

        cleaned_history.append(row)

    state["history"] = cleaned_history
    state["total_xp"] = running_total_xp
    state["streaks"]["current_completion_streak"] = current_streak
    state["streaks"]["best_completion_streak"] = best_streak

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
        save_rewards_state(state)
        return state
    except Exception:
        return _default_state()


def save_rewards_state(state: Dict[str, Any]) -> None:
    REWARDS_STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    normalized = normalize_rewards_state(state)
    REWARDS_STATE_PATH.write_text(
        json.dumps(normalized, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    try:
        if normalized.get("history") or _as_int(normalized.get("total_xp"), 0) > 0:
            from src.utils.supabase_store import upsert_state

            upsert_state("rewards_state", normalized)
    except Exception:
        return


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
            "best_completed_xp": 0,
        },
    )
    previous_topic_state = dict(topic_state)

    base_xp = _base_xp_for_clear(decision_norm, stars) if clear else 0
    previous_best_xp = _as_int(topic_state.get("best_completed_xp"), 0)
    xp_earned = max(0, base_xp - previous_best_xp) if clear else 0

    topic_state["title"] = topic_title
    topic_state["attempts"] = _as_int(topic_state.get("attempts"), 0) + 1
    topic_state["latest_stars"] = stars
    topic_state["last_decision"] = decision_norm

    if clear:
        topic_state["completed"] = True
        topic_state["best_stars"] = max(_as_int(topic_state.get("best_stars"), 0), stars)
        topic_state["best_completed_xp"] = max(previous_best_xp, base_xp)
        state["streaks"]["current_completion_streak"] = _as_int(
            state["streaks"].get("current_completion_streak"), 0
        ) + 1
    else:
        xp_earned = 0
        state["streaks"]["current_completion_streak"] = 0

    state["streaks"]["best_completion_streak"] = max(
        _as_int(state["streaks"].get("best_completion_streak"), 0),
        _as_int(state["streaks"].get("current_completion_streak"), 0),
    )

    state["total_xp"] = _as_int(state.get("total_xp"), 0) + xp_earned

    badges_awarded: List[Dict[str, str]] = []
    _award_capability_badges(
        state=state,
        topic_id=topic_id,
        decision=decision_norm,
        clear=clear,
        scores=scores,
        stars=stars,
        previous_topic_state=previous_topic_state,
        awarded=badges_awarded,
    )

    topic_state["last_badges"] = [badge["label"] for badge in badges_awarded]

    summary = {
        "run_id": run_id,
        "topic_id": topic_id,
        "topic_title": topic_title,
        "decision": decision_norm,
        "completed": clear,
        "xp_earned": xp_earned,
        "base_xp_for_attempt": base_xp,
        "best_completed_xp": topic_state.get("best_completed_xp", 0),
        "xp_policy": "best_completed_attempt_per_topic",
        "total_xp": state["total_xp"],
        "stars_earned": stars,
        "best_stars": topic_state["best_stars"],
        "scores": dict(scores or {}),
        "badges_awarded": badges_awarded,
        "badge_labels": ", ".join(badge["label"] for badge in badges_awarded),
        "current_completion_streak": state["streaks"]["current_completion_streak"],
        "best_completion_streak": state["streaks"]["best_completion_streak"],
    }

    state["history"].append(summary)
    save_rewards_state(state)
    return summary
