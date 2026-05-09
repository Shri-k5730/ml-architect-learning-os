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
    }
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
