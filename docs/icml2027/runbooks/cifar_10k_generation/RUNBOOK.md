# prospective CIFAR 10k maximum-stream generation

| Field | Value |
|---|---|
| `purpose` | prospective CIFAR 10k maximum-stream generation |
| `prerequisite_state` | BLOCKED_LEGACY_PREFLIGHT_AND_10K_BUILD_GATE |
| `input_builder` | python3 scripts/icml2027/build_kaggle_input.py --lane cifar_10k_generation |
| `input_ZIP` | BLOCKED_NOT_BUILT |
| `input_SHA256` | NOT_AVAILABLE_BLOCKED |
| `package_type` | authenticated_stage_input_or_blocked_plan |
| `notebook` | notebooks/kaggle/icml2027/certgen_icml2027_cifar_10k_generation_t4x2.ipynb |
| `accelerator` | Kaggle T4 x2 |
| `GPU_count` | 2 |
| `internet_mode` | internet_on_for_dependencies; model/data assets authenticated separately |
| `dependency_profile` | exact stage lock plus restart marker |
| `private_assets` | required only where source/license/asset registry says so |
| `disk_expectation` | planner estimate; verify preflight before launch |
| `RAM_VRAM_expectation` | planner estimate; fail closed on preflight |
| `planning_runtime` | PLANNING_ESTIMATE_NOT_MEASURED |
| `restart_behavior` | resume deterministic completed shards; never mutate configuration |
| `expected_output` | certgen_icml2027_cifar_10k_generation_output.zip |
| `copyback` | download ZIP, retain SHA-256, validate and import locally |
| `local_resume` | python3 scripts/run_all_available_cpu_stages.py --resume --explain plus ICML replay |
| `failure_recovery` | preserve input/config/logs; repair only failed stage; rerun exact immutable identity |
| `immutable_fields` | study/model/revision/seed/preprocessing/shards/output schema |
| `claim_allowed` | False |
