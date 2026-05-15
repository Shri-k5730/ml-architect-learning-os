from __future__ import annotations

from typing import Any, Dict, List


# Pre-mission learning support. This is intentionally deterministic and copy-safe.
# It helps the learner check understanding before writing free-form mission answers,
# but it does not reveal stronger sample answers for the final assessment.

ADVANCED_ML_BOOSTERS: Dict[str, Dict[str, Any]] = {
    "mlf_011": {
        "plain_language": "Model selection is not choosing the model with the prettiest score. It is choosing the model that is reliable enough for the decision it will support.",
        "worked_example": "If Model A has 92% validation accuracy but unstable recall across plants, and Model B has 89% accuracy but stable recall and simpler monitoring, Model B may be the better production choice.",
        "production_trap": "Teams often pick the highest validation score and ignore instability by segment, time period, plant, or product family.",
        "mission_hint": "In your mission answers, separate offline metric, validation method, production constraint, and go-live decision.",
        "mcqs": [
            {
                "question": "Which model is usually safer for production?",
                "options": [
                    "The model with the highest training accuracy.",
                    "The model with the best validation score and no monitoring plan.",
                    "The model whose performance is stable across relevant production segments.",
                    "The most complex model available."
                ],
                "answer_index": 2,
                "explanation": "Model selection should account for stability and production fit, not only headline score."
            },
            {
                "question": "What is a weak model-selection argument?",
                "options": [
                    "It has the best test recall for the defect class.",
                    "It is simpler and easier to monitor with acceptable performance.",
                    "It scored highest on training data, so it must generalize.",
                    "It performs consistently across product families."
                ],
                "answer_index": 2,
                "explanation": "Training performance alone is not enough because it can hide overfitting."
            }
        ],
    },
    "mlf_012": {
        "plain_language": "Feature engineering decides what signals the model sees. A feature contract decides whether those signals are valid before the model is allowed to use them.",
        "worked_example": "Suppose humidity must be between 0 and 100. Values [30, 45, 110, -5, 60] contain two contract violations: 110 and -5. If those values enter training or inference, the model may learn or act on impossible operating conditions.",
        "production_trap": "Adding more features can make the model worse if the features are noisy, unavailable in production, delayed, differently calculated, or outside valid ranges.",
        "mission_hint": "In your answers, name the feature, the rule, the violation, the downstream model impact, and the control that catches it before prediction.",
        "mcqs": [
            {
                "question": "What is the best description of a feature contract?",
                "options": [
                    "A list of all features that might improve model accuracy.",
                    "A rule set that defines valid feature type, range, freshness, and allowed values.",
                    "A model parameter that changes during training.",
                    "A dashboard that shows final model accuracy."
                ],
                "answer_index": 1,
                "explanation": "A feature contract is a validation agreement around input features before training or inference."
            },
            {
                "question": "Humidity has a valid range of 0 to 100. Which value violates the contract?",
                "options": ["30", "45", "60", "110"],
                "answer_index": 3,
                "explanation": "110% humidity is outside the valid range, so it should be rejected, corrected, or routed for investigation."
            },
            {
                "question": "Why can adding more features hurt a production ML system?",
                "options": [
                    "Because models cannot use more than three features.",
                    "Because irrelevant or unstable features can add noise and create fragile dependencies.",
                    "Because features are only useful in deep learning.",
                    "Because feature engineering removes the need for monitoring."
                ],
                "answer_index": 1,
                "explanation": "More features are not automatically better. Quality, stability, availability, and meaning matter."
            },
            {
                "question": "A model degrades after deployment because temperature readings started arriving in Fahrenheit instead of Celsius. What failed?",
                "options": [
                    "The feature contract did not enforce unit and range expectations.",
                    "The model needed a higher learning rate.",
                    "The precision metric was too high.",
                    "The target label was missing from the dashboard."
                ],
                "answer_index": 0,
                "explanation": "Unit mismatch is a feature contract and pipeline validation failure."
            }
        ],
    },
    "mlf_013": {
        "plain_language": "Categorical encoding turns labels like plant, shift, or supplier into numeric representations. Safe encoding avoids leaking future knowledge or breaking when new categories appear.",
        "worked_example": "If supplier='A' is encoded using defect rate calculated from the full dataset, the encoding may leak test-period defect information into training.",
        "production_trap": "A category that never appeared during training can arrive in production and cause bad defaults, errors, or silent misclassification.",
        "mission_hint": "Mention training-only fit, unknown-category handling, leakage risk, and consistency between training and inference pipelines.",
        "mcqs": [
            {
                "question": "What is a common leakage risk in target encoding?",
                "options": [
                    "Using only training data to calculate category statistics.",
                    "Using future or test labels to calculate category statistics.",
                    "Saving the encoder with the model.",
                    "Handling unknown categories explicitly."
                ],
                "answer_index": 1,
                "explanation": "Target encoding must not use labels from validation, test, or future data."
            }
        ],
    },
    "mlf_014": {
        "plain_language": "Scaling changes the numeric range of features. Pipeline leakage happens when scaling parameters are learned from data the model should not have seen.",
        "worked_example": "If you compute mean and standard deviation using train plus test data, the test distribution has influenced training preparation.",
        "production_trap": "Teams fit the scaler separately in production, so live inputs are transformed differently from training inputs.",
        "mission_hint": "State clearly: fit transformers on training data, reuse the same fitted transformer for validation, test, and inference.",
        "mcqs": [
            {
                "question": "Where should a scaler be fitted?",
                "options": ["On all available data", "On train data only", "On test data only", "Separately on each production batch"],
                "answer_index": 1,
                "explanation": "The scaler should learn parameters from training data only, then be reused downstream."
            }
        ],
    },
    "mlf_015": {
        "plain_language": "Regularization adds a penalty for unnecessary model complexity. It is a control against overfitting, not a magic accuracy booster.",
        "worked_example": "A model with huge coefficients may fit historical noise. L2 regularization discourages extreme weights and often improves generalization.",
        "production_trap": "Too much regularization can underfit and miss real defect drivers.",
        "mission_hint": "Discuss the tradeoff: reduce variance without creating too much bias.",
        "mcqs": [
            {
                "question": "What does regularization mainly control?",
                "options": ["Model complexity", "Database latency", "Label creation", "Number of dashboards"],
                "answer_index": 0,
                "explanation": "Regularization penalizes complexity so the model is less likely to chase noise."
            }
        ],
    },
    "mlf_016": {
        "plain_language": "Threshold tuning turns model scores into decisions. A 0.5 threshold is not automatically correct.",
        "worked_example": "If missing a defect is expensive, you may lower the defect threshold to catch more actual defects, accepting more false alarms.",
        "production_trap": "Teams optimize threshold on generic accuracy instead of business cost, recall needs, and operational workload.",
        "mission_hint": "Name the cost of false positives, false negatives, minimum recall target, and workload limit.",
        "mcqs": [
            {
                "question": "When false negatives are more costly than false positives, what often becomes more important?",
                "options": ["Recall", "Training accuracy", "Model size", "Feature count"],
                "answer_index": 0,
                "explanation": "Recall tells how many actual positives were caught."
            }
        ],
    },
    "mlf_017": {
        "plain_language": "Class imbalance means one class dominates the data. The model can look good while ignoring the rare class that matters.",
        "worked_example": "If defects are 2% of cases, predicting no defect every time gives 98% accuracy and zero defect detection.",
        "production_trap": "Teams report accuracy and miss that recall for the defect class is unusable.",
        "mission_hint": "Discuss class-specific metrics, sampling, class weights, threshold tuning, and production cost.",
        "mcqs": [
            {
                "question": "Which metric is dangerous to use alone on imbalanced defect data?",
                "options": ["Accuracy", "Recall", "Precision", "Confusion matrix"],
                "answer_index": 0,
                "explanation": "Accuracy can be inflated by the majority class."
            }
        ],
    },
    "mlf_018": {
        "plain_language": "Error analysis means looking at where the model fails, not just how much it fails.",
        "worked_example": "A 12% error rate is less useful than knowing errors are concentrated in night shift, supplier B, and high-humidity batches.",
        "production_trap": "Teams average errors across all cases and miss concentrated failure pockets.",
        "mission_hint": "Segment by plant, product, supplier, shift, time, and defect type before recommending fixes.",
        "mcqs": [
            {
                "question": "What is the main purpose of error analysis?",
                "options": ["Increase the dataset size blindly", "Find patterns in model failures", "Replace all simple models", "Avoid monitoring"],
                "answer_index": 1,
                "explanation": "Error analysis identifies where and why predictions fail."
            }
        ],
    },
    "mlf_019": {
        "plain_language": "Interpretability explains model behavior, but explanations are not always causal truth.",
        "worked_example": "A feature may rank high because it correlates with a process condition, not because it directly causes defects.",
        "production_trap": "Stakeholders treat SHAP-style explanations as causal proof and make process changes without validation.",
        "mission_hint": "Separate explanation, evidence, causality, and decision governance.",
        "mcqs": [
            {
                "question": "What is a safe way to use model explanations?",
                "options": ["Treat them as causal proof", "Use them as clues requiring domain validation", "Ignore all explanations", "Use them to skip testing"],
                "answer_index": 1,
                "explanation": "Interpretability is useful, but explanations still need validation."
            }
        ],
    },
    "mlf_020": {
        "plain_language": "ML monitoring checks whether model inputs, outputs, and business outcomes are still trustworthy after deployment.",
        "worked_example": "If input humidity distribution shifts and defect recall drops, the monitoring system should trigger investigation before damage accumulates.",
        "production_trap": "Teams monitor uptime only and ignore data drift, performance drift, and delayed label feedback.",
        "mission_hint": "Mention input drift, prediction drift, performance metrics, alert thresholds, owner, and retraining trigger.",
        "mcqs": [
            {
                "question": "Which is not enough for ML monitoring?",
                "options": ["API uptime only", "Input drift", "Recall over time", "Prediction distribution"],
                "answer_index": 0,
                "explanation": "A healthy API can still serve degraded model predictions."
            }
        ],
    },
}


def build_lesson_booster(topic_id: str, concept_note: Dict[str, Any], architect_note: Dict[str, Any], assessment_doc: Dict[str, Any]) -> Dict[str, Any]:
    """Return copy-safe pre-mission support for a lesson."""
    title = concept_note.get("title", topic_id)
    base = ADVANCED_ML_BOOSTERS.get(topic_id)

    if base is None:
        base = {
            "plain_language": concept_note.get("simple_explanation", ""),
            "worked_example": concept_note.get("tiny_example", ""),
            "production_trap": concept_note.get("edge_case", ""),
            "mission_hint": "Before answering, define the concept, apply it to the scenario, name the failure mode, and state the architecture control.",
            "mcqs": [
                {
                    "question": f"What is the safest way to use {title} in an ML system?",
                    "options": [
                        "Treat the concept as a definition only.",
                        "Connect it to model behavior, evaluation, and production controls.",
                        "Mention it only during interviews.",
                        "Ignore it once the model trains successfully."
                    ],
                    "answer_index": 1,
                    "explanation": "Architect-level understanding connects the concept to decisions and controls."
                }
            ],
        }

    mission_focus: List[str] = []
    for question in assessment_doc.get("questions", []) or []:
        qtype = str(question.get("type", ""))
        focus_items = question.get("expected_focus", []) or []
        if qtype in {"tiny_hands_on", "failure_diagnosis", "architect_decision"}:
            mission_focus.extend(str(item) for item in focus_items[:2])

    return {
        "topic_id": topic_id,
        "title": title,
        "plain_language": base.get("plain_language", ""),
        "worked_example": base.get("worked_example", ""),
        "production_trap": base.get("production_trap", ""),
        "mission_hint": base.get("mission_hint", ""),
        "mission_focus": mission_focus[:5],
        "mcqs": base.get("mcqs", []),
    }
