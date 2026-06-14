from __future__ import annotations

"""Topic-specific teaching and evidence designs.

Patch 040 makes the learning objective and the evidence required for each topic explicit.
The database may override these bundled defaults through mlos_topic_learning_designs.
Bundled content exists only so the app remains usable before/if a Supabase row is unavailable.
"""

from copy import deepcopy
from typing import Any, Dict, List, Optional

from src.schemas import ArchitectNote, Assessment, AssessmentQuestion, ConceptNote, UseCaseMapping

VERSION = "mastery_repair_tutor_depth_v2"


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


def design(topic_id: str, title: str, objective: str, prerequisite: str, steps: List[Dict[str, str]], example: Dict[str, Any], misconception: str, architect_extension: str, drill: Dict[str, str], checks: List[Dict[str, Any]], tasks: List[Dict[str, Any]], gate: bool = False, concept_map: Optional[List[Dict[str, str]]] = None, worked_examples: Optional[List[Dict[str, Any]]] = None, code_bridge: Optional[Dict[str, Any]] = None, mastery_repair: Optional[List[str]] = None) -> Dict[str, Any]:
    return {
        "design_version": VERSION,
        "topic_id": topic_id,
        "title": title,
        "learning_objective": objective,
        "prerequisite_bridge": prerequisite,
        "concept_steps": steps,
        "concept_map": concept_map or [],
        "worked_example": example,
        "worked_examples": worked_examples or [],
        "code_bridge": code_bridge or {},
        "misconception": misconception,
        "architect_extension": architect_extension,
        "diagnostic_drill": drill,
        "knowledge_checks": checks,
        "evidence_tasks": tasks,
        "mastery_repair_prompts": mastery_repair or [],
        "is_gate": gate,
        "assessment_principle": "Score demonstrated reasoning against the visible task contract. Penalize technical falsehoods. Do not reward keyword stuffing, essay length, or repeated control vocabulary.",
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
    "Store prediction context, slice metrics, assign investigation owners and convert confirmed findings into corrective actions.",
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
    "Choose validation splits that match the deployment boundary: future time, unseen groups, or both, and explain what each split can and cannot prove.",
    "Recall: train/test separation only becomes honest when the split reflects the way the model will face new data in production.",
    [
        {"heading": "1. Start from the deployment question", "body": "Do not begin with 'use cross-validation'. Begin with what the model must generalize to. Future month? New production line? New supplier? New asset? The validation split must simulate that boundary."},
        {"heading": "2. Random split answers a weaker question", "body": "Random rows test whether the model works on more rows drawn from a familiar mixture. It can leak group identity, near-duplicate behaviour, or future-adjacent patterns into both training and validation."},
        {"heading": "3. Time and group splits answer harder questions", "body": "A time holdout tests future periods. A group holdout tests unseen entities such as line, supplier, asset, plant, or vehicle family. A combined split may be needed when the rollout includes both future time and unfamiliar groups."},
        {"heading": "4. Honest scores may be lower", "body": "A lower score from a realistic split is not a failure. It is better evidence. A high random-CV score that cannot survive the deployment boundary is false comfort."},
    ],
    {"scenario": "24 months of data from 12 lines. The model will predict next-month defects and may be used on a newly commissioned line.", "rows": [
        {"validation question": "future on known lines", "split": "train months 1-21, validate months 22-24", "what it proves": "future-time generalisation"},
        {"validation question": "new line", "split": "hold out one or more full lines", "what it proves": "unseen-line generalisation"},
        {"validation question": "future new line", "split": "hold out later period for held-out line", "what it proves": "hardest rollout boundary"},
    ], "takeaway": "The split is a simulation of deployment. Random CV is not automatically wrong, but it is not enough for future or unseen-group rollout."},
    "Calling any cross-validation strategy valid without checking whether it matches the deployment boundary.",
    "Governance should record the deployment boundary, approved split design, leakage checks, release gate, owner, and what lower honest performance means for rollout scope.",
    {"question": "A random split gives 0.91 F1, but a held-out-line split gives 0.63. Which is more useful for a new-line rollout?", "reveal": "The held-out-line result. It is lower, but it tests the deployment boundary that matters."},
    [mcq("For a model deployed to a newly commissioned line, which split gives the most relevant evidence?", ["Random row split", "Hold out the new-line group", "Training score only", "Shuffle all months and lines together"], 1, "The group boundary matters for a new-line rollout.")],
    [
        task("q1", "concept_check", "Split validity", "Explain why cross-validation is not automatically valid for manufacturing ML.", "Show that validity depends on deployment boundary.", "Deployment question -> split implication -> risk of random CV.", 45, 95, ["deployment boundary", "random split limitation", "honest validation"]),
        task("q2", "tiny_hands_on", "Design split", "You have 24 months of sensor data from 12 production lines and must predict next-month defects on existing and new lines. Design the validation split you would test first.", "Combine time and group reasoning.", "Primary split, why, and what extra split tests.", 55, 115, ["time holdout", "line/group holdout", "deployment boundary"]),
        task("q3", "failure_diagnosis", "Random-CV collapse", "A model scored highly in random cross-validation, then failed on a newly commissioned line. What likely went wrong and what evidence would prove it?", "Diagnose leakage or deployment mismatch.", "Symptom -> mechanism -> evidence -> corrected validation.", 55, 115, ["group leakage", "unseen line", "evidence"]),
        task("q4", "architect_decision", "Validation standard", "Define a validation-governance standard for a predictive-quality platform supporting multiple plants and retraining cycles.", "Translate validation into release governance.", "Boundary, split policy, evidence log, approver, monitoring.", 65, 130, ["split policy", "approval evidence", "owner", "monitoring"]),
    ],
    concept_map=[
        {"concept": "Random split", "means": "rows are mixed randomly", "use when": "future data is same mixture and no group leakage risk", "danger": "inflated score under time/group deployment"},
        {"concept": "Time holdout", "means": "train earlier, validate later", "use when": "predicting future periods", "danger": "does not prove unseen-group performance"},
        {"concept": "Group holdout", "means": "entire entity excluded from train", "use when": "new line/supplier/asset rollout", "danger": "may ignore future drift unless combined with time"},
    ],
    worked_examples=[
        {"title": "How to reason from deployment to split", "steps": ["If production is next month on known lines, use a later-period holdout.", "If production includes a new line, hold out full lines.", "If both are true, evaluate a time-based holdout and a group-based holdout before broad rollout."]},
    ],
    code_bridge={"idea": "Group holdout code is just routing row indices by group membership.", "algorithm": ["Start with empty train and validation index lists.", "Loop over each row index and group.", "If group equals holdout_group, append index to validation.", "Otherwise append index to train."], "common_bug": "Do not put only the first matching group row into validation. Every row from the held-out group must stay together."},
    mastery_repair=["Given a deployment statement, name the honest split before naming any metric.", "For every validation score, ask: what future condition or group boundary did this score actually test?"],
)

TOPIC_LEARNING_DESIGNS["mlf_022"] = design(
    "mlf_022", "Hyperparameter tuning without fooling yourself",
    "Explain what hyperparameters are, compare candidate configurations fairly, and prevent tuning from contaminating final approval evidence.",
    "Recall: model parameters are learned from data; hyperparameters are chosen settings that shape how learning happens; validation chooses candidates; final test approves once.",
    [
        {"heading": "1. What is a hyperparameter?", "body": "A hyperparameter is a setting chosen before or around training. It changes how the model learns. Examples: tree max_depth, forest n_estimators, regularization strength, learning rate. It is not an input feature like humidity and not a learned coefficient."},
        {"heading": "2. Why tune it?", "body": "Different settings create different behaviour: too simple may underfit, too flexible may overfit, and a middle setting may generalize better. Tuning compares planned candidates using development validation evidence."},
        {"heading": "3. Where the trap starts", "body": "If you test many candidates against the same validation set, the winner may partly reflect luck in that validation sample. The validation set has become part of the selection process."},
        {"heading": "4. The safe path", "body": "Define the search space and budget first, log every trial, select one candidate under constraints, then open locked final evidence once for approval."},
    ],
    {"scenario": "Decision tree candidates for a defect model", "rows": [
        {"candidate": "A", "max_depth": 2, "train_f1": "0.71", "validation_f1": "0.69", "reading": "too simple / underfit"},
        {"candidate": "B", "max_depth": 8, "train_f1": "0.90", "validation_f1": "0.84", "reading": "best development candidate"},
        {"candidate": "C", "max_depth": 30, "train_f1": "1.00", "validation_f1": "0.72", "reading": "memorising / overfit"},
    ], "takeaway": "Candidate B is selected for final locked-test review. It is not automatically approved from validation."},
    "Thinking the best validation result is final proof, or calling an input feature a hyperparameter.",
    "Production tuning needs a fixed search budget, experiment registry, candidate constraints such as latency, locked final evidence, and named approval owner.",
    {"question": "If 150 trials are searched and the winner has validation F1=0.88, is 0.88 final deployment evidence?", "reveal": "No. It is selection evidence; final approval needs untouched evidence after the search is complete."},
    [mcq("Which item is a hyperparameter?", ["humidity reading", "actual defect label", "tree max_depth", "predicted defect flag"], 2, "max_depth is a chosen setting controlling the model's complexity."), mcq("Why log every tuning trial?", ["To show only the winner", "To expose the search process and selection risk", "To avoid validation", "To create labels"], 1, "The approver needs the full trial history, not just the best result.")],
    [
        task("q1", "concept_check", "Three-way distinction", "What is a hyperparameter? Distinguish it from a learned parameter and an input feature using one model example.", "Prove the base concept before governance.", "Hyperparameter vs parameter vs feature with example.", 45, 95, ["hyperparameter", "parameter", "feature"]),
        task("q2", "tiny_hands_on", "Candidate evidence", "Using the max_depth candidate table in the lesson, which setting would you take forward and why?", "Read train/validation evidence.", "Candidate choice, underfit/overfit reading, and limitation.", 45, 95, ["candidate B", "validation evidence", "not final approval"]),
        task("q3", "failure_diagnosis", "Search failure", "A team tries 150 settings, reports the best validation F1, then sees performance collapse on a later-period locked test. Diagnose.", "Explain selection overfitting and possible time shift.", "Symptom, mechanism, evidence to inspect, prevention.", 60, 120, ["selection overfitting", "trial log", "time shift"]),
        task("q4", "architect_decision", "Tuning governance", "Define a production tuning approval process for model settings and thresholds.", "Govern the search, not just the model.", "Search space/budget, registry, constraint gate, locked test, owner.", 65, 125, ["budget", "registry", "constraint", "locked test", "owner"]),
    ],
    concept_map=[
        {"concept": "Input feature", "example": "humidity", "chosen or learned": "measured from data", "role": "model input"},
        {"concept": "Learned parameter", "example": "coefficient/tree split", "chosen or learned": "learned during training", "role": "internal model fit"},
        {"concept": "Hyperparameter", "example": "max_depth / learning rate", "chosen or learned": "chosen by search/design", "role": "controls learning behaviour"},
    ],
    worked_examples=[
        {"title": "Selection is not approval", "steps": ["Use validation to compare candidates A/B/C.", "Pick B because it balances train and validation performance.", "Check latency or workload constraints.", "Approve only after one locked final test evaluation."]},
    ],
    code_bridge={"idea": "The code exercise selects the best candidate that also meets a production constraint.", "algorithm": ["Filter trials whose latency is within max_latency_ms.", "Among eligible trials, keep the one with highest validation_score.", "Return the candidate id, not the whole dictionary.", "Return None when no trial passes the latency gate."], "common_bug": "Do not choose the highest validation score before applying latency. Production constraints are part of candidate selection."},
    mastery_repair=["Before answering any tuning question, identify what is being tuned.", "Separate candidate-selection evidence from final-approval evidence every time."],
)

TOPIC_LEARNING_DESIGNS["mlf_023"] = design(
    "mlf_023", "ROC, PR curves, and operating points",
    "Convert model scores into threshold decisions, compute the resulting precision/recall/alert volume, and choose an operating point based on rare-defect risk and inspection capacity.",
    "Recall: precision and recall are calculated after a threshold turns scores into positive or negative predictions.",
    [
        {"heading": "1. A score is not yet an action", "body": "A model may output risk scores such as 0.90, 0.60, 0.20. A threshold converts those scores into actions: alert if score >= threshold."},
        {"heading": "2. A curve is many thresholds", "body": "Each possible threshold creates a different confusion matrix. Lower threshold usually raises recall and alert volume. Higher threshold usually improves precision but can miss positives."},
        {"heading": "3. ROC versus PR", "body": "ROC curves can look reassuring when negatives dominate. PR curves focus on the quality of positive alerts, which matters more when defects are rare."},
        {"heading": "4. Operating point", "body": "Deployment does not use an AUC score directly. It uses a chosen threshold plus the precision, recall, alert capacity and cost trade-off at that threshold."},
    ],
    {"scenario": "Actual labels [1,1,0,0], scores [0.9,0.6,0.7,0.2], threshold 0.5", "rows": [
        {"row": 0, "actual": 1, "score": 0.9, "prediction": 1, "result": "TP"},
        {"row": 1, "actual": 1, "score": 0.6, "prediction": 1, "result": "TP"},
        {"row": 2, "actual": 0, "score": 0.7, "prediction": 1, "result": "FP"},
        {"row": 3, "actual": 0, "score": 0.2, "prediction": 0, "result": "TN"},
    ], "takeaway": "Precision=2/3, recall=2/2, alerts=3. Threshold first, metrics second."},
    "Treating AUC as a deployment threshold or calculating TP/FP/FN before applying the threshold to scores.",
    "Approve an operating point with minimum recall, acceptable precision/alert load, named capacity owner, escalation rule and monitoring after deployment.",
    {"question": "If you raise the threshold, what usually happens to recall?", "reveal": "Recall can fall because fewer cases are flagged positive, so some true defects may be missed."},
    [mcq("What is an operating point?", ["A selected threshold with its metric/workload trade-off", "Only ROC-AUC", "The training label", "A feature value"], 0, "Operations act on a threshold, not just a curve."), mcq("For rare defects, why inspect PR curves?", ["They focus on positive alert quality", "They ignore precision", "They remove thresholds", "They prove causality"], 0, "Rare positives make precision and recall central.")],
    [
        task("q1", "concept_check", "Curve meaning", "Explain why PR curves can be more informative than ROC curves for rare defects.", "Connect imbalance to alert quality.", "Imbalance -> PR focus -> operating decision.", 40, 90, ["rare positives", "precision", "recall"]),
        task("q2", "tiny_hands_on", "Operating choice", "Choose between threshold A recall=0.92 precision=0.18 and threshold B recall=0.78 precision=0.55 when inspection capacity is constrained but missed defects are high cost.", "Make a qualified operating decision.", "Trade-off, capacity, cost, missing evidence.", 55, 115, ["recall", "precision", "capacity", "cost"]),
        task("q3", "failure_diagnosis", "AUC trap", "A model has strong ROC-AUC but floods inspectors with low-quality alerts. What was missed?", "Diagnose metric-to-operation gap.", "Failure mechanism and better evidence.", 45, 95, ["operating point", "precision", "alert volume"]),
        task("q4", "architect_decision", "Approval rule", "Design an operating-point approval rule for rare-defect alerts.", "Translate curves into policy.", "Metric floor, capacity gate, owner, monitoring.", 60, 120, ["threshold", "metric floor", "capacity", "owner"]),
    ],
    concept_map=[
        {"concept": "Threshold", "means": "score >= threshold becomes alert", "business question": "who gets inspected or escalated"},
        {"concept": "Precision", "means": "TP/(TP+FP)", "business question": "how many alerts waste capacity"},
        {"concept": "Recall", "means": "TP/(TP+FN)", "business question": "how many real defects are caught"},
        {"concept": "Alerts", "means": "count of predicted positives", "business question": "can operations handle the workload"},
    ],
    worked_examples=[
        {"title": "Code-lab algorithm", "steps": ["For each score, compute predicted_positive = score >= threshold.", "Use predicted_positive and y_true to count TP, FP and FN.", "Alerts are the number of predicted positives.", "Precision and recall use those counts, with zero-denominator guards."]},
    ],
    code_bridge={"idea": "Metrics at a threshold are computed only after scores are converted into decisions.", "algorithm": ["Loop through y_true and scores together.", "Set predicted_positive = score >= threshold.", "Count TP/FP/FN from predicted_positive and actual label.", "Return precision, recall and alert count."], "common_bug": "Do not compare scores to 0 or 1. Scores are continuous risk values; the threshold creates 0/1 decisions."},
    mastery_repair=["Before computing any metric, write the threshold rule in plain language.", "For every operating point, say both: what it catches and what workload it creates."],
)

TOPIC_LEARNING_DESIGNS["mlf_024"] = design(
    "mlf_024", "Probability calibration and confidence",
    "Determine whether model scores can be treated as honest probabilities for risk-tier decisions, not just rankings.",
    "Recall: a model can rank cases well even when its probability numbers are not honest. Ranking asks order. Calibration asks probability truth.",
    [
        {"heading": "1. Ranking asks order", "body": "Ranking performance asks whether higher-scored cases tend to be riskier than lower-scored cases. A model can rank well if most failures appear near the top of the list."},
        {"heading": "2. Calibration asks frequency honesty", "body": "Calibration asks whether a score means what it says. If cases scored near 0.8 fail about 80% of the time, that band is calibrated. If only 35% fail, the model is overconfident in that band."},
        {"heading": "3. Why business cares", "body": "Risk tiers, intervention budgets and expected-cost decisions depend on probability honesty. If raw scores are overconfident, teams may over-intervene, overload capacity, or price risk incorrectly."},
        {"heading": "4. How to govern it", "body": "Use reliability tables/curves, Brier score, calibration checks on holdout data, and recalibration policy before using scores as probabilities."},
    ],
    {"scenario": "100 cases are scored around 0.8 risk", "rows": [
        {"score band": "near 0.8", "expected if calibrated": "about 80 failures out of 100", "observed": "35 failures", "reading": "overconfident probability"},
        {"score band": "near 0.2", "expected if calibrated": "about 20 failures out of 100", "observed": "18 failures", "reading": "reasonably calibrated band"},
    ], "takeaway": "The 0.8 score may still help ranking, but it is not honest enough to drive an 80%-risk intervention tier."},
    "Calling a raw model score 'confidence' or treating a high score as a reliable probability without observed-outcome evidence.",
    "Before risk-tier deployment, require reliability evidence by score band, Brier/calibration metric, recalibration owner, threshold policy and post-release calibration monitoring.",
    {"question": "A model ranks failures near the top, but 0.8-score cases fail only 35% of the time. Is the model useless?", "reveal": "No. Ranking may still be useful, but the probability is not calibrated enough for probability-based risk decisions."},
    [mcq("Calibration asks whether...", ["predicted probabilities match observed outcome rates", "higher scores always cause failures", "the model trains faster", "all thresholds are 0.5"], 0, "Calibration is probability honesty against observed outcomes."), mcq("A model can rank well but be poorly calibrated because...", ["order and probability accuracy are different", "ranking requires no labels", "calibration proves causality", "Brier score is accuracy"], 0, "Order quality and probability honesty are different jobs.")],
    [
        task("q1", "concept_check", "Two qualities", "Explain probability calibration versus ranking performance.", "Separate order quality from probability honesty.", "Contrast plus business relevance.", 45, 95, ["ranking", "probability honesty", "observed outcomes"]),
        task("q2", "tiny_hands_on", "Band evidence", "100 cases are scored near 0.8 risk, but only 35 fail. What should you conclude and do next?", "Read calibration evidence.", "Conclusion, not-useless caveat, validation/recalibration action.", 45, 100, ["overconfident", "observed outcomes", "recalibration"]),
        task("q3", "failure_diagnosis", "Capacity overload", "Intervention capacity is exceeded because scores were treated as reliable probabilities. Diagnose.", "Link calibration error to operational overload.", "Mechanism and correction.", 50, 105, ["raw scores", "capacity", "risk tiers"]),
        task("q4", "architect_decision", "Risk policy", "Define probability-calibration evidence before risk-tier deployment.", "Govern score-based decisions.", "Reliability evidence, policy, owner, monitoring/recalibration.", 65, 125, ["reliability", "owner", "recalibration", "monitoring"]),
    ],
    concept_map=[
        {"concept": "Ranking", "question answered": "Are higher scores generally riskier?", "example evidence": "failures concentrate in top decile", "business use": "prioritise review queue"},
        {"concept": "Calibration", "question answered": "Does 0.8 mean about 80% observed failure?", "example evidence": "score-band observed rates", "business use": "risk tiers, cost and budget decisions"},
        {"concept": "Brier score", "question answered": "How large are probability errors on average?", "example evidence": "mean squared probability error", "business use": "compare probability honesty"},
    ],
    worked_examples=[
        {"title": "How to read a score band", "steps": ["Collect cases with predicted probability near 0.8.", "Count observed failures in that band.", "If 35/100 fail, observed rate is 35%, not 80%.", "Conclusion: overconfident probability; ranking may still be useful but risk tiers need recalibration or different thresholds."]},
        {"title": "Brier score intuition", "steps": ["For each row, compute (probability - outcome)^2.", "Average those squared errors.", "Lower is better probability honesty. It does not replace ranking metrics or capacity checks."]},
    ],
    code_bridge={"idea": "Brier score measures probability error row by row.", "algorithm": ["For each probability/outcome pair, subtract outcome from probability.", "Square the error so over- and under-confidence both count.", "Average squared errors across rows.", "Return 0.0 for empty input to avoid divide-by-zero."], "common_bug": "Do not treat Brier score as accuracy or ranking. It measures probability honesty."},
    mastery_repair=["Never say calibrated probability means model confidence. Say: predicted probability should match observed frequency.", "For any score band, compare predicted rate against observed rate before using it for risk tiers."],
)

TOPIC_LEARNING_DESIGNS["mlf_025"] = design(
    "mlf_025", "Data quality, label quality, and sampling bias",
    "Identify whether inputs, labels and samples are trustworthy enough for a model to learn and for evaluation to mean anything.",
    "Recall: models learn from the examples and labels they receive. Bad examples or bad labels produce bad learning, even with a strong algorithm.",
    [
        {"heading": "1. Input data quality", "body": "Input quality covers missing values, inconsistent units, broken sensors, duplicates, impossible values and pipeline mismatches."},
        {"heading": "2. Label quality", "body": "Label quality covers whether the target outcome is reliable: inspector disagreement, delayed labels, proxy labels, inconsistent definitions and ambiguous defect classes."},
        {"heading": "3. Sampling bias", "body": "Sampling bias means the training or evaluation rows do not represent the real population. A model trained only on escalated cases may fail on normal workshop traffic."},
        {"heading": "4. Why this comes before modelling", "body": "No algorithm can recover a target that is inconsistently labelled or a population that was never sampled. Data and label gates are release controls, not admin paperwork."},
    ],
    {"scenario": "Two inspectors label the same defect cases and disagree on 30%; the training set also excludes hard-to-inspect parts.", "rows": [
        {"issue": "30% label disagreement", "threat": "target truth is unstable", "gate response": "label audit and protocol repair"},
        {"issue": "hard cases excluded", "threat": "sample is not representative", "gate response": "coverage review and sample expansion"},
    ], "takeaway": "More rows do not help if the labels are inconsistent and the sampled population excludes the hardest cases."},
    "Treating volume as quality. More data with unreliable labels or biased selection can make the model more confidently wrong.",
    "Release governance should include label audit, inter-annotator agreement, missingness/outlier checks, segment coverage, sampling provenance and accountable data owners.",
    {"question": "If two inspectors disagree on 30% of labels, should model training proceed unchanged?", "reveal": "No. The label definition or annotation process must be repaired before treating labels as ground truth."},
    [mcq("Sampling bias means...", ["the sampled rows do not represent the deployment population", "the model has many features", "the labels are always correct", "the score is calibrated"], 0, "The training/evaluation population can be systematically unrepresentative."), mcq("High label disagreement threatens...", ["the target the model learns", "only UI colour", "only model latency", "only file size"], 0, "The model learns from labels, so label reliability is foundational.")],
    [
        task("q1", "concept_check", "Three failure sources", "Differentiate input data quality, label quality and sampling bias.", "Separate failure sources clearly.", "Three definitions with one example each.", 55, 115, ["input quality", "label quality", "sampling bias"]),
        task("q2", "tiny_hands_on", "Label audit", "Two labelers disagree on 30% of defect cases. What should happen before training approval?", "Use label evidence as a gate.", "Conclusion, investigation, approval gate.", 45, 95, ["label disagreement", "audit", "gate"]),
        task("q3", "failure_diagnosis", "Biased sample", "A model trained only on escalated warranty cases fails on normal workshop traffic. Diagnose.", "Recognise sampling bias.", "Mechanism and correction.", 45, 100, ["selection bias", "representative sample", "coverage"]),
        task("q4", "architect_decision", "Data gate", "Design minimum data-quality and label-quality release gates.", "Create foundation controls.", "Checks, thresholds, owners and block/release decision.", 65, 125, ["label audit", "coverage", "owner", "release gate"]),
    ],
    concept_map=[
        {"concept": "Input quality", "bad sign": "missing/broken sensors, unit mismatch", "impact": "features mislead model", "control": "profiling and validation checks"},
        {"concept": "Label quality", "bad sign": "inspectors disagree, proxy labels", "impact": "target is unreliable", "control": "label audit and protocol"},
        {"concept": "Sampling bias", "bad sign": "only easy or escalated cases", "impact": "model fails on real population", "control": "coverage and provenance review"},
    ],
    worked_examples=[
        {"title": "Release-gate reasoning", "steps": ["If label disagreement is high, pause training approval.", "Inspect disagreement by defect type, inspector, plant and time.", "Repair label protocol and relabel critical samples.", "Only approve modelling when label quality and segment coverage pass agreed thresholds."]},
    ],
    code_bridge={"idea": "Disagreement rate is a simple label-quality signal.", "algorithm": ["Compare labels from two annotators position by position.", "Count how many positions differ.", "Divide by total compared labels.", "Return 0.0 for empty input."], "common_bug": "Do not treat agreement as model accuracy. It is a data-quality gate before modelling."},
    mastery_repair=["Before asking which model to train, ask whether the labels and sample are trustworthy.", "Separate input defects, target defects and population coverage defects in every diagnosis."],
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
    if not data:
        return None
    copied = deepcopy(data)
    try:
        from src.utils.v23_tutor_quality import enhance_learning_design
        return enhance_learning_design(copied)
    except Exception:
        return copied


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
