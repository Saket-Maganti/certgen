# DINOv2 robustness preflight

| Field | Value |
|---|---|
| `purpose` | DINOv2 robustness preflight |
| `launchboard_status` | READY_AFTER_AUTHENTICATED_PREREQUISITE |
| `prerequisite_state` | BLOCKED_PINNED_PRIVATE_ASSET_AND_LICENSE_REVIEW |
| `input_builder` | python3 scripts/icml2027/build_kaggle_input.py --lane dinov2_preflight |
| `operator_inputs_before_build` | reviewed DINO asset manifest and exact local snapshot root |
| `generated_uploads` | `certgen_icml2027_dinov2_preflight_input.zip` and `certgen_icml2027_dinov2_preflight_LAUNCH_EXACT.ipynb` |
| `rename_policy` | generated input/notebook may be renamed; returned output must retain its name |
| `identity_supply` | exact launch notebook embeds the content-derived identity; no manual JSON |
| `input_ZIP` | BLOCKED_NOT_BUILT |
| `input_SHA256` | NOT_AVAILABLE_BLOCKED |
| `package_type` | authenticated_stage_input_or_blocked_plan |
| `notebook` | notebooks/kaggle/icml2027/certgen_icml2027_dinov2_preflight_t4x2.ipynb |
| `accelerator` | Kaggle T4 x2 |
| `GPU_count` | 2 |
| `internet_mode` | dependency-only if needed; DINO model and processor load local-only with network unnecessary |
| `dependency_modes` | validated preinstalled, exact Internet install, or authenticated offline wheelhouse |
| `dependency_profile` | authenticated `dinov2_preflight` exact lock with identity-bound self-created restart lifecycle |
| `private_assets` | required only where source/license/asset registry says so |
| `disk_expectation` | planner estimate; verify preflight before launch |
| `RAM_VRAM_expectation` | planner estimate; fail closed on preflight |
| `planning_runtime` | PLANNING_ESTIMATE_NOT_MEASURED |
| `restart_behavior` | resume deterministic completed shards; never mutate configuration |
| `expected_output` | certgen_icml2027_dinov2_preflight_output.zip |
| `copyback` | download ZIP, retain SHA-256, validate and import locally |
| `local_resume` | python3 scripts/run_all_available_cpu_stages.py --resume --explain plus ICML replay |
| `failure_recovery` | preserve input/config/logs; repair only failed stage; rerun exact immutable identity |
| `immutable_fields` | study/model/revision/seed/preprocessing/shards/output schema |
| `claim_allowed` | False |

## Closed execution procedure

After human license review, compute the prerequisite hash using `python3 scripts/icml2027/build_kaggle_input.py --lane dinov2_preflight --prerequisite-identity-only --input dinov2_asset_manifest=<manifest> --input dinov2_asset_root=<snapshot>`. Build the preflight worker with `python3 scripts/icml2027/build_worker_spec.py --lane dinov2_preflight --authenticated-prerequisite-set-sha256 <printed-hash> --asset-manifest <manifest> --asset-root <snapshot> --out <worker.json>`. Build the final input with the same two inputs plus `--input worker_spec=<worker.json>`.

Upload the generated ZIP and import the exact launch notebook; select **T4 x2**. Authenticate the pinned private asset manifest and revision, package inventory, source tree, worker spec, and dependency profile before any project or ML import. The notebook validates/installs only the exact lock, runs `pip check` and import smoke, writes its dependency report, and on install-triggered restart requires rerunning all cells and rejects any marker for another lane, input ZIP, source tree, profile, lock, Python, or platform.

This stage validates the DINO asset, processor contract, preprocessing hash, feature layer, 768 dimension, and human license-review state. It remains metadata-only by design. Download the exact returned ZIP without renaming, retain its SHA-256, and validate the notebook result; do not treat preflight as feature evidence. Failure recovery preserves the package, asset manifest, dependency report, and logs and changes no scientific identity.
