from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict


APPLICATION_DRILLS: Dict[str, Dict[str, Any]] = {
    "mlf_020": {
        "prompt": "A sensor feature mean shifts beyond its alert tolerance, but defect labels will arrive after 30 days. What can you conclude today, and what must wait for labels?",
        "reveal": "You can conclude that input behaviour changed and trigger investigation. You cannot conclude that recall degraded or retraining is required until performance evidence arrives. Immediate actions are data-quality and sensor checks, prediction-distribution review, and owner assignment.",
    },
    "mlf_021": {
        "prompt": "You must deploy a defect model to a new production line next quarter. Would a random row split honestly test that risk?",
        "reveal": "No. A random row split can mix the same line or machine patterns into training and validation. Hold out whole lines to test unseen-line generalisation, and add a time boundary when future-period performance also matters.",
    },
    "mlf_022": {
        "prompt": "You test 30 configurations and one reaches validation F1 = 0.88. Is 0.88 final deployment evidence? State the safe approval path.",
        "reveal": "No. That score helped select the candidate and may include validation luck. Record all 30 trials, select under the fixed budget and constraints, then evaluate the winner once on locked final evidence before approval.",
    },
    "mlf_023": {
        "prompt": "A lower alert threshold catches more real defects but doubles inspection workload. Is the lower threshold automatically better?",
        "reveal": "No. It may improve recall while damaging precision and operational capacity. Select an operating point using missed-defect cost, alert capacity and validated threshold metrics, then monitor the approved policy.",
    },
    "mlf_024": {
        "prompt": "A model assigns roughly 0.8 risk to 100 cases, but only 45 actually fail. What promise is broken?",
        "reveal": "The probability is poorly calibrated: an 0.8 risk band should show outcomes close to 80%, not 45%. Ranking could still be useful, but probability-based decisions require calibration review or recalibration evidence.",
    },
    "mlf_025": {
        "prompt": "Two inspectors disagree on 25% of defect labels for one supplier. Should model tuning continue as normal?",
        "reveal": "No. The training target is unreliable for that slice. Pause release-oriented tuning, investigate the label process and supplier coverage, agree an acceptance gate, then resume modelling only after quality evidence is adequate.",
    },
    "checkpoint_ml_architect_001": {
        "prompt": "A model has good average accuracy, weak rare-defect recall, uncertain labels on one plant and no fallback. Is it ready?",
        "reveal": "No. The release case is incomplete. The architect must require corrected evidence, a threshold decision, segment validation, label-quality action, monitoring owner and fallback before conditional approval.",
    },
    "capstone_ml_architect_001": {
        "prompt": "Your capstone model improves recall but creates high inspection load at Plant B. What belongs in the final recommendation?",
        "reveal": "Give a conditional decision, not a victory claim: approved threshold and plant scope, evidence supporting it, capacity constraint, fallback/manual-review path, monitoring trigger, accountable owner and rollback condition.",
    },
}


CODE_LAB_GUIDANCE: Dict[str, Dict[str, Any]] = {
    "mlf_020": {
        "concept_bridge": "This function detects an input-distribution warning. It compares a reference-window mean with a current-window mean. A warning means investigate; it does not prove model performance failed.",
        "worked_code_example": "If reference mean = 10, current mean = 13, and tolerance = 2, the shift is 3, so alert = True. Labels are still needed before claiming recall loss.",
    },
    "mlf_021": {
        "concept_bridge": "A group holdout keeps an entire production line, machine, supplier, or vehicle outside training. Random row splitting can leak familiar group patterns into validation and inflate confidence.",
        "worked_code_example": "For ['Line_A', 'Line_B', 'Line_A'] with holdout 'Line_B', indices [0, 2] train the model and index [1] validates it on the held-out line.",
    },
    "mlf_022": {
        "concept_bridge": "A tuning decision chooses the best eligible trial, not merely the highest score. Operational constraints such as latency are part of the selection rule.",
        "worked_code_example": "If trial A scores 0.88 at 120 ms and trial B scores 0.86 at 45 ms with a 60 ms limit, A is ineligible. B wins among eligible trials.",
    },
    "mlf_023": {
        "concept_bridge": "A threshold converts risk scores into actions. Code computes precision, recall and alert volume at one threshold so you can see the operational trade-off.",
        "worked_code_example": "A stricter threshold may produce fewer false alarms but miss true defects. A looser threshold may catch more defects but consume inspection capacity.",
    },
    "mlf_024": {
        "concept_bridge": "A Brier score checks whether probability statements match outcomes. Lower squared probability error is better; it is about probability honesty, not only ranking.",
        "worked_code_example": "Predictions [1.0, 0.0] for outcomes [1, 0] have Brier score 0.0. Predictions [0.8, 0.4] produce non-zero probability error.",
    },
    "mlf_025": {
        "concept_bridge": "Label disagreement is a direct warning about target quality. The function measures how often two labellers disagree before the model learns from those labels.",
        "worked_code_example": "If two of four paired labels disagree, disagreement rate = 0.5. That is a data-quality issue to govern before release.",
    },
    "checkpoint_ml_architect_001": {
        "concept_bridge": "This checkpoint combines metric calculation with a release rule. First quantify precision/recall/F1; then select the highest threshold that still meets the minimum recall requirement.",
        "worked_code_example": "A threshold is not accepted because it looks neat. It is accepted only if it meets the recall floor and its false-positive workload is acceptable on locked evidence.",
    },
    "capstone_ml_architect_001": {
        "concept_bridge": "The deployment policy converts a risk score into operational action bands. Threshold ordering is a governance guardrail, not a coding detail.",
        "worked_code_example": "Scores above the intervention threshold trigger action; scores in the review band go to a human; lower scores continue monitoring. Invalid threshold order must be rejected.",
    },
}


def get_application_drill(topic_id: str) -> Dict[str, Any]:
    return deepcopy(APPLICATION_DRILLS.get(str(topic_id or ""), {}))


def get_code_lab_guidance(topic_id: str) -> Dict[str, Any]:
    return deepcopy(CODE_LAB_GUIDANCE.get(str(topic_id or ""), {}))
