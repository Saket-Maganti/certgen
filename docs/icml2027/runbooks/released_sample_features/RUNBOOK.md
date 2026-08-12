# authenticated released-sample features

| Field | Value |
|---|---|
| `purpose` | authenticated released-sample features |
| `launchboard_status` | READY_AFTER_AUTHENTICATED_PREREQUISITE |
| `prerequisite_state` | BLOCKED_RELEASED_SAMPLE_IMPORT |
| `input_builder` | python3 scripts/icml2027/build_kaggle_input.py --lane released_sample_features |
| `operator_inputs_before_build` | validated released-sample import receipt+manifest; extractor asset manifest/root; separate-family feature contract |
| `generated_uploads` | `certgen_icml2027_released_sample_features_input.zip` and matching `LAUNCH_EXACT.ipynb` |
| `rename_policy` | generated input/notebook may be renamed; multipart return names are immutable |
| `identity_supply` | builder embeds exact identity; no hand-authored JSON or environment variable |
| `input_ZIP` | BLOCKED_NOT_BUILT |
| `input_SHA256` | NOT_AVAILABLE_BLOCKED |
| `package_type` | authenticated_stage_input_or_blocked_plan |
| `notebook` | notebooks/kaggle/icml2027/certgen_icml2027_released_sample_features_t4x2.ipynb |
| `accelerator` | Kaggle T4 x2 |
| `GPU_count` | 2 |
| `internet_mode` | dependency-only if needed; extractor assets load offline/local-only |
| `dependency_modes` | validated preinstalled, exact Internet install, or authenticated offline wheelhouse |
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

Compute the prerequisite identity with inputs `released_sample_import`, `released_sample_manifest`, `extractor_asset_manifest`, and `extractor_asset_root`. Build the worker with `python3 scripts/icml2027/build_worker_spec.py --lane released_sample_features --authenticated-prerequisite-set-sha256 <printed-hash> --feature-contract <feature-contract.json> --out <worker.json>`, then build the final input with the same inputs plus `worker_spec`. Upload the generated ZIP, import the exact launch notebook, and select **T4 x2**. Restart and rerun all cells if the dependency lifecycle requests it.

The worker spec and dependency marker bind the authenticated input, source tree, exact lock, extractor revisions, preprocessing hashes, source order, shard coverage, and output schema. Download the index and all named parts without renaming; validate with `python3 -m certgen icml2027 payload validate <index> --type features --worker-spec <worker.json>` and import with `python3 -m certgen icml2027 payload import <index> --out-dir <authenticated-local-dir>`. Resume, copyback, and recovery never reuse corrupt or stale shards.
