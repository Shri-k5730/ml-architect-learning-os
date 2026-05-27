from __future__ import annotations

from typing import Any, Dict

from src.blueprints.tutor_experience import get_code_lab_guidance


def _groups(*items: tuple[str, list[str]]) -> list[dict[str, Any]]:
    return [{"label": label, "keywords": keywords} for label, keywords in items]


V2_PRACTICE_EXERCISES: Dict[str, Dict[str, Any]] = {
    "mlf_020": {
        "exercise_id": "mlf_020_monitor_mean_shift_v1",
        "topic_id": "mlf_020",
        "title": "Flag a monitored feature mean shift",
        "skill_focus": ["drift signal", "threshold rule", "monitoring response"],
        "prompt": "Implement mean_shift_alert(reference_values, current_values, tolerance). Return True when the absolute difference between the two means is greater than tolerance; otherwise return False. Return False for empty inputs.",
        "function_name": "mean_shift_alert",
        "starter_code": """def mean_shift_alert(reference_values, current_values, tolerance):
    # Compare the mean of the reference and current windows.
    # Return True only when absolute mean difference > tolerance.
    pass
""",
        "interpretation_prompt": "Explain what this alert does and does not prove. Name the next investigation, an owner, and a retraining or fallback rule.",
        "expected_interpretation_focus": ["input drift signal", "not proof of performance failure", "investigation", "owner/action", "retraining or fallback"],
        "interpretation_keyword_groups": _groups(
            ("input drift signal", ["drift", "shift", "distribution", "input"]),
            ("not performance proof", ["not prove", "not proof", "labels", "performance", "recall"]),
            ("investigation", ["investigate", "check", "compare", "review"]),
            ("owner/action", ["owner", "quality", "ml", "alert", "response"]),
            ("retraining or fallback", ["retrain", "fallback", "threshold", "validate"]),
        ),
        "visible_tests": [
            {"name": "large_shift_alert", "args": [[10, 10, 10], [12, 12, 12], 1.0], "expected": True, "reason": "Mean changes by 2.0, above tolerance.", "concept_tag": "threshold_rule", "failure_hint": "Compare absolute mean difference with tolerance.", "show_inputs": True},
            {"name": "within_tolerance", "args": [[10, 10], [10.4, 10.4], 0.5], "expected": False, "reason": "Mean change is within tolerance.", "concept_tag": "no_false_alert", "failure_hint": "Use greater-than rather than greater-than-or-equal unless instructed.", "show_inputs": True},
        ],
        "hidden_tests": [
            {"name": "empty_input", "args": [[], [1], 0.1], "expected": False, "reason": "Empty monitoring windows cannot produce a valid alert.", "concept_tag": "empty_window"},
        ],
        "timeout_seconds": 2,
    },
    "mlf_021": {
        "exercise_id": "mlf_021_group_holdout_indices_v1",
        "topic_id": "mlf_021",
        "title": "Build a group holdout split",
        "skill_focus": ["group split", "entity leakage prevention", "validation evidence"],
        "prompt": "Implement group_holdout_indices(groups, holdout_group). Return {'train': [...], 'validation': [...]} containing row indices. Every row belonging to holdout_group must be in validation and no other row may be in validation.",
        "function_name": "group_holdout_indices",
        "starter_code": """def group_holdout_indices(groups, holdout_group):
    # Example groups = ['Line_A', 'Line_B', 'Line_A']
    # holdout_group = 'Line_B' -> {'train': [0, 2], 'validation': [1]}
    pass
""",
        "interpretation_prompt": "Explain what leakage this split prevents, when a time split must also be added, and what evidence you would store for approval.",
        "expected_interpretation_focus": ["group leakage", "time split", "deployment boundary", "approval evidence", "validation"],
        "interpretation_keyword_groups": _groups(
            ("group leakage", ["group", "line", "machine", "asset", "leak"]),
            ("time split", ["time", "future", "temporal", "month"]),
            ("deployment boundary", ["deployment", "new line", "unseen", "production"]),
            ("approval evidence", ["store", "record", "evidence", "fold", "report"]),
            ("validation decision", ["valid", "validation", "approve", "test"]),
        ),
        "visible_tests": [
            {"name": "holdout_one_group", "args": [["A", "B", "A", "C"], "B"], "expected": {"train": [0, 2, 3], "validation": [1]}, "reason": "All B rows belong only in validation.", "concept_tag": "group_isolation", "failure_hint": "Route each index according to its group.", "show_inputs": True},
            {"name": "repeated_holdout_group", "args": [["A", "B", "B", "C"], "B"], "expected": {"train": [0, 3], "validation": [1, 2]}, "reason": "All occurrences of a held-out entity must remain together.", "concept_tag": "repeated_entity_control", "failure_hint": "Do not split repeated group observations across train and validation.", "show_inputs": True},
        ],
        "hidden_tests": [
            {"name": "missing_holdout", "args": [["A", "C"], "B"], "expected": {"train": [0, 1], "validation": []}, "reason": "A group not present creates an empty validation slice.", "concept_tag": "missing_group_edge_case"},
        ],
        "timeout_seconds": 2,
    },
    "mlf_022": {
        "exercise_id": "mlf_022_select_tuned_candidate_v1",
        "topic_id": "mlf_022",
        "title": "Select a candidate under a latency constraint",
        "skill_focus": ["tuning decision", "operational constraint", "search evidence"],
        "prompt": "Implement select_candidate(trials, max_latency_ms). Each trial is a dictionary with 'id', 'validation_score', and 'latency_ms'. Return the id of the highest validation_score trial whose latency_ms is at most max_latency_ms. Return None if no trial qualifies.",
        "function_name": "select_candidate",
        "starter_code": """def select_candidate(trials, max_latency_ms):
    # Apply the latency gate first, then choose the highest validation_score.
    pass
""",
        "interpretation_prompt": "Explain why this selection is not final model approval. State the tuning budget, locked-test requirement, and trial evidence to retain.",
        "expected_interpretation_focus": ["constraint-aware tuning", "locked test", "budget", "trial log", "approval"],
        "interpretation_keyword_groups": _groups(
            ("constraint-aware tuning", ["latency", "constraint", "candidate", "score"]),
            ("locked test", ["locked", "final test", "holdout", "untouched"]),
            ("budget", ["budget", "trials", "search"]),
            ("trial log", ["log", "registry", "record", "experiment"]),
            ("approval", ["approve", "approval", "release", "final"]),
        ),
        "visible_tests": [
            {"name": "best_within_gate", "args": [[{"id": "A", "validation_score": 0.91, "latency_ms": 55}, {"id": "B", "validation_score": 0.88, "latency_ms": 30}], 40], "expected": "B", "reason": "A fails the latency constraint despite higher score.", "concept_tag": "operational_gate", "failure_hint": "Filter by latency before comparing scores.", "show_inputs": True},
            {"name": "best_qualifier", "args": [[{"id": "A", "validation_score": 0.81, "latency_ms": 20}, {"id": "B", "validation_score": 0.86, "latency_ms": 25}], 30], "expected": "B", "reason": "Both pass the gate; select higher validation score.", "concept_tag": "candidate_selection", "failure_hint": "Track the highest score among qualifying trials.", "show_inputs": True},
        ],
        "hidden_tests": [
            {"name": "none_qualify", "args": [[{"id": "A", "validation_score": 0.9, "latency_ms": 51}], 50], "expected": None, "reason": "No eligible candidate should return None.", "concept_tag": "no_eligible_candidate"},
        ],
        "timeout_seconds": 2,
    },
    "mlf_023": {
        "exercise_id": "mlf_023_metrics_at_threshold_v1",
        "topic_id": "mlf_023",
        "title": "Calculate an operating point",
        "skill_focus": ["thresholding", "precision recall", "alert count"],
        "prompt": "Implement metrics_at_threshold(y_true, scores, threshold). Predict positive when score >= threshold. Return {'precision': value, 'recall': value, 'alerts': count}. Use 0.0 when a denominator is zero.",
        "function_name": "metrics_at_threshold",
        "starter_code": """def metrics_at_threshold(y_true, scores, threshold):
    # Convert scores to positive/negative decisions, then compute metrics.
    pass
""",
        "interpretation_prompt": "Explain how you would use recall, precision, and alert volume to select an operating point for rare defects.",
        "expected_interpretation_focus": ["threshold", "recall", "precision", "alert capacity", "cost"],
        "interpretation_keyword_groups": _groups(
            ("threshold", ["threshold", "operating point"]),
            ("recall", ["recall", "missed", "false negative"]),
            ("precision", ["precision", "false positive", "false alarm"]),
            ("capacity", ["alert", "capacity", "inspection", "workload"]),
            ("cost", ["cost", "risk", "defect", "business"]),
        ),
        "visible_tests": [
            {"name": "threshold_tradeoff", "args": [[1, 1, 0, 0], [0.9, 0.6, 0.7, 0.2], 0.5], "expected": {"precision": 0.6666666666666666, "recall": 1.0, "alerts": 3}, "reason": "Three alerts catch both positives with one false alarm.", "concept_tag": "operating_point_metrics", "failure_hint": "Count TP, FP and FN after applying threshold.", "show_inputs": True},
            {"name": "strict_threshold", "args": [[1, 1, 0], [0.9, 0.6, 0.7], 0.8], "expected": {"precision": 1.0, "recall": 0.5, "alerts": 1}, "reason": "Raising threshold reduces alerts and misses one positive.", "concept_tag": "threshold_tradeoff", "failure_hint": "A higher threshold can reduce recall.", "show_inputs": True},
        ],
        "hidden_tests": [
            {"name": "no_alerts", "args": [[1, 0], [0.3, 0.2], 0.9], "expected": {"precision": 0.0, "recall": 0.0, "alerts": 0}, "reason": "Zero-alert edge case must not divide by zero.", "concept_tag": "zero_alerts"},
        ],
        "timeout_seconds": 2,
    },
    "mlf_024": {
        "exercise_id": "mlf_024_brier_score_v1",
        "topic_id": "mlf_024",
        "title": "Measure probability accuracy with Brier score",
        "skill_focus": ["calibration", "probability error", "risk communication"],
        "prompt": "Implement brier_score(y_true, probabilities). Return the mean squared difference between each probability and binary outcome. Return 0.0 for empty inputs.",
        "function_name": "brier_score",
        "starter_code": """def brier_score(y_true, probabilities):
    # Mean of (probability - outcome) ** 2.
    pass
""",
        "interpretation_prompt": "Explain what a poor probability score means for business risk decisions and how you would govern recalibration.",
        "expected_interpretation_focus": ["calibration", "probability", "observed outcomes", "risk decision", "recalibration"],
        "interpretation_keyword_groups": _groups(
            ("calibration", ["calibration", "calibrated", "brier"]),
            ("probability", ["probability", "score", "confidence"]),
            ("outcomes", ["observed", "actual", "outcome", "label"]),
            ("risk decision", ["risk", "decision", "triage", "budget", "inspection"]),
            ("recalibration", ["recalibrat", "monitor", "holdout", "review"]),
        ),
        "visible_tests": [
            {"name": "perfect_probabilities", "args": [[1, 0], [1.0, 0.0]], "expected": 0.0, "reason": "Perfect probability statements have zero squared error.", "concept_tag": "perfect_calibration", "failure_hint": "Square each probability error and average.", "show_inputs": True},
            {"name": "imperfect_probabilities", "args": [[1, 0], [0.8, 0.4]], "expected": 0.1, "reason": "((0.8-1)^2 + (0.4-0)^2)/2 = 0.1.", "concept_tag": "brier_formula", "failure_hint": "Average squared errors, not raw signed errors.", "show_inputs": True},
        ],
        "hidden_tests": [
            {"name": "empty", "args": [[], []], "expected": 0.0, "reason": "Empty input should be handled safely.", "concept_tag": "empty_input"},
        ],
        "timeout_seconds": 2,
    },
    "mlf_025": {
        "exercise_id": "mlf_025_label_disagreement_v1",
        "topic_id": "mlf_025",
        "title": "Measure label disagreement",
        "skill_focus": ["label audit", "annotation agreement", "release gate"],
        "prompt": "Implement disagreement_rate(labels_a, labels_b). Return the fraction of positions where the two label lists differ. Return 0.0 for empty inputs.",
        "function_name": "disagreement_rate",
        "starter_code": """def disagreement_rate(labels_a, labels_b):
    # Fraction of labels where annotator A and B disagree.
    pass
""",
        "interpretation_prompt": "Explain how disagreement and biased sample coverage affect model readiness, and define a label/data quality gate.",
        "expected_interpretation_focus": ["label quality", "disagreement", "sampling coverage", "gate", "owner"],
        "interpretation_keyword_groups": _groups(
            ("label quality", ["label", "annotator", "inspection"]),
            ("disagreement", ["disagree", "agreement", "rate", "inconsistent"]),
            ("sampling coverage", ["sample", "coverage", "bias", "segment", "supplier"]),
            ("gate", ["gate", "block", "threshold", "accept"]),
            ("owner", ["owner", "quality", "review", "audit"]),
        ),
        "visible_tests": [
            {"name": "two_disagreements", "args": [["defect", "ok", "defect", "ok"], ["defect", "defect", "ok", "ok"]], "expected": 0.5, "reason": "Two out of four labels disagree.", "concept_tag": "agreement_measure", "failure_hint": "Count non-matching pairs and divide by total.", "show_inputs": True},
            {"name": "full_agreement", "args": [[1, 0, 1], [1, 0, 1]], "expected": 0.0, "reason": "No disagreements.", "concept_tag": "clean_label_case", "failure_hint": "Equal labels should not count as disagreement.", "show_inputs": True},
        ],
        "hidden_tests": [
            {"name": "empty", "args": [[], []], "expected": 0.0, "reason": "Empty input must not fail.", "concept_tag": "empty_input"},
        ],
        "timeout_seconds": 2,
    },
    "checkpoint_ml_architect_001": {
        "exercise_id": "checkpoint_ml_architect_two_function_gate_v1",
        "topic_id": "checkpoint_ml_architect_001",
        "title": "Checkpoint Code Lab: metrics and operating-point policy",
        "skill_focus": ["precision recall F1", "threshold policy", "architect interpretation"],
        "prompt": (
            "Complete two functions in one submission. (1) calculate_precision_recall_f1(y_true, y_pred) returns "
            "{'precision': ..., 'recall': ..., 'f1': ...}. (2) choose_threshold(scores, y_true, min_recall=0.80) "
            "checks candidate thresholds taken from scores and returns the highest threshold whose recall is at least min_recall, "
            "or None when no threshold satisfies it."
        ),
        "function_name": "calculate_precision_recall_f1",
        "starter_code": """def calculate_precision_recall_f1(y_true, y_pred):
    # Return {'precision': value, 'recall': value, 'f1': value}
    pass


def choose_threshold(scores, y_true, min_recall=0.80):
    # Predict positive when score >= candidate threshold.
    # Choose the highest threshold from scores meeting minimum recall.
    pass
""",
        "interpretation_prompt": "Explain the threshold you would approve, the false-negative/alert trade-off, validation evidence required, and monitoring owner.",
        "expected_interpretation_focus": ["recall threshold", "precision or alert burden", "validation evidence", "monitoring", "owner"],
        "interpretation_keyword_groups": _groups(
            ("recall threshold", ["recall", "threshold", "minimum"]),
            ("alert burden", ["precision", "alert", "false positive", "workload"]),
            ("validation evidence", ["valid", "test", "holdout", "evidence"]),
            ("monitoring", ["monitor", "drift", "trigger"]),
            ("owner", ["owner", "quality", "ml", "response"]),
        ),
        "visible_tests": [
            {"name": "metric_function", "function_name": "calculate_precision_recall_f1", "args": [[1, 1, 1, 0, 0], [1, 0, 1, 1, 0]], "expected": {"precision": 0.6666666666666666, "recall": 0.6666666666666666, "f1": 0.6666666666666666}, "reason": "TP=2, FP=1, FN=1.", "concept_tag": "metric_formula", "failure_hint": "Compute TP, FP, FN and guard zero denominators.", "show_inputs": True},
            {"name": "threshold_function", "function_name": "choose_threshold", "args": [[0.9, 0.7, 0.6, 0.3], [1, 1, 0, 1]], "kwargs": {"min_recall": 0.66}, "expected": 0.7, "reason": "Threshold 0.7 catches two of three positives; threshold 0.9 does not.", "concept_tag": "threshold_policy", "failure_hint": "Test thresholds from high to low and return first meeting recall.", "show_inputs": True},
        ],
        "hidden_tests": [
            {"name": "metric_zero_case", "function_name": "calculate_precision_recall_f1", "args": [[0, 0], [0, 0]], "expected": {"precision": 0.0, "recall": 0.0, "f1": 0.0}, "reason": "No positive cases should not crash.", "concept_tag": "zero_denominator"},
            {"name": "threshold_none_case", "function_name": "choose_threshold", "args": [[0.4, 0.3], [1, 0]], "kwargs": {"min_recall": 1.1}, "expected": None, "reason": "Impossible recall target returns None.", "concept_tag": "no_policy_match"},
        ],
        "timeout_seconds": 2,
    },
    "capstone_ml_architect_001": {
        "exercise_id": "capstone_deployment_policy_v1",
        "topic_id": "capstone_ml_architect_001",
        "title": "Capstone Code Lab: implement a risk-action policy",
        "skill_focus": ["decision policy", "thresholds", "fallback handling"],
        "prompt": "Implement deployment_action(score, intervene_threshold, review_threshold). Return 'intervene' when score >= intervene_threshold, 'manual_review' when score >= review_threshold, otherwise 'monitor'. Raise ValueError when review_threshold is greater than intervene_threshold.",
        "function_name": "deployment_action",
        "starter_code": """def deployment_action(score, intervene_threshold, review_threshold):
    # Validate threshold order, then return 'intervene', 'manual_review', or 'monitor'.
    pass
""",
        "interpretation_prompt": "Explain how this policy fits into your capstone architecture: threshold evidence, human approval boundary, fallback, monitoring trigger, and owner.",
        "expected_interpretation_focus": ["threshold evidence", "human review", "fallback", "monitoring", "owner"],
        "interpretation_keyword_groups": _groups(
            ("threshold evidence", ["threshold", "evidence", "validation", "precision", "recall"]),
            ("human review", ["human", "manual", "approval", "review"]),
            ("fallback", ["fallback", "intervene", "monitor"]),
            ("monitoring", ["monitor", "drift", "trigger", "performance"]),
            ("owner", ["owner", "quality", "ml", "operations"]),
        ),
        "visible_tests": [
            {"name": "intervention", "args": [0.92, 0.80, 0.55], "expected": "intervene", "reason": "High risk crosses intervention threshold.", "concept_tag": "intervention_policy", "failure_hint": "Check intervention before review.", "show_inputs": True},
            {"name": "manual_review_band", "args": [0.62, 0.80, 0.55], "expected": "manual_review", "reason": "Intermediate risk routes for review.", "concept_tag": "human_in_loop", "failure_hint": "Use a middle band for manual review.", "show_inputs": True},
            {"name": "monitor_band", "args": [0.30, 0.80, 0.55], "expected": "monitor", "reason": "Lower risk is monitored without intervention.", "concept_tag": "monitor_policy", "failure_hint": "Return monitor below both thresholds.", "show_inputs": True},
        ],
        "hidden_tests": [
            {"name": "invalid_threshold_order", "args": [0.7, 0.6, 0.8], "expected_error": "ValueError", "reason": "Review threshold cannot exceed intervention threshold.", "concept_tag": "policy_validation"},
        ],
        "timeout_seconds": 2,
    },
}

# Learners see the meaning of each function before they are asked to code or interpret it.
for _topic_id, _exercise in V2_PRACTICE_EXERCISES.items():
    _exercise.update(get_code_lab_guidance(_topic_id))

