# CertGen Kaggle Notebook Forensic Audit

Verdict: `STATIC_CONTRACT_PASS_REAL_EXECUTION_NOT_RUN`; `claim_allowed=false`.

## Baseline defects found

The legacy V9 analyzer passed all notebooks, but direct cell inspection found material defects: GPU 0 and GPU 1 work was launched sequentially; the preflight allowed fewer than two GPUs; dependency installs were not fully pinned; generation could proceed without an exact successful preflight; ZIP extraction used unsafe/overwrite-prone patterns; resume trusted file/status existence rather than content hashes; overwrite/force behavior was loose; and shell failures could be ignored with `|| true`. The baseline pass was therefore a false assurance about production readiness.

## Repairs and current static verdict

| Contract | Preflight | Generation | Feature extraction |
|---|---:|---:|---:|
| two GPUs required and names logged | pass | pass | pass |
| pinned dependencies and `pip freeze` | pass | pass | pass |
| immutable model/extractor revisions | pass | pass | pass |
| mandatory exact preflight dependency | n/a | pass | n/a |
| actual concurrent GPU workers | per-model GPU assignment | `ThreadPoolExecutor(2)` with explicit GPU pinning | `ThreadPoolExecutor(2)` with explicit GPU pinning |
| non-overlapping deterministic shard allocation | smoke only | seeds `0:500` and `500:1000` per model | deterministic extractor/shard mapping |
| validated resume | status/log validation | manifest, seed, path, image hash, revision | feature shape/finite/sample identity checks |
| atomic shard completion | per-model status | temporary then `os.replace` | temporary then `os.replace` |
| safe ZIP input/output | output integrity manifest | CRC/path checks; no unsafe unzip | CRC/path checks; no unsafe unzip |
| partial failure blocks aggregate completion | pass | pass | pass |
| non-evidence labels | pass | pass | pass |
| stored notebook outputs cleared | pass | pass | pass |

`python3 -m certgen audit notebooks` passes the strengthened contract for all three notebooks. This is syntax/static evidence only. It does not establish that Kaggle images, packages, checkpoints, CUDA, disk, authentication, schedulers, or model outputs work.

## Notebook-specific risks

- **Preflight:** exact checkpoint licenses and authentication are unresolved; real loads may fail; only 1–4 validation images are permitted and must remain run-log-only.
- **Generation:** the CFM checkpoint/pipeline relationship is unverified; OOM and wall-time limits are unknown; every failed shard must be copied back with logs rather than omitted.
- **Features:** Inception and CLIP weights/revisions are recorded, but canonical preprocessing equivalence and output dimensions must be read from real sidecars; imported legacy sidecars require cache-v2 migration/validation.

## Required copied-back package

Every stage ZIP must contain one complete status object, raw logs, dependency freeze, per-model/per-shard statuses, integrity manifest with SHA-256 and size for every member, exact failed-shard rerun commands, and `claim_allowed=false`. A partial package is preserved but cannot advance the state engine.

## Execution order

Reference validation/materialization precedes checkpoint preflight. Only a fully imported preflight unlocks generation. Only validated generated manifests unlock feature packaging. Only safely imported, cache-v2-valid features unlock metric reproduction and real controls.
