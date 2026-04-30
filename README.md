# ML Architect Learning OS . V1

A focused learning loop for becoming an ML Architect.

## What it does
- starts the next unlocked lesson
- generates a concept note
- generates an architect lens note
- generates assessment questions
- captures your answers
- evaluates your answers
- updates progress and unlocks the next topic

## Core files
- `app.py` . Streamlit UI
- `src/start_lesson.py` . creates the next lesson
- `src/evaluate_lesson.py` . evaluates the current lesson
- `config/learner_profile.yaml`
- `config/model_config.yaml`
- `config/scoring_rubric.yaml`
- `topics/topic_catalog.json`
- `data/progress_tracker.csv`

## Setup
1. Create and activate a virtual environment.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Set your OpenAI key in the shell:
   ```powershell
   $env:OPENAI_API_KEY="your_key_here"
   ```

## Run
```bash
streamlit run app.py
```

## Loop
1. Click **Start Next Lesson**.
2. Read the concept and architect lens.
3. Write your answers.
4. Click **Save + Evaluate**.
5. Repeat.

## Scope of V1
V1 keeps the pipeline simple.
- live teacher
- live architect lens
- live assessor
- live evaluator
- no TinyLlama wiring yet
- no public publishing
- no background automations

## Notes
- Runtime artifacts are written under `runs/`.
- Generated notes and evaluations are written under `notes/` and `assessments/`.
- Progress is tracked in `data/progress_tracker.csv`.
