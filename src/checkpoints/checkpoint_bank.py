from __future__ import annotations

from typing import Set

from src.schemas import ArchitectNote, Assessment, AssessmentQuestion, ConceptNote, Topic, UseCaseMapping


CHECKPOINT_TOPIC_IDS: Set[str] = {"checkpoint_ml_foundations_001"}


def is_checkpoint_topic(topic_id: str | None) -> bool:
    return str(topic_id or "").strip() in CHECKPOINT_TOPIC_IDS


def build_checkpoint_concept_note(topic: Topic) -> ConceptNote:
    return ConceptNote(
        topic_id=topic.topic_id,
        title=topic.title,
        simple_explanation=(
            "This is not another lesson. It is a checkpoint across the first 10 ML foundation topics. "
            "The goal is to prove that you can connect data split, leakage, baseline, generalization, "
            "bias-variance, accuracy, precision, and recall into one production decision."
        ),
        wrong_mental_model=(
            "Treating the first 10 lessons as separate definitions that can be memorized independently."
        ),
        correct_mental_model=(
            "Treating the first 10 lessons as one evaluation discipline: define the target, protect the split, "
            "compare against a baseline, select the metric that exposes the business risk, and design guardrails "
            "for production behavior."
        ),
        tiny_example=(
            "A defect model can show 96% accuracy, beat a weak baseline, and still be rejected if recall for actual defects "
            "is poor or if test data leaked future information into training."
        ),
        why_it_matters=(
            "An ML Architect is judged on whether the system is safe to trust, not whether each concept can be explained in isolation. "
            "This checkpoint tests that judgment before advanced ML topics unlock."
        ),
        edge_case=(
            "A team deploys a model because the offline metric looks good, but later discovers that the metric hid rare failures, "
            "the split was invalid, and there was no monitoring trigger for changing production conditions."
        ),
        three_takeaways=[
            "The first 10 topics form one evaluation and deployment reasoning chain.",
            "A model can look successful offline while failing the production decision it was meant to support.",
            "Advanced ML should not unlock until metric choice, leakage control, and failure diagnosis are connected clearly.",
        ],
    )


def build_checkpoint_architect_note(topic: Topic) -> ArchitectNote:
    return ArchitectNote(
        topic_id=topic.topic_id,
        architect_summary=(
            "This checkpoint verifies readiness to move from ML foundations into advanced ML. The standard is not theory recall. "
            "The learner must diagnose whether an ML system is evaluation-safe, metric-aligned, and production-ready."
        ),
        design_implications=[
            "Every model review must include baseline comparison, split validity, class-level metric review, and failure-mode analysis.",
            "Production approval should require monitoring, threshold ownership, fallback behavior, and retraining criteria, not only an offline score.",
        ],
        common_mistakes=[
            "Approving a model because aggregate accuracy is high while ignoring minority-class recall or business cost of errors.",
            "Discussing leakage, bias-variance, and metrics as separate ideas instead of connecting them into one deployment decision.",
        ],
        production_risks=[
            "A high-scoring model may miss rare but expensive failures such as defects, downtime risk, or warranty escalation.",
            "A model may appear stable in validation but collapse when production data differs from the training/test assumptions.",
        ],
        interview_framing=(
            "I would explain that the first checkpoint for any ML system is not model complexity. It is whether the evaluation setup is valid, "
            "the baseline is meaningful, the chosen metrics expose the real business risk, and the production controls are defined."
        ),
        use_case_mapping=[
            UseCaseMapping(
                context="manufacturing_ai",
                relevance=(
                    "For predictive quality, the checkpoint forces the learner to connect defect rarity, recall, false negatives, "
                    "baseline comparison, and production monitoring before trusting a model."
                ),
            )
        ],
    )


def build_checkpoint_assessment(topic: Topic) -> Assessment:
    return Assessment(
        topic_id=topic.topic_id,
        questions=[
            AssessmentQuestion(
                question_id="q1",
                type="concept_check",
                question=(
                    "Connect these concepts in one explanation: baseline, training/test split, generalization, leakage, and metric choice. "
                    "How do they jointly decide whether an ML model is trustworthy?"
                ),
                expected_focus=[
                    "Explains the concepts as one evaluation discipline, not separate definitions.",
                    "Connects offline validation to production trust and generalization risk.",
                ],
            ),
            AssessmentQuestion(
                question_id="q2",
                type="tiny_hands_on",
                question=(
                    "A defect model has this confusion matrix for the defect class: TP=12, FP=8, FN=28, TN=952. "
                    "Calculate accuracy, precision, and recall. Which metric would you prioritize before production and why?"
                ),
                expected_focus=[
                    "Accuracy = (TP+TN)/(TP+FP+FN+TN) = 964/1000 = 0.964.",
                    "Precision = 12/(12+8) = 0.60 and recall = 12/(12+28) = 0.30.",
                    "Prioritizes recall or a recall-threshold decision because missed defects are business-critical.",
                ],
            ),
            AssessmentQuestion(
                question_id="q3",
                type="failure_diagnosis",
                question=(
                    "A model looked excellent in test results but failed immediately after deployment. Later, the team found that a feature used during training "
                    "contained information only available after inspection. What went wrong, and what pipeline control would prevent it?"
                ),
                expected_focus=[
                    "Identifies data leakage, specifically future/post-outcome information entering training or evaluation.",
                    "Names controls such as point-in-time feature validation, feature eligibility rules, and training-serving parity checks.",
                ],
            ),
            AssessmentQuestion(
                question_id="q4",
                type="architect_decision",
                question=(
                    "You are approving a predictive quality model for production. Define the minimum review checklist you would require before go-live."
                ),
                expected_focus=[
                    "Includes baseline, valid split, class-level metrics, threshold/cost review, drift monitoring, fallback, and owner for alerts.",
                    "Explains why each control reduces production risk rather than listing generic MLOps words.",
                ],
            ),
            AssessmentQuestion(
                question_id="q5",
                type="teachback",
                question=(
                    "Explain to a plant quality leader why a model with 96% accuracy may still not be safe to deploy. Keep it non-technical but precise."
                ),
                expected_focus=[
                    "Uses stakeholder-friendly language without losing the defect-recall risk.",
                    "Explains that rare but important failures can be hidden by aggregate accuracy.",
                ],
            ),
        ],
    )
