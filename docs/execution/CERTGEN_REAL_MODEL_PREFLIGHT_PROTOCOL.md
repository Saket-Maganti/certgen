# CertGen Real Model Preflight Protocol

Status: `RUN_READY_BY_LOCAL_CONTRACT`; real Kaggle execution required. Evidence: `non_evidence_preflight`; `claim_allowed=false`.

For every selected model, the worker validates the local asset inventory, resolves the canonical snapshot path, selects a family-specific adapter, loads the real pipeline on its isolated `cuda:0`, verifies precision/scheduler/revision/configuration, generates one to four decoded smoke images, validates RGB shape and range, hashes every image, records throughput and peak allocated VRAM, then unloads and clears worker-local CUDA state.

The required status chain is `ASSET_CACHE_VALID` → `MODEL_LOAD_PASS` → `SMOKE_GENERATION_PASS` → `PREFLIGHT_PASS`. Any exception produces no pass marker. Outputs live under `per_model/<model_id>/` and include `asset_manifest.json`, `model_load.json`, `scheduler.json`, `smoke_manifest.json`, `smoke_images/`, `throughput.json`, `memory.json`, `status.json`, and `worker_completion.json`.

`PREFLIGHT_PASS` is run-log evidence only. It does not validate a metric, certificate, ranking, or paper claim.
