# Patch 022 . Full Advanced ML Expert Blueprint System

This patch upgrades the teaching engine instead of fixing one lecture at a time.

## What changed

1. Adds full expert tutor blueprints for:
   - `checkpoint_ml_foundations_001`
   - `mlf_011` to `mlf_020`

2. Each blueprint now owns:
   - definition
   - plain intuition
   - why it exists
   - core mechanism
   - worked example
   - nuances
   - when it matters / matters less
   - common confusions
   - architect implications
   - system design controls
   - mission answer frame
   - do-not-overexplain guidance
   - MCQs
   - five missions

3. `src.start_lesson` now uses blueprint-generated content for Advanced ML topics.
   - Concept note
   - Architect lens
   - Assessment missions
   - Supabase lesson_blueprint artifact

4. The Current Level Learn tab now renders a tutor narrative from the blueprint.
   It is no longer just a template dump.

5. Study Booster, MCQs, Mission Readiness Map, Draft Verification, Evaluation payload,
   and Answer Coaching now receive the same blueprint context.

## Why this matters

Before this patch, the system had separate generators for teaching, missions,
verification, evaluation, and coaching. That caused mismatch:

- the lesson taught high-level concepts
- missions expected deeper architect reasoning
- evaluation penalized gaps that were not taught clearly

Patch 022 makes the blueprint the source of truth for Advanced ML.

## Important behavior

Existing active runs will display the new tutor narrative at runtime if their topic has a blueprint.
New runs for `mlf_011` to `mlf_020` will generate concept, architect, and assessment artifacts from the blueprint.

No Supabase SQL is required.

## Apply

```bash
git checkout -b v2-full-advanced-ml-blueprint-system
# unzip patch into repo root
python -m compileall app.py src

git add app.py src docs
git commit -m "Upgrade Advanced ML lessons to expert blueprint system"
git push
```

## Sanity check

Start a fresh Advanced ML topic after deployment. The run should include:

- `concept_note.json`
- `architect_note.json`
- `assessment.json`
- `lesson_blueprint.json`

The Learn tab should show:

- Start Here: The Intuition
- Precise Definition
- Why This Concept Exists
- Slow Walkthrough
- Worked Example
- Nuances
- Architect Translation
- System Design Controls
- Mission Answer Frame
- Do Not Waste Words On This
- Mission-by-Mission Prep
