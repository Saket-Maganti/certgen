# 06 — CPU Metric Reproduction and Sanity Gates

Implement/execute `CERTGEN_R1D_CPU_METRIC_REPRODUCTION_AND_SANITY_GATES`.

Goal:

> Validate copied-back feature caches and reproduce at least one reported metric point estimate or a controlled sanity estimate before any certificate run.

All CPU.

## Tasks

### 1. Validate feature caches

Run:

`commands/r0_cpu/02_validate_feature_caches.sh`

or create R1D-specific command:

`commands/r1d_cpu/00_validate_feature_caches.sh`

Checks:

- `.npz` exists;
- sidecar exists;
- sample IDs match manifest;
- feature counts match role counts;
- source manifest hash matches;
- preprocessing lock hash matches;
- `claim_allowed=false`.

### 2. Reproduce metric point estimate

If a reported KID/MMD/CMMD/FID exists for a selected source, reproduce descriptively.

If no reported metric exists for the 1k generated pilot, run controlled sanity metrics only and mark:

`metric_reproduction_status=pilot_sanity_only_not_published_reproduction`

Do not fake a published reproduction.

Write:

- `data/results/r1d_metric_reproduction.json`
- `docs/R1D_METRIC_REPRODUCTION_REPORT.md`

### 3. Sanity gates

Required sanity gates before certificates:

- reference-vs-reference/null split should be near zero for MMD/CMMD;
- reference-vs-corruption should show obvious separation;
- generated-feature counts correct;
- no NaNs;
- no duplicate sample IDs;
- feature dimension stable by extractor.

### 4. Update readiness

If gates pass:

`READY_FOR_CPU_CERTIFICATE_PILOT`

If not:

- `BLOCKED_FEATURE_CACHE_INVALID`
- `BLOCKED_METRIC_REPRODUCTION`
- `BLOCKED_SANITY_GATE_FAILED`

## Tests

No real features in tests. Use tiny fake feature arrays.

## Verification

```bash
PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES="" python3 -m pytest -q
```

Final response:

- feature-cache status;
- metric reproduction/sanity status;
- whether CPU certificate pilot is ready;
- no certificate run yet unless this prompt explicitly includes it.
