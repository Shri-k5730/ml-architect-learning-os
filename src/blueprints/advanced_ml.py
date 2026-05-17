
from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, List, Optional

from src.schemas import ArchitectNote, Assessment, AssessmentQuestion, ConceptNote, UseCaseMapping


def _mcq(question: str, options: List[str], answer_index: int, explanation: str) -> Dict[str, Any]:
    return {"question": question, "options": options, "answer_index": answer_index, "explanation": explanation}


def _mission(question_id: str, qtype: str, question: str, expected_focus: List[str]) -> Dict[str, Any]:
    return {"question_id": question_id, "type": qtype, "question": question, "expected_focus": expected_focus}


ADVANCED_ML_BLUEPRINTS: Dict[str, Dict[str, Any]] = {
    "checkpoint_ml_foundations_001": {
        "topic_id": "checkpoint_ml_foundations_001",
        "title": "Checkpoint 1: ML Foundations Review",
        "module": "Module 1 Checkpoint",
        "definition": "A checkpoint is an integrated review that tests whether the first ten ML foundations work together as one trust chain.",
        "plain_intuition": "Do not think of baseline, split, leakage, accuracy, precision, and recall as separate vocabulary words. They are connected controls for deciding whether a model deserves trust.",
        "why_it_exists": "A learner can pass individual lessons yet still fail to connect metric calculation, leakage diagnosis, and go-live judgment. The checkpoint forces that connection before Advanced ML.",
        "core_mechanism": "The trust chain is: define the target, split data correctly, compare against a baseline, prevent leakage, choose metrics from business risk, then define monitoring and fallback before go-live.",
        "worked_example": "A defect model has 96% accuracy, precision 60%, and recall 30%. The headline looks strong, but the model misses 70% of real defects. The decision is not 'deploy because accuracy is high'; it is 'fix recall, tune threshold, or add fallback inspection before deployment'.",
        "nuances": [
            "A valid metric is useless if leakage contaminated the evaluation.",
            "A strong model is not automatically production-ready without threshold policy, monitoring, and owner response.",
            "A baseline is not a production approval; it is a value comparison anchor.",
        ],
        "when_matters": "It matters whenever a model moves from learning concepts to making deployment decisions.",
        "when_less": "It matters less only for isolated practice questions where no production decision is being made.",
        "common_confusions": [
            "Treating high accuracy as sufficient evidence for go-live.",
            "Explaining leakage as a vague data problem instead of a point-in-time or feature-availability violation.",
            "Forgetting that threshold choice changes precision and recall trade-offs.",
        ],
        "architect_implications": [
            "Architects must define the model trust boundary: what was validated, what was not, and what control catches failures after go-live.",
            "Metric policy must be tied to business risk, not generic model performance language.",
        ],
        "system_design_controls": [
            "Point-in-time split validation",
            "Baseline comparison",
            "Confusion-matrix review",
            "Threshold policy",
            "Monitoring and fallback owner",
        ],
        "mission_answer_frame": [
            "Identify which foundation concept is being tested.",
            "Use the numbers or scenario evidence.",
            "State the concrete risk exposed.",
            "Make a go-live decision.",
            "Name the control that reduces the risk.",
        ],
        "do_not_waste_words": [
            "Do not repeat that models learn patterns.",
            "Do not say 'production risk' without naming the specific risk.",
            "Do not approve a model from aggregate accuracy alone.",
        ],
        "mcqs": [
            _mcq("A model has 96% accuracy but 30% defect recall. What is the safest interpretation?", ["Deploy it", "Unsafe if missed defects matter", "Ignore recall", "Retrain only because accuracy is high"], 1, "Low recall means many actual defects are missed."),
            _mcq("What makes a test score invalid?", ["Using a baseline", "Using future/post-event features", "Checking recall", "Monitoring predictions"], 1, "Future or post-event information creates leakage."),
            _mcq("What does a baseline prove?", ["Whether a complex model adds value over a simple reference", "Whether deep learning is required", "Whether monitoring can be skipped", "Whether labels are optional"], 0, "The baseline is the comparison anchor."),
            _mcq("What is missing from offline metrics alone?", ["A production response plan", "A larger chart", "An algorithm name", "A random seed only"], 0, "Go-live needs monitoring, fallback, threshold policy, and ownership."),
        ],
        "missions": [
            _mission("q1", "concept_check", "Explain how baseline, train/test split, leakage, and metric choice work together as a model trust chain.", ["connects baseline, split, leakage, and metrics", "states why one weak link invalidates trust"]),
            _mission("q2", "tiny_hands_on", "A defect model has TP=12, FP=8, FN=28, TN=952. Calculate accuracy, precision, and recall. Would you approve go-live?", ["accuracy=(TP+TN)/total", "precision=TP/(TP+FP)", "recall=TP/(TP+FN)", "go-live decision based on missed defects"]),
            _mission("q3", "failure_diagnosis", "A model scored very high because it used a field created after inspection. What went wrong and how do you prevent it?", ["identifies leakage", "mentions point-in-time feature eligibility", "prevention control"]),
            _mission("q4", "architect_decision", "Design a minimum go-live checklist for a defect detection model after the first ten foundation lessons.", ["baseline", "valid split", "leakage review", "class-level metrics", "threshold", "monitoring/fallback owner"]),
            _mission("q5", "teachback", "Explain to a plant quality leader why 96% accuracy may still be unsafe for defect detection.", ["stakeholder-friendly", "missed defects", "business consequence", "metric alternative"]),
        ],
    },
    "mlf_011": {
        "topic_id": "mlf_011",
        "title": "Model selection and validation strategy",
        "module": "Advanced ML",
        "definition": "Model selection is choosing the model that best fits the decision, data, constraints, and risk, using validation evidence instead of training excitement.",
        "plain_intuition": "The best model is not the model with the nicest headline score. It is the model you can trust under the conditions where it will actually be used.",
        "why_it_exists": "Different models fail differently. A complex model can win average validation score but be unstable by plant, defect type, latency, or explainability requirement.",
        "core_mechanism": "Model selection compares candidates on validation/test performance, segment stability, business-critical metrics, complexity, latency, interpretability, monitoring effort, and retraining cost.",
        "worked_example": "Model A has 92% accuracy but recall collapses on Plant B. Model B has 89% accuracy and stable recall across plants. For defect detection, Model B may be the better architecture choice.",
        "nuances": ["Training score is not selection evidence.", "Average validation score can hide unsafe segment performance.", "A simpler model can be better if it is stable, explainable, and monitorable."],
        "when_matters": "It matters when more than one model candidate can solve the problem and the production cost of errors differs by segment or use case.",
        "when_less": "It matters less in a throwaway experiment with no deployment decision, but even then the validation habit should remain.",
        "common_confusions": ["Selecting the highest training score.", "Treating model complexity as maturity.", "Ignoring segment-level failure pockets."],
        "architect_implications": ["Architects must define the selection criteria before comparing models.", "The chosen model must be supportable in deployment, monitoring, and retraining."],
        "system_design_controls": ["baseline comparison", "validation/test protocol", "segment-level scorecard", "latency budget", "monitoring feasibility review"],
        "mission_answer_frame": ["State candidates and decision context.", "Compare validation/test metrics.", "Check business-critical segments.", "Add deployment constraints.", "Choose and justify trade-off."],
        "do_not_waste_words": ["Do not say 'best model' without metric evidence.", "Do not use training score as proof.", "Do not ignore production constraints."],
        "mcqs": [
            _mcq("Which model is usually safer for production?", ["Highest training accuracy", "Stable performance across important production segments", "Most complex algorithm", "Newest model family"], 1, "Segment stability often matters more than average score."),
            _mcq("Why compare performance by plant or product family?", ["To detect hidden failure pockets", "To make reports longer", "To avoid validation", "To replace monitoring"], 0, "Averages can hide unsafe segments."),
            _mcq("Which is a weak model-selection argument?", ["Best test recall for defects", "Simpler and monitorable with acceptable performance", "Highest training score", "Consistent across lines"], 2, "Training score alone can hide overfitting."),
            _mcq("Which factor belongs in production model selection?", ["Latency and monitoring effort", "Only algorithm name", "Only number of rows", "Whether it sounds modern"], 0, "Deployment constraints are part of selection."),
        ],
        "missions": [
            _mission("q1", "concept_check", "Explain model selection as an ML Architect decision, not just an algorithm comparison.", ["validation evidence", "business metric", "production constraints"]),
            _mission("q2", "tiny_hands_on", "Model A has higher average accuracy, but Model B has better recall on rare defects and stable performance across plants. Which would you choose and why?", ["uses business-critical metric", "segment stability", "justified trade-off"]),
            _mission("q3", "failure_diagnosis", "A team selected a model using training accuracy and it failed after deployment. What went wrong?", ["training score misuse", "overfitting risk", "validation/test strategy"]),
            _mission("q4", "architect_decision", "Define a model-selection scorecard for a manufacturing defect prediction system.", ["baseline", "validation/test metrics", "segment metrics", "latency", "monitoring/explainability"]),
            _mission("q5", "teachback", "Explain to an interviewer why the highest-scoring model is not always the best production model.", ["clear stakeholder explanation", "trade-off", "production reliability"]),
        ],
    },
    "mlf_012": {
        "topic_id": "mlf_012",
        "title": "Feature engineering and feature contracts",
        "module": "Advanced ML",
        "definition": "Feature engineering creates useful model inputs; feature contracts define whether those inputs are valid, available, fresh, and consistent enough to use.",
        "plain_intuition": "Features are what the model sees. Contracts are the rules that stop the model from seeing impossible, stale, differently calculated, or unavailable signals.",
        "why_it_exists": "A feature can look predictive in a notebook but fail in production because it is delayed, calculated differently, has wrong units, or violates valid ranges.",
        "core_mechanism": "A feature contract specifies type, range, allowed values, unit, null handling, freshness, source, and expected availability at training and inference time.",
        "worked_example": "Humidity must be 0 to 100%. Values [30,45,110,-5,60] contain two contract violations: 110 and -5. The pipeline should reject, correct, quarantine, or fallback before prediction.",
        "nuances": ["More features can increase noise and fragility.", "A predictive feature can still be unusable if unavailable at prediction time.", "Unit mismatch, freshness, and source changes are feature-contract failures."],
        "when_matters": "It matters whenever model inputs come from live systems, sensors, manual processes, or delayed downstream sources.",
        "when_less": "It matters less for static toy datasets, but the design habit is still necessary for production learning.",
        "common_confusions": ["Thinking feature engineering means adding more columns.", "Treating feature validation as optional data cleaning.", "Ignoring training-serving feature parity."],
        "architect_implications": ["Architects must define which features are allowed into training and inference.", "Contracts should trigger operational responses, not just dashboard warnings."],
        "system_design_controls": ["schema validation", "range/unit checks", "freshness checks", "null policy", "contract violation routing", "feature store or transformation versioning"],
        "mission_answer_frame": ["Name the feature.", "State the contract rule.", "Identify violation or instability.", "Explain model impact.", "Define pipeline response and monitoring."],
        "do_not_waste_words": ["Do not only say data quality is important.", "Do not say 'add more features'.", "Do not skip availability and freshness."],
        "mcqs": [
            _mcq("What is the best description of a feature contract?", ["A rule set defining valid type, range, unit, freshness, and allowed values", "A list of all possible features", "A trained coefficient", "A dashboard"], 0, "Contracts validate feature usability."),
            _mcq("Humidity range is 0 to 100. Which value violates the contract?", ["30", "45", "60", "110"], 3, "110 is outside range."),
            _mcq("Why can adding more features hurt production ML?", ["Unstable features add noise and dependencies", "Models cannot use more than three features", "Features are only for deep learning", "It removes monitoring"], 0, "Feature stability matters."),
            _mcq("Temperature arrives in Fahrenheit instead of Celsius. What failed?", ["Unit contract", "Learning rate", "Precision threshold", "Target label"], 0, "Unit mismatch is a feature contract failure."),
        ],
        "missions": [
            _mission("q1", "concept_check", "Explain feature engineering and feature contracts, and how they are different.", ["feature creation", "validation contract", "production input reliability"]),
            _mission("q2", "tiny_hands_on", "Humidity must be 0-100%. Values are [30,45,110,-5,60]. Identify violations and what the pipeline should do.", ["110 and -5", "contract violation", "reject/correct/quarantine/fallback"]),
            _mission("q3", "failure_diagnosis", "A model degrades because a sensor starts sending Fahrenheit instead of Celsius. What went wrong?", ["unit mismatch", "contract failure", "validation/control"]),
            _mission("q4", "architect_decision", "Design feature contract controls for a predictive quality pipeline.", ["type/range/unit/freshness/null checks", "violation route", "monitoring owner"]),
            _mission("q5", "teachback", "Explain why feature contracts matter to a non-technical manufacturing stakeholder.", ["simple analogy", "invalid inputs", "business consequence"]),
        ],
    },
    "mlf_013": {
        "topic_id": "mlf_013",
        "title": "Encoding categorical variables safely",
        "module": "Advanced ML",
        "definition": "Categorical encoding converts labels into numeric model inputs while preserving meaning and avoiding training-serving mismatch.",
        "plain_intuition": "Encoding is not just turning words into numbers. It is making sure the numbers do not invent fake order, break when a new category appears, or change between training and production.",
        "why_it_exists": "Most ML models require numeric inputs, but labels such as station, supplier, fault_code, or risk_level carry different kinds of meaning.",
        "core_mechanism": "Nominal categories have no order and often need one-hot, hashing, or embeddings. Ordinal categories have meaningful order and may use ordered values. Encoders are fitted on training data, persisted, and reused during inference.",
        "worked_example": "For Size = Small, Medium, Large, one-hot creates size_small, size_medium, size_large. Small becomes [1,0,0]. If Extra Large appears later, the pipeline should use an unknown bucket, safe ignore behavior, or contract route instead of crashing or inventing a column live.",
        "nuances": ["High-cardinality features can explode with one-hot.", "Target encoding can leak labels if calculated incorrectly.", "Unseen categories are expected in production, not exceptional."],
        "when_matters": "It matters whenever categorical fields enter a deployed model, especially recommendation, defect classification, supplier, station, fault-code, and user/item systems.",
        "when_less": "It matters less for purely numeric models, but mixed production systems almost always contain categorical fields somewhere.",
        "common_confusions": ["Using 1,2,3 for nominal labels.", "Calling every ordered-looking label ordinal.", "Treating retraining as the first runtime control for unknown categories."],
        "architect_implications": ["The encoder is a production artifact and must travel with the model.", "Unknown-category rate should be monitored and tied to retraining review."],
        "system_design_controls": ["saved encoder artifact", "training-only fitting", "unknown bucket or safe ignore", "feature contract", "unknown-rate monitoring", "retraining trigger owner"],
        "mission_answer_frame": ["Classify feature type.", "Choose encoding and justify meaning preservation.", "State fit-on-training-only.", "Handle unseen categories safely.", "Add monitoring/retraining control."],
        "do_not_waste_words": ["Do not spend 100 words saying models need numbers.", "Do not say placeholder without defining behavior.", "Do not jump to retraining before runtime handling."],
        "mcqs": [
            _mcq("Station type has station, equipment, electrical_board. What kind of feature is this?", ["Ordinal", "Nominal", "Continuous", "Target"], 1, "There is no natural order."),
            _mcq("When is ordinal encoding reasonable?", ["When order is meaningful", "Whenever there are three labels", "Only for targets", "Never"], 0, "Ordinal encoding needs real order."),
            _mcq("A new category appears after one-hot training. What should safe inference do?", ["Crash", "Refit live", "Use explicit unknown handling and monitor rate", "Map randomly"], 2, "Unknown handling must be designed."),
            _mcq("What is a target-encoding leakage risk?", ["Using validation/test labels to compute category statistics", "Saving encoder", "Ignoring unknowns safely", "Using same encoder in inference"], 0, "Label statistics can leak."),
        ],
        "missions": [
            _mission("q1", "concept_check", "Explain safe categorical encoding and why encoding choice changes model behavior.", ["nominal vs ordinal", "false order", "unseen categories"]),
            _mission("q2", "tiny_hands_on", "Color has ['Red','Green','Blue'] and you one-hot encode it. How should the system handle new input 'Yellow'?", ["one-hot columns", "unknown bucket/safe ignore", "prediction impact"]),
            _mission("q3", "failure_diagnosis", "A recommendation model gives nonsensical predictions when category 'Purple' appears after deployment. Diagnose the failure.", ["unseen category", "encoder mismatch", "prevention controls"]),
            _mission("q4", "architect_decision", "Design robust categorical encoding for a manufacturing AI system with station, supplier, and fault-code features.", ["feature type", "high cardinality", "saved encoder", "unknown monitoring"]),
            _mission("q5", "teachback", "Explain to an interviewer why categorical encoding can break production if handled casually.", ["simple explanation", "business example", "production control"]),
        ],
    },
    "mlf_014": {
        "topic_id": "mlf_014",
        "title": "Scaling, normalization, and pipeline leakage",
        "module": "Advanced ML",
        "definition": "Scaling changes numeric ranges; z-score standardization expresses values relative to training mean and standard deviation; preprocessing leakage occurs when transformation parameters are learned outside the training boundary.",
        "plain_intuition": "Scaling changes the ruler. Standardization says how far a value is from the average. Leakage happens when the ruler itself was built using test or future data.",
        "why_it_exists": "Some models compare distances or optimize gradients. If one feature has much larger numbers, it can dominate behavior even if it is not more important.",
        "core_mechanism": "Min-max scaling uses (x-min)/(max-min). Z-score standardization uses (x-training_mean)/training_std. Fit learns min, max, mean, or std. Transform applies those saved values to validation, test, and production.",
        "worked_example": "For [50,60,70,80,90,100], min=50 and max=100, so 70 scales to 0.4. Mean is 75. If population std is about 17.08, 70 standardizes to -0.29. The rule is: learn these parameters from training data only.",
        "nuances": ["Tree models are usually less scale-sensitive than KNN, SVM, PCA, logistic regression, and neural networks.", "Out-of-range production values do not mean refit live; they mean monitor and respond.", "Normalization is used loosely; say min-max scaling or z-score standardization when possible."],
        "when_matters": "It matters for distance-based, gradient-based, projection-based, and neural-network models, and whenever preprocessing is part of a reusable pipeline.",
        "when_less": "It matters less for tree-based models, though pipeline consistency still matters.",
        "common_confusions": ["Fitting scalers on the full dataset.", "Fitting validation/test/production separately.", "Using normalization and standardization interchangeably without definition."],
        "architect_implications": ["Preprocessing is part of the model artifact, not a separate notebook convenience.", "The pipeline must enforce fit-on-train-only and transform-only downstream."],
        "system_design_controls": ["pipeline object", "saved transformer", "train-only fit test", "feature range contract", "out-of-training-range monitoring"],
        "mission_answer_frame": ["Define min-max and z-score separately.", "Show formula and one calculation when numbers are given.", "State fit vs transform.", "Name sensitive model families.", "Add leakage controls."],
        "do_not_waste_words": ["Do not just say scaling prevents production failure.", "Do not call z-score standardization normalization without explaining it.", "Do not skip fit vs transform."],
        "mcqs": [
            _mcq("Where should a scaler be fitted?", ["Training data only", "All data", "Test data", "Each production batch"], 0, "Fit learns parameters from training only."),
            _mcq("What is preprocessing leakage?", ["Using test/future data to learn transformation parameters", "Saving the scaler", "Transforming test with train scaler", "Checking input ranges"], 0, "The leak is learning from data outside training."),
            _mcq("What is fit vs transform?", ["Fit learns parameters; transform applies them", "They are identical", "Transform learns labels", "Fit is a dashboard"], 0, "This distinction prevents leakage."),
            _mcq("Which models are usually scale-sensitive?", ["KNN/SVM/PCA/logistic regression/neural networks", "Only decision trees", "Only dashboards", "Only SQL queries"], 0, "Distance/gradient/projection models care about magnitude."),
        ],
        "missions": [
            _mission("q1", "concept_check", "Explain the difference between min-max scaling and z-score standardization, and why the distinction matters.", ["min-max range", "z-score mean/std", "model-family sensitivity"]),
            _mission("q2", "tiny_hands_on", "For values [50,60,70,80,90,100], calculate min-max scaled values and z-score standardized values. Show method and at least two computed examples.", ["min=50 max=100", "mean/std", "formula", "calculation examples"]),
            _mission("q3", "failure_diagnosis", "A scaler was fitted on train+test data and the model later performs poorly in production. What went wrong?", ["preprocessing leakage", "invalid evaluation", "fit-on-train-only control"]),
            _mission("q4", "architect_decision", "Design preprocessing controls for a predictive quality pipeline so scaling/standardization does not leak or drift silently.", ["pipeline object", "saved transformer", "range monitoring", "train-only fit test"]),
            _mission("q5", "teachback", "Explain scaling and standardization in interview-ready language without overexplaining formulas.", ["simple distinction", "example", "leakage risk", "architect control"]),
        ],
    },
    "mlf_015": {
        "topic_id": "mlf_015",
        "title": "Regularization: controlling model complexity",
        "module": "Advanced ML",
        "definition": "Regularization adds a penalty for unnecessary complexity so a model is less tempted to fit noise as if it were signal.",
        "plain_intuition": "Regularization is a discipline mechanism. It tells the model: learn the pattern, but do not become too obsessed with every historical quirk.",
        "why_it_exists": "Models with too much freedom can memorize training noise. Regularization reduces variance by discouraging extreme or unnecessary weights.",
        "core_mechanism": "L2 penalizes large weights and tends to shrink them. L1 can drive some weights to zero and support sparse feature selection. The regularization strength is tuned using validation behavior.",
        "worked_example": "A defect model assigns huge weight to a rare sensor spike because that spike happened in a few bad batches. L2 can shrink that weight so the model relies less on a fragile coincidence.",
        "nuances": ["Too little regularization can overfit.", "Too much regularization can underfit.", "Regularization cannot fix leakage, wrong labels, or missing production features."],
        "when_matters": "It matters when models have many parameters, correlated features, noisy data, or signs of overfitting.",
        "when_less": "It matters less when model complexity is already controlled or the algorithm has different built-in constraints, but validation still decides.",
        "common_confusions": ["Treating regularization as data cleaning.", "Assuming stronger regularization is always better.", "Forgetting to tune strength using validation."],
        "architect_implications": ["Regularization choice belongs in the validation strategy, not only model code.", "Architects should watch whether regularization improves generalization or hides weak feature design."],
        "system_design_controls": ["validation curves", "train-vs-validation comparison", "regularization hyperparameter search", "coefficient/feature review", "segment-level performance check"],
        "mission_answer_frame": ["State complexity problem.", "Choose L1/L2 or other control.", "Explain bias-variance effect.", "Use validation evidence.", "State production risk of under/over-regularization."],
        "do_not_waste_words": ["Do not say only that it prevents overfitting.", "Do not ignore underfitting risk.", "Do not claim regularization fixes bad data."],
        "mcqs": [
            _mcq("What does regularization mainly control?", ["Model complexity", "Database latency", "Label creation", "Dashboard count"], 0, "Regularization penalizes complexity."),
            _mcq("What can too much regularization cause?", ["Underfitting", "Perfect recall", "Data leakage", "More categories"], 0, "Too much constraint makes the model too simple."),
            _mcq("Which regularization can push coefficients to zero?", ["L1", "L2", "Train/test split", "Confusion matrix"], 0, "L1 can create sparse models."),
            _mcq("How should regularization strength be chosen?", ["Validation evidence", "Guessing", "Alphabetical order", "Stakeholder seniority"], 0, "Tune it from validation behavior."),
        ],
        "missions": [
            _mission("q1", "concept_check", "Explain regularization and how it affects overfitting and underfitting.", ["complexity penalty", "variance control", "underfitting risk"]),
            _mission("q2", "tiny_hands_on", "A model has low training error but high validation error. What does this suggest and how could regularization help?", ["overfitting", "train-validation gap", "regularization strength"]),
            _mission("q3", "failure_diagnosis", "A model with very strong regularization misses obvious defect patterns. Diagnose the issue.", ["too much regularization", "underfitting", "validation evidence"]),
            _mission("q4", "architect_decision", "How would you tune and govern regularization in a production ML pipeline?", ["validation strategy", "hyperparameter search", "segment checks", "monitoring"]),
            _mission("q5", "teachback", "Explain regularization to a stakeholder using a practical analogy and production consequence.", ["simple analogy", "noise vs signal", "business risk"]),
        ],
    },
    "mlf_016": {
        "topic_id": "mlf_016",
        "title": "Threshold tuning and cost-sensitive decisions",
        "module": "Advanced ML",
        "definition": "Threshold tuning converts model scores into business decisions by choosing the operating point that matches false-positive and false-negative cost.",
        "plain_intuition": "The model gives a risk score; the threshold decides when the business acts. A default 0.5 threshold is not a business strategy.",
        "why_it_exists": "Different mistakes cost different amounts. Missing a defect may be worse than inspecting a good part, so the threshold should reflect that risk.",
        "core_mechanism": "Lowering the positive threshold usually increases recall and false positives. Raising it usually increases precision and false negatives. The right threshold comes from validation curves, cost, and operational capacity.",
        "worked_example": "If threshold 0.5 catches 40% of defects and threshold 0.3 catches 80% but doubles inspections, the architect must decide whether the extra inspection load is acceptable compared with missed-defect cost.",
        "nuances": ["The model score is not the final decision.", "Thresholds can differ by product or risk segment if governance allows.", "Threshold changes need ownership because they change operations."],
        "when_matters": "It matters for classification systems where predictions trigger actions: inspection, alert, fraud block, intervention, escalation.",
        "when_less": "It matters less when the output is only a ranked list or when decisions are made downstream by a separate policy, but the decision boundary still exists somewhere.",
        "common_confusions": ["Assuming 0.5 is naturally correct.", "Optimizing accuracy instead of business cost.", "Changing thresholds without monitoring operational load."],
        "architect_implications": ["Threshold is part of product policy, not just data science tuning.", "Monitoring should track precision, recall, alert volume, and cost after threshold changes."],
        "system_design_controls": ["precision-recall curve", "cost matrix", "alert volume limit", "threshold owner", "review cadence", "rollback policy"],
        "mission_answer_frame": ["State decision from score.", "Identify costlier error.", "Choose metric priority and threshold direction.", "State capacity constraints.", "Define monitoring and owner."],
        "do_not_waste_words": ["Do not just say balance precision and recall.", "Do not ignore false-negative/false-positive cost.", "Do not treat threshold as fixed model output."],
        "mcqs": [
            _mcq("If false negatives are more costly, which metric often gets priority?", ["Recall", "Training accuracy", "Model size", "Feature count"], 0, "Recall catches actual positives."),
            _mcq("What happens when the positive threshold is lowered?", ["Recall often increases and false positives may increase", "All errors disappear", "Precision always becomes 100%", "The model retrains"], 0, "Lower threshold catches more positives."),
            _mcq("Why is 0.5 not automatically right?", ["It ignores cost and class distribution", "It is illegal", "It only works in Python", "It requires deep learning"], 0, "Thresholds should reflect business cost."),
            _mcq("Who should own threshold changes?", ["Defined process owner with evidence", "Anyone with dashboard access", "Nobody", "Only the model file"], 0, "Threshold changes affect operations."),
        ],
        "missions": [
            _mission("q1", "concept_check", "Explain threshold tuning and why a model score is not the same as a business decision.", ["score vs decision", "threshold", "cost-sensitive trade-off"]),
            _mission("q2", "tiny_hands_on", "A defect model at threshold 0.5 has precision 85% and recall 35%; at 0.3 precision is 60% and recall is 75%. Which threshold is safer if missed defects are costly?", ["compares precision/recall", "missed defect cost", "inspection workload"]),
            _mission("q3", "failure_diagnosis", "A high-precision model misses most defects after go-live. What threshold issue may be present?", ["threshold too strict", "low recall", "false-negative risk"]),
            _mission("q4", "architect_decision", "Design threshold governance for a defect alerting system.", ["cost matrix", "minimum recall", "alert volume", "owner", "monitoring"]),
            _mission("q5", "teachback", "Explain threshold tuning to a quality leader without using heavy math.", ["score-to-action", "missed defects vs extra checks", "policy decision"]),
        ],
    },
    "mlf_017": {
        "topic_id": "mlf_017",
        "title": "Class imbalance handling strategies",
        "module": "Advanced ML",
        "definition": "Class imbalance occurs when one class dominates the data, making a model look good while failing on the rare class that often matters most.",
        "plain_intuition": "If defects are rare, a lazy model can look accurate by mostly predicting 'no defect'. Imbalance is dangerous when the rare class is the business event.",
        "why_it_exists": "Many production problems are naturally imbalanced: defects, fraud, failures, churn, safety events. The minority class is often the event that drives value or risk.",
        "core_mechanism": "Accuracy is dominated by the majority class. Handling options include class-specific metrics, resampling, class weights, threshold tuning, better data collection, and segment evaluation.",
        "worked_example": "In 10,000 parts, only 100 are defective. Predicting all parts as good gives 99% accuracy and 0% defect recall. The model is operationally useless despite a strong headline metric.",
        "nuances": ["Imbalance is not automatically bad; it is bad when the minority class matters.", "Oversampling can overfit if careless.", "Class weights change training penalty; threshold tuning changes decision policy."],
        "when_matters": "It matters when rare positives drive cost, safety, quality, warranty, fraud, or service risk.",
        "when_less": "It matters less when the majority class is the only business concern, but that is rare in defect/failure systems.",
        "common_confusions": ["Thinking high accuracy proves safety.", "Treating resampling as always better.", "Ignoring minority-class precision/recall after deployment."],
        "architect_implications": ["Metric policy must prioritize the minority class when it carries business risk.", "Production monitoring must track class distribution and minority-class performance."],
        "system_design_controls": ["confusion matrix", "minority recall/precision/F1", "sampling strategy", "class weights", "threshold policy", "class distribution drift monitor"],
        "mission_answer_frame": ["State class distribution.", "Explain why accuracy misleads.", "Choose minority metrics.", "Propose handling strategy.", "Define production monitoring."],
        "do_not_waste_words": ["Do not only say data is imbalanced.", "Do not propose oversampling without risk.", "Do not ignore false negatives."],
        "mcqs": [
            _mcq("Which metric is dangerous alone on imbalanced defect data?", ["Accuracy", "Recall", "Precision", "Confusion matrix"], 0, "Accuracy can be dominated by majority class."),
            _mcq("Predicting no defects in a 98% good-parts dataset gives what issue?", ["High accuracy but zero defect recall", "Perfect recall", "No need for monitoring", "No false negatives"], 0, "All defects are missed."),
            _mcq("What does class weighting change?", ["Penalty by class during training", "Sensor units", "Dashboard theme", "Deployment server"], 0, "Weights make certain errors costlier."),
            _mcq("What should be monitored?", ["Class distribution and minority recall", "Only uptime", "Only training loss", "Only model name"], 0, "Distribution and minority performance matter."),
        ],
        "missions": [
            _mission("q1", "concept_check", "Explain class imbalance and why it matters in defect detection.", ["majority/minority class", "business risk", "accuracy limitation"]),
            _mission("q2", "tiny_hands_on", "A dataset has 9,800 good parts and 200 defective parts. A model predicts all parts as good. Calculate accuracy and defect recall.", ["accuracy calculation", "recall zero", "interpretation"]),
            _mission("q3", "failure_diagnosis", "A model has strong accuracy but warranty defects keep escaping. What likely went wrong?", ["minority-class failure", "metric mismatch", "false negatives"]),
            _mission("q4", "architect_decision", "Choose strategies for handling imbalanced defect data before deployment.", ["metrics", "sampling/class weights", "threshold", "monitoring"]),
            _mission("q5", "teachback", "Explain imbalance to a non-technical quality stakeholder.", ["rare event", "high accuracy trap", "missed defect consequence"]),
        ],
    },
    "mlf_018": {
        "topic_id": "mlf_018",
        "title": "Error analysis and model debugging",
        "module": "Advanced ML",
        "definition": "Error analysis is the disciplined study of where and why a model is wrong, usually by slicing errors across segments, labels, time, features, and business context.",
        "plain_intuition": "A bad score tells you the model is wrong. Error analysis tells you where it is wrong enough to fix something.",
        "why_it_exists": "Average metrics hide failure pockets. A model can be acceptable overall but unsafe for a plant, supplier, shift, product family, defect type, or new process condition.",
        "core_mechanism": "Compare errors by meaningful slices: confusion matrix cells, product line, station, supplier, time window, feature ranges, confidence bands, and label quality. Then map each pattern to a data, model, threshold, or process fix.",
        "worked_example": "Overall recall is 80%, but recall for night shift is 35%. That points to a segment issue: sensor noise, process difference, label delay, or missing feature specific to night operations.",
        "nuances": ["Error analysis is not just reading a metric table.", "Some errors are label problems, not model problems.", "A fix should target the error cluster, not blindly change the algorithm."],
        "when_matters": "It matters after baseline evaluation, before go-live, and whenever production performance drops.",
        "when_less": "It matters less only when the model is exploratory and no decision is attached, but serious ML work still needs it.",
        "common_confusions": ["Trying a new algorithm before understanding errors.", "Ignoring segment-level failures.", "Treating every false prediction as the same kind of problem."],
        "architect_implications": ["Architects need observability that stores predictions, features, labels, confidence, and segment metadata.", "Debugging loops must connect model failures to data owners and process owners."],
        "system_design_controls": ["confusion matrix slices", "segment dashboard", "error sample review", "label audit", "root-cause workflow", "fix backlog"],
        "mission_answer_frame": ["State the error pattern.", "Slice by relevant segment.", "Hypothesize cause.", "Identify evidence to inspect.", "Choose targeted fix."],
        "do_not_waste_words": ["Do not just say retrain.", "Do not treat average score as enough.", "Do not skip segment evidence."],
        "mcqs": [
            _mcq("Why slice errors by plant/shift/product?", ["To find hidden failure pockets", "To decorate reports", "To avoid labels", "To skip metrics"], 0, "Average metrics can hide segments."),
            _mcq("What is a bad first response to errors?", ["Try a more complex model without inspecting failures", "Review false negatives", "Check label quality", "Slice by segment"], 0, "Blind model changes waste time."),
            _mcq("Which evidence helps error analysis?", ["Prediction, actual label, features, segment, time", "Only model name", "Only CPU usage", "Only final accuracy"], 0, "You need context around errors."),
            _mcq("What can look like a model error but be a data problem?", ["Wrong or delayed labels", "A good confusion matrix", "Clear feature contract", "Defined threshold owner"], 0, "Label quality can drive apparent model errors."),
        ],
        "missions": [
            _mission("q1", "concept_check", "Explain error analysis and how it differs from simply reporting overall model accuracy.", ["where/why errors", "segment slicing", "average metric limitation"]),
            _mission("q2", "tiny_hands_on", "Overall recall is 80%, but recall on night shift is 35%. What would you inspect first?", ["segment failure", "night-shift data/process/sensor", "evidence"]),
            _mission("q3", "failure_diagnosis", "A model suddenly fails for one supplier but not others. Diagnose possible causes and evidence needed.", ["supplier segment", "data/process/label shift", "checks"]),
            _mission("q4", "architect_decision", "Design an error-analysis workflow for a manufacturing AI model.", ["logged predictions", "segment dashboard", "sample review", "owner workflow"]),
            _mission("q5", "teachback", "Explain why model debugging starts with error patterns, not immediately with a new algorithm.", ["simple explanation", "targeted fix", "business efficiency"]),
        ],
    },
    "mlf_019": {
        "topic_id": "mlf_019",
        "title": "Model interpretability and explainability limits",
        "module": "Advanced ML",
        "definition": "Interpretability helps explain model behavior, but explanations are evidence clues, not automatic proof of causality or business truth.",
        "plain_intuition": "An explanation tells you what the model leaned on. It does not prove why the world behaves that way.",
        "why_it_exists": "Stakeholders need to understand and challenge predictions, but explanation tools can be misused when people treat correlation as causation.",
        "core_mechanism": "Global explanations summarize broad model behavior. Local explanations explain one prediction. Feature importance can be unstable with correlated features and does not prove causal effect.",
        "worked_example": "A defect model says humidity is important. That may mean humidity correlates with a machine setting, shift, or season. Do not change the process until domain review or experiment confirms the mechanism.",
        "nuances": ["Global and local explanations answer different questions.", "Correlated features can split or distort importance.", "Explanation is useful for review, debugging, and governance, but not causal proof."],
        "when_matters": "It matters in regulated, high-stakes, operational, or stakeholder-facing ML where decisions must be justified.",
        "when_less": "It matters less for low-risk ranking experiments, but even then explanations help debugging and trust boundaries.",
        "common_confusions": ["Treating SHAP/feature importance as causality.", "Showing explanation charts without action policy.", "Ignoring instability caused by correlated features."],
        "architect_implications": ["Architects must define how explanations are used, reviewed, stored, and caveated.", "Explanations should feed investigation, not automatic process changes."],
        "system_design_controls": ["explanation audit trail", "global/local explanation separation", "domain review", "causality warning", "approval path for process action"],
        "mission_answer_frame": ["State what explanation shows.", "State what it cannot prove.", "Identify misinterpretation risk.", "Define validation path.", "Add governance controls."],
        "do_not_waste_words": ["Do not say explanations make AI transparent without limits.", "Do not claim feature importance proves cause.", "Do not skip review process."],
        "mcqs": [
            _mcq("What is a safe use of explanations?", ["Clues requiring validation", "Causal proof", "Replacement for testing", "Reason to skip domain review"], 0, "Explanations need validation."),
            _mcq("What is a local explanation?", ["Explanation for one prediction", "A retraining pipeline", "A global policy", "A database backup"], 0, "Local explanations explain individual outputs."),
            _mcq("What is the risk of correlated features?", ["Importance may be split or unstable", "The model cannot predict", "Labels disappear", "Recall becomes impossible"], 0, "Correlated features can distort explanations."),
            _mcq("What should an architect define for explanations?", ["Usage limits, audit trail, and review path", "Chart color only", "Nothing", "Only model name"], 0, "Explainability must be governed."),
        ],
        "missions": [
            _mission("q1", "concept_check", "Explain interpretability and why explanation is not the same as causality.", ["model behavior", "not causal proof", "stakeholder risk"]),
            _mission("q2", "tiny_hands_on", "A model explanation says humidity is the top feature for defects. What should you conclude and what should you not conclude?", ["clue not proof", "domain review", "validation"]),
            _mission("q3", "failure_diagnosis", "A team changes a process because a feature-importance chart looked convincing, but defects worsen. What went wrong?", ["causality trap", "missing validation", "governance failure"]),
            _mission("q4", "architect_decision", "Design an explainability governance process for a manufacturing AI system.", ["global/local", "audit trail", "domain review", "approval path"]),
            _mission("q5", "teachback", "Explain the value and limits of model explanations to a business stakeholder.", ["simple explanation", "limits", "safe use"]),
        ],
    },
    "mlf_020": {
        "topic_id": "mlf_020",
        "title": "ML monitoring: drift, performance, and retraining triggers",
        "module": "Advanced ML",
        "definition": "ML monitoring checks whether live inputs, predictions, model metrics, and business outcomes remain trustworthy after deployment.",
        "plain_intuition": "A model can be technically online and still be wrong. API uptime tells you the service is alive; ML monitoring tells you whether the predictions still deserve trust.",
        "why_it_exists": "Data, processes, sensors, customers, products, and labels change. Without monitoring, degradation becomes visible only after business damage accumulates.",
        "core_mechanism": "Input drift checks feature distributions. Prediction drift checks output patterns. Performance drift checks quality once labels arrive. Retraining triggers define when evidence is strong enough to review, retrain, validate, and redeploy.",
        "worked_example": "Humidity distribution shifts after a new drying process, and defect recall drops two weeks later. A good monitor flags feature drift early, tracks prediction shift, and later confirms performance drift when labels arrive.",
        "nuances": ["You can monitor inputs and predictions before labels arrive.", "Performance metrics need labels and may arrive late.", "A dashboard without owner response is not monitoring."],
        "when_matters": "It matters for every deployed ML system, especially where data and processes change over time.",
        "when_less": "It matters less only for offline analysis with no repeated production use.",
        "common_confusions": ["Monitoring only uptime/latency.", "Retraining on a schedule without evidence.", "Alerting without ownership or fallback."],
        "architect_implications": ["Monitoring design must separate technical service health from ML behavior health.", "Retraining must include validation and release governance, not just data refresh."],
        "system_design_controls": ["input drift monitor", "prediction distribution monitor", "label/performance monitor", "alert thresholds", "fallback rule", "retraining trigger", "model release validation"],
        "mission_answer_frame": ["Name monitored signals.", "Separate drift without labels from performance with labels.", "Define thresholds/time windows.", "Name owner and response.", "Define retraining and validation path."],
        "do_not_waste_words": ["Do not say monitor drift generically.", "Do not confuse API uptime with model quality.", "Do not say retrain without trigger and validation."],
        "mcqs": [
            _mcq("Which is not enough for ML monitoring?", ["API uptime only", "Input drift", "Recall over time", "Prediction distribution"], 0, "A healthy API can serve bad predictions."),
            _mcq("What is input drift?", ["Feature distribution changed after deployment", "The model file got larger", "The dashboard moved", "The label was renamed"], 0, "Input drift is feature distribution change."),
            _mcq("What can be monitored before labels arrive?", ["Inputs and predictions", "True recall only", "Final warranty cost only", "Manual inspection accuracy only"], 0, "Labels are not needed for input/prediction drift."),
            _mcq("What makes a retraining trigger useful?", ["Threshold, owner, validation, release process", "A vague feeling", "Monthly meeting only", "New algorithm name"], 0, "Retraining must be governed."),
        ],
        "missions": [
            _mission("q1", "concept_check", "Explain ML monitoring and how it differs from system uptime monitoring.", ["input/prediction/performance", "not just uptime", "trust after deployment"]),
            _mission("q2", "tiny_hands_on", "A feature distribution shifts this week, predictions shift next week, and labels arrive after 30 days. What can you monitor at each stage?", ["input drift", "prediction drift", "delayed performance labels"]),
            _mission("q3", "failure_diagnosis", "A model API is healthy, but defect recall has silently dropped. What monitoring failed?", ["performance drift", "model-quality monitoring", "owner response"]),
            _mission("q4", "architect_decision", "Design a monitoring and retraining trigger plan for a predictive quality model.", ["signals", "thresholds", "owner", "fallback", "validation before release"]),
            _mission("q5", "teachback", "Explain to a stakeholder why deployed ML needs monitoring beyond uptime dashboards.", ["simple explanation", "prediction trust", "business consequence"]),
        ],
    },
}


def has_blueprint(topic_id: str) -> bool:
    return str(topic_id or "") in ADVANCED_ML_BLUEPRINTS


def get_blueprint(topic_id: str) -> Optional[Dict[str, Any]]:
    bp = ADVANCED_ML_BLUEPRINTS.get(str(topic_id or ""))
    return deepcopy(bp) if bp else None


def get_required_blueprint(topic_id: str) -> Dict[str, Any]:
    bp = get_blueprint(topic_id)
    if not bp:
        raise KeyError(f"No expert tutor blueprint configured for topic_id={topic_id}")
    return bp


def blueprint_to_concept_note(topic_id: str) -> ConceptNote:
    bp = get_required_blueprint(topic_id)
    takeaways = [
        bp["definition"],
        bp["core_mechanism"],
        (bp.get("architect_implications") or [""])[0],
    ]
    return ConceptNote(
        topic_id=bp["topic_id"],
        title=bp["title"],
        simple_explanation=(
            f"{bp['plain_intuition']} {bp['definition']} "
            f"Mechanism: {bp['core_mechanism']}"
        ),
        wrong_mental_model=(bp.get("common_confusions") or ["Treating the concept as a generic production-risk slogan."])[0],
        correct_mental_model=(
            f"Use the topic-specific mechanism first, then translate it into controls: "
            f"{'; '.join(bp.get('system_design_controls', [])[:3])}."
        ),
        tiny_example=bp.get("worked_example", ""),
        why_it_matters=bp.get("why_it_exists", ""),
        edge_case=(bp.get("common_confusions") or [bp.get("worked_example", "")])[-1],
        three_takeaways=takeaways[:3],
    )


def blueprint_to_architect_note(topic_id: str) -> ArchitectNote:
    bp = get_required_blueprint(topic_id)
    return ArchitectNote(
        topic_id=bp["topic_id"],
        architect_summary=(
            f"Architect view: {bp.get('why_it_exists', '')} "
            f"The system design implication is to implement controls such as "
            f"{', '.join(bp.get('system_design_controls', [])[:4])}."
        ),
        design_implications=list(bp.get("architect_implications", []))[:2] or [
            "Define the system boundary and controls created by this concept.",
            "Ensure the implementation is measurable, monitorable, and owned.",
        ],
        common_mistakes=list(bp.get("common_confusions", []))[:2] or [
            "Using generic production-risk language instead of the topic mechanism.",
            "Skipping the operational control required by the concept.",
        ],
        production_risks=[
            bp.get("worked_example", "Weak implementation can create misleading model behavior."),
            f"Missing controls: {', '.join(bp.get('system_design_controls', [])[:3])}.",
        ],
        interview_framing=(
            f"I would explain {bp['title']} by first stating the mechanism, then giving a small example, "
            f"then naming the architecture controls: {', '.join(bp.get('system_design_controls', [])[:3])}."
        ),
        use_case_mapping=[
            UseCaseMapping(
                context="manufacturing_ai",
                relevance=f"In manufacturing AI, {bp['title']} affects whether predictions remain reliable for quality, defect, or process decisions.",
            )
        ],
    )


def blueprint_to_assessment(topic_id: str) -> Assessment:
    bp = get_required_blueprint(topic_id)
    return Assessment(
        topic_id=bp["topic_id"],
        questions=[AssessmentQuestion(**mission) for mission in bp.get("missions", [])],
    )


def blueprint_to_booster(topic_id: str) -> Optional[Dict[str, Any]]:
    bp = get_blueprint(topic_id)
    if not bp:
        return None
    return {
        "topic_id": bp["topic_id"],
        "title": bp["title"],
        "plain_language": bp.get("plain_intuition", ""),
        "worked_example": bp.get("worked_example", ""),
        "production_trap": (bp.get("common_confusions") or [""])[0],
        "mission_hint": "Use the mission answer frame. Do not repeat generic production-risk language.",
        "key_distinctions": [bp.get("definition", ""), bp.get("core_mechanism", ""), *bp.get("nuances", [])[:3]],
        "answer_frame": bp.get("mission_answer_frame", []),
        "mission_bridge": blueprint_mission_bridge(topic_id),
        "mission_focus": _flatten_expected_focus(bp.get("missions", [])),
        "mcqs": bp.get("mcqs", []),
        "blueprint": bp,
    }


def blueprint_mission_bridge(topic_id: str) -> List[Dict[str, str]]:
    bp = get_blueprint(topic_id)
    if not bp:
        return []
    labels = {
        "concept_check": "Explain the topic-specific mechanism precisely, not as a vague definition.",
        "tiny_hands_on": "Use the concrete numbers, categories, or scenario evidence from the question.",
        "failure_diagnosis": "Separate symptom, mechanism, evidence to inspect, and prevention.",
        "architect_decision": "Name controls, ownership, thresholds, persistence, monitoring, or fallback as relevant.",
        "teachback": "Explain simply with one concrete business consequence and one control.",
    }
    out: List[Dict[str, str]] = []
    for mission in bp.get("missions", []):
        expected = mission.get("expected_focus", [])
        out.append(
            {
                "mission_type": mission.get("type", "mission"),
                "question_id": mission.get("question_id", ""),
                "tested_skill": labels.get(mission.get("type", ""), "Apply the concept to the exact scenario."),
                "use_from_booster": "; ".join(expected[:4]) if expected else "Use the mechanism, example, risk, and control.",
            }
        )
    return out


def _flatten_expected_focus(missions: List[Dict[str, Any]]) -> List[str]:
    seen: List[str] = []
    for mission in missions:
        for item in mission.get("expected_focus", [])[:3]:
            if item not in seen:
                seen.append(item)
    return seen[:8]


def blueprint_context(topic_id: str) -> Dict[str, Any]:
    bp = get_blueprint(topic_id)
    if not bp:
        return {}
    return {
        "blueprint_version": "advanced_ml_expert_blueprint_v1",
        "topic_id": bp["topic_id"],
        "title": bp["title"],
        "definition": bp.get("definition", ""),
        "core_mechanism": bp.get("core_mechanism", ""),
        "nuances": bp.get("nuances", []),
        "common_confusions": bp.get("common_confusions", []),
        "system_design_controls": bp.get("system_design_controls", []),
        "mission_answer_frame": bp.get("mission_answer_frame", []),
        "do_not_waste_words": bp.get("do_not_waste_words", []),
        "missions": bp.get("missions", []),
    }
