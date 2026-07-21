# CertGen Generation Package Contract

Generation preparation consumes a canonical successful preflight import, per-model `PREFLIGHT_PASS`, smoke reports, adapter capability snapshot, asset manifests, local caches, throughput calibration, a complete 10,000-row reference manifest, scale, and deterministic seed plan.

The deterministic input ZIP contains `generation_config.yaml`, `seed_ledger.json`, `model_runtime_configs/`, `asset_manifests/`, `model_cache/`, `preflight/`, `runtime_calibration.json`, `expected_output_schema.json`, `run_identity.json`, `KAGGLE_INSTRUCTIONS.md`, the canonical notebook, and portable runtime code. One model ID is used across registry, asset, cache, output, and certificate routing. Missing preflight, adapter, cache, smoke validation, or runtime config blocks packaging.
