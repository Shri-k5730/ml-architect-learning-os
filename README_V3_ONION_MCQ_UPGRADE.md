# MLOS V3 Onion + MCQ-First Evaluation Upgrade

Changed-files-only bundle.

## What this version changes

1. Tutor quality
   - Learn tab stays concept-first.
   - MCQ/evaluator scaffolding is no longer treated as the tutor.
   - Normal lessons get deeper authored explanation through the existing `v23_tutor_quality` runtime enhancer.

2. Onion path
   - Adds a new architect-first AI path:
     - `aia_001` Agentic AI outer layer
     - `aia_002` Agent loop
     - `aia_003` Tools, memory, guardrails, human checkpoints
     - `genai_001` GenAI application architecture
     - `rag_001` RAG
     - `llm_001` Tokens, embeddings, context windows
     - `trf_001` Transformer intuition
   - This path starts from the outer system and peels downward.
   - It does not wait for every ML repair topic.

3. Evaluation criteria
   - Normal lessons become MCQ-first:
     - 10 scored MCQs
     - >= 70%
     - all critical MCQs correct
     - 1 short written answer
     - Code Lab where relevant
   - Checkpoints stay mixed.
   - Capstone stays architecture-case based.

## Deploy order

1. Extract at repo root.
2. Commit and push to GitHub.
3. Let Streamlit Cloud redeploy.
4. Run:
   `supabase/sql/v3_onion_mcq_evaluation/99_RUN_ALL_IN_ORDER.sql`
5. Refresh Streamlit.
6. For the current active lesson, answer/save scored MCQs, answer the one visible written task, then Save + Evaluate.

## Important

Existing active runs may have old 4-5 essay tasks in their saved answer template. V3 hides the extra normal-lesson tasks at runtime and evaluates only the V3 visible written task plus MCQs.
