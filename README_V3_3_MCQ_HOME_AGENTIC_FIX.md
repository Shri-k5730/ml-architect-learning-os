# MLOS V3.3 MCQ + Home Grouping + Agentic Extension

## Why this exists
V3.2 fixed the hardcoded 10-MCQ denominator, but exposed two more issues:

1. Streamlit radio buttons selected the first option by default, so a learner could appear to pass MCQs without intentionally answering.
2. Generated MCQs often placed the correct answer in the first option, creating answer-position leakage.
3. The Home page was a long flat list, while the curriculum now needs clear groups: Agentic AI, ML, DL and NN.

## Changed files

```text
app.py
src/utils/v3_assessment_policy.py
supabase/sql/v3_3_mcq_home_agentic_fix/99_RUN_ALL_IN_ORDER.sql
README_V3_3_MCQ_HOME_AGENTIC_FIX.md
```

## What changed

### MCQ gate fix
- MCQs now start with an explicit `Select an answer...` option.
- Unselected MCQs count as unanswered.
- The gate cannot pass unless every available MCQ has a real selected answer.
- MCQ options are deterministically shuffled, so the correct option is not always first.

### Homepage grouping
The Home level map is grouped into:

```text
Agentic AI / GenAI Onion Path
Machine Learning Repair Queue
Deep Learning Foundations
Neural Networks: Regularization and Deployment
```

### Agentic AI additions
The SQL adds:

```text
aia_004 Agent planning and task decomposition
aia_005 Tool calling, APIs and action boundaries
aia_006 Agent memory, retrieval and state
aia_007 Human checkpoints, approval and escalation
aia_008 Agent evaluation: task success, groundedness and safety
aia_009 Multi-agent orchestration and handoffs
aia_010 Production agent monitoring, cost and rollback
```

It also moves `genai_001`, `rag_001`, `llm_001`, and `trf_001` after the expanded agentic chain.

## Deploy

```text
1. Extract this ZIP at repo root.
2. Commit and push to GitHub.
3. Let Streamlit Cloud redeploy.
4. Run supabase/sql/v3_3_mcq_home_agentic_fix/99_RUN_ALL_IN_ORDER.sql in Supabase.
5. Refresh the app.
```

## Expected result
- MCQ screen should show `Answered 0/N` until you explicitly select answers.
- It should no longer pass automatically.
- Home should show grouped curriculum sections.
- Agentic AI path should extend to `aia_010` before GenAI/RAG/LLM/Transformer layers.
