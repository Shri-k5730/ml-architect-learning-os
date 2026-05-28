from __future__ import annotations

"""Topic-specific teaching and evidence designs.

Patch 040 makes the learning objective and the evidence required for each topic explicit.
The database may override these bundled defaults through mlos_topic_learning_designs.
Bundled content exists only so the app remains usable before/if a Supabase row is unavailable.
"""

from copy import deepcopy
from typing import Any, Dict, List, Optional

from src.schemas import ArchitectNote, Assessment, AssessmentQuestion, ConceptNote, UseCaseMapping

VERSION = "topic_specific_evidence_v1"


def task(question_id: str, qtype: str, label: str, question: str, purpose: str, shape: str, minimum: int, maximum: int, focus: List[str]) -> Dict[str, Any]:
    return {
        "question_id": question_id,
        "type": qtype,
        "label": label,
        "question": question,
        "purpose": purpose,
        "response_shape": shape,
        "target_min_words": minimum,
        "target_max_words": maximum,
        "expected_focus": focus,
    }


def mcq(question: str, options: List[str], answer_index: int, explanation: str) -> Dict[str, Any]:
    return {"question": question, "options": options, "answer_index": answer_index, "explanation": explanation}


def design(topic_id: str, title: str, objective: str, prerequisite: str, steps: List[Dict[str, str]], example: Dict[str, Any], misconception: str, architect_extension: str, drill: Dict[str, str], checks: List[Dict[str, Any]], tasks: List[Dict[str, Any]], gate: bool = False) -> Dict[str, Any]:
    return {
        "design_version": VERSION,
        "topic_id": topic_id,
        "title": title,
        "learning_objective": objective,
        "prerequisite_bridge": prerequisite,
        "concept_steps": steps,
        "worked_example": example,
        "misconception": misconception,
        "architect_extension": architect_extension,
        "diagnostic_drill": drill,
        "knowledge_checks": checks,
        "evidence_tasks": tasks,
        "is_gate": gate,
        "assessment_principle": "Score the reasoning demonstrated in the response, not the presence of preferred vocabulary. Do not demand evidence that was not taught or requested.",
    }


TOPIC_LEARNING_DESIGNS: Dict[str, Dict[str, Any]] = {}

TOPIC_LEARNING_DESIGNS["mlf_001"] = design(
    "mlf_001", "What machine learning is actually learning",
    "Explain that a model learns statistical patterns from examples, not human meaning, and identify why that boundary matters.",
    "Before models, recall the input-output idea: examples contain information used to predict an outcome.",
    [{"heading": "Pattern, not understanding", "body": "A model adjusts internal parameters so inputs map to known outcomes more accurately. It does not understand defect, fairness or safety the way a person does."}, {"heading": "Why it can fail", "body": "If future inputs differ from the patterns in training data, confident predictions can still be wrong."}],
    {"scenario": "A model learns that past warranty claims rose for one vehicle pattern.", "takeaway": "It learned an association useful for prediction, not a human explanation of why a vehicle fails."},
    "Saying the model 'understands' the problem because accuracy is high.",
    "An architect defines data boundaries, validation evidence and monitoring because model behaviour remains data-dependent.",
    {"question": "A model predicts failures accurately in historic data. Does that prove it understands failure causes?", "reveal": "No. It proves predictive pattern fit on evaluated data; cause and future reliability need separate evidence."},
    [mcq("What does an ML model primarily learn?", ["Statistical patterns from data", "Human meaning", "Business policy automatically", "Causality by default"], 0, "Models learn patterns used for prediction.")],
    [task("q1", "concept_check", "Core idea", "In plain language, what is an ML model learning?", "Show the distinction between pattern learning and human understanding.", "Definition plus one simple example.", 35, 80, ["patterns", "not human understanding"]), task("q2", "failure_diagnosis", "Boundary test", "A model is confident on a new factory but wrong often. What likely boundary was missed?", "Connect training patterns to unseen-data failure.", "Symptom, likely reason, next check.", 45, 95, ["distribution difference", "validation/check"]), task("q3", "architect_decision", "Architect action", "Name the minimum controls before relying on a learned pattern operationally.", "Translate the concept into safeguards.", "Evidence, monitoring and owner/action.", 60, 110, ["validation", "monitoring", "owner"]), task("q4", "teachback", "Explain simply", "Explain to a non-technical leader why prediction is not understanding.", "Test clear communication.", "One analogy and consequence.", 30, 65, ["simple explanation", "consequence"])],
)

TOPIC_LEARNING_DESIGNS["mlf_002"] = design(
    "mlf_002", "Features vs labels",
    "Distinguish information available for prediction from the outcome the model is trained to predict.",
    "Recall that a prediction problem needs inputs and a target outcome.",
    [{"heading": "Feature", "body": "A feature is information available when the prediction must be made, such as sensor readings or vehicle age."}, {"heading": "Label", "body": "A label is the outcome being learned, such as whether a defect actually occurred."}],
    {"scenario": "Predict scrap before final inspection.", "rows": [{"field": "temperature", "role": "feature"}, {"field": "pressure", "role": "feature"}, {"field": "final_scrap_flag", "role": "label"}], "takeaway": "A field created after inspection cannot be an input for an earlier prediction."},
    "Treating any available column as a valid feature, even when it is actually the future outcome.",
    "Architects create a feature contract that declares prediction time, availability and label generation.",
    {"question": "Can final_scrap_flag be a feature for a model predicting scrap before inspection?", "reveal": "No. It is the label and is unavailable at prediction time."},
    [mcq("Which is the label in defect prediction?", ["sensor pressure", "actual defect outcome", "machine ID", "shift"], 1, "The label is the outcome being predicted.")],
    [task("q1", "concept_check", "Distinguish", "Explain features and labels using a manufacturing example.", "Show role distinction.", "Two definitions and one example.", 35, 75, ["feature", "label"]), task("q2", "tiny_hands_on", "Classify fields", "For predicting scrap before inspection, classify temperature, final inspection result and supplier as valid feature or label/unavailable input.", "Apply time-of-prediction reasoning.", "Classify each field with one reason.", 40, 85, ["availability", "label"]), task("q3", "failure_diagnosis", "Leakage clue", "A model uses a repair-completed flag to predict future repairs. Diagnose the problem.", "Identify invalid feature use.", "Problem and prevention.", 40, 85, ["future information", "feature contract"]), task("q4", "architect_decision", "Contract", "What would a feature/label contract store?", "Define implementable governance.", "List essential fields and gate.", 55, 105, ["prediction time", "availability", "owner"])],
)

TOPIC_LEARNING_DESIGNS["mlf_003"] = design(
    "mlf_003", "Training data vs test data",
    "Explain why learning data and independent checking data must be separated.",
    "Recall that scoring the examples a model memorised is not proof of new-case performance.",
    [{"heading": "Train", "body": "Training data is where the model learns its parameters."}, {"heading": "Test", "body": "Test data is kept outside learning and used to estimate performance on unseen cases."}],
    {"scenario": "A tree scores 100% on rows it trained on but 72% on unseen rows.", "takeaway": "The test score is the honest signal of generalisation."},
    "Reporting training performance as though it were deployment evidence.",
    "The split strategy must reflect the deployment setting, including time and groups when needed.",
    {"question": "Why can a 100% training score be useless for approval?", "reveal": "Because the model may have memorised training examples and fail on unseen cases."},
    [mcq("What is test data for?", ["Learning parameters", "Independent evaluation", "Increasing features", "Fixing labels after deployment"], 1, "Test data gives independent evidence.")],
    [task("q1", "concept_check", "Separation", "Why must training and test data be separated?", "Explain independent evidence.", "Mechanism plus example.", 35, 75, ["learn", "unseen evaluation"]), task("q2", "tiny_hands_on", "Choose evidence", "A model gets 98% train accuracy and 71% test accuracy. Which score informs trust and what does the gap suggest?", "Interpret two scores.", "Compare and decide.", 35, 80, ["test", "overfitting"]), task("q3", "failure_diagnosis", "Invalid split", "Rows from the same asset appear in both train and test and performance collapses on new assets. What went wrong?", "Diagnose split leakage.", "Mechanism and corrected split.", 45, 90, ["group split", "leakage"]), task("q4", "architect_decision", "Split policy", "Define a validation/test policy for a deployment on future production batches.", "Make split align to use.", "Split rule, evidence and release decision.", 55, 110, ["time split", "locked test"])]
)

TOPIC_LEARNING_DESIGNS["mlf_004"] = design(
    "mlf_004", "What a baseline really is",
    "Use a simple reference model to prove whether complexity adds decision value.",
    "Recall that a score is meaningful only relative to a useful comparison.",
    [{"heading": "Reference point", "body": "A baseline is a simple, defensible benchmark such as majority class, last-known value or simple rule."}, {"heading": "Value test", "body": "A complex model is worthwhile only if it beats the baseline on the metric that matters."}],
    {"scenario": "A rare-defect model has 96% accuracy, while always predicting no defect has 97% accuracy.", "takeaway": "The model has not shown value on accuracy, and accuracy is likely the wrong metric."},
    "Calling any first trained model a baseline without choosing an appropriate comparison.",
    "A release decision compares candidates against a baseline on risk-aligned metrics and operational cost.",
    {"question": "If a complex model loses to a simple baseline, is complexity itself a benefit?", "reveal": "No. It needs measurable decision value and supportable trade-offs."},
    [mcq("Why use a baseline?", ["To avoid all advanced models", "To measure added value", "To guarantee deployment", "To remove labels"], 1, "A baseline tests whether complexity adds value.")],
    [task("q1", "concept_check", "Meaning", "What is a baseline and why is it necessary?", "Explain comparison value.", "Definition and example.", 30, 70, ["reference", "added value"]), task("q2", "tiny_hands_on", "Compare", "A rule baseline catches 70% of defects; a model catches 68% with the same alert volume. What is your decision?", "Use evidence, not novelty.", "Comparison and decision.", 35, 75, ["baseline comparison", "decision"]), task("q3", "failure_diagnosis", "Headline trap", "A team reports 98% accuracy but never compares against an always-good baseline in a rare-defect problem. What is missing?", "Diagnose misleading value claim.", "Failure and correct metric/control.", 45, 90, ["baseline", "rare class"]), task("q4", "architect_decision", "Approval rule", "Design a baseline acceptance rule for predictive quality.", "Define go/no-go evidence.", "Baseline, metric, threshold and owner.", 55, 105, ["metric", "owner", "release rule"])]
)

TOPIC_LEARNING_DESIGNS["mlf_005"] = design(
    "mlf_005", "Generalization",
    "Explain whether learned patterns continue to work on genuinely new data.",
    "Training performance measures fit; generalization is about new cases.",
    [{"heading": "New cases", "body": "Generalization means performance remains useful on unseen examples from the intended operating environment."}, {"heading": "Trust boundary", "body": "It is assessed with representative validation/test evidence, not by training score."}],
    {"scenario": "A model works on one plant's historic data but fails at a new plant.", "takeaway": "Its learned pattern did not generalize across plant conditions."},
    "Equating strong training or familiar-site performance with generalization.",
    "Architects identify deployment segments and demand evidence for each material boundary.",
    {"question": "A model passes on old batches but fails on new product variants. What failed?", "reveal": "Generalization across the variant shift was not established."},
    [mcq("Generalization concerns performance on...", ["training rows only", "unseen relevant cases", "labels only", "hyperparameters only"], 1, "Generalization is about unseen cases.")],
    [task("q1", "concept_check", "Explain", "Define generalization with a factory example.", "Capture new-case reliability.", "Definition and example.", 30, 70, ["unseen", "relevant environment"]), task("q2", "tiny_hands_on", "Interpret", "A model has F1 0.90 on Plant A and 0.54 on unseen Plant B. What do you conclude?", "Interpret segment generalization.", "Evidence and decision.", 35, 80, ["Plant B", "not generalized"]), task("q3", "failure_diagnosis", "Root cause", "What data or process differences would you inspect after a cross-plant failure?", "Move from symptom to evidence.", "Hypotheses and checks.", 45, 95, ["distribution", "process"]), task("q4", "architect_decision", "Gate", "How would you gate expansion to a new plant?", "Define proof before scale.", "Evidence, threshold and fallback.", 55, 110, ["site validation", "fallback"])]
)

TOPIC_LEARNING_DESIGNS["mlf_006"] = design(
    "mlf_006", "Overfitting vs underfitting",
    "Distinguish a model too simple to capture signal from one too tailored to training data.",
    "Recall train and validation scores as two distinct signals.",
    [{"heading": "Underfitting", "body": "Poor train and validation performance suggests the model cannot capture enough useful structure."}, {"heading": "Overfitting", "body": "Very strong training and weak validation performance suggests memorisation or excessive complexity."}],
    {"scenario": "Depth 2 tree: train 0.70, validation 0.68. Depth 40 tree: train 1.00, validation 0.72.", "takeaway": "One may be too simple; the other may be overfit. Compare intermediate candidates."},
    "Calling any low validation score overfitting without checking training behaviour.",
    "Model complexity and validation policy are controlled together, with segment checks before release.",
    {"question": "Train score is low and validation score is low. Is that automatically overfitting?", "reveal": "No. It is more consistent with underfitting or weak features."},
    [mcq("Train 1.00 and validation 0.60 suggests...", ["underfitting", "overfitting", "perfect generalisation", "no need to validate"], 1, "Large train-validation gap suggests overfitting.")],
    [task("q1", "concept_check", "Distinguish", "Explain underfitting versus overfitting using train and validation behaviour.", "Show the two failure modes.", "Comparison.", 35, 80, ["train", "validation"]), task("q2", "tiny_hands_on", "Interpret scores", "Interpret: Model A train=0.71/val=0.69; Model B train=0.99/val=0.72.", "Use evidence to diagnose.", "Diagnosis for each.", 40, 90, ["underfit", "overfit"]), task("q3", "failure_diagnosis", "Response", "A highly complex model collapses on new batches. What would you change or check first?", "Target the failure mechanism.", "Cause, evidence, corrective experiment.", 45, 95, ["complexity", "validation"]), task("q4", "architect_decision", "Selection", "Define a complexity selection rule for a quality model.", "Use constraints, not maximum train score.", "Metrics, validation and release rule.", 55, 110, ["stability", "validation"])]
)

TOPIC_LEARNING_DESIGNS["mlf_007"] = design(
    "mlf_007", "Data leakage",
    "Identify when training or evaluation uses information unavailable at prediction time.",
    "A valid model must use only information available when its decision is required.",
    [{"heading": "Leakage", "body": "Leakage occurs when the model learns from information that would not exist at prediction time or when validation data influences training."}, {"heading": "Why scores explode", "body": "Leaked information makes evaluation unrealistically easy."}],
    {"scenario": "Using final inspection outcome to predict a defect before inspection.", "takeaway": "The feature reveals the future and invalidates the score."},
    "Treating leakage as only accidental duplicate rows; time and pipeline fitting can leak too.",
    "Architects enforce point-in-time feature eligibility and train-only transformation fitting.",
    {"question": "A feature is excellent but created after the decision time. Can it be used?", "reveal": "No. Predictive usefulness does not override availability at decision time."},
    [mcq("Which is leakage?", ["Using prior sensor readings", "Using post-inspection status for pre-inspection prediction", "Monitoring recall", "Setting a threshold"], 1, "Future/post-outcome information leaks.")],
    [task("q1", "concept_check", "Define", "What is data leakage and why does it invalidate evaluation?", "State mechanism.", "Definition and example.", 35, 80, ["unavailable", "inflated score"]), task("q2", "tiny_hands_on", "Detect", "Which of these are valid before failure prediction: current sensor signal, repair closure code, prior service count? Explain.", "Apply point-in-time availability.", "Classify and justify.", 45, 95, ["prediction time", "availability"]), task("q3", "failure_diagnosis", "Pipeline leak", "A scaler was fitted on all data before train/test split. What went wrong?", "Catch non-feature leakage.", "Mechanism and fix.", 40, 85, ["fit train only", "leakage"]), task("q4", "architect_decision", "Prevention", "Define leakage prevention gates for an ML pipeline.", "Turn rules into architecture.", "Contracts, tests and approver.", 55, 110, ["feature eligibility", "pipeline validation"])]
)

TOPIC_LEARNING_DESIGNS["mlf_008"] = design(
    "mlf_008", "Bias vs variance",
    "Reason about systematic error versus sensitivity to training sample changes.",
    "Recall underfitting and overfitting as observable patterns.",
    [{"heading": "Bias", "body": "High bias means the model is systematically too simple or constrained to capture useful relationships."}, {"heading": "Variance", "body": "High variance means small training-data changes cause unstable model behaviour."}],
    {"scenario": "A shallow tree fails consistently; a very deep tree changes predictions wildly across samples.", "takeaway": "The first indicates bias, the second variance."},
    "Using bias to mean human prejudice in this technical lesson, or ignoring stability evidence.",
    "Architecture balances performance, stability, monitoring cost and retraining behaviour.",
    {"question": "A model varies sharply across resampled training sets. What is the issue?", "reveal": "High variance; you need stability evidence or simpler/regularized modelling."},
    [mcq("Which indicates high variance?", ["Stable poor performance", "Predictions change greatly with training sample", "No labels", "High recall only"], 1, "Variance is sensitivity to data samples.")],
    [task("q1", "concept_check", "Distinguish", "Explain bias and variance using model behaviour, not ordinary-language meaning.", "Demonstrate technical meaning.", "Contrast plus example.", 40, 85, ["systematic", "sensitivity"]), task("q2", "tiny_hands_on", "Diagnose", "A model gets similar low scores across folds; another gets scores from 0.55 to 0.92. Diagnose each.", "Interpret fold stability.", "Two diagnoses.", 40, 90, ["bias", "variance"]), task("q3", "failure_diagnosis", "Impact", "Why might a high-variance defect model be risky in operations?", "Connect instability to decision risk.", "Risk and evidence.", 40, 90, ["unstable", "segment/fold"]), task("q4", "architect_decision", "Control", "How would you choose between more complex and more stable candidates?", "Balance model choice.", "Evidence and policy.", 55, 110, ["stability", "trade-off"])]
)

TOPIC_LEARNING_DESIGNS["mlf_009"] = design(
    "mlf_009", "Why accuracy can lie",
    "Explain why aggregate correctness can conceal failure on the business-critical minority class.",
    "Recall labels and class counts: not all outcomes are equally frequent or costly.",
    [{"heading": "Accuracy", "body": "Accuracy counts all correct predictions equally."}, {"heading": "Rare critical failures", "body": "If defects are rare, predicting 'good' most of the time can look accurate while missing defects."}],
    {"scenario": "990 good parts and 10 defective parts. A model predicts every part is good.", "rows": [{"metric": "accuracy", "value": "99%"}, {"metric": "defects caught", "value": "0 of 10"}], "takeaway": "High accuracy can be useless for defect protection."},
    "Approving an imbalanced classifier from accuracy alone.",
    "Metric policy follows business cost: recall, precision, workload and severity must be visible.",
    {"question": "Is 99% accuracy sufficient when all ten defects were missed?", "reveal": "No. The metric hides the failure that matters."},
    [mcq("A rare-defect model predicts no defects and gets 99% accuracy. What is missing?", ["Critical-class performance", "More decimals", "A larger title", "Only training time"], 0, "Inspect defect recall/precision.")],
    [task("q1", "concept_check", "Explain", "Why can accuracy be misleading in rare-defect prediction?", "Show imbalance mechanism.", "Scenario and implication.", 35, 75, ["rare class", "missed defects"]), task("q2", "tiny_hands_on", "Interpret counts", "Out of 1000 parts, 10 are defective and a model flags none. Calculate accuracy and state the operational conclusion.", "Use simple arithmetic safely.", "Calculation and decision.", 35, 80, ["99%", "unsafe"]), task("q3", "failure_diagnosis", "Bad decision", "A team deploys based on accuracy and warranty claims rise. What did evaluation miss?", "Tie metric to consequence.", "Failure and better evidence.", 40, 90, ["recall", "business cost"]), task("q4", "architect_decision", "Metric gate", "Define approval metrics for rare but costly defects.", "Make a metric policy.", "Metrics, threshold/workload and owner.", 55, 110, ["recall", "precision", "threshold"])]
)

TOPIC_LEARNING_DESIGNS["mlf_010"] = design(
    "mlf_010", "Precision vs recall",
    "Calculate and interpret false-alarm versus missed-defect trade-offs.",
    "Recall confusion-matrix terms: true positive, false positive and false negative.",
    [{"heading": "Precision", "body": "Of what the model flagged, how much was truly positive? Low precision creates unnecessary action."}, {"heading": "Recall", "body": "Of actual positives, how much did the model catch? Low recall means missed critical cases."}],
    {"scenario": "TP=40, FP=10, FN=20.", "rows": [{"metric": "precision", "value": "40/(40+10)=0.80"}, {"metric": "recall", "value": "40/(40+20)=0.67"}], "takeaway": "The business decides whether misses or extra inspections matter more."},
    "Saying precision measures misses or recall measures false-alarm workload.",
    "Threshold policy must explicitly trade missed risk against intervention capacity.",
    {"question": "Which metric exposes missed defects?", "reveal": "Recall, because false negatives are actual defects not caught."},
    [mcq("Low recall primarily means...", ["many false alarms", "many actual positives missed", "no labels", "perfect calibration"], 1, "Recall is reduced by false negatives.")],
    [task("q1", "concept_check", "Distinguish", "Explain precision and recall in a quality-inspection setting.", "Show operational meaning.", "Two definitions and consequences.", 40, 85, ["false positive", "false negative"]), task("q2", "tiny_hands_on", "Calculate", "For TP=40, FP=10, FN=20, calculate precision and recall and interpret them.", "Use formulas and meaning.", "Calculation and interpretation.", 40, 90, ["0.80", "0.67"]), task("q3", "failure_diagnosis", "Trade-off", "A threshold change reduces inspection workload but warranty escapes rise. What changed?", "Diagnose threshold-metric trade-off.", "Mechanism and response.", 45, 95, ["recall", "threshold"]), task("q4", "architect_decision", "Policy", "Set a threshold-selection policy where missed safety defects are costly.", "Translate metrics into action.", "Priority, constraint and monitoring.", 55, 110, ["recall floor", "workload"])]
)

# Advanced and completion topics. These deliberately use different evidence shapes.
TOPIC_LEARNING_DESIGNS["mlf_011"] = design(
    "mlf_011", "Model selection and validation strategy",
    "Select a model from evidence that reflects deployment constraints rather than a single headline score.",
    "Recall that validation estimates new-case performance and metrics reflect business risk.",
    [{"heading": "Selection is a decision", "body": "Choosing a model means comparing performance, stability and operational constraints."}, {"heading": "Validation must mirror use", "body": "A candidate winning average score may still fail on a critical plant or time period."}],
    {"scenario": "Model A: recall 0.90 overall but 0.42 at Plant B. Model B: recall 0.86 overall and 0.82 at Plant B.", "takeaway": "If Plant B matters, Model B is often safer despite lower headline recall."},
    "Selecting the maximum overall metric without checking critical segments or operating constraints.",
    "An architect defines selection criteria, evidence slices, latency/explainability constraints and approval rule before model comparison.",
    {"question": "Which candidate is safer when Plant B is a critical rollout site?", "reveal": "Model B, unless other evidence changes the decision, because its relevant-segment behaviour is stable."},
    [mcq("What is weak selection evidence?", ["Critical segment results", "Highest training score only", "Latency constraint", "Locked test result"], 1, "Training score is not approval evidence.")],
    [task("q1", "concept_check", "Decision concept", "What makes model selection different from simply picking the highest score?", "Explain selection criteria.", "Mechanism and example.", 40, 85, ["criteria", "deployment"]), task("q2", "tiny_hands_on", "Select candidate", "Using the Plant A/B scenario in the lesson, select a model and justify the decision.", "Interpret a comparative result.", "Choice, evidence and trade-off.", 45, 90, ["segment", "decision"]), task("q3", "failure_diagnosis", "Missed evidence", "A selected model fails on one product family after launch. What evidence was probably omitted?", "Diagnose validation design.", "Omitted check and prevention.", 45, 95, ["segment validation", "selection"]), task("q4", "architect_decision", "Selection gate", "Define model-selection evidence and approvers for production release.", "Create a release rule.", "Criteria, owner, approval/action.", 60, 115, ["scorecard", "owner"])]
)

TOPIC_LEARNING_DESIGNS["mlf_012"] = design(
    "mlf_012", "Feature engineering and feature contracts",
    "Design derived inputs that are reproducible, available at prediction time and stable in serving.",
    "Recall features versus labels and leakage at the decision-time boundary.",
    [{"heading": "Feature engineering", "body": "Derived variables can make patterns learnable, such as rolling temperature deviation."}, {"heading": "Feature contract", "body": "Every feature needs definition, source, availability time, transformation and owner."}],
    {"scenario": "A 24-hour failure-count feature is useful only if the same completed-event window is available online.", "takeaway": "A brilliant offline feature is useless or leaky if serving cannot reproduce it."},
    "Treating feature creativity as success without production parity and point-in-time availability.",
    "Architects govern feature definitions, lineage, point-in-time correctness and training-serving parity.",
    {"question": "Can a rolling defect count include defects recorded after prediction time?", "reveal": "No. That would leak future information."},
    [mcq("A feature contract should define...", ["Only a display name", "Source, transformation and availability time", "Only model type", "Only accuracy"], 1, "Feature contracts make serving trustworthy.")],
    [task("q1", "concept_check", "Concept", "Why is a feature contract necessary after feature engineering?", "Connect derivation to trust.", "Definition and failure avoided.", 40, 85, ["definition", "availability"]), task("q2", "tiny_hands_on", "Contract a feature", "Define a safe rolling-temperature-deviation feature for predicting defects at time T.", "Apply point-in-time logic.", "Formula/window, availability and owner.", 50, 105, ["time T", "window"]), task("q3", "failure_diagnosis", "Parity break", "A feature works offline but is missing or differently calculated online. Diagnose the failure.", "Identify training-serving mismatch.", "Symptom, mechanism, control.", 45, 95, ["parity", "contract"]), task("q4", "architect_decision", "Feature governance", "Design feature approval checks before model release.", "Create implementable governance.", "Checks, lineage and owner.", 60, 115, ["lineage", "owner"])]
)

TOPIC_LEARNING_DESIGNS["mlf_013"] = design(
    "mlf_013", "Encoding categorical variables safely",
    "Transform categorical inputs without inventing false order or crashing on unseen production categories.",
    "Recall that models need numeric representations but category meaning must be preserved.",
    [{"heading": "Encoding choice", "body": "One-hot encoding keeps nominal categories separate; ordinal encoding should be used only where ordering is meaningful."}, {"heading": "Unknown categories", "body": "Production may contain categories absent from training, so the pipeline needs explicit unknown handling."}],
    {"scenario": "Training colors are Red, Green and Blue; production receives Yellow.", "takeaway": "An encoder must handle Yellow safely rather than error or mislabel it as ordered."},
    "Assigning arbitrary ordinal numbers to unordered categories or ignoring unknowns.",
    "Encoding and unknown-category policy belong inside a versioned serving pipeline with monitoring.",
    {"question": "Should Red=1, Green=2, Blue=3 imply Green is between Red and Blue?", "reveal": "No, not for a nominal color category."},
    [mcq("Why configure unknown-category handling?", ["To survive new categories safely", "To guarantee causality", "To remove validation", "To hide labels"], 0, "Production can introduce unseen values.")],
    [task("q1", "concept_check", "Concept", "Why do categorical variables require careful encoding?", "Explain representation risk.", "Definition and one trap.", 35, 80, ["numeric representation", "false order"]), task("q2", "tiny_hands_on", "Unknown value", "Training contains Red/Green/Blue and production receives Yellow. What should the pipeline do?", "Handle unseen category.", "Safe behaviour and consequence.", 40, 85, ["unknown", "pipeline"]), task("q3", "failure_diagnosis", "Production crash", "A recommendation model fails when a new supplier category arrives. What was missing?", "Diagnose pipeline design.", "Cause, evidence and fix.", 45, 95, ["unseen category", "monitor"]), task("q4", "architect_decision", "Design", "Define categorical feature handling for a manufacturing model with evolving suppliers.", "Design durable pipeline.", "Method, unknown policy and monitoring.", 55, 110, ["encoding", "unknown handling"])]
)

TOPIC_LEARNING_DESIGNS["mlf_014"] = design(
    "mlf_014", "Scaling, normalization, and pipeline leakage",
    "Distinguish scaling methods and prevent leakage by fitting transformations only on training data.",
    "Recall that preprocessing can learn statistics from data just as a model does.",
    [{"heading": "Scaling", "body": "Min-max scaling maps a range; standardization uses training mean and standard deviation."}, {"heading": "Leakage boundary", "body": "The scaler learns statistics during fit, so only training data may fit it; validation and production are transformed using those values."}],
    {"scenario": "Train values define mean=10 and std=2; validation value 14 is transformed with those training statistics to z=2.", "takeaway": "Validation must not alter the scaler."},
    "Fitting the scaler on the full dataset before splitting or confusing min-max with z-score standardization.",
    "Use pipeline objects, train-only fitting tests and versioned transformations in serving.",
    {"question": "Why is fitting a scaler on all rows a leakage issue?", "reveal": "Validation/test information influences the transformation used during training."},
    [mcq("For z-score standardization, the transformation is...", ["(x-mean)/std", "x/max", "x-label", "mean/x"], 0, "Standardization uses training mean and standard deviation.")],
    [task("q1", "concept_check", "Distinguish", "Explain min-max scaling, standardization and the fitting boundary.", "Test technical precision.", "Short comparison.", 45, 95, ["formula meaning", "train-only fit"]), task("q2", "tiny_hands_on", "Compute", "With training mean=10 and std=2, standardize validation value 14 and state why you use training statistics.", "Compute and interpret.", "Calculation and leakage note.", 35, 75, ["z=2", "training statistics"]), task("q3", "failure_diagnosis", "Leak", "A scaler is fit before splitting data. Diagnose the apparent validation improvement.", "Recognise transformation leakage.", "Mechanism and fix.", 40, 90, ["leakage", "pipeline"]), task("q4", "architect_decision", "Pipeline", "Specify preprocessing controls for deployment.", "Translate to system controls.", "Fit/transform rule, versioning and monitor.", 55, 110, ["pipeline", "serving parity"])]
)

TOPIC_LEARNING_DESIGNS["mlf_015"] = design(
    "mlf_015", "Regularization: controlling model complexity",
    "Explain how penalties discourage over-complex learned weights and how strength is tuned.",
    "Recall overfitting: training fit can improve while validation behaviour weakens.",
    [{"heading": "Penalty", "body": "Regularization adds a cost for overly large learned weights, discouraging brittle complexity."}, {"heading": "Strength", "body": "The regularization strength is a hyperparameter: too weak may overfit; too strong may underfit."}],
    {"scenario": "A model fits training noise through large coefficients; increasing penalty improves validation stability but excessive penalty loses useful signal.", "takeaway": "Regularization is a trade-off, not an automatic improvement."},
    "Saying regularization reduces hyperparameters rather than penalising learned model parameters.",
    "The strength is selected using validation evidence and stability, then locked for final evaluation.",
    {"question": "What does regularization penalise: features, labels or learned weights?", "reveal": "Learned parameters/weights; the penalty strength is a chosen hyperparameter."},
    [mcq("Too-strong regularization can cause...", ["underfitting", "label creation", "future leakage automatically", "perfect recall"], 0, "Over-penalising removes useful flexibility.")],
    [task("q1", "concept_check", "Mechanism", "What does regularization do and what is tuned?", "Require precise terms.", "Penalty and strength distinction.", 35, 80, ["weights", "hyperparameter"]), task("q2", "tiny_hands_on", "Interpret", "A model improves training score but worsens validation score; adding moderate regularization improves validation. Explain why.", "Connect penalty to overfit evidence.", "Observation and mechanism.", 40, 90, ["overfitting", "validation"]), task("q3", "failure_diagnosis", "Too much", "A heavily regularized model misses clear defect patterns. Diagnose it.", "Detect underfit trade-off.", "Mechanism and tuning step.", 40, 85, ["underfitting", "strength"]), task("q4", "architect_decision", "Selection", "How should regularization strength be approved for production?", "Use controlled evidence.", "Validation, stability and final evidence.", 55, 110, ["tuning", "locked test"])]
)

TOPIC_LEARNING_DESIGNS["mlf_016"] = design(
    "mlf_016", "Threshold tuning and cost-sensitive decisions",
    "Separate model risk scores from action thresholds and choose thresholds using business cost and capacity.",
    "Recall precision and recall trade-offs and that a probability/score is not itself an action.",
    [{"heading": "Score versus decision", "body": "The model produces a risk score; the threshold determines when to alert or intervene."}, {"heading": "Trade-off", "body": "Lower thresholds usually catch more positives but create more interventions; higher thresholds usually miss more positives."}],
    {"scenario": "At threshold 0.7, recall=0.55 and alerts=40; at threshold 0.4, recall=0.84 and alerts=125.", "takeaway": "The decision depends on missed-defect cost and inspection capacity."},
    "Treating 0.5 as a universal correct threshold or saying threshold change retrains the model.",
    "Threshold policy records cost assumptions, capacity constraints, approval and monitoring triggers.",
    {"question": "If missed defects are costly, which threshold evidence becomes critical?", "reveal": "Recall and the operational cost of additional alerts."},
    [mcq("Changing a decision threshold directly changes...", ["operating trade-off", "training labels", "model architecture automatically", "causality"], 0, "Thresholds change actions from scores.")],
    [task("q1", "concept_check", "Mechanism", "Explain model score versus decision threshold.", "Separate prediction from policy.", "Definition and consequence.", 35, 80, ["score", "action"]), task("q2", "tiny_hands_on", "Choose", "Using the two threshold results in the lesson, recommend a threshold when missing defects is expensive but inspection capacity is 140 alerts.", "Make evidence-based choice.", "Choice and trade-off.", 45, 95, ["recall", "capacity"]), task("q3", "failure_diagnosis", "Wrong operating point", "Warranty failures rise after the team raises the alert threshold to reduce workload. Diagnose.", "Connect action policy to outcomes.", "Mechanism and response.", 45, 95, ["false negatives", "threshold"]), task("q4", "architect_decision", "Policy", "Define threshold governance for defect-risk scores.", "Create an operating policy.", "Cost, capacity, approval and monitoring.", 60, 120, ["cost", "owner"])]
)

TOPIC_LEARNING_DESIGNS["mlf_017"] = design(
    "mlf_017", "Class imbalance handling strategies",
    "Choose metric, sampling or weighting approaches without distorting evaluation of rare critical cases.",
    "Recall that accuracy can hide rare-class failure and precision/recall reveal consequences.",
    [{"heading": "Imbalance", "body": "One class appears far less often, such as rare defects among mostly good parts."}, {"heading": "Handling", "body": "Class weights or training resampling can help learning; the final evaluation must still reflect real-world prevalence and costs."}],
    {"scenario": "Defects are 1% of parts. Oversampling defects improves learning, but evaluation on an artificially balanced test set exaggerates operating performance.", "takeaway": "Change training carefully; preserve honest evaluation."},
    "Balancing the test set and reporting it as production performance.",
    "Architects define rare-class metric policy, sampling provenance and deployment workload checks.",
    {"question": "Can you oversample training and still evaluate on natural prevalence?", "reveal": "Yes. Training intervention must not distort final evidence."},
    [mcq("Why keep final evaluation close to real prevalence?", ["To estimate operational behaviour honestly", "To hide defects", "To guarantee accuracy", "To eliminate thresholds"], 0, "Deployment sees real prevalence.")],
    [task("q1", "concept_check", "Concept", "What problem does class imbalance create in rare-defect ML?", "Explain failure mechanism.", "Mechanism and metric impact.", 35, 80, ["rare class", "missed detection"]), task("q2", "tiny_hands_on", "Choose approach", "Defects are 1%. You may use class weights in training. What must remain true in final evaluation?", "Separate training tactic from evidence.", "Tactic and evaluation rule.", 40, 90, ["natural prevalence", "metrics"]), task("q3", "failure_diagnosis", "False confidence", "A model was tested only on a 50/50 resampled test set and alert volumes explode in production. Diagnose.", "Recognise distorted evidence.", "Failure and fix.", 45, 100, ["prevalence", "workload"]), task("q4", "architect_decision", "Governance", "Define an imbalance-handling release checklist.", "Set safe evidence.", "Training method, evaluation and monitoring.", 60, 115, ["sampling", "recall", "volume"])]
)

TOPIC_LEARNING_DESIGNS["mlf_018"] = design(
    "mlf_018", "Error analysis and model debugging",
    "Investigate where and why prediction errors occur rather than relying on aggregate performance.",
    "Recall confusion-matrix errors and critical segments such as shift, plant or supplier.",
    [{"heading": "Headline versus pattern", "body": "An overall score says how much error exists; error analysis locates failure pockets and possible mechanisms."}, {"heading": "Evidence", "body": "Slice false positives and false negatives by meaningful segments, time, features and data quality."}],
    {"scenario": "Overall recall is 80%, but night-shift recall is 35%.", "takeaway": "The model has a critical segment failure that must be investigated before broad trust."},
    "Retraining or changing algorithms before locating the error mechanism.",
    "Store prediction context, slice metrics, assign investigation owners and convert confirmed findings into fixes.",
    {"question": "Does overall recall of 80% clear the night-shift failure?", "reveal": "No. The 35% segment recall exposes a critical blind spot."},
    [mcq("What is the first value of error analysis?", ["Find failure patterns", "Hide bad slices", "Remove validation", "Guarantee cause"], 0, "It localises errors for diagnosis.")],
    [task("q1", "concept_check", "Purpose", "What is error analysis and why is an overall score insufficient?", "Define pattern investigation.", "Mechanism and example.", 40, 85, ["segments", "overall metric"]), task("q2", "tiny_hands_on", "Investigate", "Overall recall is 80%, night-shift recall is 35%. What would you inspect first?", "Use scenario evidence.", "Failure pocket, checks and action.", 45, 95, ["night shift", "false negatives"]), task("q3", "failure_diagnosis", "Supplier failure", "The model suddenly fails for one supplier only. Structure the diagnosis.", "Separate symptom and cause.", "Hypotheses, evidence, correction.", 50, 105, ["supplier", "evidence"]), task("q4", "architect_decision", "Workflow", "Design a recurring error-analysis workflow for manufacturing AI.", "Operationalise debugging.", "Logging, slices, owner and response.", 65, 125, ["logged predictions", "owner"])]
)

TOPIC_LEARNING_DESIGNS["mlf_019"] = design(
    "mlf_019", "Model interpretability and explainability limits",
    "Use model explanations as evidence about model reliance without treating them as proof of real-world cause or safe action.",
    "Recall correlation versus causation and the need for validation before business action.",
    [{"heading": "What an explanation says", "body": "An explanation describes which inputs influenced the model globally or for one prediction."}, {"heading": "What it cannot say", "body": "It does not prove the input caused the outcome, that the model is correct, or that changing a process will improve results."}],
    {"scenario": "A defect model highlights humidity as influential.", "takeaway": "Investigate humidity and correlated factors; do not change humidity policy from the chart alone."},
    "Inferring that an important feature must be retained or acted upon without checking availability, leakage, proxy risk and stability.",
    "Governance stores explanation context and requires evidence and approval before process change.",
    {"question": "Humidity is important to the model. Does it cause defects?", "reveal": "Not proven. It is a clue requiring validation against process evidence and correlated variables."},
    [mcq("SHAP importance establishes...", ["Model reliance", "Causality automatically", "Process-change approval", "No monitoring need"], 0, "It describes model attribution, not cause.")],
    [task("q1", "concept_check", "Distinguish", "Explain interpretability and why it is not causality.", "Define the boundary.", "Definition and one example.", 40, 85, ["model behaviour", "not causal proof"]), task("q2", "tiny_hands_on", "Safe conclusion", "A model explanation says humidity is influential. What is valid to conclude, invalid to conclude, and what should be checked next?", "Prevent unsafe action.", "Valid, invalid, evidence/action.", 45, 95, ["clue", "validation"]), task("q3", "failure_diagnosis", "Causality trap", "A process is changed from a feature chart and defects worsen. What failed?", "Diagnose governance failure.", "Failure, evidence, prevention.", 50, 100, ["causality", "approval"]), task("q4", "architect_decision", "Governance", "Design an explainability decision workflow for manufacturing AI.", "Require action control.", "Trigger, logged evidence, owners, approval, monitoring.", 65, 125, ["audit trail", "owner"])]
)

TOPIC_LEARNING_DESIGNS["mlf_020"] = design(
    "mlf_020", "ML monitoring: drift, performance, and retraining triggers",
    "Separate input drift signals from confirmed performance loss and define action triggers.",
    "Recall model generalisation and that production labels may arrive later than predictions.",
    [{"heading": "Two signals", "body": "Input drift detects data change; performance monitoring confirms whether prediction quality changed once labels arrive."}, {"heading": "Action", "body": "A drift alert starts investigation. Retraining or fallback requires evidence, policy and ownership."}],
    {"scenario": "Sensor mean shifts beyond tolerance today; defect labels are available next week.", "takeaway": "Investigate immediately, but do not claim recall loss until outcome evidence arrives."},
    "Treating drift as proof of performance degradation or automatic retraining permission.",
    "Define drift monitors, performance metrics, escalation owner, fallback and retraining approval rule.",
    {"question": "Does a feature mean shift prove model recall has dropped?", "reveal": "No. It is an early warning until linked to performance evidence."},
    [mcq("A drift alert is primarily...", ["An investigation trigger", "Proof of failure", "Automatic retrain order", "A causal finding"], 0, "Drift is a signal, not final proof.")],
    [task("q1", "concept_check", "Separate signals", "Explain drift monitoring versus performance monitoring.", "Show evidence difference.", "Comparison and why it matters.", 40, 85, ["input drift", "performance"]), task("q2", "tiny_hands_on", "Interpret alert", "A feature mean shifts beyond tolerance but labels are delayed. What action is justified now?", "Use alert safely.", "Signal, investigation, no premature conclusion.", 45, 90, ["investigate", "not proof"]), task("q3", "failure_diagnosis", "Silent failure", "Drift alerts occurred but no owner reviewed them before recall fell. Diagnose the system failure.", "Identify operational gap.", "Signal, missing response, fix.", 45, 95, ["owner", "trigger"]), task("q4", "architect_decision", "Monitoring policy", "Define monitoring and retraining triggers for a quality model.", "Build response governance.", "Signal, threshold, owner, fallback/retrain.", 60, 120, ["trigger", "owner", "retrain"])]
)

TOPIC_LEARNING_DESIGNS["mlf_021"] = design(
    "mlf_021", "Validation under time, group, and leakage constraints",
    "Choose splits that test the kind of unseen data the model will face: future periods or unseen groups.",
    "Recall training/test separation and leakage.",
    [{"heading": "Why random can lie", "body": "Random rows may place familiar assets, suppliers or future-adjacent patterns in both training and validation."}, {"heading": "Match deployment", "body": "Time holdout tests future periods; group holdout tests unseen production lines, suppliers or assets."}],
    {"scenario": "Hold out every row from Line_B for validation.", "rows": [{"row": 0, "group": "Line_A", "split": "train"}, {"row": 1, "group": "Line_B", "split": "validation"}, {"row": 2, "group": "Line_A", "split": "train"}], "takeaway": "The model is tested on a group it never trained on."},
    "Calling a random split honest when deployment is on future time or unseen groups.",
    "Validation strategy is an architecture decision aligned to rollout risk and feature availability.",
    {"question": "Random rows or hold out all of Line_B for a new-line rollout?", "reveal": "Hold out Line_B, because the deployment question is generalisation to an unseen line."},
    [mcq("To test a future rollout, prefer...", ["future time holdout", "mix all future rows into train", "training score", "no validation"], 0, "The split should mirror future deployment.")],
    [task("q1", "concept_check", "Choose split", "When should you use time holdout versus group holdout?", "Match split to deployment.", "Contrast and examples.", 45, 95, ["time", "group"]), task("q2", "tiny_hands_on", "Build indices", "For groups ['Line_A','Line_B','Line_A','Line_C','Line_B'], identify train and validation indices if Line_B is held out.", "Apply group split.", "Indices plus meaning.", 30, 70, ["train [0,2,3]", "validation [1,4]"]), task("q3", "failure_diagnosis", "Leakage", "A random split looks strong but performance collapses on an unseen supplier. What was the evaluation mistake?", "Diagnose mismatch.", "Mechanism and correction.", 45, 95, ["group holdout", "inflated"]), task("q4", "architect_decision", "Strategy", "Define validation strategy for future batches across multiple production lines.", "Design honest evidence.", "Split hierarchy, leakage check and gate.", 60, 120, ["time", "group", "gate"])]
)

TOPIC_LEARNING_DESIGNS["mlf_022"] = design(
    "mlf_022", "Hyperparameter tuning without fooling yourself",
    "Explain what hyperparameters are, compare candidate configurations fairly, and prevent the search from contaminating final evidence.",
    "Before tuning, recall: model parameters are learned from training data; validation data helps select design choices; the final test set is independent approval evidence.",
    [{"heading": "1. What is a hyperparameter?", "body": "A hyperparameter is a setting chosen before or around training that changes how the model learns. A decision tree's max_depth, a forest's n_estimators and a model's regularization strength are hyperparameters. Learned tree splits or coefficients are parameters."}, {"heading": "2. Why tune it?", "body": "Different settings can underfit, generalise well or overfit. Tuning compares a planned set of settings using development validation evidence."}, {"heading": "3. How can tuning fool us?", "body": "When many configurations are tested on the same validation evidence, the winner may partly reflect luck specific to that validation sample. The final test must remain outside the search."}],
    {"scenario": "Decision tree candidates for a defect model", "rows": [{"max_depth": 2, "train_f1": "0.71", "validation_f1": "0.69", "reading": "likely too simple"}, {"max_depth": 8, "train_f1": "0.90", "validation_f1": "0.84", "reading": "promising candidate"}, {"max_depth": 30, "train_f1": "1.00", "validation_f1": "0.72", "reading": "likely overfit"}], "takeaway": "Depth 8 looks better on development evidence. It is selected for one final locked-test check, not declared deployed from validation alone."},
    "A hyperparameter is not an input feature such as humidity or temperature, and the best observed validation score is not automatically final proof.",
    "For production, define the search space and budget before tuning, record every trial, approve a selected candidate only on locked final evidence and include latency/workload constraints where relevant.",
    {"question": "Candidate B has the best validation F1. Is it already approved for deployment?", "reveal": "No. It is the development winner; approve only after one independent locked-test evaluation and constraint check."},
    [mcq("Which is a hyperparameter of a decision tree?", ["humidity measurement", "max_depth", "actual defect label", "predicted defect"], 1, "max_depth controls how the tree is allowed to learn."), mcq("Why keep a final test set locked during tuning?", ["To provide independent approval evidence", "To increase trial count", "To remove all validation", "To hide results"], 0, "Repeated selection must not consume final evidence.")],
    [task("q1", "concept_check", "Core concept", "What is a hyperparameter? Distinguish it from a learned parameter and from an input feature using one model example.", "Prove the concept itself is understood before governance.", "Three-way distinction plus example.", 45, 95, ["hyperparameter", "parameter", "feature"]), task("q2", "tiny_hands_on", "Interpret candidates", "Using the max_depth candidate table in the lesson, which setting would you take forward for final evaluation and why?", "Read tuning evidence rather than repeat controls.", "Candidate choice, train/validation pattern and limitation.", 45, 95, ["depth 8", "overfit", "not final approval"]), task("q3", "failure_diagnosis", "Selection failure", "A team tries 150 settings, reports the best validation F1, then sees performance collapse on a later-period locked test. Diagnose what may have happened and what evidence you would inspect.", "Diagnose validation overuse and possible time shift.", "Symptom, two hypotheses, evidence and prevention.", 60, 120, ["selection overfitting", "time shift", "trial history"]), task("q4", "architect_decision", "Govern tuning", "Define a production tuning approval process for model parameters and thresholds.", "Demand architecture only where architecture belongs.", "Search space/budget, registry, locked evidence, owner and approval rule.", 65, 125, ["budget", "registry", "locked test", "owner"])]
)

TOPIC_LEARNING_DESIGNS["mlf_023"] = design(
    "mlf_023", "ROC, PR curves, and operating points",
    "Read threshold curves and select operating points appropriate for rare-defect risk and workload.",
    "Recall precision, recall, false positives, false negatives and threshold decisions.",
    [{"heading": "A curve is many thresholds", "body": "Each threshold creates a different combination of caught positives and false alarms."}, {"heading": "ROC versus PR", "body": "ROC can look optimistic when negatives dominate; PR focuses attention on positive detection quality and is often more informative for rare defects."}],
    {"scenario": "Rare defects: threshold A recall=0.92 precision=0.18; threshold B recall=0.78 precision=0.55.", "takeaway": "The chosen operating point depends on missed-defect risk and available inspection capacity."},
    "Treating AUC as the deployment threshold or preferring ROC-AUC without considering imbalance.",
    "Approve an operating point with metric evidence, workload capacity and escalation rules.",
    {"question": "When defects are rare, why inspect the PR curve closely?", "reveal": "It exposes the precision/recall quality of positive alerts under imbalance."},
    [mcq("An operating point is...", ["A chosen threshold and its trade-off", "A training label", "Only an AUC score", "A feature"], 0, "Deployment acts at a threshold." )],
    [task("q1", "concept_check", "Curves", "Explain why PR curves can be more informative than ROC curves for rare defects.", "Connect imbalance to evaluation.", "Mechanism and use.", 40, 90, ["rare positives", "precision-recall"]), task("q2", "tiny_hands_on", "Select point", "Choose between threshold A and B in the lesson when inspection capacity is constrained but missed defects are high cost.", "Make a qualified decision.", "Trade-off and required extra evidence.", 45, 100, ["capacity", "miss cost"]), task("q3", "failure_diagnosis", "AUC trap", "A model has strong ROC-AUC but floods inspectors with low-quality alerts. What was missed?", "Diagnose metric-to-operation gap.", "Failure and better evidence.", 45, 95, ["precision", "operating point"]), task("q4", "architect_decision", "Threshold approval", "Design an operating-point approval rule.", "Translate curves into policy.", "Metric floor, capacity, owner and monitor.", 60, 120, ["threshold", "capacity", "owner"])]
)

TOPIC_LEARNING_DESIGNS["mlf_024"] = design(
    "mlf_024", "Probability calibration and confidence",
    "Determine whether predicted probabilities are honest enough for risk-based decisions.",
    "Recall that ranking cases and estimating reliable probability are different jobs.",
    [{"heading": "Ranking versus calibration", "body": "A model may rank risky cases correctly while its 0.8 scores do not mean approximately 80% occurrence."}, {"heading": "Decision relevance", "body": "Probabilities drive thresholds, intervention tiers and expected cost calculations only if calibrated."}],
    {"scenario": "Among 100 cases scored near 0.8, only 35 fail.", "takeaway": "The model is overconfident in that score band, even if its ranking is useful."},
    "Treating a raw score as a trustworthy probability without calibration evidence.",
    "Use reliability checks, calibration metrics and policy review before probability-based action tiers.",
    {"question": "If 0.8-risk cases fail only 35% of the time, what is wrong?", "reveal": "The probability is poorly calibrated or shifted; it is overconfident in that band."},
    [mcq("Calibration asks whether...", ["Predicted probabilities match observed rates", "All features are causal", "Training is fast", "AUC is zero"], 0, "Calibration concerns probability honesty." )],
    [task("q1", "concept_check", "Concept", "Explain probability calibration versus ranking performance.", "Separate two kinds of quality.", "Contrast and business relevance.", 40, 90, ["probability", "ranking"]), task("q2", "tiny_hands_on", "Interpret band", "100 cases are scored near 0.8 risk, but only 35 fail. What should you conclude and do next?", "Read calibration evidence.", "Conclusion and validation/action.", 40, 90, ["overconfident", "review"]), task("q3", "failure_diagnosis", "Decision error", "Intervention capacity is exceeded because scores were treated as reliable probabilities. Diagnose.", "Link calibration to operations.", "Mechanism and correction.", 45, 100, ["calibration", "capacity"]), task("q4", "architect_decision", "Risk policy", "Define probability-calibration evidence before risk-tier deployment.", "Govern score-based decisions.", "Evidence, threshold policy and owner.", 60, 120, ["reliability", "owner"])]
)

TOPIC_LEARNING_DESIGNS["mlf_025"] = design(
    "mlf_025", "Data quality, label quality, and sampling bias",
    "Identify when poor input/target data or unrepresentative sampling invalidates model learning and evaluation.",
    "Recall that models learn from examples and labels rather than business truth directly.",
    [{"heading": "Data and labels", "body": "Missing values, inconsistent sensors and ambiguous labels can teach the wrong pattern."}, {"heading": "Sampling", "body": "A model trained only on easy or selected cases may fail on the real operational population."}],
    {"scenario": "Two inspectors disagree on 30% of defect labels, while the training set excludes hard-to-inspect parts.", "takeaway": "Both target reliability and sample representativeness are compromised."},
    "Treating more rows as sufficient without checking whether labels and sampling are trustworthy.",
    "Define label audit, sampling provenance, missing-data checks and approval thresholds before model release.",
    {"question": "Can a sophisticated model solve inconsistent labels on its own?", "reveal": "No. It may learn disagreement and bias rather than real defect signal."},
    [mcq("High label disagreement primarily threatens...", ["Target truth used for learning", "CSS styling", "Password length", "Only compute time"], 0, "The model learns from the labels it receives." )],
    [task("q1", "concept_check", "Concept", "Differentiate input data quality, label quality and sampling bias.", "Separate failure sources.", "Three definitions with examples.", 45, 100, ["input", "label", "sample"]), task("q2", "tiny_hands_on", "Interpret audit", "Two labelers disagree on 30% of defect cases. What should happen before training approval?", "Use quality evidence.", "Conclusion, investigation and gate.", 40, 90, ["label audit", "approval"]), task("q3", "failure_diagnosis", "Biased sample", "A model trained only on escalated warranty cases fails on normal workshop traffic. Diagnose.", "Recognise sampling bias.", "Mechanism and correction.", 45, 100, ["selection bias", "representative"]), task("q4", "architect_decision", "Data gate", "Design minimum data-quality and label-quality release gates.", "Create foundation controls.", "Checks, thresholds and owner.", 60, 120, ["audit", "owner"])]
)

# Gate items retain richer evidence because they exist to integrate topics.
TOPIC_LEARNING_DESIGNS["checkpoint_ml_foundations_001"] = design(
    "checkpoint_ml_foundations_001", "Checkpoint 1: ML Foundations Review",
    "Combine foundational concepts into a defensible model trust decision.",
    "This is a gate: revisit weak lessons before attempting an integrated defence.",
    [{"heading": "Trust chain", "body": "Target, features, split, baseline, leakage checks and risk-aligned metrics must work together."}],
    {"scenario": "A defect model shows 96% accuracy and 30% recall.", "takeaway": "The model cannot be trusted for missed-defect control from accuracy alone."},
    "Passing vocabulary checks while failing to make a deployment decision from evidence.",
    "Checkpoint answers must integrate evidence, action and control ownership.",
    {"question": "Can high accuracy compensate for very low defect recall?", "reveal": "No, where missed defects are the critical risk."},
    [mcq("What invalidates an evaluation?", ["Point-in-time leakage", "Reporting recall", "Comparing a baseline", "Monitoring"], 0, "Leakage breaks trust." )],
    [task("q1", "concept_check", "Integrate", "Explain the model trust chain from target through metric choice.", "Integrate foundations.", "Connected explanation.", 70, 130, ["target", "split", "leakage", "metric"]), task("q2", "tiny_hands_on", "Calculate", "For TP=12, FP=8, FN=28, TN=952, calculate accuracy, precision and recall and make a go-live decision.", "Compute and decide.", "Calculations plus decision.", 65, 125, ["accuracy", "precision", "recall"]), task("q3", "failure_diagnosis", "Leakage", "A model uses a post-inspection feature and scores highly. Diagnose and prevent recurrence.", "Use trust chain.", "Mechanism and controls.", 60, 120, ["leakage", "point-in-time"]), task("q4", "architect_decision", "Checklist", "Design a minimum go-live checklist for defect detection.", "Defend release control.", "Evidence, owners and fallback.", 80, 150, ["baseline", "metrics", "owner"]), task("q5", "teachback", "Explain", "Explain to a quality leader why high accuracy can still be unsafe.", "Communicate the risk.", "Simple explanation and consequence.", 45, 90, ["missed defects", "business impact"])], gate=True
)

TOPIC_LEARNING_DESIGNS["checkpoint_ml_architect_001"] = design(
    "checkpoint_ml_architect_001", "Checkpoint 2: ML Architect Readiness Review",
    "Defend a complete ML decision from validation through monitoring and governance.",
    "This gate integrates advanced lessons; it is intentionally deeper than a normal lesson.",
    [{"heading": "Architecture readiness", "body": "You must connect evidence quality, model decision, operating point, explanation limits and post-deployment control."}],
    {"scenario": "A predictive-quality system performs well overall but is weak for one line and overloads inspectors at the selected threshold.", "takeaway": "Architecture approval needs conditional rollout, capacity-aware thresholding and monitoring."},
    "Submitting a model score without an evidence hierarchy and operating policy.",
    "A ready architect states constraints, decision, fallback, owners and evidence gaps.",
    {"question": "Would you approve broad rollout when one line and workload remain unsafe?", "reveal": "No. Use conditional deployment or hold until controls and evidence are sufficient."},
    [mcq("Which is an architect approval condition?", ["Evidence, operating policy and response owner", "Only highest score", "Only a chart", "Only more trials"], 0, "Architecture combines evidence and operations." )],
    [task("q1", "concept_check", "Validation", "Select and justify validation strategy for a time- and line-dependent manufacturing dataset.", "Integrate validation design.", "Decision and risk addressed.", 70, 130, ["time", "group", "leakage"]), task("q2", "tiny_hands_on", "Operating point", "Explain how you would choose a rare-defect operating point under an inspection-capacity constraint.", "Use PR/threshold thinking.", "Metrics, constraint and decision.", 70, 135, ["PR", "capacity"]), task("q3", "failure_diagnosis", "Quality failure", "Diagnose a technically strong model that fails due to label inconsistency or sampling bias.", "Use data-quality reasoning.", "Mechanism, evidence, prevention.", 65, 130, ["labels", "sampling"]), task("q4", "architect_decision", "Govern", "Define release and monitoring governance for the system.", "Defend architecture.", "Evidence, owner, fallback and retraining.", 85, 160, ["monitoring", "fallback", "owner"]), task("q5", "teachback", "Executive summary", "Give a concise conditional go-live recommendation to a quality director.", "Communicate architecture decision.", "Decision, risk, condition.", 45, 90, ["conditional", "risk"])], gate=True
)

TOPIC_LEARNING_DESIGNS["capstone_ml_architect_001"] = design(
    "capstone_ml_architect_001", "Capstone: Predictive Quality ML Architecture",
    "Build and defend an end-to-end predictive-quality ML design using evidence, policy and operational controls.",
    "This capstone requires completed lesson foundations and checkpoint reasoning; it is not a recall quiz.",
    [{"heading": "Capstone output", "body": "You are creating a model decision package: problem framing, pipeline, evidence, operating point, errors, monitoring and architecture decision record."}],
    {"scenario": "A model reduces missed defects but adds inspection load at Plant B.", "takeaway": "A credible recommendation is conditional and capacity-aware, not a victory claim."},
    "Presenting a model metric without defending data validity, operational action and monitoring.",
    "The capstone produces artifacts an architecture review board could challenge and approve conditionally.",
    {"question": "What is a valid final recommendation when benefit and inspection load conflict?", "reveal": "A conditional decision with threshold, scope, evidence, capacity control, fallback and monitoring."},
    [mcq("A capstone decision record must include...", ["Evidence and operational conditions", "Only the algorithm name", "Only training accuracy", "No limitations"], 0, "An architecture decision is reviewable." )],
    [task("q1", "concept_check", "Frame", "Define the predictive-quality problem, outcome, decision user and success/failure costs.", "Establish purpose.", "Problem framing artifact.", 90, 170, ["target", "decision", "cost"]), task("q2", "tiny_hands_on", "Pipeline evidence", "Describe the validation, baseline, feature pipeline and model comparison evidence you would produce.", "Defend build evidence.", "Design and artifacts.", 100, 190, ["validation", "baseline", "pipeline"]), task("q3", "failure_diagnosis", "Analysis", "Describe the threshold, error-analysis and explainability investigation for the proposed model.", "Test diagnostic architecture.", "Evidence and limits.", 100, 190, ["threshold", "errors", "explainability"]), task("q4", "architect_decision", "Operate", "Define monitoring, fallback, retraining and ownership for deployment.", "Make it operational.", "Policy and controls.", 100, 190, ["monitoring", "fallback", "owner"]), task("q5", "teachback", "Decision readout", "State the final architecture recommendation, conditions, key risks and artifacts to approve.", "Produce executive readout.", "Conditional decision.", 90, 170, ["recommendation", "conditions", "risks"])], gate=True
)


def get_bundled_learning_design(topic_id: str) -> Optional[Dict[str, Any]]:
    data = TOPIC_LEARNING_DESIGNS.get(str(topic_id or ""))
    return deepcopy(data) if data else None


def has_bundled_learning_design(topic_id: str) -> bool:
    return str(topic_id or "") in TOPIC_LEARNING_DESIGNS


def design_to_concept_note(learning_design: Dict[str, Any]) -> ConceptNote:
    steps = learning_design.get("concept_steps", [])
    simple = " ".join(str(item.get("body", "")) for item in steps).strip()
    example = learning_design.get("worked_example", {})
    return ConceptNote(
        topic_id=learning_design["topic_id"],
        title=learning_design["title"],
        simple_explanation=simple,
        wrong_mental_model=str(learning_design.get("misconception", "")),
        correct_mental_model=str(learning_design.get("learning_objective", "")),
        tiny_example=str(example.get("scenario", "")) + " " + str(example.get("takeaway", "")),
        why_it_matters=str(learning_design.get("architect_extension", "")),
        edge_case=str(learning_design.get("misconception", "")),
        three_takeaways=[str(learning_design.get("learning_objective", "")), str(example.get("takeaway", "")), str(learning_design.get("architect_extension", ""))],
    )


def design_to_architect_note(learning_design: Dict[str, Any]) -> ArchitectNote:
    return ArchitectNote(
        topic_id=learning_design["topic_id"],
        architect_summary=str(learning_design.get("architect_extension", "")),
        design_implications=[str(learning_design.get("architect_extension", "")), "Evaluation must score the published evidence task rather than preferred vocabulary."],
        common_mistakes=[str(learning_design.get("misconception", "")), "Adding controls not tied to the concept or scenario."],
        production_risks=[str(learning_design.get("misconception", "")), str(learning_design.get("worked_example", {}).get("takeaway", ""))],
        interview_framing=str(learning_design.get("learning_objective", "")),
        use_case_mapping=[UseCaseMapping(context="manufacturing_ai", relevance=str(learning_design.get("architect_extension", "")))],
    )


def design_to_assessment(learning_design: Dict[str, Any]) -> Assessment:
    return Assessment(
        topic_id=learning_design["topic_id"],
        questions=[
            AssessmentQuestion(
                question_id=item["question_id"],
                type=item["type"],
                question=item["question"],
                expected_focus=list(item.get("expected_focus", [])),
            ) for item in learning_design.get("evidence_tasks", [])
        ],
    )


def design_to_booster(learning_design: Dict[str, Any]) -> Dict[str, Any]:
    tasks = learning_design.get("evidence_tasks", [])
    return {
        "topic_id": learning_design["topic_id"],
        "title": learning_design["title"],
        "plain_language": learning_design.get("learning_objective", ""),
        "worked_example": learning_design.get("worked_example", {}).get("takeaway", ""),
        "production_trap": learning_design.get("misconception", ""),
        "mission_hint": "Each response is scored for its published evidence task, not for repeating architecture vocabulary.",
        "key_distinctions": [item.get("body", "") for item in learning_design.get("concept_steps", [])],
        "answer_frame": [],
        "mission_bridge": [
            {
                "mission_type": item.get("type", "mission"), "question_id": item.get("question_id", ""),
                "tested_skill": item.get("purpose", ""), "use_from_booster": item.get("response_shape", ""),
                "required_demonstration": item.get("expected_focus", []), "not_required": "Do not add unrelated governance vocabulary.",
                "unsafe_leap": learning_design.get("misconception", ""),
            } for item in tasks
        ],
        "mission_focus": [],
        "mcqs": learning_design.get("knowledge_checks", []),
        "learning_design": learning_design,
    }


def task_for_question(learning_design: Optional[Dict[str, Any]], question_id: str) -> Optional[Dict[str, Any]]:
    if not learning_design:
        return None
    for item in learning_design.get("evidence_tasks", []):
        if item.get("question_id") == question_id:
            return deepcopy(item)
    return None

# A deployed learner may already be midway through Patch 039's persisted mlf_022
# assessment. These mappings improve that active run without rewriting saved questions.
LEGACY_ACTIVE_TASK_GUIDANCE: Dict[str, List[Dict[str, Any]]] = {
    "mlf_022": [
        task("q1", "concept_check", "Selection overfit", "Explain how hyperparameter tuning can overfit validation evidence even when training code is technically correct.", "Explain why repeated selection turns validation evidence into part of the search.", "Mechanism plus one concrete model-setting example and final-evidence boundary.", 45, 95, ["selection overfitting", "locked test"]),
        task("q2", "tiny_hands_on", "Plan 30 trials", "You can evaluate 30 model configurations before a quality-model deadline. Design a tuning and final-test process.", "Design a bounded tuning process.", "Define settings/search space, allocate the 30-trial budget, select on development evidence, evaluate winner once on locked test.", 55, 110, ["budget", "search space", "final evidence"]),
        task("q3", "failure_diagnosis", "Collapse diagnosis", "A tuned model's validation score is excellent but the final later-period test score collapses. Diagnose likely process failures.", "Separate validation-selection luck from time shift.", "Symptom, two plausible mechanisms, evidence to distinguish them and prevention.", 60, 120, ["validation overuse", "time shift", "trial evidence"]),
        task("q4", "architect_decision", "Govern tuning", "Define governance for model and threshold tuning in a production ML team.", "Turn tuning into controlled decision-making.", "Search budget, experiment record, locked evidence, owner and approval rule.", 65, 125, ["registry", "approval", "owner"]),
        task("q5", "teachback", "Explain simply", "Explain why 'we tried more options and got a higher score' is not automatically good news.", "Communicate selection luck simply.", "One analogy, one risk and one honest confirmation step.", 35, 75, ["chance", "confirmation"]),
    ]
}


def runtime_task_for_question(learning_design: Optional[Dict[str, Any]], question_id: str, question_text: str = "") -> Optional[Dict[str, Any]]:
    if not learning_design:
        return None
    topic_id = str(learning_design.get("topic_id", ""))
    for item in LEGACY_ACTIVE_TASK_GUIDANCE.get(topic_id, []):
        if item.get("question_id") == question_id and item.get("question", "").strip() == str(question_text or "").strip():
            return deepcopy(item)
    return task_for_question(learning_design, question_id)
