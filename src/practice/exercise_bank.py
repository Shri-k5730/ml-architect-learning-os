from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, Optional


PRACTICE_EXERCISES: Dict[str, Dict[str, Any]] = {
    "mlf_009": {
        "exercise_id": "mlf_009_accuracy_can_lie_v1",
        "topic_id": "mlf_009",
        "title": "Accuracy can lie on imbalanced data",
        "skill_focus": [
            "metric calculation",
            "class imbalance reasoning",
            "practical interpretation",
        ],
        "prompt": (
            "Implement calculate_accuracy(y_true, y_pred). It must return the fraction of correct predictions "
            "as a float between 0 and 1. Then explain why a high accuracy value can still be misleading "
            "when positive cases are rare."
        ),
        "function_name": "calculate_accuracy",
        "starter_code": """def calculate_accuracy(y_true, y_pred):\n    # Return the fraction of positions where y_true and y_pred match.\n    # Example: 4 correct out of 5 should return 0.8\n    pass\n""",
        "interpretation_prompt": (
            "In 4-6 lines, explain what the result means for a production ML system. "
            "Do not just say 'accuracy is bad'. Explain the business risk and what metric/check you would add."
        ),
        "expected_interpretation_focus": [
            "High accuracy can hide missed minority/positive cases.",
            "False negatives or false positives may have asymmetric business cost.",
            "Accuracy should be complemented with precision, recall, confusion matrix, or class-specific metrics.",
            "Metric choice should be tied to the production decision and cost of errors.",
        ],
        "visible_tests": [
            {
                "name": "simple_4_of_5_correct",
                "args": [[0, 0, 0, 0, 1], [0, 0, 0, 0, 0]],
                "expected": 0.8,
                "reason": "Four out of five predictions are correct, even though the only positive case is missed.",
            },
            {
                "name": "all_correct",
                "args": [[1, 0, 1, 0], [1, 0, 1, 0]],
                "expected": 1.0,
                "reason": "All predictions match the labels.",
            },
        ],
        "hidden_tests": [
            {
                "name": "half_correct",
                "args": [[1, 1, 0, 0], [1, 0, 1, 0]],
                "expected": 0.5,
                "reason": "Two out of four predictions match.",
            },
            {
                "name": "empty_input_returns_zero",
                "args": [[], []],
                "expected": 0.0,
                "reason": "Empty inputs should not crash the evaluator.",
            },
        ],
        "timeout_seconds": 2,
    },
    "checkpoint_ml_foundations_001": {
        "exercise_id": "checkpoint_ml_foundations_precision_recall_v1",
        "topic_id": "checkpoint_ml_foundations_001",
        "title": "Compute precision and recall for a defect model",
        "skill_focus": [
            "confusion matrix reasoning",
            "precision recall calculation",
            "production metric decision",
        ],
        "prompt": (
            "Implement calculate_precision_recall(y_true, y_pred, positive_label=1). "
            "It must return a dictionary with keys 'precision' and 'recall'. Then explain which metric matters more "
            "for a defect detection go-live decision and why."
        ),
        "function_name": "calculate_precision_recall",
        "starter_code": """def calculate_precision_recall(y_true, y_pred, positive_label=1):
    # Return {"precision": value, "recall": value}
    # precision = TP / (TP + FP)
    # recall = TP / (TP + FN)
    pass
""",
        "interpretation_prompt": (
            "In 5-7 lines, explain the precision/recall result as a production decision. "
            "Name the business risk, the error type, and what threshold or monitoring control you would define."
        ),
        "expected_interpretation_focus": [
            "Recall exposes missed actual defects or false negatives.",
            "Precision exposes how many flagged defects are truly defective.",
            "The metric priority must reflect the cost of false negatives versus false positives.",
            "Production approval should define threshold, monitoring, and owner response.",
        ],
        "visible_tests": [
            {
                "name": "checkpoint_confusion_matrix",
                "args": [[1] * 12 + [1] * 28 + [0] * 8 + [0] * 952, [1] * 12 + [0] * 28 + [1] * 8 + [0] * 952],
                "expected": {"precision": 0.6, "recall": 0.3},
                "reason": "TP=12, FP=8, FN=28, TN=952, so precision=12/20 and recall=12/40.",
            },
            {
                "name": "all_positive_caught",
                "args": [[1, 1, 0, 0], [1, 1, 0, 1]],
                "expected": {"precision": 0.6666666666666666, "recall": 1.0},
                "reason": "Two true positives, one false positive, and no false negatives.",
            },
        ],
        "hidden_tests": [
            {
                "name": "no_positive_predictions",
                "args": [[1, 0, 1, 0], [0, 0, 0, 0]],
                "expected": {"precision": 0.0, "recall": 0.0},
                "reason": "No positive predictions and two missed positives.",
            },
            {
                "name": "custom_positive_label",
                "args": [["defect", "ok", "defect", "ok"], ["defect", "defect", "ok", "ok"]],
                "kwargs": {"positive_label": "defect"},
                "expected": {"precision": 0.5, "recall": 0.5},
                "reason": "The function must respect the positive_label argument.",
            },
        ],
        "timeout_seconds": 2,
        "better_code": """def calculate_precision_recall(y_true, y_pred, positive_label=1):
    tp = fp = fn = 0
    for actual, predicted in zip(y_true, y_pred):
        if predicted == positive_label and actual == positive_label:
            tp += 1
        elif predicted == positive_label and actual != positive_label:
            fp += 1
        elif predicted != positive_label and actual == positive_label:
            fn += 1

    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    return {"precision": precision, "recall": recall}
""",
        "better_interpretation": (
            "The model may have high overall accuracy because most parts are non-defective, but recall shows whether actual defects are being caught. "
            "For a defect detection go-live decision, low recall means false negatives are passing through the system. "
            "That is usually more dangerous than a moderate number of false alarms. "
            "I would set a minimum defect-class recall threshold, review precision to control inspection workload, and monitor both metrics after deployment."
        ),
    },
}


def get_exercise_for_topic(topic_id: str) -> Optional[Dict[str, Any]]:
    exercise = PRACTICE_EXERCISES.get(str(topic_id or "").strip())
    return deepcopy(exercise) if exercise else None


def build_practice_submission_template(topic_id: str) -> Optional[Dict[str, Any]]:
    exercise = get_exercise_for_topic(topic_id)
    if exercise is None:
        return None

    return {
        "topic_id": exercise["topic_id"],
        "exercise_id": exercise["exercise_id"],
        "status": "pending_user_submission",
        "code": exercise["starter_code"],
        "interpretation": "",
    }
