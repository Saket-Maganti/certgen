# One-Shot Megaprompt — CertGen V3

Use this only if you want one large implementation run. Staged execution is safer.

---

You are implementing **CertGen V3** in the existing CertGen repository.

## Current state

V1 and V2 have passed. V2 final audit passed 15/15 checks. Direct tests were 66 passed. V2 implemented clean MMD/KID/CMMD streams, bounded CS core, clean certificate API/CLI, optional-stopping smoke lab, synthetic fixtures, feature-cache schema/validator, registry templates/validator, dry-run first-pilot planner, FID/FD policy reinforcement, certificate-card renderer, V2 audit, and V2 handoff docs.

## V3 mission

Build real-pilot readiness and heavy infrastructure polish, without promoting any empirical claim.

V3 should prepare the project to:

1. verify released sample/model-pair provenance;
2. validate real feature caches;
3. plan dry-run-safe feature extraction;
4. audit preprocessing and metric reproduction;
5. orchestrate a first-benchmark clean-core pilot;
6. replay certificates deterministically;
7. render no-claim pilot cards;
8. validate V3 registry availability;
9. strengthen optional-stopping validity lab;
10. finalize V3 audit and handoff.

## Non-negotiable boundaries

Do not fabricate:
- real samples;
- feature caches;
- reported scores;
- citations;
- benchmark rows;
- decidedness fractions;
- ranking changes.

Do not:
- run heavy downloads in tests;
- require paid APIs/GPU/cloud;
- claim FID has rigorous anytime-valid certification unless solved;
- allow smoke/synthetic/dry-run artifacts to become evidence;
- weaken existing gates.

Keep:
- tests CPU/local;
- heavy imports optional/lazy;
- all claim gates conservative;
- FID/FD descriptive-only by default;
- all generated V3 artifacts explicit about evidence status.

## Implement V3 deliverables

Implement the content of the staged prompts:

1. V3 global rules/status constants.
2. V3 intake audit.
3. Released-sample provenance ledger and validator.
4. Real feature-cache contracts and strict validator.
5. Dry-run feature extraction adapters/planner.
6. Preprocessing and metric reproduction audit.
7. First-benchmark pilot orchestrator.
8. Certificate replay/determinism.
9. Pilot report cards and no-claim scanner.
10. V3 registry schema and availability tables.
11. Optional-stopping lab upgrade.
12. Docs, command index, reproducibility capsule, troubleshooting.
13. V3 final audit and single-file handoff.

## Required final commands

At the end, run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q

python3 -m certgen.cli.v3_audit \
  --out docs/V3_FINAL_AUDIT.md \
  --json-out data/results/v3_final_audit.json
```

## Expected final handoff

Return a concise summary with:

- tests passed/failed;
- V3 audit status;
- files changed;
- key new commands;
- evidence boundary;
- current limitations;
- exact next V4 action.

## Final expected next action

After V3, the next action should be:

> Fill the provenance ledger for one benchmark/model-pair set, acquire or materialize real feature caches, validate them, reproduce one metric point estimate, and run the first clean-core pilot in non-claim mode.
