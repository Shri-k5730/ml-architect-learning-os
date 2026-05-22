-- Patch 038 CUMULATIVE . V2 ML Architect completion block, readiness checkpoint, capstone, and teaching-contract alignment
-- Execute in Supabase SQL Editor only after the cumulative Patch 038 code has deployed successfully through GitHub to Streamlit Cloud.
-- This migration is additive. It does not change prior run, artifact, reward, or completed-progress records.
-- The mlf_019 teaching-contract fix is code-based; a new Redo run will persist the corrected lesson artifacts without rewriting old evidence.

begin;

-- A capstone is a first-class curriculum item rather than pretending to be an ordinary lesson.
alter table public.mlos_topic_catalog
  drop constraint if exists mlos_topic_catalog_item_type_check;

alter table public.mlos_topic_catalog
  add constraint mlos_topic_catalog_item_type_check
  check (item_type in ('lesson', 'checkpoint', 'capstone'));

insert into public.mlos_topic_catalog
(topic_id, title, domain, module_id, sequence_no, item_type, difficulty, prerequisites, unlock_after, architect_relevance, tags, is_active)
values
  ('mlf_021', 'Validation under time, group, and leakage constraints', 'ml_architect_completion', 'module_003_ml_architect_completion', 22, 'lesson', 4,
   '["mlf_020"]'::jsonb, 'mlf_020',
   '["validation_architecture","temporal_validation","group_leakage_control","approval_evidence"]'::jsonb,
   '["cross_validation","time_split","group_split","leakage","validation"]'::jsonb, true),

  ('mlf_022', 'Hyperparameter tuning without fooling yourself', 'ml_architect_completion', 'module_003_ml_architect_completion', 23, 'lesson', 4,
   '["mlf_021"]'::jsonb, 'mlf_021',
   '["experiment_governance","model_selection","locked_test_evidence","cost_control"]'::jsonb,
   '["hyperparameter_tuning","search_budget","nested_validation","experiment_tracking"]'::jsonb, true),

  ('mlf_023', 'ROC, PR curves, and operating points', 'ml_architect_completion', 'module_003_ml_architect_completion', 24, 'lesson', 4,
   '["mlf_022"]'::jsonb, 'mlf_022',
   '["operating_point_policy","threshold_governance","rare_event_decisions","alert_capacity"]'::jsonb,
   '["roc","precision_recall_curve","pr_auc","threshold","operating_point"]'::jsonb, true),

  ('mlf_024', 'Probability calibration and confidence', 'ml_architect_completion', 'module_003_ml_architect_completion', 25, 'lesson', 4,
   '["mlf_023"]'::jsonb, 'mlf_023',
   '["risk_scoring","calibration_assurance","decision_confidence","monitoring"]'::jsonb,
   '["calibration","brier_score","reliability_curve","confidence","risk_score"]'::jsonb, true),

  ('mlf_025', 'Data quality, label quality, and sampling bias', 'ml_architect_completion', 'module_003_ml_architect_completion', 26, 'lesson', 4,
   '["mlf_024"]'::jsonb, 'mlf_024',
   '["data_governance","label_quality","sampling_bias","release_gate"]'::jsonb,
   '["data_quality","label_quality","sampling_bias","proxy_labels","coverage"]'::jsonb, true),

  ('checkpoint_ml_architect_001', 'Checkpoint 2: ML Architect Readiness Review', 'module_checkpoint', 'module_003_checkpoint', 27, 'checkpoint', 5,
   '["mlf_025"]'::jsonb, 'mlf_025',
   '["cross_topic_synthesis","production_approval","architecture_governance","risk_control"]'::jsonb,
   '["checkpoint","ml_architect","readiness","scenario_assessment","code_lab"]'::jsonb, true),

  ('capstone_ml_architect_001', 'Capstone: Predictive Quality ML Architecture', 'ml_architect_capstone', 'module_004_capstone', 28, 'capstone', 5,
   '["checkpoint_ml_architect_001"]'::jsonb, 'checkpoint_ml_architect_001',
   '["end_to_end_architecture","predictive_quality","deployment_governance","portfolio_evidence"]'::jsonb,
   '["capstone","predictive_quality","model_card","adr","monitoring_plan"]'::jsonb, true)
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

-- New rows begin locked. Existing completed or active progress is not altered.
insert into public.mlos_learner_progress (topic_id, status, attempt_count)
select topic_id, 'locked', 0
from public.mlos_topic_catalog
where topic_id in (
  'mlf_021','mlf_022','mlf_023','mlf_024','mlf_025',
  'checkpoint_ml_architect_001','capstone_ml_architect_001'
)
on conflict (topic_id) do nothing;

commit;

-- Verification: the chain should display at sequence 22-28 and new progress should be locked
-- until predecessor completion unlocks each item.
select
  t.sequence_no,
  t.topic_id,
  t.item_type,
  t.unlock_after,
  p.status,
  p.attempt_count
from public.mlos_topic_catalog t
left join public.mlos_learner_progress p on p.topic_id = t.topic_id
where t.sequence_no >= 21
order by t.sequence_no;
