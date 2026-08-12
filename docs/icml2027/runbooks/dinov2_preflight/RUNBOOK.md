# DINOv2 robustness preflight

| Field | Value |
|---|---|
| `purpose` | DINOv2 robustness preflight |
| `launchboard_status` | READY_AFTER_AUTHENTICATED_PREREQUISITE |
| `prerequisite_state` | BLOCKED_PINNED_PRIVATE_ASSET_AND_LICENSE_REVIEW |
| `input_builder` | python3 scripts/icml2027/build_kaggle_input.py --lane dinov2_preflight |
| `input_ZIP` | BLOCKED_NOT_BUILT |
| `input_SHA256` | NOT_AVAILABLE_BLOCKED |
| `package_type` | authenticated_stage_input_or_blocked_plan |
| `notebook` | notebooks/kaggle/icml2027/certgen_icml2027_dinov2_preflight_t4x2.ipynb |
| `accelerator` | Kaggle T4 x2 |
| `GPU_count` | 2 |
| `internet_mode` | internet_on_for_dependencies; model/data assets authenticated separately |
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

Authenticate the pinned private asset manifest and revision, package inventory, source tree, worker spec, and dependency profile before any project or ML import. The notebook validates/installs only the exact lock, runs `pip check` and import smoke, writes its dependency report, and on restart rejects any marker for another lane, input ZIP, source tree, profile, lock, Python, or platform.

This stage validates the DINO asset, processor contract, preprocessing hash, feature layer, 768 dimension, and human license-review state. It remains metadata-only by design. Copy back the exact ZIP and hash; do not treat preflight as feature evidence. Failure recovery preserves the package, asset manifest, dependency report, and logs and changes no scientific identity.
