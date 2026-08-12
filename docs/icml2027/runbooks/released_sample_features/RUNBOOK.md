# authenticated released-sample features

| Field | Value |
|---|---|
| `purpose` | authenticated released-sample features |
| `launchboard_status` | READY_AFTER_AUTHENTICATED_PREREQUISITE |
| `prerequisite_state` | BLOCKED_RELEASED_SAMPLE_IMPORT |
| `input_builder` | python3 scripts/icml2027/build_kaggle_input.py --lane released_sample_features |
| `input_ZIP` | BLOCKED_NOT_BUILT |
| `input_SHA256` | NOT_AVAILABLE_BLOCKED |
| `package_type` | authenticated_stage_input_or_blocked_plan |
| `notebook` | notebooks/kaggle/icml2027/certgen_icml2027_released_sample_features_t4x2.ipynb |
| `accelerator` | Kaggle T4 x2 |
| `GPU_count` | 2 |
| `internet_mode` | internet_on_for_dependencies; model/data assets authenticated separately |
| `dependency_profile` | authenticated `released_sample_features` exact lock with identity-bound self-created restart lifecycle |
| `private_assets` | required only where source/license/asset registry says so |
| `disk_expectation` | planner estimate; verify preflight before launch |
| `RAM_VRAM_expectation` | planner estimate; fail closed on preflight |
| `planning_runtime` | PLANNING_ESTIMATE_NOT_MEASURED |
| `restart_behavior` | resume deterministic completed shards; never mutate configuration |
| `expected_output` | `released_sample_features.output.index.json` plus ordered feature-cache `.partNNN.zip` files |
| `copyback` | download ZIP, retain SHA-256, validate and import locally |
| `local_resume` | python3 scripts/run_all_available_cpu_stages.py --resume --explain plus ICML replay |
| `failure_recovery` | preserve input/config/logs; repair only failed stage; rerun exact immutable identity |
| `immutable_fields` | study/model/revision/seed/preprocessing/shards/output schema |
| `claim_allowed` | False |

## Closed execution procedure

Before packaging, the released-sample gate validates archive SHA, model/provenance identity, sampling protocol, count, license/redistribution review, every image hash, duplicate status, and prompt/class conditioning. Released and freshly generated samples remain separate confirmatory families unless a new prospective compatibility approval explicitly joins them.

The worker spec and dependency marker bind the authenticated input, source tree, exact lock, extractor revisions, preprocessing hashes, source order, shard coverage, and output schema. Output uses the same feature multipart contract and fail-closed validator/importer as the CIFAR feature lane. Resume, copyback, and recovery never reuse corrupt or stale shards.
