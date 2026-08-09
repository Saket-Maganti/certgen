# environment diagnostic

| Field | Value |
|---|---|
| `purpose` | environment diagnostic |
| `prerequisite_state` | READY |
| `input_builder` | python3 -m certgen kaggle build-input --stage diagnostic --json |
| `input_ZIP` | artifacts/cvpr/kaggle_inputs/diagnostic/certgen_kaggle_environment_diagnostic_input.zip |
| `input_SHA256` | d9b056f220fdd3ef87d5a0c2b41df0d8012452f0f912cb2e378bbc8f764e718d |
| `package_type` | authenticated_stage_input_or_blocked_plan |
| `notebook` | notebooks/kaggle/certgen_kaggle_environment_diagnostic_t4x2.ipynb |
| `accelerator` | Kaggle T4 x2 |
| `GPU_count` | 2 |
| `internet_mode` | internet_on_for_dependencies; model/data assets authenticated separately |
| `dependency_profile` | exact stage lock plus restart marker |
| `private_assets` | required only where source/license/asset registry says so |
| `disk_expectation` | planner estimate; verify preflight before launch |
| `RAM_VRAM_expectation` | planner estimate; fail closed on preflight |
| `planning_runtime` | PLANNING_ESTIMATE_NOT_MEASURED |
| `restart_behavior` | resume deterministic completed shards; never mutate configuration |
| `expected_output` | certgen_icml2027_current_diagnostic_output.zip |
| `copyback` | download ZIP, retain SHA-256, validate and import locally |
| `local_resume` | python3 scripts/run_all_available_cpu_stages.py --resume --explain plus ICML replay |
| `failure_recovery` | preserve input/config/logs; repair only failed stage; rerun exact immutable identity |
| `immutable_fields` | study/model/revision/seed/preprocessing/shards/output schema |
| `claim_allowed` | False |
