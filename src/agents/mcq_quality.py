from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, List


def _mcq(kind: str, question: str, options: List[str], answer_index: int, explanation: str, option_explanations: List[str] | None = None) -> Dict[str, Any]:
    return {
        "kind": kind,
        "question": question,
        "options": options,
        "answer_index": answer_index,
        "explanation": explanation,
        "option_explanations": option_explanations or [],
    }

QUALITY_MCQS: Dict[str, List[Dict[str, Any]]] = {
    "checkpoint_ml_foundations_001": [
        _mcq("Scenario", "A defect model has 96% accuracy, but recall for actual defects is 30%. What is the safest go-live interpretation?", ["Deploy because aggregate accuracy is high.", "Unsafe if missed defects carry high business or safety cost.", "Ignore recall because precision is enough.", "Only compare against training accuracy."], 1, "Low recall means many real defects are missed, so aggregate accuracy is not enough for go-live."),
        _mcq("Trap", "Which situation is leakage rather than just poor model choice?", ["A simple baseline beats a complex model.", "A feature created after inspection is used during training.", "Recall is lower than precision.", "A threshold is tuned on validation data."], 1, "Post-event information contaminates training/evaluation because it would not be available at prediction time."),
        _mcq("Architecture", "What makes a model trust chain production-ready?", ["High training score only.", "Baseline, valid split, leakage review, class-level metrics, threshold policy, and monitoring owner.", "A modern algorithm name.", "More features than the baseline."], 1, "Trust is a chain of evidence and controls, not a single metric."),
        _mcq("Scenario", "A model uses a valid train/test split but chooses a threshold only from business pressure, with no precision-recall review. What is missing?", ["A threshold operating-point analysis.", "A larger notebook.", "A new label encoder.", "A random forest only."], 0, "Threshold changes the FP/FN trade-off, so it must be reviewed against business cost."),
    ],
    "mlf_011": [
        _mcq("Scenario", "Model A has the highest average validation score, but fails badly for Plant B. Model B has slightly lower average score and stable plant-level recall. Which is the better architect choice for defect detection?", ["Model A, because average score is highest.", "Model B, if Plant B defects matter operationally.", "Always choose the newest algorithm.", "Choose whichever trained fastest."], 1, "Segment stability can matter more than aggregate performance."),
        _mcq("Trap", "Which model-selection argument is weakest?", ["Better recall on the defect class.", "Stable performance across product families.", "Highest training accuracy.", "Lower latency with acceptable performance."], 2, "Training accuracy alone is not selection evidence."),
        _mcq("Architecture", "What should be defined before comparing candidate models?", ["The selection criteria and business-critical metrics.", "The chart colors.", "The final deployment date only.", "The name of the algorithm."], 0, "Selection criteria must be defined before comparison to avoid cherry-picking."),
        _mcq("Scenario", "A complex model beats a simple model by 0.2% but is slower, less explainable, and harder to monitor. What is the architect response?", ["Automatically choose the complex model.", "Compare whether the small gain justifies operational cost and risk.", "Reject all baselines.", "Skip validation."], 1, "Model selection includes supportability, not just metric gain."),
    ],
    "mlf_012": [
        _mcq("Scenario", "A feature is available during training but arrives 48 hours late in production. What is the main issue?", ["Feature availability mismatch.", "The model needs a deeper neural network.", "The label must be one-hot encoded.", "Accuracy is always invalid."], 0, "A useful training feature is unsafe if it is unavailable at prediction time."),
        _mcq("Trap", "Which is a feature contract rule, not feature engineering itself?", ["temperature_celsius must be numeric and between -30 and 80.", "Create a rolling average temperature feature.", "Derive shift_duration from timestamps.", "Group rare supplier IDs."], 0, "A contract defines validity expectations for a feature."),
        _mcq("Architecture", "A sensor changes from Celsius to Fahrenheit without notice. Which control should catch it?", ["Unit/range validation in the feature contract.", "Higher learning rate.", "More epochs.", "A different train/test split only."], 0, "Unit and range checks are contract responsibilities."),
        _mcq("Scenario", "Adding 50 extra features improves training score but worsens validation score. What is the likely lesson?", ["More features can add noise and overfit.", "Validation is unnecessary.", "All extra features are causal.", "Feature contracts are only for labels."], 0, "Feature quantity is not the same as signal quality."),
    ],
    "mlf_013": [
        _mcq("Scenario", "A nominal field station_type has values station, equipment, electrical_board. What is the risk of encoding them as 1, 2, 3?", ["The model may infer a fake order or distance.", "The model will automatically know the categories are nominal.", "It prevents all unseen categories.", "It guarantees better accuracy."], 0, "Ordinal numbers create artificial order when none exists."),
        _mcq("Trap", "When is ordinal encoding acceptable?", ["When the category order is meaningful, such as low < medium < high.", "Whenever there are three categories.", "Whenever one-hot would add columns.", "For all IDs and fault codes."], 0, "Ordinal encoding is only appropriate when order is real and useful."),
        _mcq("Architecture", "A new category appears during inference. What should happen first?", ["Safe unknown handling and monitoring, not live retraining.", "Create new production columns on the fly.", "Crash the pipeline.", "Refit the encoder on production data immediately."], 0, "Runtime needs safe handling first; retraining is a governed follow-up if needed."),
        _mcq("Scenario", "A supplier_id field has 40,000 unique values. What is the main one-hot encoding concern?", ["High-cardinality feature explosion.", "It becomes ordinal automatically.", "It removes the need for validation.", "It guarantees interpretability."], 0, "High cardinality can create huge sparse feature spaces."),
    ],
    "mlf_014": [
        _mcq("Scenario", "A KNN defect model uses temperature range 20-40 and runtime_seconds range 0-200000. What is the main risk if you do not scale?", ["runtime_seconds can dominate distance because its numeric range is much larger.", "Temperature becomes the label.", "KNN automatically ignores larger-range features.", "Scaling itself causes label leakage."], 0, "Distance-based models can be dominated by large-range features."),
        _mcq("Trap", "You split train/test, fit a scaler on train only, then transform test using that saved scaler. Is this leakage?", ["No. This is the correct pattern.", "Yes, because test data was transformed.", "Yes, because scaling is always leakage.", "No, but only for tree models."], 0, "Transforming test with train-fitted parameters is correct. Fitting on test/full data is the leak."),
        _mcq("Architecture", "A production value is outside the training min/max range. What should the pipeline do first?", ["Apply the saved transformer, flag/monitor the out-of-range event, and follow response policy.", "Refit the scaler live on production data.", "Silently delete the row.", "Disable monitoring because the API is healthy."], 0, "Out-of-range values require monitoring and response, not live refit."),
        _mcq("Trap", "Which model family is usually least sensitive to feature scaling?", ["Tree-based models such as decision trees/random forests.", "KNN.", "SVM with distance/kernel behavior.", "PCA."], 0, "Tree splits are usually less affected by monotonic scaling, though pipeline consistency still matters."),
    ],
    "mlf_015": [
        _mcq("Scenario", "A model fits training perfectly but validation performance is unstable. Which regularization idea is most relevant?", ["Add a penalty that discourages excessive complexity.", "Increase model complexity further without checking validation.", "Use training score as the only metric.", "Remove the validation set."], 0, "Regularization controls complexity to improve generalization."),
        _mcq("Trap", "What is the main difference between L1 and L2 regularization?", ["L1 can drive some weights to zero; L2 shrinks weights smoothly.", "L1 is only for images; L2 is only for text.", "Both remove the need for validation.", "L2 always selects features exactly."], 0, "L1 encourages sparsity; L2 discourages large weights."),
        _mcq("Architecture", "What should decide regularization strength?", ["Validation performance and underfit/overfit behavior.", "The highest training score.", "The number of dashboard users.", "A fixed value copied from another project."], 0, "Regularization strength is a model-selection hyperparameter."),
        _mcq("Scenario", "After very strong regularization, both train and validation scores are poor. What happened?", ["Likely underfitting.", "Always leakage.", "Always class imbalance.", "The model is production-ready."], 0, "Too much regularization can make the model too simple."),
    ],
    "mlf_016": [
        _mcq("Scenario", "A defect model outputs risk scores, but the default 0.5 threshold misses too many defects. What should you tune?", ["The decision threshold based on FP/FN cost.", "Only the feature names.", "Only API uptime.", "The train/test split after deployment."], 0, "Threshold tuning chooses an operating point for business risk."),
        _mcq("Trap", "What changes when you lower a positive-class threshold?", ["Recall often increases and precision may fall.", "Precision and recall both always increase.", "The labels change.", "The model retrains automatically."], 0, "Lowering threshold catches more positives but may increase false positives."),
        _mcq("Architecture", "What must be defined before approving a threshold?", ["Cost of false negatives vs false positives and operating constraints.", "Only the algorithm name.", "The UI theme.", "Training accuracy only."], 0, "The threshold is a business decision boundary."),
        _mcq("Scenario", "Inspection team can handle only 100 alerts/day. Which metric/control matters alongside recall?", ["Precision/alert volume limit.", "Only model file size.", "Only training loss.", "Only feature count."], 0, "Alert workload constrains how aggressive the threshold can be."),
    ],
    "mlf_017": [
        _mcq("Scenario", "A dataset has 98% non-defects and 2% defects. A model predicts non-defect for everything. Which metric exposes the failure?", ["Recall for the defect class.", "Aggregate accuracy only.", "API latency.", "Number of columns."], 0, "Minority-class recall shows whether actual defects are caught."),
        _mcq("Trap", "Which fix can help class imbalance but may distort probabilities if misused?", ["Over/under-sampling.", "Saving the model artifact.", "Using a dashboard.", "Changing chart color."], 0, "Sampling changes class distribution and must be validated carefully."),
        _mcq("Architecture", "What should imbalance handling be tied to?", ["Business cost of missed positives vs false alarms.", "Only row count.", "Only model brand.", "Only training speed."], 0, "Imbalance is a decision-risk problem, not only a data ratio problem."),
        _mcq("Scenario", "Class weighting improves recall but precision falls sharply. What is the right next step?", ["Review the precision-recall trade-off and alert workload.", "Declare the model impossible.", "Ignore precision.", "Use accuracy only."], 0, "You need an operating point, not a single metric."),
    ],
    "mlf_018": [
        _mcq("Scenario", "Overall recall is acceptable, but recall is poor for one product family. What should error analysis do?", ["Slice errors by product family and investigate data/model causes.", "Stop at the aggregate metric.", "Assume the API is broken.", "Remove all labels."], 0, "Error analysis searches for segment-level failure pockets."),
        _mcq("Trap", "What is not good error analysis?", ["Only saying the model score is low.", "Reviewing false negatives.", "Checking segments.", "Inspecting misclassified examples."], 0, "Useful error analysis names where and why the model fails."),
        _mcq("Architecture", "What should error analysis feed into?", ["Data fixes, feature changes, threshold decisions, or model selection.", "Only a static report.", "Only badge awards.", "Only UI styling."], 0, "Findings must change the system or decision process."),
        _mcq("Scenario", "Most false negatives occur on night shift data. What is a plausible next investigation?", ["Shift-specific sensor/process distribution and label quality.", "Only whether the app is online.", "Only whether Python version changed.", "Only overall accuracy."], 0, "Segment failures often point to data/process differences."),
    ],
    "mlf_019": [
        _mcq("Scenario", "SHAP says humidity is important. What can you safely conclude?", ["Humidity is a useful clue in the model behavior, not causal proof.", "Humidity definitely causes defects.", "No domain review is needed.", "The model cannot be wrong."], 0, "Explanations are clues, not causal proof."),
        _mcq("Trap", "What is the difference between local and global explanation?", ["Local explains one prediction; global summarizes broader model behavior.", "They are identical.", "Global is only for SQL.", "Local means production server."], 0, "Local and global explanations answer different questions."),
        _mcq("Architecture", "What should accompany explanation dashboards?", ["Usage limits, audit trail, domain review, and action approval path.", "No caveats.", "Automatic process changes.", "Only model accuracy."], 0, "Explanation outputs need governance."),
        _mcq("Scenario", "Two correlated features alternate as top importance across model versions. What is the risk?", ["Importance may be unstable and should not be overinterpreted.", "Both are proven causal.", "The model is unusable by default.", "Monitoring is no longer needed."], 0, "Correlated features can distort or split importance."),
    ],
    "mlf_020": [
        _mcq("Scenario", "The model API is healthy, but defect recall has dropped after a process change. What did uptime monitoring miss?", ["Model performance/behavior drift.", "Server availability.", "Network latency only.", "The model filename."], 0, "A live service can still produce bad predictions."),
        _mcq("Trap", "Which signal can be monitored before true labels arrive?", ["Input and prediction distribution drift.", "Final recall only.", "Warranty claim outcome only.", "True precision only."], 0, "Labels may be delayed, but input/prediction drift can be watched earlier."),
        _mcq("Architecture", "What makes a retraining trigger operationally useful?", ["Threshold, time window, owner, validation gate, and release process.", "A vague calendar reminder.", "A dashboard with no owner.", "Only training data size."], 0, "Retraining must be governed and validated."),
        _mcq("Scenario", "Input drift alert fires, but performance labels are delayed. What is the sensible response?", ["Investigate, increase monitoring, consider fallback if risk is high, and wait for labels before retraining approval.", "Retrain immediately with production data without validation.", "Ignore because API uptime is fine.", "Delete the model."], 0, "Input drift is evidence for review, not automatic retraining."),
    ],
}


def get_quality_mcqs(topic_id: str, fallback: List[Dict[str, Any]] | None = None) -> List[Dict[str, Any]]:
    configured = QUALITY_MCQS.get(str(topic_id or ""))
    if configured:
        return deepcopy(configured)
    return deepcopy(fallback or [])
