# DINOv2 robustness features

| Field | Value |
|---|---|
| `purpose` | DINOv2 robustness features |
| `launchboard_status` | READY_AFTER_AUTHENTICATED_PREREQUISITE |
| `prerequisite_state` | BLOCKED_PREFLIGHT_AND_IMAGE_INPUT |
| `input_builder` | python3 scripts/icml2027/build_kaggle_input.py --lane dinov2_features |
| `input_ZIP` | BLOCKED_NOT_BUILT |
| `input_SHA256` | NOT_AVAILABLE_BLOCKED |
| `package_type` | authenticated_stage_input_or_blocked_plan |
| `notebook` | notebooks/kaggle/icml2027/certgen_icml2027_dinov2_features_t4x2.ipynb |
| `accelerator` | Kaggle T4 x2 |
| `GPU_count` | 2 |
| `internet_mode` | internet_on_for_dependencies; model/data assets authenticated separately |
| `dependency_profile` | authenticated `dinov2_features` exact lock with identity-bound self-created restart lifecycle |
| `private_assets` | required only where source/license/asset registry says so |
| `disk_expectation` | planner estimate; verify preflight before launch |
| `RAM_VRAM_expectation` | planner estimate; fail closed on preflight |
| `planning_runtime` | PLANNING_ESTIMATE_NOT_MEASURED |
| `restart_behavior` | resume deterministic completed shards; never mutate configuration |
| `expected_output` | `dinov2_features.output.index.json` plus ordered feature-cache `.partNNN.zip` files |
| `copyback` | download ZIP, retain SHA-256, validate and import locally |
| `local_resume` | python3 scripts/run_all_available_cpu_stages.py --resume --explain plus ICML replay |
| `failure_recovery` | preserve input/config/logs; repair only failed stage; rerun exact immutable identity |
| `immutable_fields` | study/model/revision/seed/preprocessing/shards/output schema |
| `claim_allowed` | False |

## Closed execution procedure

Require the authenticated DINO preflight receipt, image manifest, pinned asset manifest/root, and scientifically bound worker spec. The dependency lifecycle and restart rejection rules are identical to preflight. Jobs must exactly cover every declared source shard with one pinned extractor revision and preprocessing hash; resume skips only exact valid caches.

Output parts carry NPZ feature shards, sidecars, row-order hashes, source-manifest hashes, dimensions, dtypes, finite checks, logs, runtime, and provenance. The index and every output identity must state `robustness_feature_space=true` and `confirmatory_family=false`. Validate and import with the `certgen icml2027 payload` commands. Never add DINO to the confirmatory family through a runbook edit.
