# Patch 027 . MCQ Engine Hardening

## Why this patch exists

The pre-mission MCQs were still weak after Patch 026:

- correct answer often appeared as option A
- some distractors were obviously silly
- the UI could show `Check Check`
- MCQs tested recall more than judgment

This patch hardens the MCQ layer without touching scoring, rewards, Supabase schema, or lesson state.

## What changed

### 1. Deterministic option shuffling

`src/agents/mcq_quality.py` now shuffles options using a stable hash of:

```text
topic_id + question_index + question_text
```

This means:

- answer position is no longer predictably A
- options do not reshuffle on every Streamlit rerun
- learner selections remain stable during a session

### 2. Stronger MCQ bank

Checkpoint and `mlf_011` to `mlf_020` now use more scenario-based questions and plausible distractors.

Bad distractor style removed:

```text
Dashboard count
SQL queries
Alphabetical order
Stakeholder seniority
```

Better distractor style added:

```text
underfitting vs overfitting
leakage vs metric trade-off
fit vs transform confusion
business threshold vs model score
segment failure vs aggregate score
```

### 3. Wrong-answer diagnostics

Each option can carry its own explanation. Wrong answers should explain the misconception without revealing the correct option.

### 4. UI title fix

The renderer now avoids `Check Check 1` by formatting MCQ titles consistently.

## Files changed

```text
app.py
src/agents/mcq_quality.py
docs/PATCH_027_MCQ_ENGINE_HARDENING.md
```

## Supabase

No Supabase changes required.

## Validation

Run:

```bash
python -m compileall app.py src
python - <<'PY'
from src.agents.mcq_quality import get_quality_mcqs
for i, item in enumerate(get_quality_mcqs('mlf_015'), start=1):
    print(i, item['answer_index'], item['options'][item['answer_index']])
PY
```

The correct answer should no longer always be index `0`.
