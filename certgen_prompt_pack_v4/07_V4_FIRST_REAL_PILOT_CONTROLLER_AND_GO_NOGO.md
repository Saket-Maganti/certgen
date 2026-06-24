# 07 — V4 First Real Pilot Controller and Go/No-Go

Build the controller for the first verified benchmark pilot.

## Goal

The first real pilot should be safe, deterministic, small, and claim-blocked until all gates pass. V4 should create a single controller that assembles:

1. verified provenance,
2. validated feature caches,
3. preprocessing lock,
4. metric reproduction result,
5. clean-core certificate run,
6. decidedness summary,
7. go/no-go report.

## Implement

Create:

- `certgen/pipeline/first_real_pilot.py`
- `certgen/cli/run_first_real_pilot.py`
- `docs/FIRST_REAL_PILOT_RUNBOOK_V4.md`
- `docs/FIRST_REAL_PILOT_GO_NO_GO_TEMPLATE.md`
- tests using synthetic-but-real-shaped fixture caches.

## Pipeline stages

### Stage 0 — dry run
Validate that all inputs exist and would be accepted. Do not load large features if `--dry-run` is set.

### Stage 1 — provenance gate
Check ledger row(s) are verified and not blocked.

### Stage 2 — feature cache gate
Validate cache schema, hash, shape, dtype, n, preprocessing lock.

### Stage 3 — reproduction gate
Run or read metric reproduction result.

### Stage 4 — certificate gate
Run clean-core certificate for KID/MMD/CMMD metrics.

### Stage 5 — decidedness summary
Classify outcomes.

### Stage 6 — go/no-go
Compute first benchmark pilot viability.

## Go/no-go logic

For the first benchmark:

- `GO_STRONG`: undecided fraction >= 0.25 or a ranking instability signal appears, with all gates passed.
- `GO_CONDITIONAL`: undecided fraction 0.05–0.25, or strong samples-to-decision story.
- `NO_GO_FOR_AUDIT_HEADLINE`: undecided fraction < 0.05 and no ranking/sample-budget story.
- `BLOCKED`: provenance/feature/reproduction/certificate gate failed.

If the pilot is synthetic or unverified, output only `NONCLAIM_DRY_RUN`, never GO.

## CLI example

```bash
python3 -m certgen.cli.run_first_real_pilot \
  --plan data/results/v4/real_run_plan.json \
  --ledger registry/released_sample_ledger.csv \
  --feature-cache-dir data/features/verified \
  --preprocessing-lock configs/preprocessing_locks/cifar10_inception.json \
  --out-dir data/results/v4/first_real_pilot \
  --report docs/V4_FIRST_REAL_PILOT_REPORT.md \
  --dry-run
```

## Acceptance criteria

- Dry-run mode never loads external data.
- Synthetic fixture mode exercises all stages but remains non-claim.
- Blocked gates produce actionable errors.
- Go/no-go logic is tested.
- Reports include exact next action.
