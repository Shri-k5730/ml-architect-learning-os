from __future__ import annotations

from typing import Any, Dict, List


GENERIC_PROFILE: Dict[str, Any] = {
    "core_concepts": [],
    "common_misconceptions": [],
    "golden_answers": {},
    "practical_checks": [],
    "architect_controls": [
        "validation split that resembles production",
        "metric selected from business risk",
        "drift or data quality monitoring",
        "fallback or escalation rule",
        "retraining trigger and owner",
    ],
}


TOPIC_COACHING_PROFILES: Dict[str, Dict[str, Any]] = {
    "mlf_008": {
        "core_concepts": [
            "Bias is systematic error caused by oversimplification or wrong assumptions.",
            "Variance is sensitivity to training data, noise, or sampling fluctuations.",
            "High bias usually causes underfitting; high variance usually causes overfitting.",
            "The practical diagnosis is made by comparing training and validation behavior, not by looking at feature spread alone.",
        ],
        "common_misconceptions": [
            {
                "pattern": ["biased towards", "prefers temperature", "gives less importance"],
                "issue": "You are using ordinary-language bias, not ML bias.",
                "correction": "ML bias is systematic prediction error from an oversimplified model or bad assumptions. It is not just feature preference.",
            },
            {
                "pattern": ["temperature has a high spread", "high variance in values", "large variance in temperature"],
                "issue": "This confuses feature variance with model variance.",
                "correction": "Model variance means predictions change too much when training data changes. A feature having a wide numeric range is not automatically model variance.",
            },
            {
                "pattern": ["balance out the bias and variance in the data"],
                "issue": "Bias-variance is mainly about model error behavior, not simply balancing the dataset.",
                "correction": "Data quality matters, but bias-variance is diagnosed through model fit and generalization behavior.",
            },
        ],
        "golden_answers": {
            "concept_check": "Bias is systematic error from a model being too simple or making the wrong assumptions, so it misses the real relationship. Variance is error from being too sensitive to the training data, so the model captures noise and becomes unstable on new data. High bias usually means underfitting; high variance usually means overfitting. The architect goal is to choose a model and validation strategy that generalizes reliably, not just performs well on training data.",
            "tiny_hands_on": "I would compare training and validation metrics. If both training and validation errors are high, the model is likely underfitting, which points to high bias. If training error is low but validation error is much higher, the model is likely overfitting, which points to high variance. For regression, I would use RMSE, MAE, R², and residual plots. In manufacturing, I would also check whether the errors are worse in specific operating ranges such as high temperature, high pressure, or rare defect regimes.",
            "failure_diagnosis": "A model that predicts 5% for every product is probably underfitting. It has high bias and low useful variance because it is not reacting to the input conditions. Possible causes include an overly simple model, weak or missing features, aggressive regularization, target leakage during preprocessing, or a broken production feature pipeline that sends constant/default values. The production fix is to inspect feature distributions, compare training vs validation behavior, test the live feature pipeline, and retrain with representative operating conditions.",
            "architect_decision": "I would design the lifecycle around fit diagnostics and production monitoring: compare train/validation/test metrics, inspect residuals by operating segment, monitor drift in feature distributions, track error by production line or station, define retraining triggers, and add fallback rules when inputs move outside the validated range. Bias-variance is not just a training concern; it becomes a control problem once the model is deployed.",
            "teachback": "For a manufacturing stakeholder, I would say: if the model is too rigid, it misses real defect patterns. That is high bias. If it is too jumpy and reacts to noise from past data, it may raise unreliable predictions in production. That is high variance. We need the model to learn the real signal and stay stable on new batches, lines, and operating conditions.",
        },
        "practical_checks": [
            "compare train and validation metrics",
            "name RMSE, MAE, R², residual plots, or segment-level errors",
            "separate feature spread from model variance",
            "identify underfitting vs overfitting from behavior",
        ],
    },
    "mlf_009": {
        "core_concepts": [
            "Accuracy is correct predictions divided by total predictions.",
            "Accuracy can hide minority-class failure under class imbalance.",
            "A majority-class model can look accurate and still be useless for defect detection.",
            "Metric choice must follow business risk, especially false negatives and false positives.",
        ],
        "common_misconceptions": [
            {
                "pattern": ["high accuracy means", "accuracy is enough", "accuracy alone"],
                "issue": "Accuracy alone does not prove the model catches the cases that matter.",
                "correction": "For imbalanced defect detection, inspect recall, precision, F1, and the confusion matrix.",
            },
            {
                "pattern": ["overall correct", "most predictions"],
                "issue": "Overall correctness can be dominated by the majority class.",
                "correction": "Calculate how the model performs separately on the defect/minority class.",
            },
        ],
        "golden_answers": {
            "concept_check": "Accuracy is the share of predictions the model gets right, but it can lie when the data is imbalanced. If 95% of parts are good, a model that predicts every part as good gets 95% accuracy while catching zero defects. The metric looks strong, but the business outcome is a failure.",
            "tiny_hands_on": "I would calculate the confusion matrix first. For example, if 950 parts are good and 50 are defective, a model predicting 'good' for all parts has 950 correct predictions and 95% accuracy, but defect recall is 0/50 = 0%. That is unacceptable if missed defects are the real production risk.",
            "failure_diagnosis": "The likely failure is metric mismatch. The model was judged by overall accuracy, so it learned that predicting the majority class was enough. In production, the minority class is the critical business event. The fix is to evaluate recall for defects, precision of defect alerts, F1, confusion matrix, and cost-weighted errors before deployment.",
            "architect_decision": "I would choose metrics based on the cost of errors. For defect detection, false negatives may be more expensive than false positives, so recall for the defect class should be a primary metric. I would monitor the confusion matrix, class distribution drift, defect recall, alert precision, and escalation thresholds after deployment.",
            "teachback": "I would tell a stakeholder: 95% accuracy can still be dangerous if the model misses the 5% of cases we care about. In manufacturing, missing defective parts is often worse than sending a few good parts for manual review. So we need metrics that show whether the model catches defects, not just whether it is usually right.",
        },
        "practical_checks": [
            "compute or explain class imbalance",
            "mention confusion matrix, recall, precision, or F1",
            "identify false negatives as a business risk",
            "separate high metric score from useful production behavior",
        ],
    },
}


def get_topic_coaching_profile(topic_id: str) -> Dict[str, Any]:
    profile = dict(GENERIC_PROFILE)
    specific = TOPIC_COACHING_PROFILES.get(topic_id, {})
    for key, value in specific.items():
        profile[key] = value
    return profile


def profile_core_concepts(topic_id: str) -> List[str]:
    return list(get_topic_coaching_profile(topic_id).get("core_concepts", []))


def profile_golden_answer(topic_id: str, question_type: str) -> str:
    profile = get_topic_coaching_profile(topic_id)
    return str(profile.get("golden_answers", {}).get(question_type, "")).strip()
