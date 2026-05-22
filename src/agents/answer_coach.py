from __future__ import annotations

import re
from typing import Any, Callable, Dict, List

from src.agents.topic_coaching_profiles import (
    get_topic_coaching_profile,
    profile_golden_answer,
)
from src.blueprints.advanced_ml import get_blueprint
from src.schemas import (
    ArchitectNote,
    Assessment,
    ConceptNote,
    EvaluationResult,
    UserAnswer,
)


class AnswerCoachError(Exception):
    """Raised when answer coaching generation fails."""


def _answer_map(user_answers: List[UserAnswer]) -> Dict[str, str]:
    return {answer.question_id: answer.answer for answer in user_answers}


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip().lower())


def _meaningful_words(text: str) -> List[str]:
    return [
        word.strip(".,;:()[]{}!?\"'").lower()
        for word in (text or "").split()
        if len(word.strip(".,;:()[]{}!?\"'").lower()) > 4
    ]



SEMANTIC_COVERAGE: Dict[str, List[str]] = {
    "where/why errors": ["where", "why", "failure pocket", "error pattern", "wrong", "mistake", "slices mistakes", "supplier", "shift", "defect type"],
    "average metric limitation": ["hide", "overall", "average", "accuracy", "one supplier", "one shift", "one defect", "fail badly"],
    "segment slicing": ["slice", "supplier", "shift", "plant", "station", "product", "defect type", "feature range", "confidence band", "segment"],
    "evidence": ["inspect", "compare", "confusion matrix", "false negative", "feature distribution", "missing", "label", "sensor", "process", "evidence"],
    "data/process/label shift": ["process", "material", "measurement", "missing feature", "label", "training", "represented", "feature distribution", "supplier process"],
    "checks": ["inspect", "check", "compare", "review", "audit", "confusion matrix", "missing-value", "distribution"],
    "logged predictions": ["log every prediction", "timestamp", "model score", "prediction", "actual label", "confidence", "plant", "line", "station"],
    "simple explanation": ["like", "explain", "replacing", "checking", "defect", "where", "first", "model is wrong"],
    "targeted fix": ["targeted", "right action", "better data", "threshold change", "feature improvement", "retraining", "fix backlog"],
    "business efficiency": ["business", "efficient", "waste", "will not fix", "quality", "without checking", "supplier-specific"],
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


def _contains_any(answer_l: str, tokens: List[str]) -> bool:
    return any(str(token).lower() in answer_l for token in tokens if str(token).strip())


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


def _mentions_question(evaluation: EvaluationResult, question_id: str) -> bool:
    weak_text = " ".join(evaluation.weak_spots or []).lower()
    patterns = [question_id.lower(), question_id.lower().replace("q", "question ")]
    return any(pattern in weak_text for pattern in patterns)


def _expected_focus_gaps(expected_focus: List[str], answer: str) -> List[str]:
    answer_l = _normalize(answer)
    gaps: List[str] = []
    for focus in expected_focus or []:
        if not _focus_is_covered(str(focus), answer_l):
            gaps.append(str(focus))
    return gaps[:3]


def _topic_misconceptions(topic_id: str, answer: str) -> List[Dict[str, str]]:
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

    return findings[:3]


def _type_specific_gaps(question_type: str, answer: str, question: str = "", topic_id: str = "") -> List[str]:
    answer_l = _normalize(answer)
    question_l = _normalize(question)
    gaps: List[str] = []

    if question_type == "tiny_hands_on":
        numeric_task = any(ch.isdigit() for ch in question_l) or any(token in question_l for token in ["calculate", "precision", "recall", "threshold", "score", "auc"])
        if numeric_task and not any(token in answer_l for token in ["compare", "calculate", "metric", "rmse", "mae", "r2", "r²", "precision", "recall", "confusion", "train", "validation"]):
            gaps.append("Use the provided value or calculation, then state the decision implication.")
        elif not numeric_task and not any(token in answer_l for token in ["conclude", "does not", "not mean", "not proof", "validate", "inspect", "check", "review", "evidence"]):
            gaps.append("State the valid conclusion, invalid conclusion, and validation action for this scenario.")
    elif question_type == "failure_diagnosis":
        if not any(token in answer_l for token in ["cause", "because", "mechanism", "feature", "pipeline", "training", "distribution", "drift", "underfit", "overfit"]):
            gaps.append("Name the failure mechanism, not only the symptom.")
    elif question_type == "architect_decision":
        if topic_id != "mlf_019" and not any(token in answer_l for token in ["monitor", "threshold", "fallback", "alert", "validation", "drift", "guardrail", "trigger", "owner"]):
            gaps.append("Name concrete controls such as monitoring, thresholds, fallback, validation gates, or retraining triggers.")
    elif question_type == "teachback":
        if not any(token in answer_l for token in ["manufacturing", "defect", "quality", "line", "stakeholder", "business", "production"]):
            gaps.append("Anchor the explanation in a business or production example.")

    return gaps[:2]


def _score_floor(evaluation: EvaluationResult) -> int:
    scores = evaluation.scores
    return min(
        int(scores.conceptual_clarity or 0),
        int(scores.practical_reasoning or 0),
        int(scores.architect_reasoning or 0),
        int(scores.communication or 0),
    )


def _question_quality(
    question_id: str,
    answer: str,
    expected_gaps: List[str],
    misconception_hits: List[Dict[str, str]],
    evaluation: EvaluationResult,
) -> str:
    """Align question label with final score quality.

    If the final evaluator gave all dimensions 4+, the coaching layer must not
    label normal answers WEAK merely because exact expected-focus words differ.
    """
    answer_len = len((answer or "").strip())
    floor = _score_floor(evaluation)
    if answer_len < 30:
        return "weak"
    if misconception_hits:
        return "partial" if floor >= 4 else "weak"
    if floor >= 4:
        if len(expected_gaps) >= 3:
            return "partial"
        return "strong"
    if _mentions_question(evaluation, question_id):
        return "partial"
    if len(expected_gaps) >= 3:
        return "weak"
    if expected_gaps:
        return "partial"
    return "strong"




def _exact_topic_findings(topic_id: str, question_id: str, question_type: str, answer: str) -> tuple[List[str], List[Dict[str, str]]]:
    """Deterministic precision feedback for known recurring mistakes.

    This prevents lazy coaching such as "add a concrete control" when the actual issue is
    a wrong formula, an imprecise term, or a missing fit/transform boundary.
    """
    answer_l = _normalize(answer)
    missing: List[str] = []
    findings: List[Dict[str, str]] = []

    def add(evidence: str, issue: str, correction: str) -> None:
        missing.append(issue)
        findings.append({"evidence": evidence, "issue": issue, "correction": correction})

    if topic_id == "mlf_014":
        if question_id == "q2" or question_type == "tiny_hands_on":
            if "sqrt" in answer_l or "sum(x-mean" in answer_l or "sum (x-mean" in answer_l:
                add(
                    "standardization formula",
                    "The z-score transformation formula is written incorrectly, even if your final values are close.",
                    "Use z = (x - mean) / standard_deviation. The square-root expression is for calculating standard deviation, not transforming each value.",
                )
            if "x-min/max-min" in answer_l or "x - min/max" in answer_l:
                add(
                    "min-max formula",
                    "The min-max formula needs parentheses to avoid ambiguity.",
                    "Write min-max scaling as (x - min) / (max - min).",
                )
        if question_id == "q3" or question_type == "failure_diagnosis":
            if "overfit" in answer_l and "parameter" not in answer_l:
                add(
                    "overfits the model",
                    "The leakage mechanism is preprocessing-parameter contamination, not only generic overfitting.",
                    "Say the scaler learned min/max/mean/std from test data, so evaluation was contaminated before production.",
                )
            if "fit-transform" in answer_l or "fit transformed" in answer_l or "fit-transformed" in answer_l:
                add(
                    "fit-transform",
                    "Fit/transform wording is imprecise.",
                    "State the scaler was fitted on full data; validation, test, and production should only be transformed with the train-fitted scaler.",
                )

    if topic_id == "mlf_019":
        if question_id == "q2" or question_type == "tiny_hands_on":
            if any(phrase in answer_l for phrase in ["should be available in the feature set", "should be available in production", "must be available in production", "retain humidity", "keep humidity"]):
                add(
                    "humidity feature should be available in production",
                    "High feature importance does not prove that humidity is a safe or mandatory production feature.",
                    "Conclude only that the model relied on humidity; check availability, leakage, proxy risk, segment stability and domain evidence before retaining or acting on it.",
                )
        if question_id == "q4" or question_type == "architect_decision":
            if "global explanation on the overall model performance" in answer_l:
                add(
                    "global explanation on the overall model performance",
                    "Global explanations describe broad model behaviour, not performance metrics.",
                    "Use global explanations for behaviour review; measure performance separately through recall, precision, calibration or error slices.",
                )
            if not ("model version" in answer_l and sum(1 for token in ["timestamp", "data slice", "input context", "prediction", "reviewer", "decision"] if token in answer_l) >= 2):
                add(
                    "audit trail without stored decision context",
                    "The taught audit trail is incomplete without model/version and decision context.",
                    "State that each explanation decision records model version, input/data slice, prediction, explanation, timestamp, reviewer and resulting decision.",
                )
            if not (any(token in answer_l for token in ["ml owner", "quality", "process owner", "process lead"]) and any(token in answer_l for token in ["approve", "approval", "sign-off"])):
                add(
                    "approval without named owners",
                    "The taught governance chain requires named ML, quality and process ownership before operational action.",
                    "Name who reviews evidence, who approves a process change, and what outcome is monitored after action.",
                )

    return missing[:4], findings[:4]

def _missing_points(
    topic_id: str,
    expected_focus: List[str],
    answer: str,
    question_type: str,
    question_id: str = "",
    question: str = "",
) -> tuple[List[str], List[Dict[str, str]]]:
    missing: List[str] = []

    for gap in _expected_focus_gaps(expected_focus, answer):
        if gap not in missing:
            missing.append(gap)
    for gap in _type_specific_gaps(question_type, answer, question, topic_id):
        if gap not in missing:
            missing.append(gap)

    misconceptions = _topic_misconceptions(topic_id, answer)
    for item in misconceptions:
        issue = item.get("issue", "Potential misconception detected.")
        if issue not in missing:
            missing.append(issue)

    exact_missing, exact_findings = _exact_topic_findings(topic_id, question_id, question_type, answer)
    for issue in exact_missing:
        if issue not in missing:
            missing.append(issue)
    misconceptions.extend(exact_findings)

    return missing[:5], misconceptions[:5]


def _join(items: List[str], limit: int = 4) -> str:
    return "; ".join(str(item) for item in (items or [])[:limit] if str(item).strip())


def _blueprint_by_type(topic_id: str, question_type: str, question: str, expected_focus: List[str]) -> str:
    """Build an actual sample answer from the expert blueprint.

    This intentionally avoids meta-text like "a stronger answer should...". The learner
    needs an example answer after evaluation, not another checklist.
    """
    bp = get_blueprint(topic_id) or {}
    title = bp.get("title", "this concept")
    definition = bp.get("definition", "")
    mechanism = bp.get("core_mechanism", "")
    worked = bp.get("worked_example", "")
    controls = bp.get("system_design_controls", []) or []
    nuances = bp.get("nuances", []) or []
    focus = _join(expected_focus, 4)
    control_text = _join(controls, 5) or "validation evidence, monitoring rule, fallback path, and owner response"

    # Topic-specific concrete examples where generic blueprint text is not enough.
    if topic_id == "mlf_014" and question_type == "tiny_hands_on":
        return (
            "For min-max scaling, use scaled = (x - min) / (max - min). Here min=50 and max=100, so the scaled values are "
            "[0.0, 0.2, 0.4, 0.6, 0.8, 1.0]. For z-score standardization, use z = (x - mean) / std. "
            "With mean=75 and population std about 17.08, the standardized values are approximately "
            "[-1.46, -0.88, -0.29, 0.29, 0.88, 1.46]. The architecture rule is to fit min, max, mean, and std on training data only, then transform validation, test, and production using the saved transformer."
        )
    if topic_id == "mlf_015" and question_type == "concept_check":
        return (
            "Regularization is a complexity penalty added during training so the model does not rely too heavily on noisy or overly specific patterns. "
            "It controls variance by discouraging extreme learned weights. L1 can push some coefficients to zero, while L2 usually shrinks coefficients without removing them completely. "
            "Too little regularization can leave the model overfit; too much can suppress useful signal and cause underfitting. I would choose the strength using validation curves or train-validation gap evidence."
        )
    if topic_id == "mlf_015" and question_type == "architect_decision":
        return (
            "I would treat regularization strength as a governed hyperparameter. First, compare training and validation curves across candidate strengths. "
            "Second, check segment performance so a setting that looks good on average does not miss a defect type or plant. Third, select the value that reduces overfitting without collapsing useful signal. "
            "In production, I would monitor the same business-critical metrics and trigger model review if validation-like behavior degrades after deployment."
        )
    if topic_id == "mlf_016" and question_type == "architect_decision":
        return (
            "I would define threshold governance as a business policy, not a default 0.5 setting. The policy would include a cost matrix for missed defects versus extra inspections, "
            "a minimum defect recall target, an acceptable alert volume, an owner for threshold changes, and a review cadence. I would monitor precision, recall, false negatives, and alert volume by product line or defect type. "
            "If recall drops below target or alert volume exceeds capacity, the owner reviews threshold, fallback inspection, and retraining evidence."
        )
    if topic_id == "mlf_017" and question_type == "tiny_hands_on":
        return (
            "There are 9,800 good parts and 200 defective parts, so total parts = 10,000. If the model predicts every part as good, TN=9,800, FN=200, TP=0, and FP=0. "
            "Accuracy = (TP+TN)/total = 9,800/10,000 = 98%. Defect recall = TP/(TP+FN) = 0/(0+200) = 0%. "
            "This is a bad defect model despite high accuracy because it catches none of the defective parts. I would judge it using minority recall, false negatives, precision, F1, and PR-AUC."
        )
    if topic_id == "mlf_017" and question_type == "architect_decision":
        return (
            "I would treat class imbalance as a metric and decision-control problem. First, define the cost of missed defects versus extra inspections. "
            "Second, validate with confusion matrix, minority recall, precision, F1, PR-AUC, and segment checks by defect type or plant. Third, test controls such as class weights, resampling, and threshold tuning. "
            "In production, monitor minority-class recall and false negatives, with an owner reviewing breaches against the agreed threshold."
        )

    if topic_id == "mlf_018" and question_type == "concept_check":
        return (
            "Error analysis is the process of studying where and why a model is wrong instead of trusting one overall metric. Overall accuracy can hide failure pockets: a defect model may look strong overall but fail for one supplier, shift, station, or defect type. I would slice false positives and false negatives by segment, confidence band, feature range, and label source. The goal is to identify whether the failure is caused by data coverage, label quality, threshold choice, feature drift, or model limitation, then choose a targeted fix."
        )
    if topic_id == "mlf_018" and question_type == "tiny_hands_on":
        return (
            "Overall recall of 80% is not enough because night-shift recall is only 35%, which is a segment-level failure. I would inspect night-shift false negatives first and compare them with day-shift false negatives. The evidence should include confusion matrix slices by shift, feature distributions, missing-value rates, sensor noise, label delay, and process differences. A practical control would be shift-level recall monitoring with a trigger, such as opening a quality review if night-shift recall falls below the agreed threshold."
        )
    if topic_id == "mlf_018" and question_type == "failure_diagnosis":
        return (
            "The symptom is supplier-specific failure, not necessarily full model failure. Possible causes include supplier process change, material difference, measurement shift, label inconsistency, missing supplier-specific features, or weak training coverage for that supplier. I would inspect confusion matrix slices by supplier, supplier-level false negatives, feature distribution changes, missing values, label audit results, and recent supplier process changes. The fix should target the evidence: data enrichment, label correction, feature update, threshold review, or supplier-specific monitoring."
        )
    if topic_id == "mlf_018" and question_type == "architect_decision":
        return (
            "I would design error analysis as a recurring debugging workflow. Log every prediction with timestamp, plant, line, station, supplier, product type, model score, prediction, actual label, and confidence. Build segment dashboards and confusion matrix slices for false positives and false negatives by supplier, shift, defect type, and feature range. Review error samples with ML, quality, and process owners. Repeated patterns become a fix backlog: label audit, data correction, feature change, threshold review, or retraining only when evidence supports it."
        )
    if topic_id == "mlf_018" and question_type == "teachback":
        return (
            "I would explain it like this: changing the algorithm before error analysis is like replacing a machine before checking where defects are coming from. A model may fail mainly for one supplier, one shift, or one defect type. If the cause is bad labels, missing night-shift data, or a supplier process change, a new algorithm may not fix it. Error analysis finds the failure pattern first, then points to the right fix: data repair, feature change, threshold review, or targeted retraining."
        )

    if topic_id == "mlf_019" and question_type == "concept_check":
        return (
            "Interpretability explains model behavior: what features or patterns influenced the model globally or for one prediction. It is not the same as causality. If a defect model shows humidity as important, that means the model relied on humidity, not that humidity caused defects. Humidity may correlate with shift, season, machine setting, supplier batch, or sensor drift. The risk is that stakeholders may treat a convincing chart as proof and change the process incorrectly. I would use explanations as investigation evidence, then validate with domain review, data checks, or experiments."
        )
    if topic_id == "mlf_019" and question_type == "tiny_hands_on":
        return (
            "If humidity is the top feature, I would conclude only that the model used humidity strongly in its prediction logic. I would not conclude that humidity physically causes the defects or that changing humidity will reduce defects. The next step is to inspect correlated variables such as shift, season, machine setting, supplier batch, sensor drift, and label timing. I would ask the quality or process owner to review the explanation and validate it with process evidence or a controlled experiment before approving any operational change."
        )
    if topic_id == "mlf_019" and question_type == "failure_diagnosis":
        return (
            "The team fell into the causality trap. They treated a feature-importance chart as proof of the real-world cause and changed the process without validation. The evidence to inspect includes whether the explanation was global or local, whether humidity was correlated with shift, machine setting, supplier batch, season, or sensor drift, and whether the model had leakage or unstable correlated features. Prevention requires explanation caveats, domain review, audit trail, and an approval path before any process action based on model explanations."
        )
    if topic_id == "mlf_019" and question_type == "architect_decision":
        return (
            "I would design explainability governance as a review workflow, not a charting feature. First, separate global explanations from local explanations and store each explanation with model version, data slice, timestamp, prediction, and user action. Second, add a causality warning on every explanation view. Third, require domain review when explanations conflict with process knowledge or are used to justify process change. Fourth, create an approval path owned by ML, quality, and process leads before operational action. The control is an explanation audit trail plus validation evidence before change."
        )
    if topic_id == "mlf_019" and question_type == "teachback":
        return (
            "I would tell a business stakeholder: a model explanation is like a clue, not a verdict. It can say the model paid attention to humidity when predicting defects, but it cannot prove humidity caused the defects or that changing humidity will fix them. The value is that it helps us ask better questions and investigate faster. The limit is that we still need domain review, data checks, and validation before acting. So explanations improve trust and debugging, but they must not bypass governance."
        )

    if question_type == "concept_check":
        return (
            f"{definition or title}. In practical terms, the mechanism is: {mechanism or focus}. "
            f"The important distinction is not the label of the technique, but how it changes model behavior. A strong answer should connect the concept to {focus or 'the topic-specific risk'} without turning it into generic production-risk language."
        )
    if question_type == "tiny_hands_on":
        return (
            f"Start from the exact numbers or scenario in the question, then apply the mechanism: {mechanism or focus}. "
            f"After the calculation or comparison, state the practical decision. For this topic, the decision should be tied to {focus or control_text}, not to a broad statement that the model may fail."
        )
    if question_type == "failure_diagnosis":
        return (
            f"The symptom should be separated from the cause. The likely mechanism is: {mechanism or focus}. "
            f"Evidence to inspect would include the relevant metrics, pipeline step, or segment behavior. Prevention should use controls such as {control_text}."
        )
    if question_type == "architect_decision":
        return (
            f"I would govern {title} through explicit controls: {control_text}. The decision should be validated with evidence tied to {focus or 'the business-critical metric'}. "
            "A production-ready answer should also name the monitoring signal, threshold or review rule, and owner/action when the rule is breached."
        )
    if question_type == "teachback":
        return (
            f"I would explain it simply: {bp.get('plain_intuition', definition) or definition}. "
            f"For a business example, {worked or 'connect the concept to a concrete defect, inspection, or quality decision'}. "
            "The key message is the business consequence and the control, not the technical vocabulary."
        )

    return (
        f"{definition or title}. Mechanism: {mechanism or focus}. Controls: {control_text}. "
        "Tie the answer to the exact scenario and finish with the production decision."
    )


def _fallback_better_answer(
    topic_id: str,
    question_type: str,
    question: str,
    expected_focus: List[str],
    concept_note: ConceptNote,
    architect_note: ArchitectNote,
) -> str:
    return _blueprint_by_type(topic_id, question_type, question, expected_focus)


def _better_answer(
    topic_id: str,
    question_type: str,
    question: str,
    expected_focus: List[str],
    concept_note: ConceptNote,
    architect_note: ArchitectNote,
) -> str:
    golden = profile_golden_answer(topic_id, question_type)
    if golden:
        return golden
    return _fallback_better_answer(topic_id, question_type, question, expected_focus, concept_note, architect_note)

def _why_better(question_type: str) -> str:
    if question_type == "tiny_hands_on":
        return "It uses observable behavior, metrics, or calculation instead of staying at theory level."
    if question_type == "failure_diagnosis":
        return "It names the likely mechanism and what evidence would confirm it, instead of only describing the symptom."
    if question_type == "architect_decision":
        return "It converts a broad intention into controls that can be implemented, monitored, and owned."
    if question_type == "teachback":
        return "It is simpler, business-facing, and still keeps the production consequence visible."
    return "It defines the concept precisely and connects it to model behavior rather than vague system language."


def _five_star_upgrade(question_type: str, topic_id: str) -> str:
    if topic_id == "mlf_019" and question_type == "tiny_hands_on":
        return "To move from 4 to 5, state the valid conclusion, reject the causal/feature-retention leap, and name reliability, leakage/proxy-risk and domain-validation checks."
    if topic_id == "mlf_019" and question_type == "architect_decision":
        return "To move from 4 to 5, show the taught governance chain: trigger, logged evidence, ML/quality/process owner, approval action, and post-change monitoring."
    if question_type == "architect_decision":
        return "To move from 4 to 5, add owner, review cadence, metric threshold, breach trigger, and operational response."
    if question_type == "failure_diagnosis":
        return "To move from 4 to 5, add the exact evidence you would inspect and how each evidence path changes the fix."
    if question_type == "tiny_hands_on":
        return "To move from 4 to 5, connect the number or segment comparison to a concrete decision trigger."
    if question_type == "teachback":
        return "To move from 4 to 5, make the analogy simpler and close with the business efficiency or risk consequence."
    return "To move from 4 to 5, add one precise mechanism, one concrete example, and one operational control."


def _architect_upgrade(question_type: str, architect_note: ArchitectNote) -> str:
    if architect_note.topic_id == "mlf_019" and question_type == "tiny_hands_on":
        return "Upgrade by checking inference-time availability, leakage, proxy risk, stability across segments and domain evidence before trusting humidity operationally."
    if architect_note.topic_id == "mlf_019" and question_type == "architect_decision":
        return "Upgrade by implementing the taught chain: trigger, explanation record, evidence review, named approvers, approved action and outcome monitoring."
    if question_type == "architect_decision":
        return "Upgrade by naming the exact controls: validation gate, metric threshold, monitoring signal, fallback policy, retraining trigger, and response owner."
    if question_type == "failure_diagnosis":
        return "Upgrade by separating observed symptom, likely model failure, data/pipeline evidence, and production control fix."
    if question_type == "tiny_hands_on":
        return "Upgrade by adding the metric comparison or numerical check you would use before trusting the model."
    if question_type == "teachback":
        return "Upgrade by explaining the business consequence in one concrete manufacturing, monitoring, or quality example."
    return architect_note.interview_framing or "Upgrade the answer by tying the concept to evaluation, deployment risk, and monitoring decisions."


def generate_answer_coaching(
    concept_note: ConceptNote,
    architect_note: ArchitectNote,
    assessment: Assessment,
    user_answers: List[UserAnswer],
    evaluation: EvaluationResult,
    llm_callable: Callable[[str, str], str] | None = None,
) -> Dict[str, Any]:
    """Generate topic-grounded, evidence-bound per-question coaching.

    This is deterministic by design. The LLM can still evaluate the final attempt,
    but coaching must not hallucinate a generic answer or leak rubric text.
    """
    answers = _answer_map(user_answers)
    coaching: List[Dict[str, Any]] = []

    for question in assessment.questions:
        answer = answers.get(question.question_id, "")
        missing, misconception_hits = _missing_points(
            topic_id=concept_note.topic_id,
            expected_focus=question.expected_focus,
            answer=answer,
            question_type=question.type,
            question_id=question.question_id,
            question=question.question,
        )
        quality = _question_quality(question.question_id, answer, missing, misconception_hits, evaluation)
        display_missing = missing
        if _score_floor(evaluation) >= 4 and quality == "strong":
            display_missing = [_five_star_upgrade(question.type, concept_note.topic_id)]

        coaching.append(
            {
                "question_id": question.question_id,
                "question": question.question,
                "your_answer": answer,
                "answer_quality": quality,
                "what_was_missing": display_missing,
                "what_kept_from_5": _five_star_upgrade(question.type, concept_note.topic_id),
                "evidence_bound_findings": misconception_hits,
                "better_answer": _better_answer(
                    topic_id=concept_note.topic_id,
                    question_type=question.type,
                    question=question.question,
                    expected_focus=question.expected_focus,
                    concept_note=concept_note,
                    architect_note=architect_note,
                ),
                "why_this_is_better": _why_better(question.type),
                "architect_upgrade": _architect_upgrade(question.type, architect_note),
            }
        )

    return {
        "topic_id": concept_note.topic_id,
        "mode": "contract_aligned_semantic_coaching_v3",
        "coaching": coaching,
    }
