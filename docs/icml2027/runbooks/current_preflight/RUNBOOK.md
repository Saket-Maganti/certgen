# legacy two-model preflight

| Field | Value |
|---|---|
| `purpose` | legacy two-model preflight |
| `prerequisite_state` | READY_AFTER_DIAGNOSTIC |
| `input_builder` | python3 -m certgen kaggle build-input --stage preflight --json |
| `input_ZIP` | artifacts/cvpr/kaggle_inputs/preflight/certgen_cvpr_preflight_input.zip |
| `input_SHA256` | d3a5b585383e12cfad82d94694fa1d8e2701de399617e8e515bafae57f33e93f |
| `package_type` | authenticated_stage_input_or_blocked_plan |
| `notebook` | notebooks/kaggle/certgen_cvpr_checkpoint_preflight_t4x2.ipynb |
| `accelerator` | Kaggle T4 x2 |
| `GPU_count` | 2 |
| `internet_mode` | internet_on_for_dependencies; model/data assets authenticated separately |
| `dependency_profile` | exact stage lock plus restart marker |
| `private_assets` | required only where source/license/asset registry says so |
| `disk_expectation` | planner estimate; verify preflight before launch |
| `RAM_VRAM_expectation` | planner estimate; fail closed on preflight |
| `planning_runtime` | PLANNING_ESTIMATE_NOT_MEASURED |
| `restart_behavior` | resume deterministic completed shards; never mutate configuration |
| `expected_output` | certgen_icml2027_current_preflight_output.zip |
| `copyback` | download ZIP, retain SHA-256, validate and import locally |
| `local_resume` | python3 scripts/run_all_available_cpu_stages.py --resume --explain plus ICML replay |
| `failure_recovery` | preserve input/config/logs; repair only failed stage; rerun exact immutable identity |
| `immutable_fields` | study/model/revision/seed/preprocessing/shards/output schema |
| `claim_allowed` | False |
