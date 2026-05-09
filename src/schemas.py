from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Literal, Optional


TopicStatus = Literal["not_started", "locked", "in_progress", "completed", "revise", "borderline"]
SelectionMode = Literal["next_unlocked", "retry", "prerequisite_recovery", "manual_selected"]
QuestionType = Literal["concept", "example", "scenario", "architect", "teachback", "concept_check", "tiny_hands_on", "failure_diagnosis", "architect_decision", "code_exercise"]
DecisionType = Literal["pass", "borderline", "revise", "fail_prereq"]
NextActionType = Literal["next_topic", "retry_same_topic", "go_to_prerequisite", "reinforce_and_continue"]


@dataclass
class Topic:
    topic_id: str
    title: str
    domain: str
    difficulty: int
    prerequisites: List[str]
    architect_relevance: List[str]
    tags: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class SelectedTopic:
    selected_topic_id: str
    reason: str
    selection_mode: SelectionMode
    prerequisite_gap: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ConceptNote:
    topic_id: str
    title: str
    simple_explanation: str
    wrong_mental_model: str
    correct_mental_model: str
    tiny_example: str
    why_it_matters: str
    edge_case: str
    three_takeaways: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class UseCaseMapping:
    context: str
    relevance: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ArchitectNote:
    topic_id: str
    architect_summary: str
    design_implications: List[str]
    common_mistakes: List[str]
    production_risks: List[str]
    interview_framing: str
    use_case_mapping: List[UseCaseMapping] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["use_case_mapping"] = [item.to_dict() for item in self.use_case_mapping]
        return data


@dataclass
class AssessmentQuestion:
    question_id: str
    type: QuestionType
    question: str
    expected_focus: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class Assessment:
    topic_id: str
    questions: List[AssessmentQuestion]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "topic_id": self.topic_id,
            "questions": [question.to_dict() for question in self.questions],
        }


@dataclass
class UserAnswer:
    question_id: str
    answer: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class Scores:
    conceptual_clarity: int
    practical_reasoning: int
    architect_reasoning: int
    communication: int

    def total(self) -> int:
        return (
            self.conceptual_clarity
            + self.practical_reasoning
            + self.architect_reasoning
            + self.communication
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class EvaluationResult:
    topic_id: str
    scores: Scores
    strengths: List[str]
    weak_spots: List[str]
    decision: DecisionType
    decision_reason: str
    refined_explanation: str
    refined_architect_summary: str
    next_action: NextActionType

    def to_dict(self) -> Dict[str, Any]:
        return {
            "topic_id": self.topic_id,
            "scores": self.scores.to_dict(),
            "strengths": self.strengths,
            "weak_spots": self.weak_spots,
            "decision": self.decision,
            "decision_reason": self.decision_reason,
            "refined_explanation": self.refined_explanation,
            "refined_architect_summary": self.refined_architect_summary,
            "next_action": self.next_action,
        }


@dataclass
class RunArtifacts:
    concept_note: Optional[str] = None
    architect_note: Optional[str] = None
    assessment: Optional[str] = None
    answers: Optional[str] = None
    evaluation: Optional[str] = None
    refined_note: Optional[str] = None
    practice_exercise: Optional[str] = None
    practice_submission: Optional[str] = None
    practice_result: Optional[str] = None
    practice_coaching: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class RunScores:
    conceptual_clarity: Optional[int] = None
    practical_reasoning: Optional[int] = None
    architect_reasoning: Optional[int] = None
    communication: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class RunState:
    run_id: str
    topic_id: str
    topic_name: str
    phase: str
    status: str
    prerequisites: List[str]
    artifacts: RunArtifacts = field(default_factory=RunArtifacts)
    scores: RunScores = field(default_factory=RunScores)
    next_action: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "run_id": self.run_id,
            "topic_id": self.topic_id,
            "topic_name": self.topic_name,
            "phase": self.phase,
            "status": self.status,
            "prerequisites": self.prerequisites,
            "artifacts": self.artifacts.to_dict(),
            "scores": self.scores.to_dict(),
            "next_action": self.next_action,
        }