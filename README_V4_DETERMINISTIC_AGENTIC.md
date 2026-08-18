# MLOS V4.0 Deterministic Agentic Tutor and Assessment

## Why this version exists

The previous normal-agentic lesson flow had two failure modes at the same time:

1. Generic MCQs could be solved by visual cues such as selecting the longest, most detailed option.
2. The LLM evaluator sometimes claimed that a risk or control was missing even when the learner had explicitly written one.

V4 removes those failure modes from the normal Agentic AI lessons.

## Architecture

For `aia_001` through `aia_010`:

- Curriculum content is repository-authored and deterministic.
- Each lesson has 10 authored MCQs with plausible distractors.
- MCQ answer positions are still deterministically shuffled per run.
- Each lesson has one 80-140 word written response.
- The written response is graded only against a published rubric stored with the lesson.
- The grader records the exact learner sentence used as evidence for each criterion.
- No LLM is used as the final grader for these normal Agentic AI lessons.
- LLM functionality remains available for legacy/deeper evaluation paths and optional coaching where appropriate.

The local V4 Agentic AI design intentionally overrides older Supabase agentic learning-design rows at runtime. This prevents a stale database row from bringing the old giveaway MCQs back.

## Published normal lesson gate

A normal authored Agentic AI lesson requires:

- all displayed MCQs answered;
- MCQ score >= 70%;
- all critical MCQs correct;
- written response demonstrates the four published requirements:
  - mechanism;
  - concrete example;
  - one specific risk;
  - one implementable control.

Optional evidence such as a tool boundary, evidence-per-step, stop condition or escalation can improve displayed scores, but it cannot replace a missing required criterion.

## AIA_004 fairness check

The previous AIA_004 answer supplied in the August 2026 evaluation is now recognized as containing:

- planning mechanism;
- procurement example;
- unauthorised-information risk;
- human-approval/read-only control.

Under V4 it passes the written rubric. The evaluator no longer claims those elements are absent.

## MCQ quality

V4 removes the generic MCQ-padding behavior that produced questions such as:

- "Only a vendor name"
- "A longer prompt"
- "Only a demo video"

Agentic lessons now have ten authored questions each. For older non-agentic lesson banks, V4 prefers fewer authored questions to low-quality generic filler.

## Single learning-design resolver

All runtime components now use `src/utils/learning_design_registry.py`.

This prevents the teacher, booster, verifier, evaluator and coach from independently choosing different lesson-design versions.

## Active-run safety

The earlier active-run fix remains in place. A newly started repair run is not hidden merely because an older attempt achieved historical mastery.

The V4 MCQ payload also has a bank fingerprint. When an active run survives a deployment but its MCQ bank changes, old MCQ selections are reset instead of being mapped onto new questions.

## Deployment

1. Commit or tag the current repository before replacement.
2. Replace the repository with this corrected codebase.
3. Push to the GitHub branch used by Streamlit Cloud.
4. Let Streamlit redeploy.
5. In Supabase SQL Editor, run only:
   `supabase/sql/040_v4_deterministic_agentic_assessment.sql`
6. Refresh the Streamlit app.
7. Continue the existing AIA_004 repair attempt. Do not create another repair run unless the existing one is explicitly abandoned.

`supabase/sql/99_RUN_V4_FIX.sql` is an identical convenience copy of the V4 migration.

## Historical data

The migration does not rewrite old evaluations, rewards, runs or learner progress. Historical records remain historical evidence.

New evaluations use the V4 architecture.

## Validation performed

- Python compile check for `app.py`, `src`, and tests.
- Unit tests for active/mastery policy and V4 deterministic grading.
- Agentic curriculum tests:
  - 10 Agentic AI topics;
  - 10 authored MCQs per topic;
  - no known giveaway filler options;
  - balanced correct-answer positions after per-run shuffle;
  - "choose the longest option" is not a reliable answer strategy;
  - the previously rejected AIA_004 answer passes its published rubric;
  - an AIA_004 answer genuinely missing risk evidence does not pass.
