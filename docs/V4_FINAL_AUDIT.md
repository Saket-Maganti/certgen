# CertGen V4 Final Audit

Summary: `passed`

`NO_REAL_EVIDENCE`

Checks passed: `27/27`
Evidence status: `dry_run_only`
Claim allowed: `false`

| Check | Status | Detail |
|---|---:|---|
| `package_imports_as_v4` | `pass` | 0.4.0 |
| `v4_state_intake_audit_exists` | `pass` | 99/99 checks |
| `provenance_to_real_run_planner_exists` | `pass` | ['provenance_status must be verified', 'sample license not verified free/allowed', 'sample_count_available_a below requested budget', 'sample_count_available_b below requested budget', 'reported preprocessing is unknown'] |
| `feature_notebook_generator_exists` | `pass` | generated Kaggle script |
| `preprocessing_lock_validator_exists` | `pass` | strict lock valid |
| `metric_reproduction_gate_exists` | `pass` | not_applicable_no_expected_value |
| `batch_certificate_runner_exists` | `pass` | 2 rows |
| `multiple_comparison_policy_exists` | `pass` | {'policy': 'bonferroni', 'alpha_used': 0.01, 'adjusted_for_multiplicity': True, 'claim_allowed': False} |
| `dependence_diagnostics_exist` | `pass` | {'v4_smoke_a_close_vs_b_far': ['feature cache reused: data/smoke/v4/audit/features/reference.npz', 'overlapping reference samples/cache reused'], 'v4_smoke_equal_models': ['feature cache reused: data/smoke/v4/audit/features/reference.npz', 'overlapping reference samples/cache reused']} |
| `decidedness_audit_exists` | `pass` | {'undecided_at_budget': 2} |
| `ranking_stability_report_exists` | `pass` | 2 undecided |
| `first_real_pilot_controller_exists` | `pass` | supply validated real feature caches |
| `literature_claim_ingestion_exists` | `pass` | 1 template trace |
| `paper_figure_table_scaffold_exists` | `pass` | figures/tables spec generated |
| `cvpr_paper_scaffold_exists` | `pass` | paper/main.tex, paper/sections/introduction.tex, docs/CVPR_PAPER_SCAFFOLD_V4.md, docs/RELATED_WORK_TASK_BOARD_V4.md |
| `claim_language_audit_exists` | `pass` | selected V4 docs are claim-safe |
| `reviewer_attack_harness_exists` | `pass` | 15 attacks |
| `reproducibility_capsule_validator_exists` | `pass` | capsule requirements present |
| `release_safety_scan_exists` | `pass` | ['unknown license present in template: registry/reported_metric_claims_v4_template.csv', 'unknown license present in template: registry/released_sample_ledger_template.csv', 'unknown license present in template: registry/reported_metric_claims_v4_smoke.csv', 'unknown license present in template: registry/provenance/released_sample_ledger_template.csv', 'unknown license present in template: registry/provenance/v4_plan_ledger_template.csv', 'unknown license present in template: registry/v3/benchmarks_template.csv', 'unknown license present in template: registry/v3/model_pairs_template.csv', 'unknown license present in template: registry/v3/feature_caches_template.csv', 'unknown license present in template: registry/templates/candidate_model_pairs_template.csv'] |
| `fid_policy_remains_descriptive` | `pass` | rigorous FID claim rejected |
| `smoke_synthetic_artifacts_non_claim` | `pass` | no claim promotion found |
| `no_result_claims_without_real_evidence` | `pass` | no unguarded result claims |
| `pytest_passes_or_failure_recorded` | `pass` | 89 passed, 3 skipped in 0.42s |
| `command_index_updated` | `pass` | docs/COMMAND_INDEX_V4.md |
| `handoff_summarizes_blockers` | `pass` | docs/V4_SINGLE_FILE_HANDOFF.md |
| `next_v5_action_concrete` | `pass` | populate one real provenance ledger with verified released sample/model-pair rows, materialize or validate real feature caches, reproduce one reported metric point estimate, and run the first real clean-core pilot in non-claim mode to measure the first-benchmark undecided fraction |
| `audit_has_at_least_25_checks` | `pass` | 27 checks |

## Blockers
- none

## Warnings
- unknown license present in template: registry/reported_metric_claims_v4_template.csv
- unknown license present in template: registry/released_sample_ledger_template.csv
- unknown license present in template: registry/reported_metric_claims_v4_smoke.csv
- unknown license present in template: registry/provenance/released_sample_ledger_template.csv
- unknown license present in template: registry/provenance/v4_plan_ledger_template.csv
- unknown license present in template: registry/v3/benchmarks_template.csv
- unknown license present in template: registry/v3/model_pairs_template.csv
- unknown license present in template: registry/v3/feature_caches_template.csv
- unknown license present in template: registry/templates/candidate_model_pairs_template.csv

## Exact Next V5 Action

populate one real provenance ledger with verified released sample/model-pair rows, materialize or validate real feature caches, reproduce one reported metric point estimate, and run the first real clean-core pilot in non-claim mode to measure the first-benchmark undecided fraction
