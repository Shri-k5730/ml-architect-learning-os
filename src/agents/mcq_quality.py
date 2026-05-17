from __future__ import annotations

import hashlib
import random
from copy import deepcopy
from typing import Any, Dict, List


MCQ = Dict[str, Any]


def _mcq(
    kind: str,
    question: str,
    options: List[str],
    answer_index: int,
    explanation: str,
    option_explanations: List[str] | None = None,
) -> MCQ:
    """Create one MCQ.

    Authoring rule: options may be written in any order. Rendering will shuffle them
    deterministically so the correct answer is not predictably option A.
    """
    return {
        "kind": kind,
        "question": question,
        "options": options,
        "answer_index": answer_index,
        "explanation": explanation,
        "option_explanations": option_explanations or [],
    }


def _explanations(items: List[str]) -> List[str]:
    return items


QUALITY_MCQS: Dict[str, List[MCQ]] = {
    "checkpoint_ml_foundations_001": [
        _mcq(
            "Scenario",
            "A defect model reports 96% accuracy, but defect recall is only 30%. What is the safest go-live interpretation?",
            [
                "Unsafe if missed defects carry high business or safety cost, even though aggregate accuracy is high.",
                "Safe to deploy because aggregate accuracy is above 95%.",
                "Safe if precision is high, because recall only matters during training.",
                "The train/test split is automatically invalid because accuracy and recall differ.",
            ],
            0,
            "High accuracy can hide minority-class failure. For defect detection, missed defects can dominate go-live risk.",
            _explanations([
                "Correct. This connects the metric to the business cost of false negatives.",
                "High aggregate accuracy can be a majority-class illusion.",
                "Recall is a production concern when actual defects must be caught.",
                "Metric disagreement does not automatically prove split invalidity; it signals class-level review.",
            ]),
        ),
        _mcq(
            "Trap",
            "Which case is true leakage rather than merely a weak model choice?",
            [
                "A feature created after inspection is used to train a model that must predict before inspection.",
                "A simple baseline outperforms a complex model on validation data.",
                "Recall is lower than precision on the defect class.",
                "A threshold is tuned using a properly isolated validation set.",
            ],
            0,
            "Leakage is availability-bound contamination: the model learns from information unavailable at prediction time.",
            _explanations([
                "Correct. Post-event information contaminates training for a pre-event prediction task.",
                "That is model selection evidence, not leakage.",
                "That is a metric trade-off, not leakage by itself.",
                "Validation-based threshold tuning is legitimate if the validation set is isolated.",
            ]),
        ),
        _mcq(
            "Architecture",
            "Which evidence chain is strongest before a defect model is trusted for production?",
            [
                "Baseline comparison, valid split, leakage review, class-level metrics, threshold policy, and monitoring owner.",
                "High training accuracy, a modern algorithm name, and a dashboard screenshot.",
                "More features than the baseline and a single aggregate accuracy value.",
                "One successful notebook run and stakeholder approval.",
            ],
            0,
            "Production trust comes from a chain of validation and controls, not a single score.",
            _explanations([
                "Correct. It covers evidence, decision policy, and ownership.",
                "Training accuracy and algorithm branding are not enough.",
                "More features can add fragility; aggregate accuracy can hide minority failure.",
                "A notebook run is not production evidence.",
            ]),
        ),
        _mcq(
            "Scenario",
            "A model has a valid train/test split, but the go-live threshold was picked only because the business wanted fewer alerts. What is missing?",
            [
                "A precision-recall operating-point review linked to false-positive and false-negative cost.",
                "A new random train/test split after deployment.",
                "A label encoder, regardless of feature types.",
                "A higher training score, even if recall drops.",
            ],
            0,
            "Thresholds are business decision boundaries. They need evidence, not preference alone.",
            _explanations([
                "Correct. Thresholds should be justified by the FP/FN trade-off.",
                "Changing the split does not justify the threshold.",
                "Encoding is unrelated unless categorical features are the issue.",
                "Training score does not settle production operating point risk.",
            ]),
        ),
    ],
    "mlf_011": [
        _mcq(
            "Scenario",
            "Model A has the highest average validation score, but fails badly for Plant B. Model B has slightly lower average score and stable plant-level recall. Which is the better architect choice for defect detection?",
            [
                "Model B, if Plant B defects matter operationally.",
                "Model A, because the aggregate score is highest.",
                "Whichever model has the most complex algorithm.",
                "Whichever model trained fastest, regardless of segment behavior.",
            ],
            0,
            "Model selection should consider segment reliability, not just aggregate performance.",
            _explanations([
                "Correct. Stable segment performance can matter more than aggregate score.",
                "Aggregate score can hide critical segment failure.",
                "Algorithm complexity is not business evidence.",
                "Training speed is only one operational factor, not the selection rule.",
            ]),
        ),
        _mcq("Trap", "Which model-selection argument is weakest?", ["Highest training accuracy.", "Better recall on the defect class.", "Stable performance across product families.", "Lower latency with acceptable performance."], 0, "Training accuracy alone is not selection evidence.", _explanations(["Correct. Training accuracy can reward memorization.", "Defect recall is relevant if missed defects are costly.", "Segment stability is strong production evidence.", "Latency can matter if performance stays acceptable."])),
        _mcq("Architecture", "What should be defined before comparing candidate models?", ["Selection criteria and business-critical metrics.", "Chart colors and page title.", "The final deployment date only.", "The most impressive algorithm name."], 0, "Define criteria first to avoid cherry-picking.", _explanations(["Correct. Criteria create an objective comparison frame.", "Presentation choices do not define model suitability.", "Deployment date does not define model quality.", "Algorithm name is not evidence."])),
        _mcq("Scenario", "A complex model beats a simple baseline by 0.2%, but is slower, less explainable, and harder to monitor. What is the architect response?", ["Check whether the small gain justifies operational cost and risk.", "Always choose the complex model.", "Reject all baselines after a complex model wins once.", "Skip validation because the difference is small."], 0, "Model selection includes supportability and governance, not just metric gain.", _explanations(["Correct. Architect selection weighs performance against operational burden.", "Complexity needs justification.", "Baselines remain useful evidence.", "Small differences need stronger validation, not skipped validation."])),
    ],
    "mlf_012": [
        _mcq("Scenario", "A feature is highly predictive in training but arrives 48 hours late in production. What is the core issue?", ["Feature availability mismatch between training and inference.", "The model needs deeper neural layers.", "The target label should be one-hot encoded.", "Accuracy is invalid for every dataset."], 0, "A training-useful feature is unsafe if unavailable at prediction time.", _explanations(["Correct. Feature availability is part of the feature contract.", "Architecture depth does not solve missing production availability.", "Label encoding is unrelated here.", "Accuracy may be incomplete, but this issue is feature availability."])),
        _mcq("Trap", "Which is a feature contract rule rather than feature engineering?", ["temperature_celsius must be numeric, Celsius, and between -30 and 80.", "Create a rolling average temperature feature.", "Derive shift_duration from timestamps.", "Group rare supplier IDs into an 'other' bucket."], 0, "A contract defines validity expectations; engineering creates or transforms signals.", _explanations(["Correct. This defines allowed type/unit/range.", "This creates a feature.", "This derives a feature.", "This transforms categories; the contract would define validity."])),
        _mcq("Architecture", "A sensor silently changes from Celsius to Fahrenheit. Which control should catch it first?", ["Unit and range validation in the feature contract.", "A higher learning rate.", "More epochs.", "A different split after deployment."], 0, "Unit/range checks are feature-contract responsibilities.", _explanations(["Correct. The pipeline should reject or flag impossible units/ranges.", "Learning rate does not validate units.", "More epochs do not fix input contract violations.", "A split change does not catch live unit drift."])),
        _mcq("Scenario", "Adding 50 features improves training score but worsens validation score. What is the likely lesson?", ["More features can add noise and overfitting risk.", "Validation is unnecessary.", "All extra features are causal.", "Feature contracts only apply to labels."], 0, "Feature quantity is not signal quality.", _explanations(["Correct. Extra features can increase fragility.", "Validation exposed the problem.", "Predictive signal is not causal proof.", "Feature contracts apply to input features."])),
    ],
    "mlf_013": [
        _mcq("Scenario", "A nominal field station_type has station, equipment, electrical_board. What is the risk of encoding them as 1, 2, 3?", ["The model may infer fake order or distance.", "The model will automatically know they are nominal.", "It prevents all unseen categories.", "It guarantees better accuracy."], 0, "Ordinal numbers create artificial order when none exists.", _explanations(["Correct. Numeric codes can imply ranking/distance.", "Models do not understand semantic category type automatically.", "Encoding known categories does not solve unseen values.", "Encoding choice can harm accuracy."])),
        _mcq("Trap", "When is ordinal encoding acceptable?", ["When the category order is meaningful and useful, such as low < medium < high.", "Whenever there are exactly three categories.", "Whenever one-hot would add columns.", "For all IDs and fault codes."], 0, "Ordinal encoding requires real order.", _explanations(["Correct. The numeric order must match meaning.", "Count of categories does not create order.", "Column count alone does not justify fake order.", "IDs and fault codes are often nominal or high-cardinality."])),
        _mcq("Architecture", "A new category appears during inference. What should happen first?", ["Safe unknown handling plus monitoring, not live retraining.", "Create new production columns on the fly.", "Crash the pipeline so the issue is visible.", "Refit the encoder on production data immediately."], 0, "Runtime needs safe handling first; retraining is a governed follow-up.", _explanations(["Correct. Unknown handling keeps inference stable while monitoring informs review.", "Live new columns break model schema.", "Crashing may be safer than silent corruption in some cases, but not the primary robust design.", "Live refit contaminates inference and destabilizes the artifact."])),
        _mcq("Scenario", "A supplier_id field has 40,000 unique values. What is the main one-hot encoding concern?", ["High-cardinality feature explosion and sparse signals.", "It becomes ordinal automatically.", "It removes the need for validation.", "It guarantees interpretability."], 0, "High cardinality can create huge sparse feature spaces.", _explanations(["Correct. One-hot can explode dimensionality.", "One-hot is not ordinal by itself.", "Validation is still required.", "Large sparse encodings are not automatically interpretable."])),
    ],
    "mlf_014": [
        _mcq("Scenario", "A KNN defect model uses temperature range 20-40 and runtime_seconds range 0-200000. What is the main risk if you do not scale?", ["runtime_seconds can dominate distance because its numeric range is much larger.", "Temperature becomes the target label.", "KNN automatically ignores larger-range features.", "Scaling itself causes label leakage."], 0, "Distance-based models can be dominated by large-range features.", _explanations(["Correct. Distance is numerically dominated by the largest scale.", "Feature scaling does not change the label.", "KNN uses distances; it does not automatically ignore magnitude.", "Scaling is not leakage; fitting scaling parameters on the wrong data is leakage."])),
        _mcq("Trap", "You split train/test, fit a scaler on training only, then transform test using the saved scaler. Is this leakage?", ["No. This is the correct fit/transform pattern.", "Yes, because test data was transformed.", "Yes, because all scaling is leakage.", "No, but only if the model is a decision tree."], 0, "Transforming test with train-fitted parameters is correct. Fitting on test/full data is the leak.", _explanations(["Correct. Fit belongs to training; transform applies learned parameters.", "Test transformation is expected; test fitting is the problem.", "Scaling itself is not leakage.", "The fit/transform boundary matters regardless of model family."])),
        _mcq("Architecture", "A production value is outside the training min/max range. What should the pipeline do first?", ["Apply the saved transformer, flag/monitor the event, and follow the response policy.", "Refit the scaler live on production data.", "Silently delete the row.", "Disable monitoring because the API is healthy."], 0, "Out-of-range values require monitoring and response, not live refit.", _explanations(["Correct. Production should be stable and observable.", "Live refit changes the model pipeline without validation.", "Deletion can hide operational problems.", "API health does not mean model input health."])),
        _mcq("Trap", "Which model family is usually least sensitive to feature scaling?", ["Tree-based models such as decision trees/random forests.", "KNN.", "SVM with distance/kernel behavior.", "PCA."], 0, "Tree splits are usually less affected by monotonic scaling, though pipeline consistency still matters.", _explanations(["Correct. Tree split logic is usually less scale-sensitive.", "KNN is distance-sensitive.", "SVM can be scale-sensitive.", "PCA is variance/magnitude-sensitive."])),
    ],
    "mlf_015": [
        _mcq("Scenario", "A model has very low training error but much higher validation error. What is regularization mainly trying to reduce?", ["Overfitting caused by excessive model complexity.", "Underfitting caused by too little model capacity.", "Data leakage from fitting preprocessing on test data.", "Label imbalance caused by rare positives."], 0, "Regularization adds a complexity penalty to reduce overfitting and improve generalization.", _explanations(["Correct. This is the classic high-variance pattern.", "Underfitting would usually hurt both train and validation.", "Leakage is a different pipeline problem.", "Imbalance may matter, but this symptom points to complexity/overfit."])),
        _mcq("Trap", "Which statement best separates L1 and L2 regularization?", ["L1 can drive some coefficients to zero; L2 usually shrinks coefficients without necessarily zeroing them.", "L2 removes rows from the dataset; L1 changes the train/test split.", "L1 is only for neural networks; L2 is only for dashboards.", "L1 improves recall; L2 improves precision by definition."], 0, "L1 encourages sparsity; L2 discourages large weights smoothly.", _explanations(["Correct. This is the key coefficient behavior difference.", "Neither regularization changes rows or splits.", "Both are broader than one model family, and dashboards are irrelevant.", "Metric movement depends on data and threshold, not the regularizer name."])),
        _mcq("Architecture", "How should regularization strength be selected?", ["Choose the value that gives the best validation behavior without collapsing training performance.", "Choose the largest value because more regularization is always safer.", "Choose the smallest value because regularization always hurts models.", "Choose it from stakeholder preference without validation evidence."], 0, "Regularization strength is a hyperparameter selected from validation behavior.", _explanations(["Correct. You tune against underfit/overfit behavior.", "Too much regularization can underfit.", "Too little regularization can overfit.", "Stakeholders define trade-offs, not unsupported hyperparameters."])),
        _mcq("Scenario", "After very strong regularization, both training and validation scores become poor. What likely happened?", ["The model became underfit because useful signal was suppressed.", "The model became overfit because it memorized noise.", "The model leaked validation data into training.", "The model is now production-ready because both scores are low."], 0, "Too much regularization can make the model too simple.", _explanations(["Correct. Poor train and validation scores indicate underfitting.", "Overfit usually has good train and poor validation.", "Leakage often makes validation look too good, not poor.", "Low scores are not production evidence."])),
    ],
    "mlf_016": [
        _mcq("Scenario", "A defect model outputs calibrated risk scores, but the default 0.5 threshold misses too many defects. What should you tune?", ["The decision threshold based on false-positive and false-negative cost.", "The feature names only.", "API uptime only.", "The train/test split after deployment."], 0, "Threshold tuning chooses a business operating point for model scores.", _explanations(["Correct. Threshold controls alerting trade-off.", "Names do not set the decision boundary.", "Uptime does not govern classification trade-off.", "Changing split after deployment does not set go-live threshold."])),
        _mcq("Trap", "What often happens when you lower the positive-class threshold?", ["Recall increases, while precision may fall.", "Precision and recall both always increase.", "Labels change from negative to positive in the training data.", "The model retrains automatically."], 0, "Lower thresholds catch more positives but can increase false positives.", _explanations(["Correct. Lower threshold usually increases sensitivity.", "There is usually a trade-off.", "Thresholding does not alter ground-truth labels.", "Threshold change is not retraining."])),
        _mcq("Architecture", "What must be defined before approving a production threshold?", ["False-negative cost, false-positive cost, operating constraints, and owner for review.", "Only the algorithm name.", "Only the UI theme.", "Training accuracy only."], 0, "The threshold is a business decision boundary.", _explanations(["Correct. Threshold approval needs business and operational context.", "Algorithm name is insufficient.", "UI is irrelevant to operating-point risk.", "Training accuracy does not decide threshold."])),
        _mcq("Scenario", "Inspection can handle only 100 alerts/day. Which control matters alongside recall?", ["Precision or alert-volume constraint.", "Only model file size.", "Only training loss.", "Only the number of features."], 0, "Alert workload constrains how aggressive the threshold can be.", _explanations(["Correct. Recall must be balanced against operational capacity.", "File size does not control alert burden.", "Training loss is not inspection capacity.", "Feature count is not alert volume."])),
    ],
    "mlf_017": [
        _mcq("Scenario", "A dataset has 98% non-defects and 2% defects. A model predicts non-defect for everything. Which metric exposes the failure best?", ["Recall for the defect class.", "Aggregate accuracy only.", "API latency.", "Number of columns."], 0, "Minority-class recall shows whether actual defects are caught.", _explanations(["Correct. Recall reveals missed positives.", "Accuracy can look high in imbalanced data.", "Latency is operational, not detection quality.", "Column count does not expose minority failure."])),
        _mcq("Trap", "Which imbalance fix can help but may distort probability interpretation if used carelessly?", ["Over/under-sampling.", "Saving the model artifact.", "Adding a dashboard.", "Changing chart color."], 0, "Sampling changes class distribution and must be validated carefully.", _explanations(["Correct. Sampling affects the data distribution seen by the learner.", "Artifact saving is deployment hygiene.", "Dashboards do not fix imbalance.", "Chart color is irrelevant."])),
        _mcq("Architecture", "What should imbalance handling be tied to?", ["Business cost of missed positives versus false alarms.", "Only row count.", "Only model brand.", "Only training speed."], 0, "Imbalance is a decision-risk problem, not only a data ratio problem.", _explanations(["Correct. The business cost defines the target trade-off.", "Row count alone is not enough.", "Model brand is not a trade-off policy.", "Speed is secondary unless it constrains deployment."])),
        _mcq("Scenario", "Class weighting improves recall but precision falls sharply. What is the right next step?", ["Review the precision-recall trade-off and alert workload.", "Declare the model impossible.", "Ignore precision entirely.", "Use accuracy only."], 0, "You need an operating point, not a single metric.", _explanations(["Correct. Improved recall may be good, but false alarms must be governed.", "This is normal trade-off behavior, not impossibility.", "Precision affects trust and workload.", "Accuracy hides minority dynamics."])),
    ],
    "mlf_018": [
        _mcq("Scenario", "Overall recall is acceptable, but recall is poor for one product family. What should error analysis do?", ["Slice errors by product family and investigate data/model causes.", "Stop at the aggregate metric.", "Assume the API is broken.", "Remove all labels."], 0, "Error analysis searches for segment-level failure pockets.", _explanations(["Correct. Segment slicing finds hidden weaknesses.", "Aggregate metrics can hide segment failures.", "API health is not the only explanation.", "Removing labels destroys evaluation."])),
        _mcq("Trap", "Which is not good error analysis?", ["Only saying the model score is low.", "Reviewing false negatives.", "Checking segment-level performance.", "Inspecting misclassified examples."], 0, "Useful error analysis names where and why the model fails.", _explanations(["Correct. It names no mechanism or segment.", "False negatives are important evidence.", "Segment checks are central.", "Misclassified examples can reveal patterns."])),
        _mcq("Architecture", "What should error analysis feed into?", ["Data fixes, feature changes, threshold decisions, or model selection.", "Only a static report.", "Only badge awards.", "Only UI styling."], 0, "Findings must change the system or decision process.", _explanations(["Correct. Error analysis should produce action.", "A report without action is weak governance.", "Badges are unrelated.", "UI styling does not fix model errors."])),
        _mcq("Scenario", "Most false negatives occur on night-shift data. What is a plausible next investigation?", ["Shift-specific sensor/process distribution and label quality.", "Only whether the app is online.", "Only whether Python version changed.", "Only overall accuracy."], 0, "Segment failures often point to data/process differences.", _explanations(["Correct. Night shift may have different distributions or labels.", "Uptime does not explain segment-specific recall.", "Runtime version is unlikely to explain only night-shift misses.", "Overall accuracy hides the segment issue."])),
    ],
    "mlf_019": [
        _mcq("Scenario", "SHAP says humidity is important for defect prediction. What can you safely conclude?", ["Humidity is a useful clue in model behavior, not causal proof.", "Humidity definitely causes defects.", "No domain review is needed.", "The model cannot be wrong."], 0, "Explanations are clues, not causal proof.", _explanations(["Correct. Importance explains model behavior, not root causality.", "Causality needs stronger evidence.", "Domain review remains important.", "Explanations do not prove correctness."])),
        _mcq("Trap", "What is the difference between local and global explanation?", ["Local explains one prediction; global summarizes broader model behavior.", "They are identical.", "Global is only for SQL.", "Local means production server."], 0, "Local and global explanations answer different questions.", _explanations(["Correct. Local is instance-level; global is model-level.", "They answer different scopes.", "SQL is irrelevant.", "Local does not mean server locality."])),
        _mcq("Architecture", "What should accompany explanation dashboards in production governance?", ["Usage limits, audit trail, domain review, and action approval path.", "No caveats, because explanations are always causal.", "Automatic process changes without review.", "Only aggregate accuracy."], 0, "Explanation outputs need governance.", _explanations(["Correct. Explanations can influence decisions and need controls.", "Explanations are not causal proof.", "Automatic action without review is risky.", "Accuracy does not govern explanation use."])),
        _mcq("Scenario", "Two correlated features alternate as top importance across model versions. What is the risk?", ["Importance may be unstable and should not be overinterpreted.", "Both are proven causal.", "The model is unusable by default.", "Monitoring is no longer needed."], 0, "Correlated features can distort or split importance.", _explanations(["Correct. Attribution can shift among correlated signals.", "Correlation/importance is not causality.", "Instability requires review, not automatic rejection.", "Monitoring remains necessary."])),
    ],
    "mlf_020": [
        _mcq("Scenario", "The model API is healthy, but defect recall has dropped after a process change. What did uptime monitoring miss?", ["Model performance or behavior drift.", "Server availability.", "Network latency only.", "The model filename."], 0, "A live service can still produce bad predictions.", _explanations(["Correct. Model monitoring must track behavior, not just service health.", "Availability was already healthy.", "Latency is only one operational metric.", "Filename does not reveal drift."])),
        _mcq("Trap", "Which signal can be monitored before true labels arrive?", ["Input and prediction distribution drift.", "Final recall only.", "Warranty claim outcome only.", "True precision only."], 0, "Labels may be delayed, but input/prediction drift can be watched earlier.", _explanations(["Correct. These are early-warning signals.", "Recall needs labels.", "Warranty outcomes may be delayed.", "Precision needs labels."])),
        _mcq("Architecture", "What makes a retraining trigger operationally useful?", ["Threshold, time window, owner, validation gate, and release process.", "A vague calendar reminder.", "A dashboard with no owner.", "Only training data size."], 0, "Retraining must be governed and validated.", _explanations(["Correct. Retraining is a controlled release process.", "A reminder is not a trigger policy.", "No owner means no accountability.", "Size alone does not define readiness."])),
        _mcq("Scenario", "Input drift alert fires, but performance labels are delayed. What is the sensible response?", ["Investigate, increase monitoring, consider fallback if risk is high, and wait for labels before retraining approval.", "Retrain immediately with production data without validation.", "Ignore because API uptime is fine.", "Delete the model."], 0, "Input drift is evidence for review, not automatic retraining.", _explanations(["Correct. Drift response should be staged and governed.", "Immediate unvalidated retraining is risky.", "API uptime does not dismiss input drift.", "Deletion is not a measured response."])),
    ],
}


def _stable_seed(topic_id: str, idx: int, question: str) -> int:
    digest = hashlib.sha256(f"{topic_id}|{idx}|{question}".encode("utf-8")).hexdigest()
    return int(digest[:16], 16)


def _shuffle_mcq(topic_id: str, idx: int, item: MCQ) -> MCQ:
    shuffled = deepcopy(item)
    options = list(shuffled.get("options", []) or [])
    if len(options) <= 1:
        return shuffled

    answer_index = int(shuffled.get("answer_index", -1))
    if answer_index < 0 or answer_index >= len(options):
        return shuffled

    option_explanations = list(shuffled.get("option_explanations", []) or [])
    if len(option_explanations) != len(options):
        option_explanations = ["" for _ in options]

    indices = list(range(len(options)))
    random.Random(_stable_seed(topic_id, idx, str(shuffled.get("question", "")))).shuffle(indices)

    shuffled["options"] = [options[i] for i in indices]
    shuffled["option_explanations"] = [option_explanations[i] for i in indices]
    shuffled["answer_index"] = indices.index(answer_index)
    shuffled["option_order_seed"] = _stable_seed(topic_id, idx, str(shuffled.get("question", "")))
    return shuffled


def normalize_and_shuffle_mcqs(topic_id: str, mcqs: List[MCQ]) -> List[MCQ]:
    """Return MCQs with stable shuffled answer order.

    Stable shuffle prevents answer-position gaming while avoiding Streamlit rerun
    reshuffling that would invalidate a learner's selected radio option.
    """
    normalized: List[MCQ] = []
    for idx, item in enumerate(mcqs or [], start=1):
        normalized.append(_shuffle_mcq(str(topic_id or ""), idx, item))
    return normalized


def get_quality_mcqs(topic_id: str, fallback: List[MCQ] | None = None) -> List[MCQ]:
    configured = QUALITY_MCQS.get(str(topic_id or ""))
    source = deepcopy(configured if configured else (fallback or []))
    return normalize_and_shuffle_mcqs(str(topic_id or ""), source)
