from __future__ import annotations

import re
from typing import Any, Dict, Iterable, List, Tuple

from src.agents.writing_assist import analyze_answer_text
from src.schemas import EvaluationResult, UserAnswer


LANGUAGE_ONLY_PATTERNS = [
    r"\btypo\b",
    r"\bspelling\b",
    r"\bgrammar\b",
    r"\bcapitalization\b",
    r"\bminor language\b",
]

TECHNICAL_TERM_PATTERNS = [
    r"hyperparameter",
    r"parameter",
    r"precision",
    r"recall",
    r"normalization",
    r"standardization",
    r"threshold",
    r"feature",
    r"label",
]


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", str(text or "").strip().lower())


def _quoted_tokens(text: str) -> List[str]:
    return re.findall(r"['\"]([^'\"]{2,40})['\"]", text or "")


def _looks_language_only(weak_spot: str, known_typos: Dict[str, str]) -> bool:
    weak_l = _norm(weak_spot)
    if not weak_l:
        return False

    # Explicit language-only wording from the LLM.
    if any(re.search(pattern, weak_l) for pattern in LANGUAGE_ONLY_PATTERNS):
        # Keep it only if the statement also contains a real technical-term pattern.
        return not any(re.search(pattern, weak_l) for pattern in TECHNICAL_TERM_PATTERNS)

    # The common bad evaluator pattern: "Confused terminology: 'calss' instead of 'class'".
    if "confused terminology" in weak_l:
        quoted = [q.lower() for q in _quoted_tokens(weak_spot)]
        if quoted and any(q in known_typos for q in quoted):
            return True
        if "instead of" in weak_l and any(q in known_typos for q in quoted):
            return True

    # If the weak spot is built around only a detected misspelling, remove it.
    for original, suggestion in known_typos.items():
        if original in weak_l and suggestion in weak_l and not any(re.search(pattern, weak_l) for pattern in TECHNICAL_TERM_PATTERNS):
            return True
        if f"'{original}'" in weak_l or f'"{original}"' in weak_l:
            if not any(re.search(pattern, weak_l) for pattern in TECHNICAL_TERM_PATTERNS):
                return True

    return False


def collect_language_noise(user_answers: Iterable[UserAnswer]) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    for answer in user_answers:
        analysis = analyze_answer_text(answer.answer)
        spelling = analysis.get("spelling_suggestions", []) or []
        technical = analysis.get("technical_precision_hints", []) or []
        if spelling or technical:
            items.append(
                {
                    "question_id": answer.question_id,
                    "spelling_suggestions": spelling,
                    "technical_precision_hints": technical,
                    "policy": "Spelling/grammar is language noise. Technical-term misuse is content feedback.",
                }
            )
    return items


def sanitize_evaluation_language_noise(
    evaluation: EvaluationResult,
    user_answers: Iterable[UserAnswer],
) -> Tuple[EvaluationResult, List[Dict[str, Any]]]:
    """Remove typo-only feedback from content weak spots.

    The evaluator sometimes calls misspellings "confused terminology". That is wrong:
    a typo is communication noise, not a concept/practical/architect gap. This guard
    strips typo-only weak spots before persistence while preserving genuine technical
    terminology errors such as feature/parameter/hyperparameter misuse.
    """
    language_noise = collect_language_noise(user_answers)
    known_typos: Dict[str, str] = {}
    for item in language_noise:
        for sug in item.get("spelling_suggestions", []) or []:
            original = str(sug.get("original", "")).lower()
            suggestion = str(sug.get("suggestion", "")).lower()
            if original and suggestion:
                known_typos[original] = suggestion

    cleaned: List[str] = []
    removed: List[str] = []
    for weak in evaluation.weak_spots or []:
        if _looks_language_only(weak, known_typos):
            removed.append(weak)
            continue
        cleaned.append(weak)

    if removed:
        evaluation.weak_spots = cleaned or [
            "No major content weak spot after separating typo-only language noise from technical evaluation."
        ]
        language_noise.append(
            {
                "question_id": "evaluation_guard",
                "removed_from_content_weak_spots": removed,
                "policy": "Removed because these were typo/language issues, not ML understanding gaps.",
            }
        )

    return evaluation, language_noise
