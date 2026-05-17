from __future__ import annotations

from typing import Any, Dict, List

from src.blueprints.advanced_ml import blueprint_to_booster


# Study Booster is a deterministic, copy-safe learning layer.
# It exists to close the gap between what the lesson teaches and what missions evaluate.
# It should guide thinking, not provide final answers to paste.

DEFAULT_ANSWER_FRAME = [
    "1. Define the concept in one precise sentence.",
    "2. Apply it to the exact scenario in the question.",
    "3. Name the failure mode if the concept is misunderstood.",
    "4. State the practical metric, data check, or design control you would use.",
    "5. Close with the production or business consequence.",
]

MISSION_TYPE_SKILL_MAP = {
    "concept_check": "Explain the concept precisely, not as a vague definition.",
    "tiny_hands_on": "Use the numbers, table, categories, or scenario. Do not stay theoretical.",
    "failure_diagnosis": "Separate symptom, likely cause, evidence to inspect, and prevention.",
    "architect_decision": "Name design controls, thresholds, monitoring signals, ownership, and fallback where relevant.",
    "teachback": "Explain it simply for an interview or stakeholder, while keeping the production implication visible.",
}


def _bridge(topic_focus: str) -> List[Dict[str, str]]:
    return [
        {
            "mission_type": mission_type,
            "tested_skill": skill,
            "use_from_booster": f"Use the Study Booster for {topic_focus}. Apply the answer frame instead of repeating the basic definition.",
        }
        for mission_type, skill in MISSION_TYPE_SKILL_MAP.items()
    ]


ADVANCED_ML_BOOSTERS: Dict[str, Dict[str, Any]] = {
    "checkpoint_ml_foundations_001": {
        "plain_language": "The first 10 lessons form one trust chain: target, split, baseline, generalization, leakage, metric choice, and go-live controls.",
        "worked_example": "A model can show 96% accuracy and still be unsafe if it catches only 30% of actual defects. The checkpoint tests whether you can connect metric calculation to go-live judgment.",
        "production_trap": "Treating each foundation topic as separate theory. In production, leakage, metric choice, and threshold policy fail together.",
        "mission_hint": "Connect the concepts: baseline proves value, split validates generalization, leakage invalidates scores, precision/recall expose production risk.",
        "key_distinctions": [
            "Accuracy asks how often the model is right overall; recall asks how many actual positives it catches.",
            "A baseline is a comparison anchor; it is not a production approval.",
            "A good test score is meaningless if the split leaks future or post-event information.",
            "A model is production-ready only when metric policy, monitoring, fallback, and ownership are defined.",
        ],
        "answer_frame": [
            "1. Identify the ML foundation concept involved.",
            "2. Calculate or reason from the metric/data given.",
            "3. State what failure the result exposes.",
            "4. Decide whether go-live is safe.",
            "5. Name the production controls required before deployment.",
        ],
        "mission_bridge": _bridge("foundation integration"),
        "mcqs": [
            {
                "question": "A defect model has 96% accuracy but recall of 30% for defects. What is the safest interpretation?",
                "options": ["It is production-ready.", "It is unsafe if missed defects matter.", "The baseline is unnecessary.", "Recall can be ignored because accuracy is high."],
                "answer_index": 1,
                "explanation": "Low defect recall means many actual defects are missed, even if overall accuracy is high.",
            },
            {
                "question": "Which issue makes a test score invalid?",
                "options": ["Using a simple baseline.", "Checking a confusion matrix.", "Using future or post-event data in features.", "Monitoring recall after go-live."],
                "answer_index": 2,
                "explanation": "Future/post-event features create leakage and make evaluation unrealistically strong.",
            },
            {
                "question": "What should a baseline answer?",
                "options": ["Whether the complex model adds value over a simpler reference.", "Whether the model is deep learning.", "Whether deployment is free.", "Whether labels can be skipped."],
                "answer_index": 0,
                "explanation": "A baseline is a value-comparison anchor.",
            },
            {
                "question": "What is missing from a go-live decision based only on offline metrics?",
                "options": ["A production monitoring and response plan.", "A longer model name.", "A larger dashboard font.", "A random train/test split only."],
                "answer_index": 0,
                "explanation": "Production readiness requires monitoring, thresholds, fallback, retraining triggers, and ownership.",
            },
        ],
    },
    "mlf_011": {
        "plain_language": "Model selection means choosing the model that is reliable enough for the decision, not the one with the prettiest score.",
        "worked_example": "Model A has 92% validation accuracy but recall collapses on Plant B. Model B has 89% accuracy but stable recall across plants. For defect detection, Model B may be safer.",
        "production_trap": "Teams pick the highest validation score and ignore segment instability, inference cost, monitoring difficulty, and business risk.",
        "mission_hint": "Separate metric score, validation strategy, business cost, production constraint, and final model choice.",
        "key_distinctions": [
            "Training score tells fit; validation/test score estimates generalization.",
            "Best average score can still hide poor performance by plant, product, shift, supplier, or defect type.",
            "Simple models are often better when they are stable, explainable, and monitorable enough.",
            "Model selection is a decision under constraints: accuracy, recall, latency, maintainability, cost, and failure risk.",
        ],
        "answer_frame": [
            "1. State the model options and the decision context.",
            "2. Compare validation/test metrics, not training metrics only.",
            "3. Check segment-level stability and business-critical metrics.",
            "4. Consider deployment constraints: latency, monitoring, explainability, retraining effort.",
            "5. Pick the model and justify the trade-off.",
        ],
        "mission_bridge": _bridge("model selection under production constraints"),
        "mcqs": [
            {
                "question": "Which model is usually safer for production?",
                "options": ["Highest training accuracy.", "Best validation score with no monitoring plan.", "Stable performance across relevant production segments.", "Most complex model available."],
                "answer_index": 2,
                "explanation": "Production selection must consider stability and production fit, not only headline score.",
            },
            {
                "question": "What is a weak model-selection argument?",
                "options": ["It has the best test recall for defects.", "It is simpler and easier to monitor with acceptable performance.", "It scored highest on training data, so it must generalize.", "It performs consistently across product families."],
                "answer_index": 2,
                "explanation": "Training score alone can hide overfitting.",
            },
            {
                "question": "Why compare performance by plant or product family?",
                "options": ["To make the report longer.", "To detect hidden failure pockets behind average metrics.", "To avoid using validation data.", "To replace all business rules."],
                "answer_index": 1,
                "explanation": "Averages can hide segments where the model is unsafe.",
            },
            {
                "question": "Which factor belongs in production model selection?",
                "options": ["Latency and monitoring effort.", "Only the algorithm name.", "Only number of rows.", "Whether the model sounds modern."],
                "answer_index": 0,
                "explanation": "Deployment constraints are part of model selection.",
            },
        ],
    },
    "mlf_012": {
        "plain_language": "Feature engineering decides what signals the model sees. A feature contract decides whether those signals are valid before the model uses them.",
        "worked_example": "Humidity must be between 0 and 100. Values [30, 45, 110, -5, 60] contain two contract violations: 110 and -5. Those values should be rejected, corrected, or routed before prediction.",
        "production_trap": "Adding more features can make the model worse if the features are noisy, unavailable in production, delayed, differently calculated, or outside valid ranges.",
        "mission_hint": "Name the feature, rule, violation, model impact, and validation control that catches the issue before prediction.",
        "key_distinctions": [
            "Feature engineering creates or transforms signals; feature contracts validate whether those signals are allowed.",
            "A feature can be predictive in training but unavailable, delayed, or differently calculated in production.",
            "Contracts should cover type, range, allowed values, nulls, units, freshness, and source.",
            "Contract violations should have a response: reject, impute, fallback, alert, or quarantine.",
        ],
        "answer_frame": [
            "1. Name the engineered feature or raw feature.",
            "2. State the contract rule: type, range, unit, allowed value, freshness, or null rule.",
            "3. Identify the violation or instability.",
            "4. Explain the downstream model impact.",
            "5. Define the pipeline control and monitoring response.",
        ],
        "mission_bridge": _bridge("feature engineering and feature contracts"),
        "mcqs": [
            {
                "question": "What is the best description of a feature contract?",
                "options": ["A list of all features that might improve accuracy.", "A rule set defining valid type, range, freshness, and allowed values.", "A trainable model parameter.", "A dashboard showing final accuracy."],
                "answer_index": 1,
                "explanation": "A feature contract validates input features before training or inference.",
            },
            {
                "question": "Humidity has valid range 0 to 100. Which value violates the contract?",
                "options": ["30", "45", "60", "110"],
                "answer_index": 3,
                "explanation": "110% humidity is outside the valid range.",
            },
            {
                "question": "Why can adding more features hurt production ML?",
                "options": ["Models cannot use more than three features.", "Irrelevant or unstable features add noise and fragile dependencies.", "Features are only for deep learning.", "Feature engineering removes monitoring needs."],
                "answer_index": 1,
                "explanation": "Feature quality, stability, availability, and meaning matter more than count.",
            },
            {
                "question": "Temperature readings started arriving in Fahrenheit instead of Celsius. What failed?",
                "options": ["The feature contract did not enforce unit/range expectations.", "The model needed a higher learning rate.", "Precision was too high.", "The target label was missing from the dashboard."],
                "answer_index": 0,
                "explanation": "Unit mismatch is a feature contract and pipeline validation failure.",
            },
        ],
    },
    "mlf_013": {
        "plain_language": "Categorical variables are labels, not numbers. Encoding is the controlled conversion of those labels into numeric signals. Safe encoding means the conversion is fitted on training data only, reused unchanged in validation/test/production, and has an explicit plan for unseen categories.",
        "worked_example": "For Size = Small, Medium, Large, one-hot encoding creates size_small, size_medium, and size_large. A Small record becomes [1, 0, 0]. If Extra Large appears in production, the system should not crash. It should route it to an unknown bucket, ignore it safely, or trigger a controlled retraining review depending on risk.",
        "production_trap": "Treating encoding as a notebook step instead of a production contract. The model trains with one set of columns, then production sends a new category or different column order, and prediction fails or silently becomes wrong.",
        "mission_hint": "Use this pattern: identify category type, choose encoding, state how the encoder is fitted, state how unseen categories are handled, and name the production control that prevents mismatch.",
        "key_distinctions": [
            "Nominal categories have no natural order, such as station_type = station, equipment, electrical_board. One-hot encoding is usually safer than assigning 1, 2, 3.",
            "Ordinal categories have meaningful order, such as low, medium, high. Ordinal encoding can be valid only when the order and spacing make sense.",
            "High-cardinality categories have many values, such as supplier_id, user_id, item_id, or fault_code. One-hot may explode feature space.",
            "Unseen categories are production reality. Use unknown bucket, handle_unknown='ignore'-style behavior, feature contracts, unknown-rate monitoring, and retraining triggers.",
        ],
        "answer_frame": [
            "1. Name whether the feature is nominal, ordinal, binary, or high-cardinality.",
            "2. Pick the encoding method and justify why it preserves meaning.",
            "3. State that the encoder is fitted on training data only and reused for validation, test, and inference.",
            "4. State how unseen categories are handled without crashing prediction.",
            "5. Add controls: saved encoder artifact, feature contract, unknown-category monitoring, alert threshold, and retraining owner.",
        ],
        "mission_bridge": [
            {"mission_type": "concept_check", "tested_skill": "Explain safe encoding, not just 'convert text to numbers'.", "use_from_booster": "Define nominal vs ordinal, false numeric order risk, and unseen-category handling."},
            {"mission_type": "tiny_hands_on", "tested_skill": "Translate a category list into one-hot columns and handle a new category.", "use_from_booster": "Show binary columns, then state unknown bucket / ignore / retraining review as handling strategy."},
            {"mission_type": "failure_diagnosis", "tested_skill": "Diagnose why production failed when a new category appeared.", "use_from_booster": "Separate symptom, cause, prevention, and control: new category, encoder mismatch, unknown handling, feature contract."},
            {"mission_type": "architect_decision", "tested_skill": "Design a robust encoding strategy for recommendation or manufacturing systems.", "use_from_booster": "Mention cardinality, training-only fitting, saved encoder, unknown-rate monitoring, leakage avoidance, retraining trigger."},
            {"mission_type": "teachback", "tested_skill": "Explain production risk in simple interview language.", "use_from_booster": "Use one business example: the model cannot safely use new categories unless the encoding pipeline knows what to do."},
        ],
        "mcqs": [
            {"question": "Station type has values station, equipment, and electrical_board. What kind of categorical feature is this?", "options": ["Ordinal, because there are three values.", "Nominal, because the values have no natural order.", "Continuous, because models need numbers.", "Target, because it affects defects."], "answer_index": 1, "explanation": "The values are labels without natural order. Assigning 1, 2, 3 creates fake ranking."},
            {"question": "Risk level has values low, medium, and high. When can ordinal encoding be reasonable?", "options": ["When the order carries meaning for the model decision.", "Whenever there are exactly three categories.", "Only when the feature is the target label.", "Never. Ordinal encoding is always leakage."], "answer_index": 0, "explanation": "Ordinal encoding is reasonable only when the order is real and useful."},
            {"question": "A one-hot encoder is trained on Small, Medium, Large. Production receives Extra Large. What should a safe pipeline do?", "options": ["Crash so the data scientist notices later.", "Silently map Extra Large to Large.", "Use an explicit unknown-category strategy and monitor unknown rate.", "Refit the encoder on the single production request."], "answer_index": 2, "explanation": "Unseen categories need explicit runtime handling. Re-fitting live changes the input contract."},
            {"question": "What is the leakage risk in target encoding?", "options": ["Using validation/test/future labels to calculate category statistics.", "Saving the fitted encoder with the model.", "Handling unknown categories explicitly.", "Using the same encoder in training and inference."], "answer_index": 0, "explanation": "Target encoding uses label statistics, so it must avoid validation/test/future labels."},
        ],
    },
    "mlf_014": {
        "plain_language": "Scaling changes feature ranges. Normalization makes numeric features comparable. Pipeline leakage happens when those transformation parameters are learned from data the model should not have seen.",
        "worked_example": "If you calculate mean and standard deviation using train + test data, the test set has influenced preprocessing. The model evaluation is now contaminated.",
        "production_trap": "Fitting a scaler separately in production creates a different transformation from training, so the model receives inputs in a shape it was not trained to interpret.",
        "mission_hint": "Always say: fit preprocessing on training data only, save the fitted transformer, reuse it for validation/test/inference, and monitor input ranges.",
        "key_distinctions": [
            "Fit means learning parameters like mean, standard deviation, min, or max. Transform means applying already-learned parameters.",
            "Training-time preprocessing must be reused in inference. Do not refit on validation/test/production data.",
            "Scaling affects model behavior strongly for distance-based and gradient-based models, but less for tree models.",
            "Leakage can enter through preprocessing even when the model training code looks clean.",
        ],
        "answer_frame": [
            "1. Identify the numeric features and why scaling is needed or not needed.",
            "2. State what parameters the scaler learns.",
            "3. State fit-on-train-only and transform validation/test/inference.",
            "4. Name the leakage risk if future/test data is used.",
            "5. Add controls: pipeline object, saved transformer, feature contract, monitoring of input ranges.",
        ],
        "mission_bridge": _bridge("scaling, normalization, and pipeline leakage"),
        "mcqs": [
            {"question": "Where should a scaler be fitted?", "options": ["All available data", "Training data only", "Test data only", "Each production batch separately"], "answer_index": 1, "explanation": "The scaler learns parameters from training data only, then applies them downstream."},
            {"question": "What is leakage in scaling?", "options": ["Using test/future data to learn preprocessing parameters.", "Saving the scaler with the model.", "Transforming validation data with the training scaler.", "Checking input ranges."], "answer_index": 0, "explanation": "Using data outside training to learn preprocessing contaminates evaluation."},
            {"question": "What is the difference between fit and transform?", "options": ["Fit learns parameters; transform applies them.", "They are always identical.", "Transform learns labels.", "Fit is only for dashboards."], "answer_index": 0, "explanation": "This distinction is central to avoiding preprocessing leakage."},
            {"question": "Which model family is usually most sensitive to feature scale?", "options": ["Distance/gradient-based models", "Decision trees only", "Rule engines only", "SQL queries"], "answer_index": 0, "explanation": "Models using distance or gradient updates can be strongly affected by scale."},
        ],
    },
    "mlf_015": {
        "plain_language": "Regularization adds a penalty for unnecessary complexity. It controls overfitting by discouraging a model from chasing noise.",
        "worked_example": "If a linear model uses huge coefficients to fit small historical quirks, L2 regularization pushes weights toward smaller values so the model generalizes better.",
        "production_trap": "Too little regularization overfits; too much regularization underfits and misses real defect drivers.",
        "mission_hint": "Discuss the trade-off: lower variance without creating too much bias. Mention validation curves or train-vs-validation behavior.",
        "key_distinctions": [
            "L1 can drive some coefficients to zero and support feature selection.",
            "L2 discourages large weights and usually keeps features with smaller coefficients.",
            "Regularization strength is a hyperparameter chosen through validation, not guessed emotionally.",
            "Regularization is not data cleaning. It cannot fix leakage, wrong labels, or missing production features.",
        ],
        "answer_frame": [
            "1. State what complexity problem exists.",
            "2. Name whether L1, L2, or another control is appropriate.",
            "3. Explain the bias-variance effect.",
            "4. Use validation performance to justify strength.",
            "5. State the production risk of under- or over-regularization.",
        ],
        "mission_bridge": _bridge("regularization and model complexity"),
        "mcqs": [
            {"question": "What does regularization mainly control?", "options": ["Model complexity", "Database latency", "Label creation", "Dashboard count"], "answer_index": 0, "explanation": "Regularization penalizes complexity so the model is less likely to chase noise."},
            {"question": "What can too much regularization cause?", "options": ["Underfitting", "Guaranteed perfect recall", "Data leakage", "More categories"], "answer_index": 0, "explanation": "Too much constraint can make the model too simple."},
            {"question": "Which regularization can push some coefficients exactly to zero?", "options": ["L1", "L2", "Train/test split", "Confusion matrix"], "answer_index": 0, "explanation": "L1 can create sparse models by zeroing some coefficients."},
            {"question": "How should regularization strength be chosen?", "options": ["Validation strategy", "Alphabetical order", "Production uptime", "Stakeholder seniority"], "answer_index": 0, "explanation": "Regularization strength is tuned using validation evidence."},
        ],
    },
    "mlf_016": {
        "plain_language": "Threshold tuning turns model scores into decisions. A default 0.5 threshold is rarely a business policy.",
        "worked_example": "If missing a defect is expensive, you may lower the defect threshold to catch more defects, accepting extra false alarms and inspection workload.",
        "production_trap": "Teams optimize threshold on generic accuracy instead of false-negative cost, false-positive workload, and operational capacity.",
        "mission_hint": "Name the cost of false positives, false negatives, minimum recall target, acceptable alert volume, and owner of threshold changes.",
        "key_distinctions": [
            "Model score is not the same as final decision.",
            "Lowering a positive threshold often increases recall and lowers precision.",
            "Raising a threshold often increases precision and lowers recall.",
            "Thresholds should be chosen from validation data and business cost, then monitored after go-live.",
        ],
        "answer_frame": [
            "1. State the decision being made from the score.",
            "2. Identify which error is costlier: false positive or false negative.",
            "3. Choose the metric priority and threshold direction.",
            "4. State operational constraints such as inspection capacity.",
            "5. Define monitoring, review cadence, and threshold owner.",
        ],
        "mission_bridge": _bridge("threshold tuning and cost-sensitive decisions"),
        "mcqs": [
            {"question": "If false negatives are more costly than false positives, which metric often becomes more important?", "options": ["Recall", "Training accuracy", "Model size", "Feature count"], "answer_index": 0, "explanation": "Recall measures how many actual positives are caught."},
            {"question": "What usually happens when the positive threshold is lowered?", "options": ["Recall increases, false positives may increase.", "All errors disappear.", "Precision always becomes 100%.", "The model retrains itself."], "answer_index": 0, "explanation": "Lower thresholds catch more positives but can create more false alarms."},
            {"question": "Why is 0.5 not automatically the right threshold?", "options": ["It ignores business cost and class distribution.", "It is illegal.", "It only works in Python.", "It requires deep learning."], "answer_index": 0, "explanation": "Thresholds should reflect business cost and validation evidence."},
            {"question": "Who should own threshold changes in production?", "options": ["A defined process owner with monitoring evidence.", "Anyone with dashboard access.", "Only the model file.", "Nobody."], "answer_index": 0, "explanation": "Threshold changes affect operations and need ownership/governance."},
        ],
    },
    "mlf_017": {
        "plain_language": "Class imbalance means one class dominates the data. The model can look good while ignoring the rare class that matters most.",
        "worked_example": "If defects are 2% of cases, predicting no defect every time gives 98% accuracy and zero defect detection.",
        "production_trap": "Teams report high accuracy and miss that defect-class recall is unusable.",
        "mission_hint": "Discuss class-specific metrics, sampling, class weights, threshold tuning, and the business cost of missed minority cases.",
        "key_distinctions": [
            "Imbalance is not automatically bad; it is dangerous when the minority class carries business risk.",
            "Accuracy is weak on imbalanced data because majority-class correctness dominates the score.",
            "Sampling changes data distribution; class weights change training penalty; threshold tuning changes decisions.",
            "Evaluation must report minority-class precision, recall, F1, confusion matrix, and segment behavior.",
        ],
        "answer_frame": [
            "1. State the class distribution and minority class risk.",
            "2. Explain why accuracy is misleading.",
            "3. Choose relevant metrics for the minority class.",
            "4. Propose handling: sampling, class weights, thresholding, or data collection.",
            "5. State production monitoring for class distribution and recall.",
        ],
        "mission_bridge": _bridge("class imbalance handling"),
        "mcqs": [
            {"question": "Which metric is dangerous to use alone on imbalanced defect data?", "options": ["Accuracy", "Recall", "Precision", "Confusion matrix"], "answer_index": 0, "explanation": "Accuracy can be inflated by majority-class predictions."},
            {"question": "A model predicts no defects in a 98% good-parts dataset. What is likely true?", "options": ["Accuracy may be high but defect recall is zero.", "Recall must be perfect.", "Precision is always 100%.", "No monitoring is needed."], "answer_index": 0, "explanation": "The model can look accurate while missing all defects."},
            {"question": "What does class weighting change?", "options": ["The penalty the model sees for mistakes by class.", "The physical sensor units.", "The deployment server.", "The number of dashboards."], "answer_index": 0, "explanation": "Class weights make mistakes on important/rare classes costlier during training."},
            {"question": "What should be monitored after deploying an imbalance-sensitive model?", "options": ["Class distribution and minority-class recall.", "Only API uptime.", "Only model file size.", "Only training accuracy."], "answer_index": 0, "explanation": "Production class mix and minority-class performance can drift."},
        ],
    },
    "mlf_018": {
        "plain_language": "Error analysis means finding where the model fails, not just how much it fails overall.",
        "worked_example": "A 12% error rate is less useful than knowing errors concentrate in night shift, supplier B, and high-humidity batches.",
        "production_trap": "Teams average errors across all cases and miss concentrated failure pockets that create real operational damage.",
        "mission_hint": "Segment failures by plant, product, supplier, shift, time, defect type, confidence band, and data source before recommending fixes.",
        "key_distinctions": [
            "Aggregate error rate tells size of the problem; error analysis tells shape of the problem.",
            "Error clusters often reveal data gaps, process changes, sensor issues, or segment-specific drift.",
            "False positives and false negatives need separate analysis because they create different costs.",
            "Good error analysis leads to targeted action: data collection, feature fix, threshold change, retraining, or process review.",
        ],
        "answer_frame": [
            "1. State the observed error pattern.",
            "2. Segment errors by relevant operational dimensions.",
            "3. Separate false positives and false negatives.",
            "4. Identify likely root cause and evidence to confirm.",
            "5. Recommend targeted remediation and monitoring.",
        ],
        "mission_bridge": _bridge("error analysis and model debugging"),
        "mcqs": [
            {"question": "What is the main purpose of error analysis?", "options": ["Find patterns in model failures.", "Increase dataset size blindly.", "Replace all simple models.", "Avoid monitoring."], "answer_index": 0, "explanation": "Error analysis identifies where and why predictions fail."},
            {"question": "Why segment errors by plant or shift?", "options": ["To detect hidden failure pockets.", "To make charts prettier.", "To remove labels.", "To avoid metrics."], "answer_index": 0, "explanation": "Failures are often concentrated in specific production contexts."},
            {"question": "Why separate false positives from false negatives?", "options": ["They create different operational costs.", "They are the same error.", "Only false positives matter.", "Only dashboards use them."], "answer_index": 0, "explanation": "Different error types require different fixes and business trade-offs."},
            {"question": "Which is a targeted action after error analysis?", "options": ["Collect more data for the failing segment.", "Ignore the segment.", "Report only average accuracy.", "Delete the validation set."], "answer_index": 0, "explanation": "Focused remediation beats generic model tweaking."},
        ],
    },
    "mlf_019": {
        "plain_language": "Interpretability explains model behavior, but explanations are not causal proof. They are clues that need domain validation.",
        "worked_example": "A feature may rank high because it correlates with a process condition, not because it directly causes defects.",
        "production_trap": "Stakeholders treat SHAP-style explanations as causal proof and make process changes without experimentation or domain review.",
        "mission_hint": "Separate explanation, correlation, causality, stakeholder action, and governance. Say how you would validate before changing the process.",
        "key_distinctions": [
            "Global explanation describes average model behavior; local explanation describes one prediction.",
            "Feature importance is not causal proof.",
            "Explanations can be unstable if correlated features split importance.",
            "Architects must define how explanations are used, reviewed, audited, and communicated.",
        ],
        "answer_frame": [
            "1. State what the explanation method shows.",
            "2. State what it does not prove.",
            "3. Identify the risk of stakeholder misinterpretation.",
            "4. Define validation: domain review, experiment, process check, or counterfactual test.",
            "5. Add governance: audit trail, explanation limits, approval path.",
        ],
        "mission_bridge": _bridge("interpretability and explainability limits"),
        "mcqs": [
            {"question": "What is a safe way to use model explanations?", "options": ["Use them as clues requiring validation.", "Treat them as causal proof.", "Ignore all explanations.", "Use them to skip testing."], "answer_index": 0, "explanation": "Interpretability is useful, but explanations still need validation."},
            {"question": "What is the risk of correlated features?", "options": ["Importance can be split or unstable across related features.", "Models stop making predictions.", "Labels disappear.", "Recall becomes impossible."], "answer_index": 0, "explanation": "Correlated features can make explanation rankings misleading."},
            {"question": "What is a local explanation?", "options": ["An explanation for one prediction.", "A full retraining pipeline.", "A database backup.", "A global company policy."], "answer_index": 0, "explanation": "Local explanations focus on individual predictions."},
            {"question": "What should an architect define for explanations?", "options": ["Usage limits, audit trail, and review path.", "Only chart color.", "Only model file name.", "Nothing."], "answer_index": 0, "explanation": "Explainability must be governed, not just displayed."},
        ],
    },
    "mlf_020": {
        "plain_language": "ML monitoring checks whether inputs, predictions, metrics, and business outcomes are still trustworthy after deployment.",
        "worked_example": "If humidity distribution shifts and defect recall drops, the monitoring system should trigger investigation before warranty or scrap cost accumulates.",
        "production_trap": "Teams monitor API uptime only and ignore data drift, prediction drift, performance drift, delayed labels, and owner response.",
        "mission_hint": "Mention input drift, prediction drift, performance metrics, alert thresholds, owner, fallback, and retraining trigger.",
        "key_distinctions": [
            "System monitoring checks uptime/latency; ML monitoring checks data and model behavior.",
            "Input drift means feature distribution changed; performance drift means model quality changed.",
            "Prediction drift can be monitored before labels arrive; performance metrics need labels.",
            "A monitor without an owner and response playbook is only a dashboard.",
        ],
        "answer_frame": [
            "1. Name what will be monitored: features, predictions, metrics, business outcomes.",
            "2. Define thresholds and time windows.",
            "3. Separate drift without labels from performance with labels.",
            "4. Define escalation, fallback, and owner.",
            "5. Define retraining trigger and post-retraining validation.",
        ],
        "mission_bridge": _bridge("ML monitoring, drift, and retraining triggers"),
        "mcqs": [
            {"question": "Which is not enough for ML monitoring?", "options": ["API uptime only", "Input drift", "Recall over time", "Prediction distribution"], "answer_index": 0, "explanation": "A healthy API can still serve degraded predictions."},
            {"question": "What is input drift?", "options": ["Feature distribution changed after deployment.", "The model file got larger.", "The dashboard moved.", "The target label was renamed only."], "answer_index": 0, "explanation": "Input drift means incoming data no longer resembles expected/training patterns."},
            {"question": "What can be monitored before labels arrive?", "options": ["Prediction distribution and input drift.", "True recall only.", "Final warranty impact only.", "Manual inspection accuracy only."], "answer_index": 0, "explanation": "Performance metrics need labels, but inputs and predictions can be monitored earlier."},
            {"question": "What makes a retraining trigger useful?", "options": ["Clear threshold, owner, validation, and release process.", "A vague feeling that model is old.", "A monthly meeting only.", "A new algorithm name."], "answer_index": 0, "explanation": "Retraining must be governed by evidence and release controls."},
        ],
    },
}


def _fallback_mcqs(title: str) -> List[Dict[str, Any]]:
    return [
        {
            "question": f"What is the safest way to use {title} in an ML system?",
            "options": [
                "Treat it as a definition only.",
                "Connect it to model behavior, evaluation, and production controls.",
                "Mention it only during interviews.",
                "Ignore it once the model trains successfully.",
            ],
            "answer_index": 1,
            "explanation": "Architect-level understanding connects the concept to decisions and controls.",
        },
        {
            "question": "What usually makes an ML answer stronger?",
            "options": [
                "A generic definition only.",
                "A concrete scenario, failure mode, metric/check, and control.",
                "Repeating the question.",
                "Avoiding production implications.",
            ],
            "answer_index": 1,
            "explanation": "Strong answers connect concept, evidence, and production action.",
        },
    ]


def _fallback_key_distinctions(concept_note: Dict[str, Any], architect_note: Dict[str, Any]) -> List[str]:
    distinctions: List[str] = []
    wrong = str(concept_note.get("wrong_mental_model", "")).strip()
    correct = str(concept_note.get("correct_mental_model", "")).strip()
    if wrong and correct:
        distinctions.append(f"Wrong vs correct mental model: {wrong} Instead, {correct}")
    risks = architect_note.get("production_risks", []) or []
    for risk in risks[:2]:
        distinctions.append(str(risk))
    return distinctions[:3]


def _mission_bridge_from_questions(booster: Dict[str, Any], questions: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    configured = booster.get("mission_bridge", []) or []
    if configured:
        return configured

    bridge: List[Dict[str, str]] = []
    for question in questions:
        qtype = str(question.get("type", "mission"))
        expected = question.get("expected_focus", []) or []
        expected_text = "; ".join(str(item) for item in expected[:3])
        if not expected_text:
            expected_text = "Use the concept, scenario evidence, failure mode, and production control."
        bridge.append(
            {
                "mission_type": qtype,
                "tested_skill": MISSION_TYPE_SKILL_MAP.get(qtype, "Apply the concept to the exact mission scenario."),
                "use_from_booster": expected_text,
            }
        )
    return bridge


def build_lesson_booster(topic_id: str, concept_note: Dict[str, Any], architect_note: Dict[str, Any], assessment_doc: Dict[str, Any]) -> Dict[str, Any]:
    """Return copy-safe pre-mission support aligned to final missions.

    Patch 022: for Advanced ML, use the Expert Tutor Blueprint as the source of truth.
    The older ADVANCED_ML_BOOSTERS table remains as a fallback for backward compatibility.
    """
    blueprint_booster = blueprint_to_booster(topic_id)
    if blueprint_booster:
        return blueprint_booster

    title = concept_note.get("title", topic_id)
    base = dict(ADVANCED_ML_BOOSTERS.get(topic_id, {}))

    if not base:
        base = {
            "plain_language": concept_note.get("simple_explanation", ""),
            "worked_example": concept_note.get("tiny_example", ""),
            "production_trap": concept_note.get("edge_case", ""),
            "mission_hint": "Before answering, define the concept, apply it to the scenario, name the failure mode, and state the architecture control.",
            "key_distinctions": _fallback_key_distinctions(concept_note, architect_note),
            "answer_frame": DEFAULT_ANSWER_FRAME,
            "mcqs": _fallback_mcqs(str(title)),
        }

    questions = assessment_doc.get("questions", []) or []
    mission_focus: List[str] = []
    for question in questions:
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
        "key_distinctions": base.get("key_distinctions", []) or _fallback_key_distinctions(concept_note, architect_note),
        "answer_frame": base.get("answer_frame", []) or DEFAULT_ANSWER_FRAME,
        "mission_bridge": _mission_bridge_from_questions(base, questions),
        "mission_focus": mission_focus[:6],
        "mcqs": base.get("mcqs", []) or _fallback_mcqs(str(title)),
    }
