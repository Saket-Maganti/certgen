# CertGen V2 Final Audit

Audit status: `passed`

| Check | Status | Detail |
|---|---:|---|
| `pytest_suite_passes` | `pass` | 65 passed, 1 skipped in 0.38s |
| `clean_core_stream_code_exists` | `pass` | MMD difference stream imports and follows direction |
| `cs_implementation_exists` | `pass` | time_uniform_hoeffding_union_bound_v2 |
| `certificate_api_exists` | `pass` | not_decided_at_budget |
| `optional_stopping_lab_exists` | `pass` | module importable |
| `feature_cache_schema_exists` | `pass` | 20 required fields |
| `registry_v2_fields_exist` | `pass` | V2 registry template present |
| `first_pilot_v2_planner_exists` | `pass` | module importable |
| `fid_rigorous_claims_blocked` | `pass` | rigorous FID flag rejected |
| `smoke_artifacts_cannot_become_evidence` | `pass` | real_evidence_candidate is blocked in smoke mode |
| `certificate_reports_warn_not_evidence` | `pass` | certificate card warning present |
| `no_forbidden_v2_claim_phrases` | `pass` | selected V2 docs are claim-safe |
| `heavy_dependencies_optional_lazy` | `pass` | not imported: torch, torchvision, transformers, timm |
| `no_gpu_command_in_tests` | `pass` | tests do not invoke GPU/CUDA |
| `handoff_states_no_real_evidence` | `pass` | handoff contains no-real-evidence label |
