from __future__ import annotations

import re
from collections import Counter
from typing import Any, Dict, List

COMMON_CORRECTIONS = {
    "calulcated": "calculated",
    "caluculated": "calculated",
    "calculte": "calculate",
    "calculatd": "calculated",
    "suseptible": "susceptible",
    "susceptable": "susceptible",
    "insensical": "nonsensical",
    "nonsencial": "nonsensical",
    "incoorect": "incorrect",
    "incorect": "incorrect",
    "predicitons": "predictions",
    "prediciton": "prediction",
    "collumn": "column",
    "collumns": "columns",
    "lable": "label",
    "lables": "labels",
    "therby": "thereby",
    "unkown": "unknown",
    "unnown": "unknown",
    "sequnetial": "sequential",
    "predifined": "predefined",
    "definintion": "definition",
    "explanantion": "explanation",
    "applciable": "applicable",
    "grammer": "grammar",
    "verift": "verify",
    "normlization": "normalization",
    "standarization": "standardization",
    "standarisation": "standardization",
    "minumum": "minimum",
    "maxium": "maximum",
    "tranform": "transform",
    "tranformed": "transformed",
    "fittted": "fitted",
    "seperate": "separate",
    "occured": "occurred",
    "recieve": "receive",
    "acheive": "achieve",
    "wich": "which",
    "becuase": "because",
    "teh": "the",
    "hte": "the",
    "alot": "a lot",
}

GENERIC_FILLER_PHRASES = [
    "model fails in production",
    "fails to generalize",
    "leads to incorrect predictions",
    "better model outcome",
    "properly set",
    "balance between",
    "important in production",
    "monitoring mechanism",
]

TECHNICAL_PRECISION_HINTS = [
    {
        "pattern": r"\bnormalization\b.*\bmean\s*0\b|\bnormalization\b.*\bstandard deviation\s*1\b",
        "hint": "Use precise wording: if you mean mean=0/std=1, call it z-score standardization. If you mean range 0-1, call it min-max scaling.",
    },
    {
        "pattern": r"x\s*-\s*min\s*/\s*max\s*-\s*min",
        "hint": "Formula clarity: write min-max scaling as (x - min) / (max - min). Parentheses matter.",
    },
    {
        "pattern": r"sqrt\s*\(|sum\s*\(\s*x\s*-\s*mean",
        "hint": "Formula clarity: z-score standardization is z = (x - mean) / standard_deviation. Do not use the standard-deviation formula as the transformation formula.",
    },
    {
        "pattern": r"fit[- ]?transform(ed)?\s+on\s+.*entire dataset|fit[- ]?transformed\s+on\s+.*test",
        "hint": "Fit/transform clarity: say the scaler/transformer was fitted on full data. The prevention is train-only fit, then transform validation/test/production.",
    },
]


def _words(text: str) -> List[str]:
    return re.findall(r"[A-Za-z][A-Za-z_'-]*", text or "")


def _sentence_count(text: str) -> int:
    return len([s for s in re.split(r"[.!?]+", text or "") if s.strip()])


def _spelling_suggestions(text: str) -> List[Dict[str, str]]:
    seen = set()
    suggestions: List[Dict[str, str]] = []
    for raw in _words(text):
        key = raw.lower().strip("_'-")
        if key in COMMON_CORRECTIONS and key not in seen:
            seen.add(key)
            suggestions.append({"original": raw, "suggestion": COMMON_CORRECTIONS[key]})
    return suggestions[:8]


def _repeated_phrases(text: str) -> List[str]:
    normalized = re.sub(r"\s+", " ", (text or "").lower())
    hits = [phrase for phrase in GENERIC_FILLER_PHRASES if normalized.count(phrase) >= 2]
    return hits[:5]


def _technical_hints(text: str) -> List[str]:
    hints: List[str] = []
    for item in TECHNICAL_PRECISION_HINTS:
        if re.search(item["pattern"], text or "", flags=re.IGNORECASE):
            hints.append(item["hint"])
    return hints[:4]


def analyze_answer_text(answer_text: str, question_type: str | None = None) -> Dict[str, Any]:
    text = answer_text or ""
    words = len(text.split())
    sentences = _sentence_count(text)
    spelling = _spelling_suggestions(text)
    repeated = _repeated_phrases(text)
    technical_hints = _technical_hints(text)

    target_min = 80
    target_max = 140
    if question_type == "tiny_hands_on":
        target_min = 60
        target_max = 160
    elif question_type == "teachback":
        target_min = 70
        target_max = 130

    length_status = "empty"
    length_hint = "Start with the answer frame: definition, example, risk, control."
    if words:
        if words < target_min:
            length_status = "thin"
            length_hint = "Likely thin. Add the concrete example, mechanism, or control being asked for."
        elif words <= target_max:
            length_status = "good"
            length_hint = "Good length. Make sure every sentence contributes to the mission."
        elif words <= target_max + 40:
            length_status = "long"
            length_hint = "A bit long. Cut repeated definitions and keep the mechanism/control."
        else:
            length_status = "essay"
            length_hint = "Too long. You are probably overexplaining the easy part and under-specifying the hard part."

    return {
        "word_count": words,
        "sentence_count": sentences,
        "target_min": target_min,
        "target_max": target_max,
        "length_status": length_status,
        "length_hint": length_hint,
        "spelling_suggestions": spelling,
        "repeated_phrases": repeated,
        "technical_precision_hints": technical_hints,
        "has_language_noise": bool(spelling or repeated or technical_hints or length_status in {"long", "essay"}),
        "policy": "Writing assist corrects language noise and precision hints only. It must not add new technical content or answer the mission for the learner.",
    }
