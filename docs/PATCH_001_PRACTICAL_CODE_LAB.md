# Patch 001 . Practical Code Lab

## What this patch adds

This patch adds the first V2 practical exercise path without disrupting the V1 lesson flow.

Target topic:

- `mlf_009` . Why accuracy can lie

New learner task:

- implement `calculate_accuracy(y_true, y_pred)`
- run visible and hidden tests
- explain why high accuracy can be misleading in production

## New files

- `src/practice/__init__.py`
- `src/practice/exercise_bank.py`
- `src/utils/code_runner.py`
- `docs/V2_ROADMAP.md`
- `docs/PATCH_001_PRACTICAL_CODE_LAB.md`

## Updated files

- `app.py`
- `src/start_lesson.py`
- `src/evaluate_lesson.py`
- `src/schemas.py`
- `src/agents/evaluator_refiner.py`
- `src/prompts.py`

## New artifacts created during a lesson

At lesson start:

- `runs/<run_id>/practice_exercise.json`
- `assessments/answers/<run_id>_practice_submission.json`

At evaluation:

- `runs/<run_id>/practice_result.json`
- `runs/<run_id>/practice_coaching.json`

Supabase artifact types:

- `practice_exercise`
- `practice_submission_template`
- `practice_submission`
- `practice_result`
- `practice_coaching`

## Practical gate

If code tests fail:

- practical reasoning is capped at 2
- lesson decision is forced to `revise`
- next action is forced to `retry_same_topic`

If code passes but interpretation is weak:

- practical reasoning is capped at 3
- `pass` is downgraded to `borderline`

## How to apply

Replace the files from this patch into the repo, then run:

```bash
python -m compileall app.py src
```

Then commit:

```bash
git add app.py src docs
git commit -m "Add V2 practical code lab foundation"
git push
```

## How to test

Start or manually run topic `mlf_009`:

```bash
python -m src.start_lesson --topic_id mlf_009
```

Open Current Level in Streamlit. You should see a new Code Lab panel under the written mission responses.
