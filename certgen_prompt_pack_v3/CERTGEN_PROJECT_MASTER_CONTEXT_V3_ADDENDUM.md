# CertGen Project Master Context — V3 Addendum

## V3 status target

After V2, CertGen has a clean statistical scaffold and smoke-only certificate infrastructure.

V3 upgrades the project toward **first real pilot readiness**.

## V3 goal

Prepare the project to run a first benchmark pilot only after:

1. released samples/features/checkpoints are recorded in a provenance ledger;
2. licenses and availability are checked;
3. real feature caches satisfy strict sidecar/hash/preprocessing contracts;
4. metric point estimates can be reproduced or marked as unreproducible;
5. clean-core certificates can be run and replayed;
6. reports remain non-claim unless evidence gates pass.

## V3 is not

- a results pack;
- a paper-writing pack;
- a benchmark audit pack with real conclusions;
- a FID-rigorous-certification pack;
- a heavy GPU/data-download pack.

## V3 new core objects

### Provenance ledger

A table of candidate benchmark/model/sample/feature/report rows with license and availability status.

### Feature-cache contract

A strict `.npz` + JSON sidecar standard describing features, preprocessing, source, hashes, and license status.

### Metric reproduction audit

A command that checks whether metric values computed from feature caches reproduce known or expected values under declared preprocessing.

### First-pilot orchestrator

A command that runs a dry-run or validated-real-features pilot, defaulting to non-claim mode.

### Certificate replay

A tool that recomputes a certificate from its recorded inputs and verifies determinism.

### Pilot report card

A human-readable report that summarizes pilot status without overclaiming.

## V3 evidence boundary

V3 artifacts default to:

```json
"claim_allowed": false
```

A real pilot summary may compute diagnostic numbers only after validated real features exist. Even then, V3 should keep paper claims blocked unless an explicit future claim-eligibility gate passes.

## V3 decisive next action after implementation

After V3:

> Fill the provenance ledger for one benchmark, validate one real feature-cache set, reproduce one metric point estimate, and run the first clean-core pilot in non-claim mode.

## V3 success sentence

CertGen V3 makes the first real pilot auditable before it is interesting.
