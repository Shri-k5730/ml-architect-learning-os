# Patch 038 Cumulative . V2 Completion Block + Teaching-to-Evaluation Contract Alignment

## Baseline used

This package is built on the latest `codebase.zip` supplied after Patch 036. Patch 037 was **not** assumed to be deployed. This cumulative package therefore contains both:

1. the unapplied V2 curriculum/checkpoint/capstone additions originally prepared in Patch 037, and
2. the new teaching-to-evaluation contract correction exposed by the completed `mlf_019` attempt.

Do not apply the earlier Patch 037 zip or its SQL separately. Use this package only.

## What was wrong in `mlf_019`

The lesson taught the principle: explanation shows model reliance, not causality. The final evaluation then expected deeper architecture workflow detail that had not been taught visibly. It also penalised Q2 using a generic request for a metric/calculation even though the humidity scenario contained no numeric task.

That is a product defect. The learner should be judged against a visible contract plus any technically unsafe claims they personally make, not hidden post-evaluation standards.

## Contract alignment added

### Visible lesson contract

Blueprint-backed lessons now expose an assessment contract before missions. For `mlf_019`, the learner now sees explicitly:

- Q2 requires valid conclusion, invalid conclusion, evidence check, and safe action.
- Q2 does **not** require an invented metric or calculation.
- High SHAP importance does not prove a feature is safe, non-leaky, stable, or mandatory in production.
- Q4 requires the governance chain: trigger, logged evidence, owner, approval/action, and monitoring.
- The audit trail must include model version, input/data slice, prediction, explanation, timestamp, reviewer, and decision.

### UI

The Learn tab now displays `Assessment Contract: What You Will Actually Be Scored On`.
The Mission Readiness Map now displays:

- required demonstration,
- what is not required,
- unsafe conclusion to avoid,
- mission-specific guidance.

### Verify Draft

Verify Draft now catches the exact issues in the learner's `mlf_019` answers before final evaluation:

- Q2: treating feature importance as a reason humidity should be retained in production.
- Q4: describing global explanation as overall model performance.
- Q4: naming an audit trail without the stored decision context and named ownership taught in the contract.

Replaying the submitted answer set now produces Q1=4, Q2=3, Q3=4, Q4=3, Q5=4, with a recommendation to improve partial drafts rather than falsely promising a 4-star submission.

### Final evaluator and coaching

- Final evaluation receives the visible teaching contract in its blueprint payload.
- It is instructed not to invent unstated metric, calculation, or workflow requirements.
- For scenario-only hands-on questions with no numbers, it must judge conclusion, invalid conclusion, evidence and safe action.
- Coaching no longer tells the learner to add a calculation to the non-numeric humidity question.
- Coaching now names the actual Q2 feature-retention error and Q4 governance/behaviour-vs-performance errors.

## V2 curriculum included from the unapplied Patch 037 work

Sequence after `mlf_020`:

1. `mlf_021` . Validation under time, group, and leakage constraints
2. `mlf_022` . Hyperparameter tuning without fooling yourself
3. `mlf_023` . ROC, PR curves, and operating points
4. `mlf_024` . Probability calibration and confidence
5. `mlf_025` . Data quality, label quality, and sampling bias
6. `checkpoint_ml_architect_001` . Checkpoint 2: ML Architect Readiness Review
7. `capstone_ml_architect_001` . Capstone: Predictive Quality ML Architecture

The contract framework is generated for the new V2 blueprint-backed items as well, so new lessons do not silently recreate the same teaching/evaluation mismatch.

## V2 Code Labs included

- `mlf_020`: monitor feature mean shift.
- `mlf_021`: group-holdout validation split.
- `mlf_022`: candidate selection under latency constraint.
- `mlf_023`: metrics at an operating threshold.
- `mlf_024`: Brier score.
- `mlf_025`: label disagreement rate.
- `checkpoint_ml_architect_001`: two-function precision/recall/F1 plus threshold policy lab.
- `capstone_ml_architect_001`: risk-action deployment policy with manual-review fallback.

Additional fix found during validation: the checkpoint threshold exercise requires safe use of `sorted()` and `set()`. The sandbox now allows those safe built-ins. Without this correction, valid learner code for the supplied task could fail at runtime.

## Deployment order

Your operational path remains Supabase + GitHub + Streamlit Cloud. Local execution is validation only.

1. Extract this patch into the GitHub repository root, replacing/adding the included files.
2. Commit and push the code changes. Wait for Streamlit Cloud deployment to complete successfully.
3. Run `supabase/sql/038_cumulative_v2_ml_architect_completion_teaching_contract.sql` in Supabase SQL Editor.
4. Check the verification result at the end of the SQL: new curriculum records should exist at sequence 22 through 28 and begin locked.
5. Continue to `mlf_020`, or use Redo on `mlf_019` to experience the corrected teaching contract.

**Do not run the old Patch 037 SQL. Do not apply both patch zips.**

## Supabase impact

The SQL is additive:

- permits the `capstone` item type,
- inserts/updates the seven new curriculum rows,
- creates missing progress rows for new items as locked,
- does not modify historical runs, artifacts, rewards, or completed progress.

The `mlf_019` content correction requires no database rewrite. New lesson or redo runs will persist the corrected contract artifacts from the deployed code. Existing historical artifacts remain preserved as evidence of the previous attempt.

## Validation completed

- `python -m compileall -q app.py src` passed.
- `mlf_019` contract appears in tutor narrative and Mission Readiness Map payload.
- Replayed learner answer set no longer verifies as 4-star ready: Q2 and Q4 are correctly flagged before submission.
- Q2 coaching no longer demands a metric/calculation for a non-numeric scenario.
- V2 contract payload exists for `mlf_021` through `mlf_025`, the checkpoint, and capstone.
- All eight new/extended Code Labs passed visible and hidden tests, including the two-function checkpoint and capstone exception guardrail.

## Files in this cumulative patch

- `app.py`
- `topics/topic_catalog.json`
- `topics/topic_unlock_rules.json`
- `src/agents/answer_coach.py`
- `src/agents/draft_verifier.py`
- `src/agents/evaluator_refiner.py`
- `src/agents/lesson_booster.py`
- `src/agents/tutor_narrative.py`
- `src/blueprints/advanced_ml.py`
- `src/blueprints/ml_architect_completion.py`
- `src/checkpoints/checkpoint_bank.py`
- `src/evaluate_lesson.py`
- `src/practice/exercise_bank.py`
- `src/practice/v2_exercise_bank.py`
- `src/prompts.py`
- `src/utils/cloud_run_cache.py`
- `src/utils/code_runner.py`
- `src/utils/curriculum_catalog.py`
- `supabase/sql/038_cumulative_v2_ml_architect_completion_teaching_contract.sql`
- `docs/PATCH_038_CUMULATIVE_V2_TEACHING_CONTRACT_ALIGNMENT.md`
