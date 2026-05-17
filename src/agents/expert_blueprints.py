from __future__ import annotations

from typing import Any, Dict, List, Optional

from src.schemas import ArchitectNote, Assessment, AssessmentQuestion, ConceptNote, Topic, UseCaseMapping


def _mission(qid: str, qtype: str, question: str, focus: List[str]) -> Dict[str, Any]:
    return {"question_id": qid, "type": qtype, "question": question, "expected_focus": focus}


def _mcq(question: str, options: List[str], answer_index: int, explanation: str) -> Dict[str, Any]:
    return {"question": question, "options": options, "answer_index": answer_index, "explanation": explanation}


EXPERT_BLUEPRINTS: Dict[str, Dict[str, Any]] = {
    "mlf_011": {
        "title": "Model selection and validation strategy",
        "definition": "Model selection is the disciplined choice of model family and configuration based on validation evidence, constraints, and the business decision the model must support.",
        "why_it_exists": "It prevents teams from choosing the most impressive algorithm instead of the model that is reliable, maintainable, and good enough for the production decision.",
        "core_mechanism": "Different model families make different assumptions. Linear models trade flexibility for stability and interpretability. Tree ensembles capture non-linear behavior but may be harder to explain. Validation strategy estimates how each candidate behaves on unseen-but-representative data before deployment.",
        "worked_example": "For defect prediction, compare logistic regression, random forest, and gradient boosting on the same train/validation split. Do not select only by validation accuracy. Compare defect recall, false alarm workload, stability across time-based folds, inference latency, and explanation needs.",
        "nuances": [
            "The best offline metric is not automatically the best production model.",
            "Cross-validation helps estimate stability, but time-dependent data often needs time-based validation.",
            "A simpler model can be the right architecture choice if it is stable, explainable, and operationally cheaper.",
            "Model selection includes constraints: latency, retraining cost, explainability, monitoring complexity, and deployment environment.",
        ],
        "when_it_matters": "It matters most when several model families perform similarly offline but have different operational risk, cost, or explainability profiles.",
        "when_it_matters_less": "It matters less when the problem is exploratory and the immediate goal is only to establish a rough baseline.",
        "common_confusions": [
            "Picking the model with the highest single validation score without checking variance across folds or time windows.",
            "Treating model selection as an algorithm competition instead of an architecture decision.",
        ],
        "architect_implications": [
            "Define the validation scheme before comparing models, especially for temporal or plant-specific data.",
            "Select models using metric policy plus operational constraints, not leaderboard score alone.",
            "Require model-selection artifacts: candidate list, validation method, metric table, error analysis, selected trade-off, and approval rationale.",
        ],
        "system_controls": [
            "Time-based or group-based validation where needed.",
            "Baseline comparison before complex models are accepted.",
            "Model card or decision log recording why the model was selected.",
            "Acceptance gates for recall, precision, latency, interpretability, and monitoring readiness.",
        ],
        "mission_answer_frame": [
            "State the production decision first.",
            "Name candidate model families and why each is plausible.",
            "Choose validation design, not just metric.",
            "Compare trade-offs: performance, stability, explainability, latency, maintainability.",
            "State the approval gate and owner.",
        ],
        "missions": [
            _mission("q1", "concept_check", "Explain model selection and validation strategy in your own words. Why is model selection more than choosing the highest-scoring algorithm?", ["Model selection as trade-off decision", "Validation strategy estimates unseen performance", "Operational constraints beyond metric score"]),
            _mission("q2", "tiny_hands_on", "A logistic regression model has defect recall 72% and precision 68%. A gradient boosting model has recall 78% and precision 55% with 3x inference cost. How would you reason about model choice for a manufacturing quality system?", ["Compares recall and precision trade-off", "Mentions false alarm workload and inference cost", "States decision depends on defect cost and operations capacity"]),
            _mission("q3", "failure_diagnosis", "A team selected a model because it had the best random validation score, but it failed at a new plant. What likely went wrong in the validation strategy?", ["Validation did not represent deployment setting", "Need group/site/time validation", "Offline score was not enough evidence"]),
            _mission("q4", "architect_decision", "As an ML Architect, what validation and model-selection controls would you define before approving a predictive quality model?", ["Baseline comparison", "Validation design", "Metric policy", "Error analysis", "Operational constraints and approval gate"]),
            _mission("q5", "teachback", "Explain to an interviewer how you would choose between two models that perform similarly offline but differ in interpretability and operational complexity.", ["Stakeholder-ready explanation", "Trade-off reasoning", "Production constraints and governance"]),
        ],
        "mcqs": [
            _mcq("What is the safest model-selection principle?", ["Pick the most complex model", "Pick the model with the highest single score only", "Pick the model that best satisfies metric, stability, and operational constraints", "Pick the newest algorithm"], 2, "Model selection is an architecture trade-off, not a leaderboard contest."),
            _mcq("When is random train/test validation risky?", ["When data has time, plant, user, or batch dependencies", "When the model is linear", "When the dataset has numbers", "Never"], 0, "Random splits can hide temporal or group-specific failure."),
            _mcq("Why keep a baseline during model selection?", ["To prove complex models add value over a simple reference", "To avoid validation", "To remove labels", "To increase feature count"], 0, "A baseline prevents unjustified complexity."),
            _mcq("Which artifact should support model-selection approval?", ["A model decision log with metrics, trade-offs, and constraints", "Only a screenshot of accuracy", "Only source code", "Only model name"], 0, "Architecture approval needs evidence and rationale."),
        ],
    },
    "mlf_012": {
        "title": "Feature engineering and feature contracts",
        "definition": "Feature engineering designs useful input signals; feature contracts define what valid versions of those signals must look like before the model can use them.",
        "why_it_exists": "Models do not receive raw business reality. They receive engineered columns. If those columns are unstable, delayed, miscalculated, or invalid, the model learns and predicts from broken signals.",
        "core_mechanism": "Feature engineering changes what information the model sees. A feature contract protects the boundary by specifying type, range, units, allowed values, freshness, null rules, and source expectations.",
        "worked_example": "Humidity should be a percentage from 0 to 100. Values 110 and -5 are not unusual patterns; they are invalid inputs. A contract catches them before training or inference and routes them to reject, impute, quarantine, or fallback handling.",
        "nuances": [
            "A predictive feature can still be unusable if it is unavailable at prediction time.",
            "A feature can be valid in training but unstable in production if source systems change definitions.",
            "More features can reduce performance by adding noise and fragile dependencies.",
            "Contracts should define response behavior, not just validation rules.",
        ],
        "when_it_matters": "It matters whenever model inputs come from operational systems, sensors, business rules, or upstream pipelines that can change independently of the model.",
        "when_it_matters_less": "It matters less in a one-off notebook experiment where the goal is exploration, not production reliability.",
        "common_confusions": ["Thinking feature engineering means adding more columns.", "Treating validation errors as data-science cleanup instead of architecture boundary failures."],
        "architect_implications": ["Define feature contracts before production go-live.", "Add validation and response policies to the pipeline.", "Track contract violations as operational signals, not just data errors."],
        "system_controls": ["Schema/range/unit/freshness checks", "Contract violation logging and alerting", "Fallback, reject, impute, or quarantine decision", "Feature ownership and source-change governance"],
        "mission_answer_frame": ["Name the feature and business meaning.", "Define the contract rule.", "Identify violation and model impact.", "State the pipeline response.", "Define monitoring and owner."],
        "missions": [
            _mission("q1", "concept_check", "Explain feature engineering and feature contracts. Why are both needed for reliable ML systems?", ["Feature engineering creates signals", "Feature contracts validate signal integrity", "Reliability depends on both usefulness and validity"]),
            _mission("q2", "tiny_hands_on", "Humidity must be between 0 and 100%. Values are [30, 45, 110, -5, 60]. Which values violate the contract and what should the pipeline do?", ["110 and -5 are violations", "Explains model impact", "Defines reject/impute/quarantine/fallback response"]),
            _mission("q3", "failure_diagnosis", "A model degrades after deployment because temperature starts arriving in Fahrenheit instead of Celsius. What failed?", ["Unit contract failure", "Training-serving mismatch", "Need unit validation and source contract"]),
            _mission("q4", "architect_decision", "Design feature-contract controls for a predictive quality pipeline. What checks and responses would you implement?", ["Type/range/unit/freshness/null checks", "Violation response", "Monitoring and ownership"]),
            _mission("q5", "teachback", "Explain feature contracts to a stakeholder using a manufacturing AI example.", ["Simple language", "Concrete example", "Business consequence and control"]),
        ],
        "mcqs": [
            _mcq("What is a feature contract?", ["A rule set defining valid feature type, range, freshness, units, and allowed values", "A list of nice-to-have features", "A model parameter", "A final accuracy report"], 0, "Feature contracts protect the model input boundary."),
            _mcq("Why can more features hurt?", ["Irrelevant or unstable features add noise and dependencies", "Models can only use three features", "Features are only for deep learning", "Monitoring becomes unnecessary"], 0, "Feature quality matters more than feature count."),
            _mcq("Temperature changed from Celsius to Fahrenheit. What is the primary failure?", ["Unit contract failure", "Learning rate problem", "Precision too high", "Missing dashboard"], 0, "Units must be part of the feature contract."),
            _mcq("A contract violation should trigger what?", ["Defined response: reject, impute, quarantine, fallback, or alert", "Silent prediction only", "Automatic model approval", "Ignore all rows forever"], 0, "Contracts need response policies."),
        ],
    },
    "mlf_013": {
        "title": "Encoding categorical variables safely",
        "definition": "Categorical encoding converts labels into numeric signals while preserving their meaning and keeping the training and inference pipeline consistent.",
        "why_it_exists": "Most ML models need numeric inputs, but careless numeric conversion can create fake order, explode feature space, leak label information, or break on unseen production categories.",
        "core_mechanism": "Nominal categories have no order and usually need one-hot, hashing, or embedding-style handling. Ordinal categories have meaningful order and may use ordinal encoding. High-cardinality categories need special care. Encoders must be fitted on training data only, persisted, and reused unchanged in validation, test, and production.",
        "worked_example": "Station type = station, equipment, electrical_board is nominal. Encoding it as 1, 2, 3 tells some models that electrical_board is greater than station, which is fake meaning. One-hot avoids that fake order. If production sends a new station type, the pipeline needs an unknown-category strategy instead of creating live columns or crashing.",
        "nuances": ["Nominal is about labels without order; ordinal is about meaningful order.", "High-cardinality values such as supplier_id or fault_code can make one-hot impractical.", "Target encoding must avoid using validation/test/future labels.", "Unseen category handling is a production design decision, not an afterthought."],
        "when_it_matters": "It matters whenever categories enter a model, especially when the category list changes over time or has high cardinality.",
        "when_it_matters_less": "It matters less for tree models with native categorical support, but training-serving consistency and unseen categories still matter.",
        "common_confusions": ["Using label encoding for nominal categories.", "Thinking retraining is the immediate response to every unseen category."],
        "architect_implications": ["Persist the fitted encoder with the model artifact.", "Define unknown-category behavior before go-live.", "Monitor unknown-category rate and category distribution changes."],
        "system_controls": ["Training-only encoder fitting", "Saved encoder artifact", "Unknown bucket or safe ignore behavior", "Feature contract for allowed values", "Unknown-rate alert and retraining review"],
        "mission_answer_frame": ["Identify category type.", "Choose encoding and justify meaning preservation.", "State training-only fit and inference reuse.", "Define unseen-category behavior.", "Add monitoring and retraining review trigger."],
        "missions": [
            _mission("q1", "concept_check", "Explain why encoding categorical variables is essential and why the encoding method must match the category type.", ["Models need numeric inputs", "Nominal vs ordinal distinction", "Wrong encoding creates fake meaning"]),
            _mission("q2", "tiny_hands_on", "Color has values Red, Green, Blue and is one-hot encoded. Production receives Yellow. What should happen and why?", ["One-hot columns for known values", "Yellow handled by unknown/ignore/contract route", "Impact if pipeline crashes or creates live columns"]),
            _mission("q3", "failure_diagnosis", "A recommendation model produces nonsensical predictions after encountering a new category Purple. What went wrong and how could it be prevented?", ["Unseen category not handled", "Encoder mismatch", "Saved encoder and unknown strategy"]),
            _mission("q4", "architect_decision", "Design robust categorical encoding for a manufacturing AI system. Include nominal, ordinal, high-cardinality, and unseen-category handling.", ["Category type classification", "Encoding strategy", "Training-only fit", "Feature contract", "Monitoring and retraining review"]),
            _mission("q5", "teachback", "Explain safe categorical encoding in an interview using one business example.", ["Simple explanation", "Concrete example", "Production implication"]),
        ],
        "mcqs": [
            _mcq("Station, equipment, and electrical_board are what type of category?", ["Ordinal", "Nominal", "Continuous", "Target"], 1, "They have no natural order."),
            _mcq("When is ordinal encoding reasonable?", ["When order is meaningful", "Whenever there are three values", "Only for target labels", "Never"], 0, "Ordinal encoding needs real order."),
            _mcq("What should production do with an unseen category?", ["Use explicit unknown handling and monitor rate", "Crash silently", "Refit encoder on one request", "Map it randomly"], 0, "Runtime behavior must be defined."),
            _mcq("What is target encoding leakage?", ["Using validation/test/future labels to compute category statistics", "Saving the encoder", "Handling unknowns", "Using one-hot"], 0, "Target encoding uses labels, so leakage control is critical."),
        ],
    },
    "mlf_014": {
        "title": "Scaling, normalization, and pipeline leakage",
        "definition": "Scaling changes numeric ranges; standardization expresses values relative to training mean and standard deviation; preprocessing leakage happens when transformation parameters are learned from data outside the training boundary.",
        "why_it_exists": "Some model families are sensitive to feature magnitude. Without controlled preprocessing, one feature can dominate distances or optimization, and evaluation can become contaminated if preprocessing learns from validation/test/future data.",
        "core_mechanism": "Min-max scaling uses (x - min) / (max - min). Z-score standardization uses (x - training_mean) / training_std. Fit learns min, max, mean, or std. Transform applies those learned parameters. Fit belongs to training data only; validation, test, and production should only be transformed using the saved training transformer.",
        "worked_example": "For values [50, 60, 70, 80, 90, 100], min=50 and max=100, so 70 scales to (70-50)/(100-50)=0.4. The mean is 75. If population std is about 17.08, 70 standardizes to (70-75)/17.08=-0.29. The exact calculation matters less than the architecture rule: learn these parameters from training data only.",
        "nuances": ["Scaling is not always needed; tree models are usually less scale-sensitive than KNN, SVM, PCA, logistic regression, and neural networks.", "Normalization is often used loosely. Be precise: min-max scaling vs z-score standardization.", "Out-of-range production values do not require refitting live; they require monitoring and a response policy.", "Pipeline leakage can happen even when the model code itself uses a clean train/test split."],
        "when_it_matters": "It matters most for distance-based, gradient-based, and projection-based models, and whenever preprocessing is part of an ML pipeline.",
        "when_it_matters_less": "It matters less for tree-based models, although train/inference pipeline consistency still matters.",
        "common_confusions": ["Calling z-score standardization normalization without explaining mean/std.", "Fitting scalers separately on validation, test, or production data."],
        "architect_implications": ["Use a pipeline object so preprocessing and model travel together.", "Fit transformers on training only, then persist and reuse them.", "Monitor input ranges and out-of-training-distribution values."],
        "system_controls": ["Pipeline with fit-on-train-only", "Saved transformer artifact", "Feature range contract", "Out-of-range monitoring", "Data split tests to detect preprocessing leakage"],
        "mission_answer_frame": ["Define min-max scaling and z-score standardization separately.", "Show calculation if numbers are given.", "State fit vs transform clearly.", "Name model families affected by scale.", "Add pipeline controls to prevent leakage."],
        "missions": [
            _mission("q1", "concept_check", "Explain the difference between min-max scaling and z-score standardization. Why should an architect care?", ["Range vs mean/std", "Scale-sensitive models", "Pipeline consistency"]),
            _mission("q2", "tiny_hands_on", "For values [50, 60, 70, 80, 90, 100], calculate min-max scaled values to 0-1 and z-score standardized values using the training mean and standard deviation. Show the calculation pattern.", ["Min-max formula", "Mean/std formula", "Uses training parameters"]),
            _mission("q3", "failure_diagnosis", "A scaler was fitted on train + test data before validation, and the model later performs worse in production. What went wrong?", ["Preprocessing leakage", "Test data influenced transformation", "Offline performance was optimistic"]),
            _mission("q4", "architect_decision", "Design a preprocessing pipeline for a predictive quality model that prevents scaling leakage and preserves training-serving consistency.", ["Fit on train only", "Persist transformer", "Transform validation/test/inference", "Monitor ranges", "Pipeline object"]),
            _mission("q5", "teachback", "Explain scaling, standardization, and leakage in interview-ready language with one simple numeric example.", ["Clear distinction", "Example", "Production control"]),
        ],
        "mcqs": [
            _mcq("What does fit do for a scaler?", ["Learns parameters like min/max/mean/std", "Applies already learned parameters only", "Creates target labels", "Deletes outliers automatically"], 0, "Fit learns transformation parameters."),
            _mcq("Where should a scaler be fitted?", ["Training data only", "All data", "Test data only", "Each production request"], 0, "Fitting outside training causes leakage or inconsistency."),
            _mcq("Which models are usually scale-sensitive?", ["KNN, SVM, PCA, logistic regression, neural networks", "Only decision trees", "Only SQL rules", "Only dashboards"], 0, "Distance/gradient/projection methods often care about scale."),
            _mcq("What is preprocessing leakage?", ["Learning preprocessing parameters from validation/test/future data", "Saving a pipeline", "Transforming test with training scaler", "Monitoring input range"], 0, "Data outside training must not influence fitted preprocessing parameters."),
        ],
    },
    "mlf_015": {
        "title": "Regularization: controlling model complexity",
        "definition": "Regularization adds a penalty for unnecessary model complexity so the model is less tempted to chase noise in the training data.",
        "why_it_exists": "A flexible model can fit historical quirks that do not repeat. Regularization trades some training fit for better validation stability.",
        "core_mechanism": "In many models, regularization adds a penalty term to the loss. L2 discourages large weights. L1 can push some weights to zero. The regularization strength controls the bias-variance trade-off.",
        "worked_example": "If a linear defect model gives huge weight to a noisy sensor because it happened to correlate with defects in one month, L2 regularization can shrink that weight. If the signal is truly useful, validation performance should show the right balance.",
        "nuances": ["Regularization is not data cleaning and cannot fix leakage or wrong labels.", "Too little regularization can overfit; too much can underfit.", "The regularization strength is chosen using validation evidence, not intuition.", "L1 supports sparsity; L2 supports smoother weight shrinkage."],
        "when_it_matters": "It matters when model capacity is high relative to dataset size, noise, or feature count.",
        "when_it_matters_less": "It matters less when the model is already too simple or when failure is caused by bad labels, leakage, or missing features.",
        "common_confusions": ["Treating regularization as a universal fix for poor data.", "Thinking stronger regularization is always better."],
        "architect_implications": ["Require validation curves or train-vs-validation comparison before approving regularization strength.", "Track whether regularization improves generalization or merely hides underfitting.", "Document chosen hyperparameters and validation rationale."],
        "system_controls": ["Hyperparameter search with validation", "Train/validation learning curves", "Bias-variance diagnosis", "Model card with chosen regularization strength"],
        "mission_answer_frame": ["State the complexity problem.", "Name L1/L2 or another control.", "Explain bias-variance effect.", "Use validation evidence.", "State under/over-regularization risk."],
        "missions": [
            _mission("q1", "concept_check", "Explain regularization in your own words. How is it different from simply making a model smaller?", ["Penalty for complexity", "Controls overfitting", "Not data cleaning"]),
            _mission("q2", "tiny_hands_on", "A model has training recall 96% and validation recall 61%. After stronger regularization, training recall is 82% and validation recall is 76%. How would you interpret this?", ["Overfitting reduced", "Training score dropped but validation improved", "Trade-off is beneficial if business threshold is met"]),
            _mission("q3", "failure_diagnosis", "A team keeps increasing regularization and both training and validation performance become poor. What likely happened?", ["Too much regularization", "Underfitting", "Need validation-based tuning"]),
            _mission("q4", "architect_decision", "What controls would you define for selecting regularization strength in a production ML pipeline?", ["Validation strategy", "Hyperparameter search", "Learning curves", "Acceptance criteria"]),
            _mission("q5", "teachback", "Explain regularization to an interviewer using a practical manufacturing AI example.", ["Plain language", "Noise vs real signal", "Validation-based decision"]),
        ],
        "mcqs": [
            _mcq("What does regularization mainly control?", ["Model complexity", "Database latency", "Label creation", "Dashboard count"], 0, "Regularization penalizes complexity."),
            _mcq("What can too much regularization cause?", ["Underfitting", "Perfect recall", "Leakage", "More categories"], 0, "Too much constraint can make the model too simple."),
            _mcq("Which regularization can drive weights to zero?", ["L1", "L2", "Train/test split", "Confusion matrix"], 0, "L1 can create sparse models."),
            _mcq("How should regularization strength be chosen?", ["Validation evidence", "Alphabetical order", "Stakeholder seniority", "Model name"], 0, "Use validation, not guesswork."),
        ],
    },
    "mlf_016": {
        "title": "Threshold tuning and cost-sensitive decisions",
        "definition": "Threshold tuning converts model scores into actions by choosing the decision boundary that best matches business cost and operational capacity.",
        "why_it_exists": "A model score is not a business decision. The same probability can lead to different actions depending on whether false positives or false negatives are more costly.",
        "core_mechanism": "For binary classifiers, lowering the positive threshold usually catches more positives and increases recall, but may create more false positives. Raising the threshold usually improves precision but can miss positives.",
        "worked_example": "If missing a defect costs warranty claims but extra inspections cost time, you may set a minimum defect recall target first, then tune precision so inspection workload stays manageable.",
        "nuances": ["0.5 is a default, not a policy.", "Thresholds should be chosen on validation data and reviewed after deployment.", "Different plants, products, or defect types may need different thresholds.", "Threshold changes require governance because they change operational workload."],
        "when_it_matters": "It matters when model outputs trigger actions: inspect, reject, approve, escalate, or notify.",
        "when_it_matters_less": "It matters less for pure ranking or regression tasks where there is no binary action threshold yet.",
        "common_confusions": ["Treating probability score as the final decision.", "Optimizing generic accuracy instead of error cost."],
        "architect_implications": ["Define metric policy before go-live.", "Set thresholds using cost of FP/FN and capacity.", "Assign ownership for threshold changes."],
        "system_controls": ["Threshold review board or owner", "Precision-recall curve review", "Minimum recall or precision gate", "Alert volume/capacity monitor", "Change log for threshold updates"],
        "mission_answer_frame": ["State the action decision.", "Name FP/FN cost.", "Choose metric priority.", "Use validation curve and capacity.", "Define owner and monitoring."],
        "missions": [
            _mission("q1", "concept_check", "Explain threshold tuning. Why is a 0.5 threshold not automatically right?", ["Score vs decision", "Business cost", "0.5 is default not policy"]),
            _mission("q2", "tiny_hands_on", "A defect model at threshold 0.7 has precision 90% and recall 35%. At threshold 0.4 it has precision 62% and recall 78%. Which would you consider for go-live if missed defects are costly?", ["Prioritize recall when false negatives are costly", "Mention inspection workload", "Use threshold trade-off"]),
            _mission("q3", "failure_diagnosis", "A deployed model has high precision but customers still receive defective products. What threshold-related issue may exist?", ["Recall too low", "Threshold too strict", "False negatives not controlled"]),
            _mission("q4", "architect_decision", "Design threshold governance for a manufacturing defect model.", ["Metric target", "Capacity", "Owner", "Review cadence", "Monitoring"]),
            _mission("q5", "teachback", "Explain threshold tuning to a quality leader in simple terms.", ["Business decision boundary", "FP/FN trade-off", "Operational example"]),
        ],
        "mcqs": [
            _mcq("If false negatives are costlier, what often matters more?", ["Recall", "Model file size", "Feature count", "Training speed"], 0, "Recall controls missed positives."),
            _mcq("Lowering the positive threshold usually does what?", ["Increases recall and may increase false positives", "Guarantees perfect precision", "Deletes labels", "Retrains the model"], 0, "Lower thresholds catch more positives but raise alarms."),
            _mcq("Why is 0.5 not automatically right?", ["It ignores cost and capacity", "It is illegal", "It only works in Python", "It requires neural networks"], 0, "Thresholds are business policies."),
            _mcq("What should govern threshold changes?", ["Owner, evidence, review cadence, and monitoring", "Anyone's preference", "No records", "Only chart color"], 0, "Thresholds affect operations."),
        ],
    },
    "mlf_017": {
        "title": "Class imbalance handling strategies",
        "definition": "Class imbalance means one class dominates the dataset, making aggregate metrics look good while the minority class may be ignored.",
        "why_it_exists": "Many business-critical events are rare: defects, fraud, churn, failures. Models can learn the majority shortcut unless training, metrics, and thresholds force attention to the minority class.",
        "core_mechanism": "Imbalance affects objective and evaluation. Sampling changes the training distribution. Class weights change error penalty. Threshold tuning changes final decisions. Metrics must report minority-class behavior.",
        "worked_example": "If 2% of parts are defective, predicting 'good' for every part gives 98% accuracy and 0% defect recall. That model is accurate and useless for defect detection.",
        "nuances": ["Imbalance is not automatically bad; it is dangerous when the rare class carries business risk.", "Oversampling can overfit duplicated minority cases.", "Undersampling can discard useful majority information.", "Class weights and threshold tuning solve different parts of the problem."],
        "when_it_matters": "It matters when the minority class is the class the business cares about or when error costs are asymmetric.",
        "when_it_matters_less": "It matters less when the rare class is not decision-critical or when ranking quality is the main goal and evaluated properly.",
        "common_confusions": ["Thinking high accuracy means imbalance is solved.", "Using one imbalance technique without validating minority-class outcomes."],
        "architect_implications": ["Define class-specific metric gates.", "Compare sampling, class weights, threshold tuning, and data collection.", "Monitor minority-class recall and class distribution after go-live."],
        "system_controls": ["Confusion matrix", "Minority recall/precision/F1", "Sampling strategy approval", "Threshold policy", "Class distribution monitoring"],
        "mission_answer_frame": ["State class distribution.", "Explain majority shortcut.", "Choose class-specific metrics.", "Select handling strategy.", "Define production monitoring."],
        "missions": [
            _mission("q1", "concept_check", "Explain class imbalance and why accuracy can become misleading.", ["Majority class dominance", "Minority-class risk", "Accuracy weakness"]),
            _mission("q2", "tiny_hands_on", "In 1000 inspections, 20 parts are defective. A model predicts all parts as good. Calculate accuracy and defect recall. What does this show?", ["98% accuracy", "0% defect recall", "Accuracy is misleading"]),
            _mission("q3", "failure_diagnosis", "A model has high accuracy but misses most rare defects. What likely went wrong in training/evaluation?", ["Majority shortcut", "Wrong metric policy", "Need class-specific evaluation"]),
            _mission("q4", "architect_decision", "What imbalance handling strategy would you design for rare but costly manufacturing defects?", ["Class weights/sampling/threshold/data collection", "Metric gates", "Monitoring"]),
            _mission("q5", "teachback", "Explain class imbalance to a non-technical quality stakeholder.", ["Simple rare-event example", "Business risk", "Recall/inspection trade-off"]),
        ],
        "mcqs": [
            _mcq("Which metric is dangerous alone on imbalanced data?", ["Accuracy", "Recall", "Confusion matrix", "Class-specific F1"], 0, "Accuracy can hide minority failure."),
            _mcq("A no-defect predictor in 98% good-parts data likely has what?", ["High accuracy and zero defect recall", "Perfect defect detection", "No false negatives", "Guaranteed production readiness"], 0, "It misses all defects."),
            _mcq("What do class weights change?", ["Mistake penalty by class", "Sensor units", "Deployment server", "Dashboard title"], 0, "Weights make some class errors costlier in training."),
            _mcq("What should be monitored after deployment?", ["Class distribution and minority-class recall", "Only API uptime", "Only feature count", "Only model name"], 0, "Minority behavior can degrade."),
        ],
    },
    "mlf_018": {
        "title": "Error analysis and model debugging",
        "definition": "Error analysis is the structured investigation of where, when, and why a model is wrong, instead of looking only at one average score.",
        "why_it_exists": "Average metrics hide segment failures. A model may look acceptable overall but fail for a plant, product family, supplier, shift, sensor range, or defect type.",
        "core_mechanism": "Slice errors by meaningful segments, inspect false positives/false negatives, compare prediction confidence, check data quality, review labels, and turn findings into a prioritized fix backlog.",
        "worked_example": "Overall recall is 75%, but for night-shift Line 3 it is 38%. That slice points to a specific operational or data issue that the global score hides.",
        "nuances": ["Debugging starts with error taxonomy, not random model tweaking.", "Some errors are data issues, some are labeling issues, some are model-capacity issues, and some are business-rule mismatches.", "Fixes should be prioritized by business impact and evidence.", "A dashboard without investigation workflow is not error analysis."],
        "when_it_matters": "It matters after any model misses acceptance targets or before expanding from pilot to production.",
        "when_it_matters_less": "It matters less in the very first proof-of-concept stage before labels and metrics are trustworthy.",
        "common_confusions": ["Trying a new algorithm before understanding error slices.", "Treating all false negatives as one generic failure."],
        "architect_implications": ["Require error-slice reporting before go-live.", "Define debugging workflow and ownership.", "Connect error analysis to data collection and retraining backlog."],
        "system_controls": ["Slice metrics", "False positive/false negative review", "Label audit", "Data-quality checks", "Fix backlog with owner and impact"],
        "mission_answer_frame": ["State observed error pattern.", "Slice by meaningful segments.", "Separate data/label/model/business causes.", "Prioritize fix by impact.", "Define follow-up validation."],
        "missions": [
            _mission("q1", "concept_check", "Explain error analysis and how it differs from just reporting average model accuracy.", ["Slice-level investigation", "Error types", "Average metrics hide failures"]),
            _mission("q2", "tiny_hands_on", "Overall defect recall is 76%, but recall is 42% for Supplier B and 81% for others. What would you investigate first?", ["Supplier slice", "Data/label/process difference", "Prioritized investigation"]),
            _mission("q3", "failure_diagnosis", "A team switches algorithms repeatedly but the same segment keeps failing. What is wrong with their debugging approach?", ["No root-cause slicing", "Could be data/label issue", "Algorithm swapping is premature"]),
            _mission("q4", "architect_decision", "Design an error-analysis workflow before releasing a model to multiple plants.", ["Slice metrics", "FP/FN review", "Owner", "Fix backlog", "Validation after fix"]),
            _mission("q5", "teachback", "Explain why an ML Architect cares about error analysis using a manufacturing example.", ["Stakeholder language", "Segment failure", "Operational fix"]),
        ],
        "mcqs": [
            _mcq("What does error analysis add beyond average accuracy?", ["Where and why the model fails", "Only prettier charts", "Automatic retraining", "More labels always"], 0, "It locates failure patterns."),
            _mcq("Which is a useful error slice?", ["Plant, line, supplier, shift, product family", "Font size", "Model filename", "Dashboard color"], 0, "Operational segments explain failure."),
            _mcq("What should happen before algorithm swapping?", ["Inspect errors and likely causes", "Ignore labels", "Delete validation", "Increase badge count"], 0, "Debug first, then choose fixes."),
            _mcq("What is a good output of error analysis?", ["Prioritized fix backlog", "Generic complaint", "Only one metric", "No ownership"], 0, "Analysis must turn into action."),
        ],
    },
    "mlf_019": {
        "title": "Model interpretability and explainability limits",
        "definition": "Interpretability helps explain model behavior, but explanations are evidence about model logic, not proof of real-world causality.",
        "why_it_exists": "Stakeholders need to understand and challenge model decisions, but explanation tools can be misread as causal truth or operational approval.",
        "core_mechanism": "Global explanations describe broad model behavior. Local explanations describe one prediction. Feature importance shows association inside the model, not necessarily the true cause in the process.",
        "worked_example": "If temperature ranks high in a defect model, it may be a useful signal. It does not prove temperature causes defects. It may correlate with shift, machine type, or operating condition.",
        "nuances": ["Correlated features can split or distort importance.", "Explanations can change when data distribution changes.", "Local and global explanations answer different questions.", "Explanations need governance: usage limits, audit trail, review path, and communication rules."],
        "when_it_matters": "It matters when model outputs affect decisions, approvals, escalations, customer impact, or regulated processes.",
        "when_it_matters_less": "It matters less for low-risk batch analytics where predictions are advisory and not used directly for action.",
        "common_confusions": ["Treating feature importance as causal proof.", "Using explanations to skip validation or domain review."],
        "architect_implications": ["Define how explanations are generated and reviewed.", "State explanation limits to stakeholders.", "Require domain validation before process changes."],
        "system_controls": ["Explanation method selection", "Audit trail", "Causality warning", "Domain review workflow", "Counterfactual or experiment plan where needed"],
        "mission_answer_frame": ["State what explanation shows.", "State what it does not prove.", "Give example of misuse.", "Define review/validation control.", "Explain stakeholder communication."],
        "missions": [
            _mission("q1", "concept_check", "Explain interpretability and why feature importance is not the same as causality.", ["Model behavior vs real-world cause", "Global/local distinction", "Causality limit"]),
            _mission("q2", "tiny_hands_on", "A defect model says temperature is the most important feature. What conclusions can and cannot be drawn?", ["Useful signal", "Not causal proof", "Need domain/process validation"]),
            _mission("q3", "failure_diagnosis", "A team changes factory settings because SHAP showed one feature was important, and defects increase. What went wrong?", ["Explanation misused as causality", "No domain validation", "Governance failure"]),
            _mission("q4", "architect_decision", "Design explainability governance for a manufacturing AI system.", ["Method choice", "Audit trail", "Usage limits", "Review path", "Communication rules"]),
            _mission("q5", "teachback", "Explain to a stakeholder what model explanations can and cannot tell them.", ["Simple language", "Example", "Limits and action rule"]),
        ],
        "mcqs": [
            _mcq("Feature importance proves what?", ["Model association, not causality", "Guaranteed real-world cause", "Perfect prediction", "No need for review"], 0, "Importance is not causal proof."),
            _mcq("What is a local explanation?", ["Explanation for one prediction", "Company-wide policy", "Model retraining", "Database backup"], 0, "Local explains one case."),
            _mcq("Why can correlated features confuse explanations?", ["Importance can split across related features", "Models cannot predict", "Labels vanish", "Recall is impossible"], 0, "Correlation can distort attribution."),
            _mcq("What should govern explanation use?", ["Usage limits, audit trail, review path", "Chart color only", "No documentation", "Random action"], 0, "Explanations affect decisions."),
        ],
    },
    "mlf_020": {
        "title": "ML monitoring: drift, performance, and retraining triggers",
        "definition": "ML monitoring checks whether inputs, predictions, performance, and business outcomes remain trustworthy after deployment.",
        "why_it_exists": "A model can be technically available while its predictions degrade. API uptime is not model reliability.",
        "core_mechanism": "Monitor input drift, prediction drift, performance drift when labels arrive, data quality, business KPIs, and operational actions. A useful monitor has thresholds, owner, response path, and retraining criteria.",
        "worked_example": "If humidity distribution shifts after a process change and defect recall drops two weeks later, monitoring should trigger investigation before scrap or warranty cost accumulates.",
        "nuances": ["Input and prediction drift can be monitored before labels arrive.", "Performance metrics need labels and often arrive late.", "Retraining is not automatic; it needs data review, validation, approval, and release controls.", "A dashboard without owner and playbook is not monitoring architecture."],
        "when_it_matters": "It matters after any model is used for operational decisions or stakeholder reporting.",
        "when_it_matters_less": "It matters less for one-off offline analysis with no repeated production use.",
        "common_confusions": ["Monitoring only uptime and latency.", "Retraining whenever drift appears without diagnosing impact."],
        "architect_implications": ["Define monitoring signals and thresholds before go-live.", "Separate drift detection from performance measurement.", "Create response playbooks and retraining governance."],
        "system_controls": ["Input drift", "Prediction drift", "Delayed-label performance", "Alert thresholds", "Owner and escalation", "Fallback and retraining trigger"],
        "mission_answer_frame": ["Name signals to monitor.", "Separate no-label and label-based metrics.", "Define thresholds/time windows.", "State owner and response.", "Define retraining trigger and validation."],
        "missions": [
            _mission("q1", "concept_check", "Explain ML monitoring and how it differs from normal system monitoring.", ["Model behavior vs API uptime", "Data/prediction/performance signals", "Trust after deployment"]),
            _mission("q2", "tiny_hands_on", "A model API is healthy, but predicted defect rates suddenly drop to near zero while input sensor distributions changed. What would you check?", ["Prediction drift", "Input drift", "Possible silent degradation"]),
            _mission("q3", "failure_diagnosis", "A model degraded for weeks because labels arrived late and nobody owned the monitoring response. What failed architecturally?", ["Delayed label monitoring", "No owner/playbook", "Governance failure"]),
            _mission("q4", "architect_decision", "Design monitoring and retraining triggers for a deployed predictive quality model.", ["Input/prediction/performance metrics", "Thresholds", "Owner", "Fallback", "Retraining validation"]),
            _mission("q5", "teachback", "Explain to an interviewer why ML monitoring is more than checking whether the API is up.", ["Simple distinction", "Example", "Operational response"]),
        ],
        "mcqs": [
            _mcq("What is not enough for ML monitoring?", ["API uptime only", "Input drift", "Prediction distribution", "Recall over time"], 0, "A healthy API can serve poor predictions."),
            _mcq("What can be monitored before labels arrive?", ["Input and prediction drift", "True recall only", "Final warranty cost only", "Manual inspection accuracy only"], 0, "Labels are needed for performance, not for all monitoring."),
            _mcq("What makes a retraining trigger useful?", ["Threshold, owner, validation, release process", "A vague feeling", "Monthly meeting only", "New algorithm name"], 0, "Retraining needs governance."),
            _mcq("What is input drift?", ["Feature distribution changed", "Model file got larger", "Dashboard moved", "Target renamed only"], 0, "Input drift means incoming features changed."),
        ],
    },
}


def get_topic_blueprint(topic_id: str) -> Optional[Dict[str, Any]]:
    blueprint = EXPERT_BLUEPRINTS.get(str(topic_id or ""))
    if not blueprint:
        return None
    enriched = dict(blueprint)
    enriched["topic_id"] = topic_id
    enriched.setdefault("blueprint_version", "expert_tutor_blueprint_v1_2026_05")
    return enriched


def has_topic_blueprint(topic_id: str) -> bool:
    return str(topic_id or "") in EXPERT_BLUEPRINTS


def _first(items: List[str], fallback: str = "") -> str:
    return items[0] if items else fallback


def build_concept_note_from_blueprint(topic: Topic) -> ConceptNote:
    bp = get_topic_blueprint(topic.topic_id)
    if bp is None:
        raise ValueError(f"No expert blueprint found for topic {topic.topic_id}")
    return ConceptNote(
        topic_id=topic.topic_id,
        title=bp.get("title", topic.title),
        simple_explanation=" ".join([
            str(bp.get("definition", "")),
            str(bp.get("why_it_exists", "")),
            str(bp.get("core_mechanism", "")),
        ]).strip(),
        wrong_mental_model=_first(bp.get("common_confusions", []), f"Treating {topic.title} as a generic production-risk topic instead of understanding its specific mechanism."),
        correct_mental_model=(
            f"Understand the specific mechanism first, then connect it to the architect controls. "
            f"For {topic.title}, the core mechanism is: {bp.get('core_mechanism', '')}"
        ),
        tiny_example=str(bp.get("worked_example", "")),
        why_it_matters=str(bp.get("when_it_matters", bp.get("why_it_exists", ""))),
        edge_case=str(_first(bp.get("common_confusions", [""]), "A generic answer hides the exact failure mechanism and leads to weak architecture decisions.")),
        three_takeaways=[
            str(bp.get("definition", "")),
            str(bp.get("core_mechanism", "")),
            "Architect-level answers must name the mechanism, the evidence, and the control instead of repeating generic production-risk language.",
        ],
    )


def build_architect_note_from_blueprint(topic: Topic) -> ArchitectNote:
    bp = get_topic_blueprint(topic.topic_id)
    if bp is None:
        raise ValueError(f"No expert blueprint found for topic {topic.topic_id}")
    controls = bp.get("system_controls", []) or []
    implications = bp.get("architect_implications", []) or []
    confusions = bp.get("common_confusions", []) or []
    return ArchitectNote(
        topic_id=topic.topic_id,
        architect_summary=(
            f"As an ML Architect, the point of {topic.title} is not to repeat the definition. "
            f"It is to design the pipeline, validation, ownership, and monitoring controls around the concept-specific mechanism. "
            f"Mechanism: {bp.get('core_mechanism', '')}"
        ),
        design_implications=(implications + controls + ["Document the decision rule and owner before go-live."])[:3] or [
            "Define the design control created by this concept.",
            "Validate the control before production use.",
        ],
        common_mistakes=(confusions + ["Using generic leakage/generalization language without naming the specific mechanism."])[:3],
        production_risks=[
            str(bp.get("production_trap", "Generic production failure caused by not controlling the concept-specific mechanism.")),
            f"Weak architecture review if the team cannot state: mechanism, evidence to inspect, and control for {topic.title}.",
        ],
        interview_framing=(
            f"I would explain {topic.title} by first defining the mechanism, then showing a small example, "
            "then naming the architecture control. "
            f"Example: {bp.get('worked_example', '')}"
        ),
        use_case_mapping=[
            UseCaseMapping(
                context="manufacturing_ai",
                relevance=f"Use this concept to make predictive quality models safer by applying controls such as: {', '.join(controls[:3])}.",
            )
        ],
    )


def build_assessment_from_blueprint(topic: Topic) -> Assessment:
    bp = get_topic_blueprint(topic.topic_id)
    if bp is None:
        raise ValueError(f"No expert blueprint found for topic {topic.topic_id}")
    questions = [AssessmentQuestion(**item) for item in bp.get("missions", [])]
    if len(questions) != 5:
        raise ValueError(f"Expert blueprint for {topic.topic_id} must define exactly 5 missions.")
    return Assessment(topic_id=topic.topic_id, questions=questions)


def build_booster_from_blueprint(topic_id: str) -> Optional[Dict[str, Any]]:
    bp = get_topic_blueprint(topic_id)
    if bp is None:
        return None
    return {
        "topic_id": topic_id,
        "title": bp.get("title", topic_id),
        "plain_language": bp.get("definition", ""),
        "why_it_exists": bp.get("why_it_exists", ""),
        "core_mechanism": bp.get("core_mechanism", ""),
        "worked_example": bp.get("worked_example", ""),
        "nuances": bp.get("nuances", []),
        "when_it_matters": bp.get("when_it_matters", ""),
        "when_it_matters_less": bp.get("when_it_matters_less", ""),
        "production_trap": "; ".join(bp.get("common_confusions", [])[:2]),
        "mission_hint": "Use the mission answer frame. Do not repeat generic leakage/generalization language unless you connect it to the topic-specific mechanism.",
        "key_distinctions": bp.get("nuances", []),
        "answer_frame": bp.get("mission_answer_frame", []),
        "mission_bridge": _mission_bridge_from_blueprint(bp),
        "mission_focus": _mission_focus_from_blueprint(bp),
        "mcqs": bp.get("mcqs", []),
        "blueprint_version": bp.get("blueprint_version", "expert_tutor_blueprint_v1_2026_05"),
    }


def _mission_bridge_from_blueprint(bp: Dict[str, Any]) -> List[Dict[str, str]]:
    items: List[Dict[str, str]] = []
    for mission in bp.get("missions", []) or []:
        items.append(
            {
                "mission_type": str(mission.get("type", "mission")),
                "tested_skill": "; ".join(str(x) for x in mission.get("expected_focus", [])[:2]) or "Apply the concept precisely.",
                "use_from_booster": f"Use the mechanism: {bp.get('core_mechanism', '')} Answer frame: {' | '.join(bp.get('mission_answer_frame', [])[:3])}",
            }
        )
    return items


def _mission_focus_from_blueprint(bp: Dict[str, Any]) -> List[str]:
    focus: List[str] = []
    focus.append(str(bp.get("core_mechanism", "")))
    focus.extend(str(item) for item in bp.get("system_controls", [])[:4])
    return [item for item in focus if item][:6]
