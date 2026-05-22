from __future__ import annotations

from typing import Set

from src.schemas import ArchitectNote, Assessment, AssessmentQuestion, ConceptNote, Topic, UseCaseMapping


CHECKPOINT_TOPIC_IDS: Set[str] = {
    "checkpoint_ml_foundations_001",
    "checkpoint_ml_architect_001",
}


def is_checkpoint_topic(topic_id: str | None) -> bool:
    return str(topic_id or "").strip() in CHECKPOINT_TOPIC_IDS


def build_checkpoint_concept_note(topic: Topic) -> ConceptNote:
    if topic.topic_id == "checkpoint_ml_architect_001":
        return _build_ml_architect_concept_note(topic)
    return _build_foundations_concept_note(topic)


def build_checkpoint_architect_note(topic: Topic) -> ArchitectNote:
    if topic.topic_id == "checkpoint_ml_architect_001":
        return _build_ml_architect_architect_note(topic)
    return _build_foundations_architect_note(topic)


def build_checkpoint_assessment(topic: Topic) -> Assessment:
    if topic.topic_id == "checkpoint_ml_architect_001":
        return _build_ml_architect_assessment(topic)
    return _build_foundations_assessment(topic)


def _build_foundations_concept_note(topic: Topic) -> ConceptNote:
    return ConceptNote(
        topic_id=topic.topic_id,
        title=topic.title,
        simple_explanation=(
            "This is not another lesson. It is a checkpoint across the first 10 ML foundation topics. "
            "The goal is to prove that you can connect data split, leakage, baseline, generalization, "
            "bias-variance, accuracy, precision, and recall into one production decision."
        ),
        wrong_mental_model="Treating the first 10 lessons as separate definitions that can be memorized independently.",
        correct_mental_model=(
            "Treating the first 10 lessons as one evaluation discipline: define the target, protect the split, "
            "compare against a baseline, select the metric that exposes business risk, and design guardrails."
        ),
        tiny_example=(
            "A defect model can show 96% accuracy, beat a weak baseline, and still be rejected if recall for actual defects "
            "is poor or if test data leaked future information into training."
        ),
        why_it_matters=(
            "An ML Architect is judged on whether the system is safe to trust, not whether each concept can be explained in isolation."
        ),
        edge_case=(
            "A model is deployed on impressive offline metrics, then the team discovers rare failures were hidden and the split was invalid."
        ),
        three_takeaways=[
            "The first 10 topics form one evaluation and deployment reasoning chain.",
            "A model can look successful offline while failing the production decision.",
            "Advanced ML should not unlock until metric choice and leakage control are connected clearly.",
        ],
    )


def _build_foundations_architect_note(topic: Topic) -> ArchitectNote:
    return ArchitectNote(
        topic_id=topic.topic_id,
        architect_summary=(
            "This checkpoint verifies readiness to move from ML foundations into advanced ML. The learner must diagnose "
            "whether an ML system is evaluation-safe, metric-aligned, and production-ready."
        ),
        design_implications=[
            "Every model review must include baseline comparison, split validity, class-level metric review, and failure analysis.",
            "Production approval requires monitoring, threshold ownership, fallback behaviour, and retraining criteria.",
        ],
        common_mistakes=[
            "Approving a model because aggregate accuracy is high while ignoring minority-class recall.",
            "Discussing leakage, bias-variance, and metrics as separate ideas instead of one deployment decision.",
        ],
        production_risks=[
            "A high-scoring model may miss rare but expensive failures.",
            "A model may appear stable in validation but collapse when production data violates split assumptions.",
        ],
        interview_framing=(
            "The first checkpoint for an ML system is whether evaluation is valid, the baseline is meaningful, "
            "metrics expose business risk, and production controls are defined."
        ),
        use_case_mapping=[
            UseCaseMapping(
                context="manufacturing_ai",
                relevance="For predictive quality, defect recall and leakage control must be proven before the model is trusted.",
            )
        ],
    )


def _build_foundations_assessment(topic: Topic) -> Assessment:
    return Assessment(
        topic_id=topic.topic_id,
        questions=[
            AssessmentQuestion(
                question_id="q1", type="concept_check",
                question="Connect baseline, training/test split, generalization, leakage, and metric choice. How do they jointly decide whether a model is trustworthy?",
                expected_focus=["evaluation discipline", "offline validation", "production trust"],
            ),
            AssessmentQuestion(
                question_id="q2", type="tiny_hands_on",
                question="A defect model has TP=12, FP=8, FN=28, TN=952. Calculate accuracy, precision, and recall. Which metric should govern production review and why?",
                expected_focus=["accuracy 0.964", "precision 0.60", "recall 0.30", "missed defects"],
            ),
            AssessmentQuestion(
                question_id="q3", type="failure_diagnosis",
                question="A model looked excellent in testing but used a feature available only after inspection. What failed, and what control prevents it?",
                expected_focus=["data leakage", "point-in-time feature rule", "training-serving parity"],
            ),
            AssessmentQuestion(
                question_id="q4", type="architect_decision",
                question="Define the minimum go-live checklist for a predictive quality model.",
                expected_focus=["baseline", "valid split", "metrics", "threshold", "monitoring", "fallback", "owner"],
            ),
            AssessmentQuestion(
                question_id="q5", type="teachback",
                question="Explain to a plant quality leader why 96% accuracy may still be unsafe.",
                expected_focus=["simple language", "rare defects", "recall risk"],
            ),
        ],
    )


def _build_ml_architect_concept_note(topic: Topic) -> ConceptNote:
    return ConceptNote(
        topic_id=topic.topic_id,
        title=topic.title,
        simple_explanation=(
            "This is the ML Architect gate before the capstone. It checks whether you can connect honest validation, "
            "disciplined tuning, operating-point selection, calibration, data and label quality, monitoring, and release governance."
        ),
        wrong_mental_model=(
            "Treating architecture as a list of techniques or approving a model because one score is attractive."
        ),
        correct_mental_model=(
            "An architect issues an evidence-backed release decision: what is trusted, what is not, what blocks release, "
            "what is monitored, and who acts when a control fails."
        ),
        tiny_example=(
            "A defect model has strong ROC-AUC but low precision at the proposed recall, inflated probabilities for a new supplier, "
            "and no clean time/group test. The correct answer is not immediate deployment. It is repair the evidence and operating policy first."
        ),
        why_it_matters=(
            "Deep learning will add modelling complexity. It should not be introduced before the learner can govern classical ML decisions rigorously."
        ),
        edge_case=(
            "A model can be statistically promising yet remain unapprovable because validation is contaminated, labels are unreliable, "
            "or the production response has no accountable owner."
        ),
        three_takeaways=[
            "Architect readiness is a production decision skill, not vocabulary recall.",
            "Validation, threshold, calibration, data quality, and monitoring fail together if not governed together.",
            "The capstone unlocks only after a clean checkpoint result and passing practical work.",
        ],
    )


def _build_ml_architect_architect_note(topic: Topic) -> ArchitectNote:
    return ArchitectNote(
        topic_id=topic.topic_id,
        architect_summary=(
            "This checkpoint evaluates whether the learner can defend or reject a predictive model through an implementable evidence pack, "
            "decision policy, monitoring plan, fallback, and accountable ownership."
        ),
        design_implications=[
            "Approval must cite split validity, model comparison, threshold/capacity trade-off, calibration, data/label quality, and monitoring.",
            "A clean checkpoint pass requires a passing practical exercise and a decision that specifies conditions, triggers, and owners.",
        ],
        common_mistakes=[
            "Listing technical checks without stating whether release should proceed.",
            "Calling risk scores trustworthy probabilities without calibration evidence or segment coverage.",
        ],
        production_risks=[
            "An unsafe threshold can flood inspection operations or miss expensive defects.",
            "Poor calibration or biased samples can direct intervention money toward the wrong assets or suppliers.",
        ],
        interview_framing=(
            "I would approve an ML risk service only after honest validation, cost-aligned operating point selection, "
            "probability and label-quality evidence, and explicit monitoring and fallback ownership are documented."
        ),
        use_case_mapping=[
            UseCaseMapping(
                context="predictive_quality",
                relevance="The checkpoint mirrors a quality-model release board deciding whether early warnings are trustworthy enough for operations.",
            )
        ],
    )


def _build_ml_architect_assessment(topic: Topic) -> Assessment:
    return Assessment(
        topic_id=topic.topic_id,
        questions=[
            AssessmentQuestion(
                question_id="q1", type="concept_check",
                question="Connect honest validation, disciplined tuning, operating-point choice, calibration, and data/label quality into one ML approval argument.",
                expected_focus=["integrated decision", "release evidence", "approval gate"],
            ),
            AssessmentQuestion(
                question_id="q2", type="tiny_hands_on",
                question="A rare-defect model has ROC-AUC=0.94, PR-AUC=0.31, and at the proposed threshold recall=0.82 with precision=0.16. What must be reviewed before go-live?",
                expected_focus=["rare-event evidence", "alert workload", "false-positive burden", "threshold decision"],
            ),
            AssessmentQuestion(
                question_id="q3", type="failure_diagnosis",
                question="A deployed risk model floods inspectors with alerts and overstates risk for a new supplier. Diagnose validation, calibration, and sampling failures and name confirming evidence.",
                expected_focus=["supplier coverage", "calibration bands", "threshold", "data bias"],
            ),
            AssessmentQuestion(
                question_id="q4", type="architect_decision",
                question="Issue a production approval decision for a predictive-quality model. Define the minimum evidence pack, release conditions, monitoring triggers, fallback, and owners.",
                expected_focus=["decision", "evidence pack", "triggers", "fallback", "owner"],
            ),
            AssessmentQuestion(
                question_id="q5", type="teachback",
                question="Explain to an operations leader what must be proven before trusting a model-generated risk score.",
                expected_focus=["plain language", "probability caution", "operational action"],
            ),
        ],
    )
