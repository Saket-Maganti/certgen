# CertGen Failure and Resume Playbook

Status: `RUNBOOK_ONLY`; no real failure or recovery has been observed.

## Universal rule

Never delete or overwrite the original input ZIP, copied-back ZIP, raw log, completed shard, or registry entry. Hash first, import to a new run ID, and distinguish `complete`, `failed`, and `partial`. A resume is valid only when the prior shard's manifest and content revalidate under the exact configuration/revision.

## Checkpoint preflight

| Failure | Required record | Recovery |
|---|---|---|
| dependency/import | package versions, traceback, model ID | correct pinned package set in a new notebook revision; rerun only preflight |
| authentication/access | repository response without token value | obtain authorized access outside logs or replace prospectively before results |
| model load/revision | exact ID/revision/cache path and traceback | verify revision exists; do not float to latest silently |
| scheduler/pipeline | config class and error | repair explicit adapter; keep checkpoint blocked until 1–4 images validate |
| image validation | mode/size/range/hash error | block model and preserve output; do not enter generation |

Preflight succeeds only when every registered model has `PREFLIGHT_PASS` at the exact revision. Import its ZIP with `python3 -m certgen import preflight <zip>`.

## Generation

Each model has GPU-0 and GPU-1 seed shards. A shard is reusable only if status is `SHARD_COMPLETE`, its expected seed set is exact, every image decodes at the declared dimensions/mode, hashes match, and checkpoint revision/config hash match. Otherwise rerun only the exact failed seed range from its recorded command into a new/empty shard directory.

Do not merge when seeds, sample IDs, paths, or image hashes duplicate; a shard is absent; or any model failed. Preserve partial outputs and logs as `RUN_LOG_ONLY`. After all shards pass, create the integrity ZIP once and safely import with `python3 -m certgen import generation <zip>`.

## Feature extraction

A feature shard is reusable only if extractor ID/revision, preprocessing lock, source-manifest hash, shard assignment, sample IDs/order, feature dimension/dtype, finiteness, and NPZ hash match. Stale or partial arrays are never completed in place. Rerun the failed extractor/shard into a fresh temporary directory and atomically publish its status.

Merge only a complete disjoint shard set. Migrate/imported sidecars to `certgen.feature_cache.v2` without overwriting originals, resolve every migration blocker, then validate. Use `python3 -m certgen import feature <zip>` for copied-back archives.

## Import failures

- Unsafe path, symlink, nested archive, executable, encryption, duplicate name, CRC, size, or compression-ratio failure: reject without extraction.
- Missing/failed/partial status or integrity mismatch: preserve ZIP hash, report blocked, do not append a validated artifact.
- Existing destination: verify exact idempotent artifact identity; otherwise allocate a new run ID. Never use `--force` to replace it.
- Schema mismatch: preserve original extracted run and migrate to a new sidecar/artifact; never edit the copied-back ZIP.

## Statistical resume

A certificate resume must preserve comparison/family ID, stream order and prefix hash, alpha allocation, method, bounds, block size, kernel/gamma, extractor/preprocessing, A/B/R cache hashes, reference draw-plan hash, and maximum horizon. Any mismatch starts a new registered analysis and cannot be selected against the old run by outcome.

## Escalation

Three repeated failures with the same root cause should produce one blocker record containing the exact artifact, command, logs, and minimal user/external action. Do not broaden the pipeline or change scientific choices merely to make a run pass.
