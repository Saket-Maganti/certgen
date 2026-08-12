# prospective CIFAR 10k Inception/CLIP features

| Field | Value |
|---|---|
| `purpose` | prospective CIFAR 10k Inception/CLIP features |
| `launchboard_status` | READY_AFTER_AUTHENTICATED_PREREQUISITE |
| `prerequisite_state` | BLOCKED_10K_GENERATION_IMPORT |
| `input_builder` | python3 scripts/icml2027/build_kaggle_input.py --lane cifar_10k_features |
| `operator_inputs_before_build` | validated 10k generation index+parts; exact reference manifest; extractor aggregate manifest/root; feature-contract JSON derived from those artifacts |
| `generated_uploads` | `certgen_icml2027_cifar_10k_features_input.zip` and `certgen_icml2027_cifar_10k_features_LAUNCH_EXACT.ipynb` |
| `rename_policy` | input ZIP/notebook may be renamed; output index and every part must retain generated names |
| `identity_supply` | exact launch notebook embeds builder-derived identity; no environment variable or hand-written identity JSON |
| `input_ZIP` | BLOCKED_NOT_BUILT |
| `input_SHA256` | NOT_AVAILABLE_BLOCKED |
| `package_type` | authenticated_stage_input_or_blocked_plan |
| `notebook` | notebooks/kaggle/icml2027/certgen_icml2027_cifar_10k_features_t4x2.ipynb |
| `accelerator` | Kaggle T4 x2 |
| `GPU_count` | 2 |
| `internet_mode` | Internet may be on only for exact dependency installation; CLIP/Inception assets load offline after authentication |
| `dependency_modes` | validated preinstalled, exact Internet install, or authenticated offline wheelhouse |
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

Compute the prerequisite identity with the builder's `--prerequisite-identity-only` mode and `--input generation_10k_output=... --input reference_manifest=... --input extractor_asset_manifest=... --input extractor_asset_root=...`. Build the exact worker with `python3 scripts/icml2027/build_worker_spec.py --lane cifar_10k_features --authenticated-prerequisite-set-sha256 <printed-hash> --feature-contract <feature-contract.json> --out <worker.json>`, then build again with the same inputs plus `--input worker_spec=<worker.json>`. The builder accepts only a generation payload index whose parts, all expected models, 10k sample IDs/model, generator seeds, image hashes, and shard coverage validate. The authenticated feature worker spec binds study/config/reference/seed identities, Inception and CLIP revisions, preprocessing hashes, source-role order hashes, output schema, and the exact extractor × role × shard partition.

Upload the generated ZIP and import the generated exact launch notebook; select **T4 x2**. The notebook authenticates before project imports, validates or installs the exact lane lock, runs `pip check` and import smoke, and verifies an identity-bound marker on any second pass. If installation requests a restart, restart and rerun all cells. Each shard writes the NPZ bytes and validated actual runtime sidecar with exact sample order, dimension, dtype, finite-value check, extractor revision/class/processor, preprocessing hash, source manifest, asset inventory, and local-only status. Resume skips only an exactly valid shard.

Download the index and every `.partNNN.zip` it names without renaming. Run `python3 -m certgen icml2027 payload validate <index> --type features --worker-spec <worker.json>` followed by `python3 -m certgen icml2027 payload import <index> --out-dir <authenticated-local-dir>`. Never reconstruct directories manually. Preserve the failed shard and logs for recovery; do not mutate the frozen spec.
