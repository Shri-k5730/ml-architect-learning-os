# Patch 002 . Coaching and Verify Draft Upgrade

## Purpose

This patch fixes the weak learning loop in V1 before expanding V2 further.

The previous coaching flow had two problems:

1. Final coaching sometimes used generic mission-type answers instead of topic-specific answers.
2. The learner had no way to check a draft before final evaluation.

This patch introduces a copy-safe `Verify Draft` stage and topic-grounded coaching for the first problem topics.

## What changed

### 1. Added `Verify Draft`

Current Level now has three actions:

- `Save Answers`
- `Verify Draft`
- `Save + Evaluate`

`Verify Draft` saves the current answers and generates a copy-safe review:

- likely score per question
- weak/partial/strong draft verdict
- missing points
- possible misconception detection
- next improvement

It deliberately does **not** show a full better answer before final evaluation.

### 2. Better answers are hidden after final evaluation

The Last Evaluation tab now shows coaching by question, but the stronger answer is inside a collapsed section:

`Show stronger sample answer`

This reduces accidental copy-paste behavior.

### 3. Topic-grounded coaching profiles

New file:

```text
src/agents/topic_coaching_profiles.py
```

Currently includes strong profiles for:

- `mlf_008` . Bias vs variance
- `mlf_009` . Why accuracy can lie

The profile defines:

- core concepts
- common misconceptions
- topic-specific golden answers by question type
- practical checks

This prevents bias-variance from getting generic generalization coaching.

### 4. Evidence-bound findings

Final coaching can now show findings like:

```text
Evidence: `high variance in temperature values`
Issue: This confuses feature variance with model variance.
Correction: Model variance means prediction instability caused by sensitivity to training data, not merely spread in one feature.
```

### 5. Teacher and assessor prompts tightened

`src/prompts.py` now tells the teacher and assessor to:

- avoid repeating the same point across every field
- include numeric or operational examples where possible
- make tiny hands-on missions require a number, metric comparison, table interpretation, or decision
- penalize polished generic answers that miss the question-specific practical point

## Files included

```text
app.py
src/agents/answer_coach.py
src/agents/draft_verifier.py
src/agents/topic_coaching_profiles.py
src/prompts.py
docs/PATCH_002_COACHING_AND_VERIFY_DRAFT.md
```

## Apply

Unzip into repo root, replacing files.

```bash
git checkout -b v2-coaching-verify-draft
python -m compileall app.py src
git add app.py src docs
git commit -m "Add copy-safe draft verification and topic-grounded coaching"
git push
```

## How to test

1. Start or continue a lesson.
2. Write intentionally weak answers.
3. Click `Verify Draft`.
4. Confirm it gives hints, not full better answers.
5. Fix answers.
6. Click `Save + Evaluate`.
7. Open Last Evaluation.
8. Confirm stronger answers are collapsed and coaching is topic-specific.

## Important note

This patch does not change the Supabase schema.

It writes a new artifact type when Supabase is enabled:

```text
draft_verification
```

It also emits a new event type:

```text
draft_verified
```

Both use existing tables.
