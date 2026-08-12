# prospective CIFAR 10k maximum-stream generation

| Field | Value |
|---|---|
| `purpose` | prospective CIFAR 10k maximum-stream generation |
| `launchboard_status` | READY_AFTER_AUTHENTICATED_PREREQUISITE |
| `prerequisite_state` | BLOCKED_LEGACY_PREFLIGHT_AND_10K_BUILD_GATE |
| `input_builder` | python3 scripts/icml2027/build_kaggle_input.py --lane cifar_10k_generation |
| `operator_inputs_before_build` | authenticated legacy preflight output; aggregate/per-model asset manifest contract; local model snapshot root |
| `generated_uploads` | `certgen_icml2027_cifar_10k_generation_input.zip` and `certgen_icml2027_cifar_10k_generation_LAUNCH_EXACT.ipynb` |
| `rename_policy` | input ZIP and launch notebook may be renamed; authentication is content-addressed; never rename output index/parts |
| `identity_supply` | exact launch notebook embeds builder-derived identity; generic notebook uses the builder launch manifest; no environment JSON |
| `input_ZIP` | BLOCKED_NOT_BUILT |
| `input_SHA256` | NOT_AVAILABLE_BLOCKED |
| `package_type` | authenticated_stage_input_or_blocked_plan |
| `notebook` | notebooks/kaggle/icml2027/certgen_icml2027_cifar_10k_generation_t4x2.ipynb |
| `accelerator` | Kaggle T4 x2 |
| `GPU_count` | 2 |
| `internet_mode` | Internet may be on only for exact dependency installation; model loading is offline/local-only after authentication |
| `dependency_modes` | `USE_PREINSTALLED_VALIDATED`, `KAGGLE_INTERNET_ON_INSTALL`, or authenticated `PRIVATE_WHEELHOUSE_OFFLINE` |
| `dependency_profile` | authenticated `cifar_10k_generation` exact lock; validate/install/pip-check/import-smoke; marker binds package/source/profile/lock/Python/platform |
| `private_assets` | required only where source/license/asset registry says so |
| `disk_expectation` | planner estimate; verify preflight before launch |
| `RAM_VRAM_expectation` | planner estimate; fail closed on preflight |
| `planning_runtime` | PLANNING_ESTIMATE_NOT_MEASURED |
| `restart_behavior` | resume deterministic completed shards; never mutate configuration |
| `expected_output` | `cifar_10k_generation.output.index.json` plus ordered `.partNNN.zip` image/manifests/log/provenance shards |
| `copyback` | download ZIP, retain SHA-256, validate and import locally |
| `local_resume` | python3 scripts/run_all_available_cpu_stages.py --resume --explain plus ICML replay |
| `failure_recovery` | preserve input/config/logs; repair only failed stage; rerun exact immutable identity |
| `immutable_fields` | study/model/revision/seed/preprocessing/shards/output schema |
| `claim_allowed` | False |

## Closed execution procedure

First compute the prerequisite hash with `python3 scripts/icml2027/build_kaggle_input.py --lane cifar_10k_generation --prerequisite-identity-only` plus `--input legacy_preflight_output=... --input model_asset_manifest=... --input model_asset_root=...`. Build the worker with `python3 scripts/icml2027/build_worker_spec.py --lane cifar_10k_generation --authenticated-prerequisite-set-sha256 <printed-hash> --asset-contract <exact-asset-contract.json> --out <worker.json>`. Run the input builder again with the same three inputs plus `--input worker_spec=<worker.json>`.

Upload only the generated input ZIP to Kaggle and import the generated `LAUNCH_EXACT` notebook. Select **T4 x2**. Authenticate the exact input ZIP with the stdlib-only first cell. The input binds the v2 study/config/reference plan, execution contract, 20k-record seed manifest, checkpoint revisions, worker-spec hash, source tree, dependency lock, and exact nonoverlapping job coverage. Let the notebook create or verify its own dependency state; after an install-triggered restart, rerun **all cells from the top** so the wrong-package, wrong-source, wrong-lock, or wrong-lane marker is rejected.

Every worker consumes its exact `sample_index_start:sample_index_stop` seed-manifest slice. It may resume only when every existing PNG decodes and the shard manifest, image hashes, checkpoint revision, sample IDs, and generator seeds match. Missing or corrupt shards rerun; stale shards are never reused.

Download the index and every `.partNNN.zip` named by it, without renaming any of them. Run `python3 -m certgen icml2027 payload validate <index> --type generation --seed-manifest registry/manifests/icml2027/cifar10k_generator_seed_manifest_v1.json --worker-spec <worker.json>`. The feature builder consumes the validated index directly. On failure retain the authenticated input, index, parts, dependency report, worker logs, and runtime metrics; repair only the failed shard under the same immutable identity.
