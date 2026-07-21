# Prompt 00 — V3 Global Rules and Boundaries

You are implementing **CertGen V3**.

## Current project state assumed

V1 has passed:
- scaffold, claim gates, smoke artifacts, command index, V1 audit.

V2 has passed:
- 15/15 V2 final audit checks;
- 66 direct tests passed;
- clean MMD/KID/CMMD streams and kernels;
- bounded CS core;
- clean certificate API/CLI;
- optional-stopping smoke lab;
- synthetic fixtures;
- feature-cache schema and validator;
- V2 registry templates and validator;
- dry-run first-pilot planner;
- FID/FD policy reinforcement;
- certificate-card renderer;
- V2 audit and handoff docs.

## V3 mission

Upgrade the codebase so the project can safely approach the first real benchmark pilot.

The goal is:

> real-pilot readiness, not real-paper claims.

## Non-negotiable rules

Do not:
- fabricate real benchmark data;
- fabricate feature caches;
- fabricate generated samples;
- fabricate published scores;
- fabricate citations;
- fabricate decidedness fractions;
- weaken claim gates;
- allow smoke/synthetic/non-evidence artifacts to support claims;
- automatically download large datasets/models in tests;
- require paid APIs/cloud/GPU;
- run heavy GPU work in normal tests;
- claim rigorous anytime-valid FID certification unless mathematically justified.

Do:
- keep tests CPU/local;
- keep heavy dependencies optional and lazy;
- preserve V1/V2 behavior;
- add regression tests for every new gate;
- emit explicit evidence statuses;
- require provenance for real feature caches;
- make every pilot artifact auditable;
- keep FID/FD-DINOv2 descriptive-only unless a rigorous policy says otherwise;
- use real data only when explicitly supplied by user/local paths/registry rows;
- mark dry-run and smoke outputs as non-evidence.

## Evidence statuses

Use strict statuses everywhere:

- `smoke_only`
- `synthetic_only`
- `dry_run_only`
- `planned_only`
- `real_features_unvalidated`
- `real_features_validated`
- `real_pilot_pending`
- `real_pilot_non_claim`
- `real_pilot_claim_blocked`
- `real_pilot_claim_eligible`

Only `real_pilot_claim_eligible` can support a paper-facing empirical statement, and V3 should make this hard to reach unless every gate passes.

## Claim allowance

Any artifact should expose:

```json
{
  "evidence_status": "...",
  "claim_allowed": false,
  "claim_blockers": [...]
}
```

`claim_allowed` must remain false unless all real gates pass.

## FID policy

FID and FD-DINOv2 can be:
- computed descriptively,
- audited for preprocessing sensitivity,
- reported in non-claim cards,
- used for sanity checks.

They must not be presented as rigorous anytime-valid certificates unless a later implementation proves and audits a watertight method.

## Deliverables for this prompt

1. Add/update a V3 rules doc under `docs/`.
2. Add a small constants module or config entries defining evidence statuses.
3. Add tests ensuring unknown statuses are rejected and smoke/dry-run statuses cannot set `claim_allowed=true`.
4. Do not touch real pilot execution yet.

## Verification

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q
```

Expected: all prior tests plus new status/gate tests pass.
