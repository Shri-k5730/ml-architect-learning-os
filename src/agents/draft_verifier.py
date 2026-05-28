from __future__ import annotations

import re
from typing import Any, Dict, List

from src.agents.topic_coaching_profiles import get_topic_coaching_profile
from src.agents.writing_assist import analyze_answer_text
from src.schemas import ArchitectNote, Assessment, ConceptNote
from src.blueprints.learning_design import get_bundled_learning_design, runtime_task_for_question
from src.utils.supabase_store import fetch_topic_learning_design


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip().lower())


def _contains_any(answer_l: str, tokens: List[str]) -> bool:
    return any(str(token).lower() in answer_l for token in tokens if str(token).strip())


SEMANTIC_COVERAGE: Dict[str, List[str]] = {
    # generic rubric phrases that learners often satisfy without exact wording
    "where/why errors": ["where", "why", "failure pocket", "error pattern", "wrong", "mistake", "slices mistakes", "supplier", "shift", "defect type"],
    "average metric limitation": ["hide", "overall", "average", "92%", "80%", "accuracy", "one supplier", "one shift", "one defect"],
    "segment slicing": ["slice", "supplier", "shift", "plant", "station", "product", "defect type", "feature range", "confidence band", "segment"],
    "evidence": ["inspect", "compare", "confusion matrix", "false negative", "feature distribution", "missing", "label", "sensor", "process", "evidence"],
    "data/process/label shift": ["process", "material", "measurement", "missing feature", "label", "training", "represented", "feature distribution", "supplier process"],
    "checks": ["inspect", "check", "compare", "review", "audit", "confusion matrix", "missing-value", "distribution"],
    "logged predictions": ["log every prediction", "timestamp", "model score", "prediction", "actual label", "confidence", "plant", "line", "station"],
    "simple explanation": ["like", "explain", "first", "model is wrong", "replacing", "checking", "defect", "where"],
    "targeted fix": ["targeted", "right action", "better data", "threshold change", "feature improvement", "retraining", "choose the right action", "fix backlog"],
    "business efficiency": ["business", "efficient", "waste", "without checking", "will not fix", "quality", "supplier-specific", "review"],
    "score-to-action": ["score", "action", "decision", "threshold", "decision point", "business policy"],
    "missed defects vs extra checks": ["missed defect", "extra inspection", "false negative", "false positive", "inspection", "business loss"],
    "owner": ["owner", "quality owner", "ml owner", "review", "approval", "responsible"],
    "monitoring": ["monitor", "dashboard", "track", "trigger", "alert", "weekly", "monthly"],
    "minority-class failure": ["minority", "defect", "recall", "false negative", "accuracy", "escape", "warranty"],
    "interpretation": ["bad model", "despite high accuracy", "0 recall", "catches none", "quality", "business loss"],
    "model behavior": ["model behavior", "model leaned", "model relied", "feature influenced", "prediction", "global", "local", "importance"],
    "not causal proof": ["not causal", "not causality", "does not prove", "not proof", "clue", "correlation", "not cause"],
    "stakeholder risk": ["stakeholder", "misread", "misinterpret", "process change", "business action", "unsafe action", "trust"],
    "clue not proof": ["clue", "not proof", "does not prove", "investigate", "validate", "evidence", "domain review"],
    "domain review": ["domain", "review", "process owner", "quality", "expert", "manufacturing", "approval"],
    "validation": ["validate", "validation", "experiment", "check", "inspect", "evidence", "data slice", "process evidence"],
    "causality trap": ["causality", "causal", "cause", "correlation", "wrongly changed", "trap", "convincing chart"],
    "missing validation": ["without validation", "missing validation", "did not validate", "no experiment", "no review", "domain review"],
    "governance failure": ["governance", "approval", "audit", "review path", "policy", "owner", "process action"],
    "global/local": ["global", "local", "overall model", "one prediction", "individual prediction"],
    "audit trail": ["audit", "stored", "logged", "trace", "record", "explanation history"],
    "approval path": ["approval", "approve", "sign-off", "review path", "owner", "domain review"],
    "limits": ["limit", "cannot prove", "does not prove", "not causal", "not correct", "not safe"],
    "safe use": ["safe", "clue", "investigate", "validate", "review", "caveat", "approval"],
    "deployment boundary": ["deployment", "production", "future", "new line", "unseen", "boundary"],
    "time or group leakage": ["time", "temporal", "future", "group", "machine", "line", "asset", "leak"],
    "group leakage": ["group", "machine", "line", "asset", "entity", "overlap", "leak"],
    "honest validation": ["honest", "valid", "validation", "realistic", "holdout", "test"],
    "time cutoff": ["time", "temporal", "future", "month", "cutoff"],
    "line grouping": ["line", "group", "plant", "machine", "asset"],
    "split policy": ["split", "holdout", "fold", "time", "group", "policy"],
    "test-set isolation": ["test", "locked", "untouched", "isolate", "final"],
    "approval evidence": ["approval", "evidence", "report", "record", "audit"],
    "trustworthy estimate": ["trust", "honest", "estimate", "realistic", "valid"],
    "selection overfitting": ["overfit", "selection", "trial", "search", "validation"],
    "locked test": ["locked", "untouched", "final test", "holdout", "test set"],
    "search discipline": ["budget", "search", "trial", "registry", "record"],
    "trial evidence": ["trial", "experiment", "registry", "record", "evidence"],
    "operating point": ["threshold", "operating point", "decision", "score"],
    "alert workload": ["alert", "inspection", "workload", "capacity", "false positive"],
    "threshold selection": ["threshold", "select", "recall", "precision", "cost"],
    "operational adoption": ["operator", "operations", "use", "adoption", "alert"],
    "calibration": ["calibrat", "probability", "observed", "brier", "reliability"],
    "probability caution": ["probability", "confidence", "calibrat", "observed", "risk score"],
    "calibration drift": ["calibrat", "drift", "supplier", "population", "shift"],
    "holdout": ["holdout", "validation", "test", "unseen", "locked"],
    "three distinctions": ["input", "label", "sample", "quality", "bias"],
    "label quality": ["label", "annotat", "inspector", "disagree", "agreement"],
    "sampling bias": ["sample", "sampling", "selection", "coverage", "represented", "bias"],
    "coverage gap": ["coverage", "underrepresent", "supplier", "segment", "missing"],
    "label protocol": ["label", "protocol", "audit", "inspector", "agreement"],
    "release gate": ["gate", "release", "approve", "block", "validation"],
    "integrated reasoning": ["validation", "threshold", "calibrat", "quality", "monitor", "decision"],
    "decision evidence": ["decision", "evidence", "approve", "reject", "condition"],
    "rare-event evidence": ["rare", "defect", "precision", "recall", "pr-auc", "alert"],
    "evidence pack": ["evidence", "report", "record", "model card", "plan", "pack"],
    "triggers": ["trigger", "threshold", "alert", "breach", "drift"],
    "fallback": ["fallback", "manual", "review", "escalat", "stop"],
    "problem framing": ["problem", "target", "scope", "prediction", "cost"],
    "target timing": ["target", "timing", "prediction", "before", "available"],
    "cost of errors": ["cost", "false negative", "false positive", "missed", "alert"],
    "data profile": ["data", "profile", "missing", "quality", "distribution"],
    "metrics": ["metric", "precision", "recall", "auc", "f1"],
    "segments": ["segment", "supplier", "shift", "plant", "line", "defect"],
    "release block": ["block", "reject", "release", "stop", "gate"],
    "retraining": ["retrain", "trigger", "validation", "release"],
    "recommendation": ["recommend", "approve", "reject", "deploy", "conditional"],
    "model card": ["model card", "model", "limitation", "metric", "scope"],
    "adr": ["adr", "architecture decision", "decision record", "rationale"],
}


def _meaningful_words(text: str) -> List[str]:
    return [
        word.strip(".,;:()[]{}!?\"'").lower()
        for word in (text or "").split()
        if len(word.strip(".,;:()[]{}!?\"'").lower()) > 4
    ]


def _focus_is_covered(focus: str, answer_l: str) -> bool:
    focus_l = _normalize(focus)
    if not focus_l:
        return True
    if focus_l in answer_l:
        return True
    for key, tokens in SEMANTIC_COVERAGE.items():
        if key in focus_l and _contains_any(answer_l, tokens):
            return True
    words = _meaningful_words(focus_l)
    if not words:
        return True
    hits = sum(1 for word in words if word in answer_l)
    required = 1 if len(words) <= 2 else 2
    return hits >= required


def _coverage_gap(expected_focus: List[str], answer: str) -> List[str]:
    answer_l = _normalize(answer)
    gaps: List[str] = []
    for focus in expected_focus or []:
        if not _focus_is_covered(str(focus), answer_l):
            gaps.append(str(focus))
    return gaps[:3]


def _profile_gap(topic_id: str, answer: str) -> List[Dict[str, str]]:
    answer_l = _normalize(answer)
    profile = get_topic_coaching_profile(topic_id)
    findings: List[Dict[str, str]] = []

    for item in profile.get("common_misconceptions", []) or []:
        patterns = item.get("pattern", [])
        if isinstance(patterns, str):
            patterns = [patterns]
        for pattern in patterns:
            if pattern and pattern.lower() in answer_l:
                findings.append(
                    {
                        "evidence": pattern,
                        "issue": str(item.get("issue", "Potential misconception detected.")),
                        "correction": str(item.get("correction", "Tighten the concept before final evaluation.")),
                    }
                )
                break
    return findings[:2]


def _contract_findings(topic_id: str, question_id: str, answer: str) -> List[Dict[str, str]]:
    """Detect unsafe inferences explicitly taught in the lesson contract."""
    answer_l = _normalize(answer)
    findings: List[Dict[str, str]] = []
    if topic_id == "mlf_019" and question_id == "q2":
        unsafe_feature_claim = any(
            phrase in answer_l
            for phrase in [
                "should be available in the feature set",
                "should be available in production",
                "must be available in production",
                "retain humidity",
                "keep humidity",
            ]
        )
        if unsafe_feature_claim:
            findings.append({
                "evidence": "humidity feature should be available in production",
                "issue": "High feature importance does not by itself justify requiring humidity in production.",
                "correction": "Conclude only that the model relied on humidity. Before retaining or acting on it, check inference-time availability, leakage, proxy risk, segment stability and domain evidence.",
                "severity": "blocking",
            })
    if topic_id == "mlf_019" and question_id == "q4" and "global explanation on the overall model performance" in answer_l:
        findings.append({
            "evidence": "global explanation on the overall model performance",
            "issue": "A global explanation summarises aggregate model behaviour; it is not a model-performance metric.",
            "correction": "Separate behaviour explanation from performance monitoring metrics such as recall, precision or error slices.",
            "severity": "blocking",
        })
    return findings


def _contract_requirement_gaps(topic_id: str, question_id: str, answer: str) -> List[str]:
    """Check only requirements shown to the learner in the visible authored contract."""
    answer_l = _normalize(answer)
    gaps: List[str] = []
    if topic_id == "mlf_019" and question_id == "q4":
        if not ("model version" in answer_l and sum(1 for token in ["timestamp", "data slice", "input context", "prediction", "reviewer", "decision"] if token in answer_l) >= 2):
            gaps.append("The taught audit trail needs stored decision context: model version, input/data slice, prediction, explanation, reviewer and decision.")
        if not (any(token in answer_l for token in ["ml owner", "quality", "process owner", "process lead"]) and any(token in answer_l for token in ["approve", "approval", "sign-off"])):
            gaps.append("The taught governance chain needs named ML/quality/process ownership and approval before process action.")
    return gaps[:2]


def _type_gap(question_type: str, answer: str, question: str = "") -> List[str]:
    answer_l = _normalize(answer)
    gaps: List[str] = []
    word_count = len(answer.split())

    if word_count > 190:
        gaps.append("Too long. Cut repeated definitions and keep the answer to mechanism, evidence, and control.")
    elif word_count > 155 and question_type in {"teachback", "concept_check"}:
        gaps.append("Tighten the answer. This question needs clarity, not an essay.")

    if question_type == "tiny_hands_on":
        question_l = _normalize(question)
        numeric_task = any(ch.isdigit() for ch in question_l) or any(token in question_l for token in ["calculate", "precision", "recall", "threshold", "score", "auc"])
        if numeric_task:
            if not any(token in answer_l for token in ["metric", "precision", "recall", "confusion", "calculate", "compare", "inspect", "false negative", "feature distribution", "segment"]):
                gaps.append("Use the number or scenario first, then interpret it.")
        elif not any(token in answer_l for token in ["conclude", "does not", "not mean", "not proof", "validate", "inspect", "check", "review", "evidence"]):
            gaps.append("State the valid conclusion, the invalid conclusion, and the safe next validation action.")
    if question_type == "failure_diagnosis":
        if not any(token in answer_l for token in ["cause", "because", "mechanism", "evidence", "inspect", "check", "distribution", "label", "feature", "threshold", "segment"]):
            gaps.append("Separate symptom, likely cause, evidence to inspect, and prevention.")
    if question_type == "architect_decision":
        has_control = any(token in answer_l for token in ["monitor", "threshold", "fallback", "alert", "validation", "owner", "trigger", "dashboard", "audit", "review"])
        if not has_control:
            gaps.append("Name the concrete controls, owner, trigger, or review path you would design into the system.")
    if question_type == "teachback":
        if len(answer.split()) > 150:
            gaps.append("Shorten the explanation. Stakeholder teachback should be clear, not exhaustive.")
        if not any(token in answer_l for token in ["like", "example", "manufacturing", "defect", "quality", "business", "supplier", "shift"]):
            gaps.append("Anchor the explanation in a simple analogy or business example.")

    return gaps[:3]


def _serious_technical_hints(writing_assist: Dict[str, Any]) -> List[str]:
    hints = writing_assist.get("technical_precision_hints", []) or []
    # These are concept precision risks, not spelling. Keep them separate from language noise.
    return [str(hint) for hint in hints if str(hint).strip()][:3]


def _readiness_score(answer: str, gap_count: int, misconception_count: int, serious_hint_count: int, blocking_count: int = 0) -> int:
    word_count = len((answer or "").split())
    if word_count < 20:
        return 1
    if blocking_count:
        return 3 if word_count >= 40 else 2
    if misconception_count >= 2 or serious_hint_count >= 2:
        return 2
    if misconception_count == 1:
        return 3
    if gap_count >= 3:
        return 2
    if gap_count == 2:
        return 3
    if gap_count == 1:
        return 4 if word_count >= 60 and serious_hint_count == 0 else 3
    return 4


def _verdict(score: int) -> str:
    if score <= 2:
        return "Weak draft"
    if score == 3:
        return "Partial draft"
    return "Submit-ready draft"


def _next_action(question_type: str, gaps: List[str], misconceptions: List[Dict[str, str]], serious_hints: List[str]) -> str:
    if serious_hints:
        return serious_hints[0]
    if misconceptions:
        return misconceptions[0]["correction"]
    if gaps:
        return gaps[0]
    if question_type == "architect_decision":
        return "To push from 4 to 5, add owner, trigger threshold, review cadence, and operational action."
    if question_type == "tiny_hands_on":
        return "To push from 4 to 5, add the concrete interpretation and the decision implication."
    if question_type == "teachback":
        return "To push from 4 to 5, add a simple analogy plus one business consequence."
    return "Submit-ready. To push higher, add one sharper mechanism or control."


def verify_draft_answers(
    concept_note: ConceptNote,
    architect_note: ArchitectNote,
    assessment: Assessment,
    answers_doc: Dict[str, Any],
) -> Dict[str, Any]:
    """Copy-safe draft verification calibrated against final-evaluation behavior.

    This verifier is semantic, not keyword-only. It should not call a strong answer weak
    merely because the answer used different wording from expected_focus.
    """
    by_question = {item.get("question_id"): item for item in answers_doc.get("answers", [])}
    items: List[Dict[str, Any]] = []
    profile = get_topic_coaching_profile(concept_note.topic_id)
    learning_design = fetch_topic_learning_design(concept_note.topic_id) or get_bundled_learning_design(concept_note.topic_id)

    for question in assessment.questions:
        answer = str(by_question.get(question.question_id, {}).get("answer", "")).strip()
        task_meta = runtime_task_for_question(learning_design, question.question_id, question.question) if learning_design else None
        if learning_design:
            # Patch 040: draft checking is a technical guardrail, not a keyword/star predictor.
            expected_gaps = ["Provide a response for this evidence task."] if not answer else []
            type_gaps = []
            contract_gaps = []
        else:
            expected_gaps = _coverage_gap(question.expected_focus, answer)
            type_gaps = _type_gap(question.type, answer, question.question)
            contract_gaps = _contract_requirement_gaps(concept_note.topic_id, question.question_id, answer)
        concept_findings = [*_profile_gap(concept_note.topic_id, answer), *_contract_findings(concept_note.topic_id, question.question_id, answer)]
        writing_assist = analyze_answer_text(answer, question.type)
        serious_hints = _serious_technical_hints(writing_assist)

        all_gaps: List[str] = []
        for gap in [*expected_gaps, *type_gaps, *contract_gaps]:
            if gap not in all_gaps:
                all_gaps.append(gap)

        # Do not count spelling suggestions as readiness blockers. They are language noise.
        blocking_count = sum(1 for finding in concept_findings if finding.get("severity") == "blocking")
        score = _readiness_score(answer, len(all_gaps), len(concept_findings), len(serious_hints), blocking_count)
        items.append(
            {
                "question_id": question.question_id,
                "question": question.question,
                "question_type": question.type,
                "verdict": _verdict(score),
                "readiness_score": score,
                "likely_score": score,
                "coverage_gaps": all_gaps[:4],
                "misconceptions": concept_findings,
                "technical_precision_hints": serious_hints,
                "writing_assist": writing_assist,
                "language_noise_note": (
                    "Language noise detected. Clean it if possible, but it should not be treated as a concept gap."
                    if writing_assist.get("spelling_suggestions") else ""
                ),
                "next_improvement": _next_action(question.type, all_gaps, concept_findings, serious_hints),
                "copy_safe": True,
                "evidence_task": task_meta or {},
            }
        )

    weak_items = [item for item in items if item["readiness_score"] <= 2]
    partial_items = [item for item in items if item["readiness_score"] == 3]
    submit_ready_items = [item for item in items if item["readiness_score"] >= 4]
    readiness_avg = round(sum(item["readiness_score"] for item in items) / len(items), 2) if items else 0
    four_star_ready = (not weak_items and len(submit_ready_items) >= max(3, len(items) - 1) and readiness_avg >= 3.6)

    if weak_items:
        recommendation = "Do not submit yet. Fix empty responses or flagged technical/unsafe claims first."
    elif learning_design:
        recommendation = "No blocking technical issue detected by the draft guardrail. Final evaluation will judge whether your reasoning demonstrates each evidence task."
    elif four_star_ready:
        recommendation = "Submit-ready for a strong attempt. Final evaluation may still be stricter."
    elif partial_items:
        recommendation = "Borderline submit-ready. Improve the partial drafts if you want a stronger score."
    else:
        recommendation = "Evaluable. Final evaluation checks cross-answer consistency and may still be stricter."

    return {
        "topic_id": concept_note.topic_id,
        "topic_title": concept_note.title,
        "mode": "evidence_guardrail_no_keyword_scoring_v3" if learning_design else "draft_verification_semantic_calibrated_v2",
        "summary": {
            "readiness_average": readiness_avg,
            "likely_average": readiness_avg,
            "weak_count": len(weak_items),
            "partial_count": len(partial_items),
            "submit_ready_count": len(submit_ready_items),
            "four_star_ready": four_star_ready,
            "recommendation": recommendation,
        },
        "core_concepts_to_check": profile.get("core_concepts", [])[:5],
        "items": items,
        "note": "For upgraded topic designs, Verify Draft is a technical guardrail only: it catches empty or unsafe/incorrect claims and does not predict stars from keyword presence. Final evaluation judges reasoning against the published evidence task.",
    }
