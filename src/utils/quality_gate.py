from __future__ import annotations

import re
from typing import Dict, List


VAGUE_PATTERNS = [
    r"\breal-world complexities\b",
    r"\breal-world scenarios\b",
    r"\bunderlying truth\b",
    r"\bunderlying truths\b",
    r"\bunderlying rules\b",
    r"\bcostly mistakes\b",
    r"\bcritical deployment errors\b",
    r"\bimportant\b",
    r"\bcrucial\b",
    r"\bflawed deployment strategies\b",
    r"\bbetter monitoring systems\b",
    r"\bcorrelations, not causations\b",
    r"\bsignificance or context\b",
    r"\bpoor monitoring and decision-making\b",
    r"\bineffective evaluation strategies\b",
]

WEAK_EXAMPLE_PATTERNS = [
    r"\bcats? vs dogs?\b",
    r"\bphotos? of cats? and dogs?\b",
]

MIN_LENGTH_FIELDS = {
    "simple_explanation": 80,
    "why_it_matters": 60,
    "edge_case": 60,
}

REQUIRED_ARCHITECT_TERMS = {
    "why_it_matters": ["evaluation", "monitor", "deploy", "design", "production", "drift"],
    "edge_case": ["fail", "break", "drift", "wrong", "unseen", "distribution", "production"],
}

class QualityGateError(Exception):
    """Raised when note quality is unacceptable."""


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


def _find_pattern_hits(text: str, patterns: List[str]) -> List[str]:
    hits = []
    normalized = _normalize(text)
    for pattern in patterns:
        if re.search(pattern, normalized):
            hits.append(pattern)
    return hits


def check_teacher_note_quality(note: Dict) -> Dict:
    problems: List[str] = []

    required_fields = [
        "topic_id",
        "title",
        "simple_explanation",
        "wrong_mental_model",
        "correct_mental_model",
        "tiny_example",
        "why_it_matters",
        "edge_case",
        "three_takeaways",
    ]

    for field in required_fields:
        if field not in note:
            problems.append(f"Missing field: {field}")

    if problems:
        return {"decision": "reject", "problems": problems}

    combined_text = " ".join(
        [
            str(note.get("simple_explanation", "")),
            str(note.get("wrong_mental_model", "")),
            str(note.get("correct_mental_model", "")),
            str(note.get("tiny_example", "")),
            str(note.get("why_it_matters", "")),
            str(note.get("edge_case", "")),
            " ".join(note.get("three_takeaways", [])),
        ]
    )

    vague_hits = _find_pattern_hits(combined_text, VAGUE_PATTERNS)
    weak_example_hits = _find_pattern_hits(combined_text, WEAK_EXAMPLE_PATTERNS)

    for hit in vague_hits:
        problems.append(f"Contains vague or banned phrase pattern: {hit}")

    for hit in weak_example_hits:
        problems.append(f"Contains weak stock example pattern: {hit}")

    for field, min_len in MIN_LENGTH_FIELDS.items():
        value = str(note.get(field, "")).strip()
        if len(value) < min_len:
            problems.append(
                f"Field '{field}' is too short to be useful. Minimum {min_len} characters."
            )

    for field_name, required_terms in REQUIRED_ARCHITECT_TERMS.items():
        field_text = _normalize(str(note.get(field_name, "")))
        if not any(term in field_text for term in required_terms):
            problems.append(
                f"Field '{field_name}' does not contain a strong enough system or failure anchor."
            )

    takeaways = note.get("three_takeaways", [])
    if not isinstance(takeaways, list) or len(takeaways) != 3:
        problems.append("Field 'three_takeaways' must contain exactly 3 items.")

    takeaway_text = " ".join(note.get("three_takeaways", []))
    takeaway_hits = _find_pattern_hits(takeaway_text, VAGUE_PATTERNS)
    for hit in takeaway_hits:
        problems.append(f"Three takeaways contain vague or banned phrase pattern: {hit}")

    decision = "pass" if not problems else "reject"
    return {"decision": decision, "problems": problems}