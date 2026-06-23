"""V2.4 tutor-quality contract.

Purpose:
- Stop presenting answer scaffolds as the lesson.
- Teach the concept first, with formulas/numbers/examples where needed.
- Keep assessment aligned to visible teaching.
- Override shallow or generic Supabase designs at runtime for repair-critical topics.

This module is deterministic and safe to deploy without schema changes.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, List, Optional


REPAIR_TOPICS = {"mlf_009", "mlf_010", "mlf_012", "mlf_014", "mlf_022", "mlf_023", "mlf_025"}


def _clean(value: Any) -> str:
    return str(value or "").strip()


def _task_sample(text: str) -> str:
    return " ".join(_clean(text).split())


TOPIC_SAMPLE_ANSWERS: Dict[str, Dict[str, str]] = {
    "mlf_001": {
        "q1": _task_sample(
            "An ML model learns statistical patterns from examples. It learns that certain inputs tend to map to certain outputs, "
            "but it does not understand the real-world meaning or cause behind those outputs. For example, a defect model may learn "
            "that humidity and machine speed are associated with scrap risk. That is useful for prediction, but it is not proof that the model understands why scrap happens."
        ),
        "q2": _task_sample(
            "The likely missed boundary is distribution difference between the old training/validation data and the new factory. "
            "The model may have learned patterns from one factory setup, supplier mix, sensor behavior, or process condition, then faced a different production distribution. "
            "I would check segment performance on the new factory, compare feature distributions, and validate before trusting confident scores."
        ),
        "q3": _task_sample(
            "Minimum controls are deployment-like validation, monitoring, and ownership. First, validate on data that matches the intended factory, time period, and operating conditions. "
            "Second, monitor input drift, prediction confidence, error rates, and segment performance after release. Third, assign an ML owner and quality/process owner who decide whether to retrain, rollback, or add manual inspection."
        ),
        "q4": _task_sample(
            "I would explain it like this: the model is not thinking like an engineer. It is matching patterns it has seen before. "
            "If past data shows certain sensor patterns before defects, it can flag similar cases. But if the factory changes, the same pattern may stop meaning the same thing. "
            "So prediction needs validation and monitoring, not blind trust."
        ),
    },
    "mlf_009": {
        "q1": _task_sample(
            "Accuracy can be misleading when defects are rare because the model can be right on most normal parts while missing the few cases that matter. "
            "For example, if only 10 out of 1000 parts are defective, a model that predicts every part as non-defective is 99% accurate but catches zero defects. "
            "That is unsafe for quality decisions."
        ),
        "q2": _task_sample(
            "The model is correct on 990 normal parts and wrong on 10 defective parts, so accuracy is 990/1000 = 0.99 or 99%. "
            "Operationally, this is not acceptable because the model missed every defective part. The headline metric looks strong, but defect recall is zero."
        ),
        "q3": _task_sample(
            "The evaluation missed minority-class performance, especially recall for actual defects. The model probably looked good because most parts were normal. "
            "Warranty claims rose because false negatives were hidden by high overall accuracy. I would add a confusion matrix, defect recall, precision, and class-specific performance before release."
        ),
        "q4": _task_sample(
            "For rare but costly defects, approval should require a minimum defect recall, acceptable precision, a confusion matrix, and threshold evidence. "
            "The quality owner should approve the false-negative risk and inspection workload. If recall drops below the floor or false alarms exceed capacity, the threshold and release scope should be reviewed."
        ),
    },
    "mlf_010": {
        "q1": _task_sample(
            "Precision asks: of the parts the model flagged, how many were truly defective? Low precision creates wasted inspections. "
            "Recall asks: of all truly defective parts, how many did the model catch? Low recall means missed defects. "
            "In quality inspection, precision controls false-alarm workload, while recall controls escape risk."
        ),
        "q2": _task_sample(
            "Precision = TP/(TP+FP) = 40/(40+10) = 0.80. So 80% of flagged parts were actually defective. "
            "Recall = TP/(TP+FN) = 40/(40+20) = 0.67. So the model caught about 67% of actual defects and missed about 33%. "
            "The business must decide whether that miss rate is acceptable."
        ),
        "q3": _task_sample(
            "The threshold likely became stricter, so fewer cases were flagged. That reduces inspection workload and can improve precision, but it often lowers recall because more actual defects fall below the alert threshold. "
            "The response is to review false negatives, warranty escapes, threshold setting, and inspection capacity before approving the operating point."
        ),
        "q4": _task_sample(
            "Where missed safety defects are costly, the policy should set a minimum recall floor first, then choose the highest precision threshold that stays within inspection capacity. "
            "The quality owner approves the missed-defect risk and workload. Monitoring should track recall, precision, false negatives, and alert volume by line or defect type, with review if recall drops."
        ),
    },
    "mlf_012": {
        "q1": _task_sample(
            "A feature contract is necessary because engineered features must be reproducible and available at prediction time. "
            "A clever offline feature is dangerous if production cannot calculate it the same way. The contract records definition, source, timing, transformation, owner, and validation checks so the model uses trustworthy inputs."
        ),
        "q2": _task_sample(
            "For time T, I would define rolling_temperature_deviation as current temperature minus the average temperature from a fixed past window, such as T-60 minutes to T. "
            "The feature must use only data available before T, specify sensor source and missing-value logic, and have a process or data owner responsible for quality."
        ),
        "q3": _task_sample(
            "This is a training-serving mismatch. The model learned from a feature calculated one way offline, but production supplies a missing or different value. "
            "That breaks model assumptions and can cause silent prediction failure. The control is a feature contract, parity test, lineage check, and release gate before deployment."
        ),
        "q4": _task_sample(
            "Feature approval should check point-in-time correctness, source lineage, transformation code, missing-value handling, drift risk, and training-serving parity. "
            "Each feature needs an owner and a test proving production can reproduce the training calculation. If a feature fails parity or availability checks, the model should not be released."
        ),
    },
    "mlf_014": {
        "q1": _task_sample(
            "Scaling changes numeric feature ranges so one large-scale feature does not dominate learning unfairly. Pipeline leakage happens when scaling parameters are learned using validation or test data. "
            "The scaler must be fitted only on training data, then applied unchanged to validation, test, and production data."
        ),
        "q2": _task_sample(
            "The safe pattern is: split data first, fit the scaler on the training set only, transform training, validation, and test using that fitted scaler, then save the scaler with the model pipeline. "
            "This prevents future evaluation data from influencing preprocessing and keeps production behavior consistent."
        ),
        "q3": _task_sample(
            "If scaling was fitted before the split, validation information leaked into training preprocessing. The validation score may look better because the model indirectly saw distribution information from the validation set. "
            "I would rebuild the pipeline with split-first preprocessing, rerun validation, and compare the corrected result."
        ),
        "q4": _task_sample(
            "The release pipeline should require preprocessing code inside a fitted pipeline object, split-first validation, versioned scaler parameters, and a training-serving parity test. "
            "The ML owner approves the pipeline artifact. If production input ranges drift or scaler parity fails, predictions should be reviewed before operational use."
        ),
    },
    "mlf_022": {
        "q1": _task_sample(
            "Hyperparameter tuning can overfit validation evidence because every trial uses validation performance to choose the next candidate or final winner. "
            "Even if training code is correct, trying many settings increases the chance of selecting a configuration that got lucky on that validation sample. Final approval needs locked test evidence."
        ),
        "q2": _task_sample(
            "I would define the search space before tuning, allow 30 trials inside the development process, log every trial, and select the best candidate using validation evidence only. "
            "After selection, I would evaluate the winner once on a locked final test set. That final score is approval evidence, not another tuning signal."
        ),
        "q3": _task_sample(
            "The collapse may come from validation overuse, where the selected model fit quirks of the validation set, or from time shift between validation and later-period test data. "
            "I would inspect trial history, validation-test gap, segment results, and time-based distribution changes, then tighten the tuning budget and final-test lock."
        ),
        "q4": _task_sample(
            "Tuning governance should define the search space, trial budget, experiment registry, selection metric, locked final test, and approval owner before tuning starts. "
            "Threshold tuning should follow the same rule because it is also a decision search. If the locked test fails, the candidate returns to development rather than reopening final evidence repeatedly."
        ),
        "q5": _task_sample(
            "Trying more options can improve a score by luck, like repeatedly taking practice tests until one looks best. That does not prove the model is better for future data. "
            "The honest confirmation step is to choose the winner once, then test it on locked data that was not used during the search."
        ),
    },
    "mlf_023": {
        "q1": _task_sample(
            "ROC and PR curves show how model behavior changes across thresholds. ROC compares true-positive rate and false-positive rate. PR compares precision and recall. "
            "For rare defects, PR is often more useful because it directly shows how many flagged cases are useful and how many true defects are caught."
        ),
        "q2": _task_sample(
            "I would use the PR curve first for rare defects because precision and recall expose the operational trade-off: inspection workload versus missed defects. "
            "A good ROC curve can still hide poor precision when positives are rare. PR evidence is closer to the production decision."
        ),
        "q3": _task_sample(
            "The model may rank cases reasonably but the chosen operating threshold may be wrong for the business. The curve shows possible trade-offs, but deployment uses one operating point. "
            "I would review the selected threshold, expected alert volume, recall, precision, and cost of false negatives before changing the model."
        ),
        "q4": _task_sample(
            "For release, I would select an operating point using minimum recall, acceptable precision, inspection capacity, and defect cost. "
            "The owner should approve the chosen threshold and document why other points were rejected. Monitoring should track whether live precision, recall proxy, and alert volume remain within policy."
        ),
    },
    "mlf_025": {
        "q1": _task_sample(
            "Data quality is whether inputs are accurate, complete, timely, and consistent. Label quality is whether the target outcome is correct and generated consistently. "
            "Sampling bias is when the training data does not represent the population where the model will be used. Any one of these can make a good-looking model fail in production."
        ),
        "q2": _task_sample(
            "I would check missing values, outliers, duplicate records, sensor reliability, label definition, label delay, disagreement between inspectors, and whether each plant, line, shift, supplier, and defect type is represented. "
            "The goal is to prove the data matches the deployment problem before trusting model metrics."
        ),
        "q3": _task_sample(
            "If the model performs well in one plant but fails in another, I would suspect sampling bias, different label practices, different process conditions, or missing segment coverage. "
            "I would compare feature distributions, label rates, data quality, and performance by plant before approving wider rollout."
        ),
        "q4": _task_sample(
            "The data-readiness gate should require data completeness, label definition approval, label-quality audit, segment coverage, bias check, and owner sign-off. "
            "If a critical plant, shift, supplier, or defect type is underrepresented, release should be limited or blocked until more representative evidence is available."
        ),
    },
    "mlf_016": {
        "q1": _task_sample(
            "A model score estimates relative risk; a decision threshold decides when the business acts. For example, a defect model may score one part as 0.42 risk. "
            "That score alone does not say inspect or release. The threshold converts the score into action. Changing the threshold changes alert volume, missed defects, and inspection workload, not the trained model itself."
        ),
        "q2": _task_sample(
            "I would choose threshold 0.3 if missed defects are costly and inspection capacity can handle 125 alerts. It reduces precision from 85% to 60%, so more alerts will be false alarms, but recall improves from 35% to 75%, meaning fewer defects are missed. Since capacity is 140 alerts, the safer policy is the lower threshold with workload monitoring."
        ),
        "q3": _task_sample(
            "The threshold may be too high for the business risk. High precision can mean the model alerts only on very obvious cases, so it misses many real defects. "
            "The response is not automatically retraining. I would review recall, false negatives, alert volume, and cost of missed defects, then lower or segment the threshold if inspection capacity allows."
        ),
        "q4": _task_sample(
            "Threshold governance should record the missed-defect cost, false-alert cost, inspection capacity, minimum recall target, and approved alert volume. "
            "The quality owner and ML owner should approve the threshold before release. Monitoring should track recall, false negatives, precision, and alert volume by line or defect type."
        ),
        "q5": _task_sample(
            "I would tell a quality leader: the model gives a risk score, but the threshold decides when your team acts. A lower threshold catches more possible defects but creates more inspections. "
            "A higher threshold reduces workload but may miss defects. So the right threshold must match defect cost, available inspection capacity, and agreed quality risk."
        ),
    },
}


AUTHOR_TUTOR_OVERRIDES: Dict[str, Dict[str, Any]] = {
    "mlf_009": {
        "learning_objective": "Judge whether accuracy is safe evidence when one class is rare, and choose checks that expose missed business-critical cases.",
        "concept_steps": [
            {"heading": "The core idea", "body": "Accuracy is total correct predictions divided by total cases. It answers: how often was the model right overall? It does not answer: did the model catch the rare cases that matter?"},
            {"heading": "Why imbalance breaks the comfort", "body": "If 990 out of 1000 parts are normal, a useless model can predict 'normal' for everything and still get 99% accuracy. That number hides the 10 missed defects."},
            {"heading": "Business meaning", "body": "In production, the rare class is often the expensive class: defect, fraud, failure, warranty escape, safety issue. Missing it can be worse than creating extra checks."},
            {"heading": "What to add", "body": "Use a confusion matrix and class-specific metrics. For rare positives, inspect recall, precision, false negatives, false positives, and the decision threshold."},
        ],
        "worked_example": {"scenario": "1000 parts arrive. 10 are defective. The model predicts every part as normal.", "rows": [{"case": "Normal parts correctly released", "count": "990"}, {"case": "Defective parts missed", "count": "10"}, {"case": "Accuracy", "count": "990/1000 = 99%"}], "takeaway": "The model looks excellent by accuracy but catches zero defects. That is production failure, not success."},
        "worked_examples": [
            {"title": "Accuracy calculation", "body": "Correct predictions are 990 normal parts. Total cases are 1000. Accuracy = 990/1000 = 0.99. The metric is mathematically correct but operationally misleading."},
            {"title": "Decision interpretation", "body": "The right conclusion is not 'accuracy is bad.' The right conclusion is: accuracy alone is incomplete when the minority class carries the business risk."},
        ],
        "misconception": "Assuming high accuracy means the model is safe for deployment.",
        "architect_extension": "Metric approval must be tied to the production decision, class distribution, cost of false negatives/false positives, and capacity to act on alerts.",
    },
    "mlf_010": {
        "learning_objective": "Use precision and recall to separate false-alarm workload from missed-defect risk, then choose an operating point for the business decision.",
        "concept_steps": [
            {"heading": "Start with the confusion matrix", "body": "True positive means the model flagged a defect and it was really defective. False positive means the model flagged a defect but it was actually normal. False negative means the model missed an actual defect."},
            {"heading": "Precision in plain English", "body": "Precision asks: out of all items the model flagged, how many were truly positive? Formula: precision = TP / (TP + FP). Low precision means too many false alarms and wasted inspection effort."},
            {"heading": "Recall in plain English", "body": "Recall asks: out of all actual positives, how many did the model catch? Formula: recall = TP / (TP + FN). Low recall means the model misses real defects, failures, fraud, or safety cases."},
            {"heading": "Why both matter", "body": "A model can be precise but miss many defects, or catch most defects while creating many false alarms. The business chooses the trade-off based on defect cost and inspection capacity."},
            {"heading": "Architect translation", "body": "Threshold policy converts model scores into action. The policy must state the minimum recall, acceptable false-alarm workload, owner approval, monitoring trigger, and response when live performance changes."},
        ],
        "worked_example": {"scenario": "A defect model has TP=40, FP=10, FN=20.", "rows": [{"metric": "Precision", "formula": "TP/(TP+FP)", "calculation": "40/(40+10)=0.80", "meaning": "80% of flagged parts were truly defective."}, {"metric": "Recall", "formula": "TP/(TP+FN)", "calculation": "40/(40+20)=0.67", "meaning": "About 67% of real defects were caught; 33% were missed."}], "takeaway": "Precision tells you inspection usefulness. Recall tells you missed-defect risk."},
        "worked_examples": [
            {"title": "Precision answer", "body": "If the model flags 50 parts and 40 are truly defective, precision is 40/50 = 0.80. This means inspection teams will see some false alarms, but most alerts are useful."},
            {"title": "Recall answer", "body": "If there are 60 actual defective parts and the model catches 40, recall is 40/60 = 0.67. This means one-third of actual defects are missed, which may be unacceptable for safety or warranty risk."},
            {"title": "Threshold trade-off", "body": "Raising the threshold usually reduces alerts and can improve precision, but recall may drop because borderline true defects are no longer flagged. Lowering the threshold usually catches more defects but increases inspection workload."},
        ],
        "misconception": "Saying precision measures missed defects or recall measures false-alarm workload.",
        "architect_extension": "For costly defects, set a recall floor first, then choose the highest precision threshold that inspection capacity can support.",
    },
    "mlf_012": {
        "learning_objective": "Design engineered features that are useful offline and also reproducible, available, and safe in production.",
        "concept_steps": [
            {"heading": "Feature engineering", "body": "Feature engineering creates useful input signals from raw data. Example: convert raw temperature readings into 'temperature deviation from last-hour average'."},
            {"heading": "The production catch", "body": "A feature that works in a notebook can still fail in production if it uses future data, unavailable data, or a calculation the live system cannot reproduce."},
            {"heading": "Feature contract", "body": "A feature contract records definition, source, time window, transformation, missing-value logic, owner, and when the value is available for prediction."},
            {"heading": "Architect translation", "body": "Before release, prove point-in-time correctness, lineage, and training-serving parity. If production cannot compute the feature the same way, model evidence is not trustworthy."},
        ],
        "worked_example": {"scenario": "Predict defects at time T using rolling temperature deviation.", "rows": [{"field": "Window", "safe definition": "Use readings from T-60 minutes to T only"}, {"field": "Leakage risk", "safe definition": "Do not include readings after T"}, {"field": "Owner", "safe definition": "Manufacturing data/process owner validates source and missing logic"}], "takeaway": "The feature is safe only if it is available and reproducible at the moment of prediction."},
        "worked_examples": [{"title": "Bad feature", "body": "A 24-hour defect count that includes defects recorded after prediction time is leaky. It may improve offline metrics but cannot be trusted for earlier prediction."}, {"title": "Good feature", "body": "A rolling temperature deviation using only past sensor data is valid if the same calculation runs in production and has defined missing-value handling."}],
        "misconception": "Treating feature creativity as success without checking prediction-time availability and serving parity.",
        "architect_extension": "Feature approval must include point-in-time checks, lineage, reproducibility, parity tests, and owner sign-off.",
    },
    "mlf_014": {
        "learning_objective": "Apply scaling safely by fitting preprocessing only on training data and shipping the same preprocessing logic with the model.",
        "concept_steps": [
            {"heading": "Why scaling exists", "body": "Some models are sensitive to numeric scale. A feature measured in thousands can dominate a feature measured between 0 and 1 unless values are scaled."},
            {"heading": "The leakage trap", "body": "If you calculate scaling parameters before the train/test split, information from validation or test data leaks into training preprocessing."},
            {"heading": "Safe order", "body": "Split first. Fit the scaler on training data only. Transform train, validation, test, and production using that fitted scaler. Save scaler and model together."},
            {"heading": "Architect translation", "body": "The deployable artifact is the full pipeline, not just the model. Release evidence must prove training-serving parity for preprocessing."},
        ],
        "worked_example": {"scenario": "A standard scaler is used for sensor values.", "rows": [{"step": "1", "safe action": "Split train/validation/test"}, {"step": "2", "safe action": "Fit scaler on train only"}, {"step": "3", "safe action": "Apply same scaler to validation/test/production"}], "takeaway": "The scaler learns from training data only. Evaluation data must remain independent."},
        "worked_examples": [{"title": "Unsafe pattern", "body": "Fitting the scaler on the full dataset before splitting lets validation/test distribution influence preprocessing. The score may become optimistic."}, {"title": "Safe pattern", "body": "Use a pipeline object that contains preprocessing and model together. This makes training, validation, and serving behavior consistent."}],
        "misconception": "Treating preprocessing as harmless because it is not the final model.",
        "architect_extension": "Govern preprocessing as a model dependency with versioning, parity tests, drift checks, and release approval.",
    },
    "mlf_022": {
        "learning_objective": "Tune model settings without turning validation results into overused approval evidence.",
        "concept_steps": [
            {"heading": "What is being tuned", "body": "Hyperparameters are settings chosen before or around training, such as tree depth, regularization strength, learning rate, or threshold. Tuning searches for useful settings."},
            {"heading": "Why tuning can fool you", "body": "Each trial looks at validation performance. After many trials, the best validation score may partly reflect luck on that validation set."},
            {"heading": "Safe separation", "body": "Use validation evidence to select a candidate. Use locked final test evidence once to approve the selected candidate. Do not keep reopening final test results during search."},
            {"heading": "Architect translation", "body": "Define search space, trial budget, experiment log, selection metric, final evidence lock, and approval owner before tuning starts."},
        ],
        "worked_example": {"scenario": "A team tries 150 model settings and reports the best validation F1.", "rows": [{"risk": "Validation overuse", "meaning": "The winner may fit quirks of the validation sample"}, {"control": "Trial budget", "meaning": "Limit search and log all attempts"}, {"approval": "Locked final test", "meaning": "Evaluate selected winner once"}], "takeaway": "The best validation score is selection evidence, not final deployment evidence."},
        "worked_examples": [{"title": "Selection vs approval", "body": "Validation helps choose the winner. Locked test evidence approves or rejects the winner. Mixing these roles creates overconfident claims."}, {"title": "Threshold tuning too", "body": "Choosing a threshold is also tuning. If you try many thresholds, final evidence must still be protected."}],
        "misconception": "Believing more trials automatically create more trustworthy evidence.",
        "architect_extension": "Tuning must be governed as a controlled experiment with budget, registry, locked evidence, and approval rule.",
    },
    "mlf_023": {
        "learning_objective": "Use ROC, PR curves, and operating points to choose thresholds that match the production decision.",
        "concept_steps": [
            {"heading": "Curves show choices", "body": "ROC and PR curves do not deploy a model by themselves. They show how metrics change as the threshold moves."},
            {"heading": "ROC curve", "body": "ROC compares true-positive rate against false-positive rate. It is useful for ranking behavior, but can look optimistic when positives are rare."},
            {"heading": "PR curve", "body": "Precision-recall curves show the trade-off between useful alerts and caught positives. For rare defects, PR is often closer to the operational decision."},
            {"heading": "Operating point", "body": "Deployment uses one threshold. Pick it based on recall requirement, precision/workload, capacity, cost of errors, and monitoring plan."},
        ],
        "worked_example": {"scenario": "A rare-defect model has good ROC-AUC but creates too many poor-quality alerts at the chosen threshold.", "rows": [{"view": "ROC", "risk": "May hide poor precision under class imbalance"}, {"view": "PR", "risk": "Shows alert usefulness and missed-defect trade-off"}, {"view": "Decision", "risk": "Choose threshold against capacity and defect cost"}], "takeaway": "A curve is evidence. The operating point is the production decision."},
        "worked_examples": [{"title": "Rare defect decision", "body": "For rare positives, start with PR evidence because precision and recall directly show workload and missed-defect risk."}, {"title": "Release decision", "body": "Document the selected threshold, rejected alternatives, expected alert volume, minimum recall, owner, and review trigger."}],
        "misconception": "Treating high AUC as enough to approve a production threshold.",
        "architect_extension": "Operating-point approval must connect curve evidence to capacity, cost, owner, and monitoring.",
    },
    "mlf_025": {
        "learning_objective": "Decide whether data, labels, and sample coverage are trustworthy enough for model evidence to mean anything.",
        "concept_steps": [
            {"heading": "Data quality", "body": "Data quality is about input reliability: missing values, wrong values, duplicates, stale records, broken sensors, or inconsistent definitions."},
            {"heading": "Label quality", "body": "Label quality is about outcome reliability. If defect labels are delayed, inconsistent, or subjective, the model learns noisy truth."},
            {"heading": "Sampling bias", "body": "Sampling bias means training data does not represent the population where the model will run, such as missing a plant, line, supplier, shift, or defect type."},
            {"heading": "Architect translation", "body": "Before modelling, require data-readiness checks: completeness, label audit, segment coverage, bias review, lineage, and owner approval."},
        ],
        "worked_example": {"scenario": "A defect model is trained mostly on Plant A data and deployed to Plant B.", "rows": [{"check": "Feature distribution", "why": "Plant B process may differ"}, {"check": "Label practice", "why": "Inspectors may record defects differently"}, {"check": "Segment coverage", "why": "Plant B may be underrepresented"}], "takeaway": "Poor data coverage can make validation evidence irrelevant to the rollout population."},
        "worked_examples": [{"title": "Label noise", "body": "If two inspectors label the same defect differently, the model learns inconsistent targets. Agreement checks are part of model readiness."}, {"title": "Sampling bias", "body": "If night-shift data is absent, the model cannot be assumed safe for night-shift deployment."}],
        "misconception": "Treating model performance as trustworthy before checking whether data and labels are trustworthy.",
        "architect_extension": "Data readiness is a release gate, not a data-cleaning side task.",
    },
}


def _is_repair_topic(topic_id: str) -> bool:
    return _clean(topic_id) in REPAIR_TOPICS


def _generic_sample_answer(design: Dict[str, Any], task: Dict[str, Any]) -> str:
    title = _clean(design.get("title")) or "this concept"
    objective = _clean(design.get("learning_objective"))
    example = design.get("worked_example") or {}
    scenario = _clean(example.get("scenario")) if isinstance(example, dict) else ""
    takeaway = _clean(example.get("takeaway")) if isinstance(example, dict) else ""
    architect = _clean(design.get("architect_extension"))
    qtype = _clean(task.get("type"))

    if qtype == "failure_diagnosis":
        return _task_sample(
            f"The symptom should be tied to the failure mode. For {title}, the likely issue is {takeaway or objective}. "
            "I would check the relevant metric, data slice, threshold, or pipeline boundary before changing the model. "
            "The response should name the evidence and the operating action."
        )
    if qtype == "architect_decision":
        return _task_sample(
            f"I would govern {title} with a clear control: evidence to check, owner to approve, trigger for review, and action after breach. "
            f"{architect or 'That turns the concept into a production decision rather than a theory answer.'}"
        )
    if qtype == "teachback":
        return _task_sample(
            f"In simple terms, {title} means {objective or takeaway}. The business consequence is that a model output should not become automatic action without the right evidence and decision rule."
        )
    return _task_sample(
        f"{title} means {objective or takeaway}. In practice, {scenario or 'a model result must be interpreted against the decision context'}. "
        "The important part is the consequence if this is ignored and the control that prevents the failure."
    )


def _apply_author_override(design: Dict[str, Any]) -> Dict[str, Any]:
    topic_id = _clean(design.get("topic_id"))
    override = AUTHOR_TUTOR_OVERRIDES.get(topic_id)
    if not override:
        return design
    merged = deepcopy(design)
    for key, value in override.items():
        merged[key] = deepcopy(value)
    merged["tutor_quality_level"] = "v2_4_authored_repair_lesson"
    return merged


def _build_expanded_steps(design: Dict[str, Any]) -> List[Dict[str, str]]:
    original = [s for s in (design.get("concept_steps") or []) if isinstance(s, dict)]
    title = _clean(design.get("title")) or "this topic"
    objective = _clean(design.get("learning_objective"))
    bridge = _clean(design.get("prerequisite_bridge"))
    example = design.get("worked_example") or {}
    scenario = _clean(example.get("scenario")) if isinstance(example, dict) else ""
    takeaway = _clean(example.get("takeaway")) if isinstance(example, dict) else ""
    misconception = _clean(design.get("misconception"))
    architect = _clean(design.get("architect_extension"))

    # Authored repair-topic lessons should stay exactly as authored.
    if _is_repair_topic(_clean(design.get("topic_id"))) and len(original) >= 4:
        return original

    # Keep detailed authored lessons intact. Expand only shallow lessons.
    if len(original) >= 5:
        return original

    mechanism = " ".join(_clean(s.get("body")) for s in original if _clean(s.get("body"))) or objective
    steps = [
        {"heading": "Plain-English meaning", "body": objective or f"Understand {title} as a decision concept, not as vocabulary to memorize."},
        {"heading": "Mechanism", "body": mechanism or f"This concept changes how you judge model behavior, evidence, or production action for {title}."},
        {"heading": "Concrete example", "body": f"{scenario} {takeaway}".strip() or "Use a small manufacturing example and state what the model output can and cannot prove."},
        {"heading": "Common wrong answer", "body": misconception or "The weak answer stays at textbook definition level and never explains the production consequence."},
        {"heading": "Architect translation", "body": architect or "Translate the concept into validation evidence, monitoring, trigger, owner, and action."},
    ]
    if bridge:
        steps.insert(0, {"heading": "Before this topic", "body": bridge})
    return steps


def _build_worked_examples(design: Dict[str, Any]) -> List[Dict[str, Any]]:
    existing = [w for w in (design.get("worked_examples") or []) if isinstance(w, dict)]
    if existing:
        return existing

    tasks = [t for t in (design.get("evidence_tasks") or []) if isinstance(t, dict)]
    title = _clean(design.get("title")) or "this topic"
    example = design.get("worked_example") or {}
    scenario = _clean(example.get("scenario")) if isinstance(example, dict) else ""
    takeaway = _clean(example.get("takeaway")) if isinstance(example, dict) else ""

    # Fallback still teaches with an example. It must not become a meta-scaffold.
    worked: List[Dict[str, Any]] = []
    for task in tasks[:2]:
        label = _clean(task.get("label")) or _clean(task.get("type")) or "Evidence task"
        sample = TOPIC_SAMPLE_ANSWERS.get(_clean(design.get("topic_id")), {}).get(_clean(task.get("question_id")))
        body = sample or _generic_sample_answer(design, task)
        worked.append({"title": f"Example answer for {label}", "body": body})
    if not worked and (scenario or takeaway):
        worked.append({"title": f"{title} example", "body": f"{scenario} {takeaway}".strip()})
    return worked


def _enhance_tasks(design: Dict[str, Any]) -> List[Dict[str, Any]]:
    topic_id = _clean(design.get("topic_id"))
    samples = TOPIC_SAMPLE_ANSWERS.get(topic_id, {})
    enhanced: List[Dict[str, Any]] = []
    for task in (design.get("evidence_tasks") or []):
        if not isinstance(task, dict):
            continue
        item = deepcopy(task)
        qid = _clean(item.get("question_id"))
        item["sample_answer"] = samples.get(qid) or _clean(item.get("sample_answer")) or _generic_sample_answer(design, item)
        item["common_weak_answer"] = _clean(item.get("common_weak_answer")) or "Repeats the metric name or vocabulary but does not explain the consequence for the production decision."
        item["repair_instruction"] = _clean(item.get("repair_instruction")) or "Rewrite as: direct answer + number/example/evidence + business consequence/action."
        enhanced.append(item)
    return enhanced


def enhance_learning_design(learning_design: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    if not isinstance(learning_design, dict) or not learning_design:
        return learning_design

    design = deepcopy(learning_design)
    design = _apply_author_override(design)

    # Do not skip older v2_3 rows from Supabase. They may contain the generic tutor text that V2.4 is replacing.
    if _clean(design.get("tutor_quality_level")) == "v2_4_final":
        return design

    design["design_version"] = f"{design.get('design_version') or 'unknown'}_v2_4"
    design["concept_steps"] = _build_expanded_steps(design)
    design["worked_examples"] = _build_worked_examples(design)
    design["evidence_tasks"] = _enhance_tasks(design)
    design["assessment_principle"] = (
        "Score only against what this lesson visibly teaches. A 3-star answer can be concise if it gives the mechanism, "
        "one concrete example or evidence point, and the decision consequence. Penalize technical falsehoods and copied scaffolds. "
        "Do not demand hidden vocabulary or thesis-length answers."
    )
    design["answer_quality_bar"] = {
        "three_star": "Plain definition + concrete example/evidence + consequence + one control where relevant.",
        "four_star": "Adds trade-off and explains why the selected evidence supports the decision.",
        "five_star": "Adds owner, trigger, monitoring signal, fallback/retrain/review action, and clear release decision.",
    }
    design["mastery_repair_prompts"] = design.get("mastery_repair_prompts") or [
        "Can I explain the concept in one simple sentence?",
        "Can I calculate or identify the one key metric/check?",
        "Can I state what goes wrong in production if this is ignored?",
        "Can I name the action or owner without writing a generic governance essay?",
    ]
    design["tutor_quality_level"] = "v2_4_final"
    return design


def sample_answer_for_task(learning_design: Optional[Dict[str, Any]], question_id: str) -> Optional[str]:
    design = enhance_learning_design(learning_design)
    if not design:
        return None
    for task in design.get("evidence_tasks", []) or []:
        if isinstance(task, dict) and str(task.get("question_id")) == str(question_id):
            sample = _clean(task.get("sample_answer"))
            return sample or None
    return None
