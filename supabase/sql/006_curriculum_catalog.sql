-- Patch 006 . Supabase-native curriculum catalog and learner progress
-- Run this once in Supabase SQL Editor before deploying Patch 006.

create table if not exists public.mlos_topic_catalog (
  topic_id text primary key,
  title text not null,
  domain text not null,
  module_id text not null,
  sequence_no integer not null unique,
  item_type text not null default 'lesson' check (item_type in ('lesson', 'checkpoint')),
  difficulty integer not null default 1,
  prerequisites jsonb not null default '[]'::jsonb,
  unlock_after text,
  architect_relevance jsonb not null default '[]'::jsonb,
  tags jsonb not null default '[]'::jsonb,
  is_active boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists idx_mlos_topic_catalog_sequence on public.mlos_topic_catalog(sequence_no);
create index if not exists idx_mlos_topic_catalog_active on public.mlos_topic_catalog(is_active);

create table if not exists public.mlos_learner_progress (
  topic_id text primary key references public.mlos_topic_catalog(topic_id) on delete cascade,
  status text not null default 'locked',
  attempt_count integer not null default 0,
  last_run_id text,
  last_decision text,
  last_score_conceptual integer,
  last_score_practical integer,
  last_score_architect integer,
  last_score_communication integer,
  last_score_coding integer,
  completed_at timestamptz,
  last_attempted_at timestamptz,
  updated_at timestamptz not null default now()
);

create index if not exists idx_mlos_learner_progress_status on public.mlos_learner_progress(status);


insert into public.mlos_topic_catalog
(topic_id, title, domain, module_id, sequence_no, item_type, difficulty, prerequisites, unlock_after, architect_relevance, tags, is_active)
values
  ('mlf_001', 'What machine learning is actually learning', 'machine_learning_fundamentals', 'module_001_ml_foundations', 1, 'lesson', 1, '[]'::jsonb, null, '["generalization", "data_dependency", "model_risk"]'::jsonb, '["learning", "patterns", "prediction", "generalization"]'::jsonb, true),
  ('mlf_002', 'Features vs labels', 'machine_learning_fundamentals', 'module_001_ml_foundations', 2, 'lesson', 1, '["mlf_001"]'::jsonb, 'mlf_001', '["data_contracts", "feature_quality", "label_definition"]'::jsonb, '["features", "labels", "supervised_learning", "data_design"]'::jsonb, true),
  ('mlf_003', 'Training data vs test data', 'machine_learning_fundamentals', 'module_001_ml_foundations', 3, 'lesson', 1, '["mlf_002"]'::jsonb, 'mlf_002', '["evaluation_discipline", "data_split_strategy", "deployment_readiness"]'::jsonb, '["train_test_split", "evaluation", "generalization", "validation"]'::jsonb, true),
  ('mlf_004', 'What a baseline really is', 'machine_learning_fundamentals', 'module_001_ml_foundations', 4, 'lesson', 1, '["mlf_003"]'::jsonb, 'mlf_003', '["benchmarking", "solution_justification", "cost_vs_complexity"]'::jsonb, '["baseline", "benchmark", "model_comparison", "decision_quality"]'::jsonb, true),
  ('mlf_005', 'Generalization', 'machine_learning_fundamentals', 'module_001_ml_foundations', 5, 'lesson', 2, '["mlf_004"]'::jsonb, 'mlf_004', '["production_reliability", "distribution_shift", "model_confidence"]'::jsonb, '["generalization", "unseen_data", "robustness", "reliability"]'::jsonb, true),
  ('mlf_006', 'Overfitting vs underfitting', 'machine_learning_fundamentals', 'module_001_ml_foundations', 6, 'lesson', 2, '["mlf_005"]'::jsonb, 'mlf_005', '["model_selection", "capacity_control", "error_diagnosis"]'::jsonb, '["overfitting", "underfitting", "bias_variance", "model_behavior"]'::jsonb, true),
  ('mlf_007', 'Data leakage', 'machine_learning_fundamentals', 'module_001_ml_foundations', 7, 'lesson', 2, '["mlf_006"]'::jsonb, 'mlf_006', '["evaluation_failure", "feature_pipeline_design", "governance_risk"]'::jsonb, '["data_leakage", "leakage", "invalid_evaluation", "pipeline_risk"]'::jsonb, true),
  ('mlf_008', 'Bias vs variance', 'evaluation_and_metrics', 'module_001_ml_foundations', 8, 'lesson', 2, '["mlf_007"]'::jsonb, 'mlf_007', '["model_tradeoffs", "capacity_tuning", "error_pattern_analysis"]'::jsonb, '["bias", "variance", "tradeoff", "error_analysis"]'::jsonb, true),
  ('mlf_009', 'Why accuracy can lie', 'evaluation_and_metrics', 'module_001_ml_foundations', 9, 'lesson', 2, '["mlf_008"]'::jsonb, 'mlf_008', '["metric_selection", "business_alignment", "false_confidence"]'::jsonb, '["accuracy", "metrics", "class_imbalance", "evaluation_risk"]'::jsonb, true),
  ('mlf_010', 'Precision vs recall', 'evaluation_and_metrics', 'module_001_ml_foundations', 10, 'lesson', 2, '["mlf_009"]'::jsonb, 'mlf_009', '["threshold_design", "cost_of_errors", "stakeholder_tradeoffs"]'::jsonb, '["precision", "recall", "false_positives", "false_negatives"]'::jsonb, true),
  ('checkpoint_ml_foundations_001', 'Checkpoint 1: ML Foundations Review', 'module_checkpoint', 'module_001_checkpoint', 11, 'checkpoint', 3, '["mlf_010"]'::jsonb, 'mlf_010', '["cross_topic_synthesis", "metric_decision_quality", "production_readiness_review"]'::jsonb, '["checkpoint", "ml_foundations", "evaluation", "practical_review", "architecture_readiness"]'::jsonb, true),
  ('mlf_011', 'Model selection and validation strategy', 'advanced_machine_learning', 'module_002_advanced_ml', 12, 'lesson', 3, '["checkpoint_ml_foundations_001"]'::jsonb, 'checkpoint_ml_foundations_001', '["model_selection", "validation_design", "offline_to_online_risk"]'::jsonb, '["validation", "cross_validation", "holdout", "model_selection"]'::jsonb, true),
  ('mlf_012', 'Feature engineering and feature contracts', 'advanced_machine_learning', 'module_002_advanced_ml', 13, 'lesson', 3, '["mlf_011"]'::jsonb, 'mlf_011', '["feature_design", "data_contracts", "pipeline_reliability"]'::jsonb, '["feature_engineering", "feature_store", "data_contracts", "schema"]'::jsonb, true),
  ('mlf_013', 'Encoding categorical variables safely', 'advanced_machine_learning', 'module_002_advanced_ml', 14, 'lesson', 3, '["mlf_012"]'::jsonb, 'mlf_012', '["categorical_encoding", "production_schema_drift", "unseen_categories"]'::jsonb, '["one_hot_encoding", "target_encoding", "categorical_features", "unseen_categories"]'::jsonb, true),
  ('mlf_014', 'Scaling, normalization, and pipeline leakage', 'advanced_machine_learning', 'module_002_advanced_ml', 15, 'lesson', 3, '["mlf_013"]'::jsonb, 'mlf_013', '["preprocessing_pipeline", "leakage_control", "training_serving_consistency"]'::jsonb, '["scaling", "normalization", "standardization", "pipeline_leakage"]'::jsonb, true),
  ('mlf_015', 'Regularization: controlling model complexity', 'advanced_machine_learning', 'module_002_advanced_ml', 16, 'lesson', 3, '["mlf_014"]'::jsonb, 'mlf_014', '["capacity_control", "overfitting_control", "model_robustness"]'::jsonb, '["regularization", "l1", "l2", "complexity", "generalization"]'::jsonb, true),
  ('mlf_016', 'Threshold tuning and cost-sensitive decisions', 'advanced_machine_learning', 'module_002_advanced_ml', 17, 'lesson', 3, '["mlf_015"]'::jsonb, 'mlf_015', '["threshold_design", "cost_of_errors", "business_decision_alignment"]'::jsonb, '["threshold", "precision_recall_tradeoff", "cost_sensitive", "classification"]'::jsonb, true),
  ('mlf_017', 'Class imbalance handling strategies', 'advanced_machine_learning', 'module_002_advanced_ml', 18, 'lesson', 3, '["mlf_016"]'::jsonb, 'mlf_016', '["imbalanced_learning", "sampling_strategy", "minority_class_reliability"]'::jsonb, '["class_imbalance", "resampling", "class_weights", "rare_events"]'::jsonb, true),
  ('mlf_018', 'Error analysis and model debugging', 'advanced_machine_learning', 'module_002_advanced_ml', 19, 'lesson', 3, '["mlf_017"]'::jsonb, 'mlf_017', '["error_slicing", "debugging_workflow", "failure_taxonomy"]'::jsonb, '["error_analysis", "model_debugging", "slices", "failure_modes"]'::jsonb, true),
  ('mlf_019', 'Model interpretability and explainability limits', 'advanced_machine_learning', 'module_002_advanced_ml', 20, 'lesson', 3, '["mlf_018"]'::jsonb, 'mlf_018', '["explainability", "governance", "stakeholder_trust", "model_risk"]'::jsonb, '["interpretability", "explainability", "shap", "feature_importance"]'::jsonb, true),
  ('mlf_020', 'ML monitoring: drift, performance, and retraining triggers', 'advanced_machine_learning', 'module_002_advanced_ml', 21, 'lesson', 3, '["mlf_019"]'::jsonb, 'mlf_019', '["monitoring_architecture", "drift_detection", "retraining_policy", "production_governance"]'::jsonb, '["monitoring", "data_drift", "concept_drift", "retraining", "model_ops"]'::jsonb, true)

on conflict (topic_id) do update set
  title = excluded.title,
  domain = excluded.domain,
  module_id = excluded.module_id,
  sequence_no = excluded.sequence_no,
  item_type = excluded.item_type,
  difficulty = excluded.difficulty,
  prerequisites = excluded.prerequisites,
  unlock_after = excluded.unlock_after,
  architect_relevance = excluded.architect_relevance,
  tags = excluded.tags,
  is_active = excluded.is_active,
  updated_at = now();

-- Seed progress rows for any catalog item that does not yet have progress.
insert into public.mlos_learner_progress (topic_id, status, attempt_count)
select
  topic_id,
  case when sequence_no = 1 then 'not_started' else 'locked' end as status,
  0 as attempt_count
from public.mlos_topic_catalog
where is_active = true
on conflict (topic_id) do nothing;
