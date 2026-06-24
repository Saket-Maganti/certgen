# 00 — V5 Global Rules and Stop Condition

You are implementing CertGen V5 in the existing CertGen repository.

## Mission

Bring the project as close as possible to **CVPR-ready-except-runs**.

This means:

- paper-ready structure;
- result slots and contracts;
- audit gates;
- reproducibility capsule;
- reviewer-defense infrastructure;
- citation board;
- supplement/proof scaffolds;
- command bundles for real execution;
- zero fake empirical claims.

## Absolute Boundaries

Do not:

- fabricate results;
- fabricate citations;
- insert fake FID/KID/CMMD/undecided-fraction/ranking-change numbers;
- let smoke/synthetic/dry-run artifacts become evidence;
- set `claim_allowed=true` for any artifact without real provenance, real features, metric reproduction, certificate execution, and audit approval;
- claim a rigorous anytime-valid FID certificate unless the FID functional issue has been solved and audited;
- run paid APIs, paid GPUs, paid annotation, or hosted inference;
- make heavy dependencies mandatory;
- break V1–V4 commands/tests;
- initialize git, commit, or tag unless explicitly asked.

Do:

- keep all result placeholders clearly marked `TBD_REAL_RUN_REQUIRED` or equivalent;
- preserve `claim_allowed=false` for dry-run/smoke/template artifacts;
- add tests for every new gate;
- keep imports lazy where possible;
- document all commands;
- update command indices and handoff docs;
- make CVPR paper/release materials structurally ready but evidence-blocked.

## Evidence Status Taxonomy

Enforce these statuses consistently:

- `template_only`
- `smoke_only`
- `synthetic_only`
- `dry_run_only`
- `pilot_candidate`
- `pilot_nonclaim`
- `evidence_candidate`
- `claim_eligible`
- `rejected`

Only `claim_eligible` can support paper claims. V5 should not produce `claim_eligible` unless real data already exists and passes all gates. In the expected V5 state, most artifacts remain `dry_run_only`, `template_only`, or `pilot_candidate`.

## Stop Condition

After V5, stop building generic infrastructure. The project should say:

> The next step is real execution, not V6 infrastructure.

Only build further if real execution exposes a concrete missing piece.

## Required V5 Audit Outcome

The final V5 audit must report:

- tests pass;
- V5 audit passed;
- paper scaffold present;
- supplement scaffold present;
- result contracts present;
- claim trace present;
- no unsupported claims;
- all placeholders are marked;
- FID policy is enforced;
- release/anonymity scan passed;
- next action is real pilot execution.
