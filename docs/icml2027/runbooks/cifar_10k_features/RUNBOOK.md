# prospective CIFAR 10k Inception/CLIP features

| Field | Value |
|---|---|
| `purpose` | prospective CIFAR 10k Inception/CLIP features |
| `launchboard_status` | READY_AFTER_AUTHENTICATED_PREREQUISITE |
| `prerequisite_state` | BLOCKED_10K_GENERATION_IMPORT |
| `input_builder` | python3 scripts/icml2027/build_kaggle_input.py --lane cifar_10k_features |
| `input_ZIP` | BLOCKED_NOT_BUILT |
| `input_SHA256` | NOT_AVAILABLE_BLOCKED |
| `package_type` | authenticated_stage_input_or_blocked_plan |
| `notebook` | notebooks/kaggle/icml2027/certgen_icml2027_cifar_10k_features_t4x2.ipynb |
| `accelerator` | Kaggle T4 x2 |
| `GPU_count` | 2 |
| `internet_mode` | internet_on_for_dependencies; model/data assets authenticated separately |
| `dependency_profile` | authenticated `cifar_10k_features` exact lock with identity-bound self-created restart lifecycle |
| `private_assets` | required only where source/license/asset registry says so |
| `disk_expectation` | planner estimate; verify preflight before launch |
| `RAM_VRAM_expectation` | planner estimate; fail closed on preflight |
| `planning_runtime` | PLANNING_ESTIMATE_NOT_MEASURED |
| `restart_behavior` | resume deterministic completed shards; never mutate configuration |
| `expected_output` | `cifar_10k_features.output.index.json` plus ordered feature-cache `.partNNN.zip` files |
| `copyback` | download ZIP, retain SHA-256, validate and import locally |
| `local_resume` | python3 scripts/run_all_available_cpu_stages.py --resume --explain plus ICML replay |
| `failure_recovery` | preserve input/config/logs; repair only failed stage; rerun exact immutable identity |
| `immutable_fields` | study/model/revision/seed/preprocessing/shards/output schema |
| `claim_allowed` | False |

## Closed execution procedure

The builder accepts only a generation payload index whose parts, all expected models, 10k sample IDs/model, generator seeds, image hashes, and shard coverage validate. The authenticated feature worker spec binds study/config/reference/seed identities, Inception and CLIP revisions, preprocessing hashes, source-role order hashes, output schema, and the exact extractor × role × shard partition.

The notebook authenticates before project imports, validates or installs the exact lane lock, runs `pip check` and import smoke, and verifies an identity-bound marker on any second pass. Each shard writes the NPZ bytes and normalized sidecar with exact sample order, dimension, dtype, finite-value check, extractor revision, preprocessing hash, source manifest hash, runtime, and provenance. Resume skips only an exactly valid shard.

Copy back the index and all parts, then run `python3 -m certgen icml2027 payload validate <index> --type features` followed by `python3 -m certgen icml2027 payload import <index> --out-dir <authenticated-local-dir>`. Never reconstruct directories manually. Preserve the failed shard and logs for recovery; do not mutate the frozen spec.
