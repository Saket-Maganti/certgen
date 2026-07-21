# 14 — One-Shot Megaprompt V4

Use this only if the implementation agent can handle a broad multi-file upgrade safely. Staged execution is preferred.

---

You are working in the existing CertGen repository after V1, V2, and V3 have passed.

Implement **CertGen V4: CVPR-Range Upgrade Pack**.

V4 must broaden the codebase from real-pilot readiness into a CVPR-facing empirical machine while preserving strict evidence boundaries.

## Current project state

V1 passed:

- repo scaffold,
- claim-safe smoke artifacts,
- registry/config validation,
- no real evidence.

V2 passed:

- clean MMD/KID/CMMD streams,
- bounded CS core,
- clean certificate API,
- optional-stopping smoke lab,
- feature cache schema,
- dry-run pilot planner,
- FID/FD descriptive-only policy.

V3 passed:

- provenance ledger validator,
- real feature-cache validator,
- dry-run feature extraction adapters,
- metric reproduction audit,
- first-pilot orchestrator,
- certificate replay,
- pilot report cards,
- registry/availability tables,
- upgraded optional-stopping lab,
- V3 docs/runbook/handoff.

## V4 objective

Add:

1. V4 state intake/destructive audit.
2. Provenance-to-real-run pipeline.
3. Kaggle/Colab/local feature notebook generators.
4. Preprocessing locks and metric reproduction gates.
5. Batch certificates with multiple-comparison policies.
6. Dependence diagnostics and sensitivity analysis.
7. Decidedness and ranking-stability audit.
8. First-real-pilot controller and go/no-go report.
9. Literature claim ingestion and claim trace.
10. Paper figures/tables/result-card scaffolds.
11. CVPR paper scaffold and related-work board.
12. Claim-language audit.
13. Reviewer attack harness and response bank.
14. Reproducibility capsule and release safety scanner.
15. V4 final audit, command index, and handoff.

## Absolute boundaries

Do not:

- download real datasets in tests,
- require paid services,
- fabricate results,
- insert fake paper numbers,
- claim real decidedness fraction,
- claim real ranking movement,
- claim rigorous FID certificate,
- promote smoke/synthetic artifacts to evidence,
- initialize git or commit.

Keep all generated non-real outputs `claim_allowed=false`.

## Required final validation

Run or document:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q
python3 -m certgen.audit.v4_audit --out docs/V4_FINAL_AUDIT.md --json-out data/results/v4_final_audit.json
```

## Required handoff

Create `docs/V4_SINGLE_FILE_HANDOFF.md` with:

- what changed,
- tests/audit result,
- evidence boundary,
- commands,
- blockers,
- next V5 action.

## Final V5 next action

The expected V5 next action is:

> populate one real provenance ledger with verified released sample/model-pair rows, materialize or validate real feature caches, reproduce one reported metric point estimate, and run the first real clean-core pilot in non-claim mode to measure the first-benchmark undecided fraction.

Do not build endless infrastructure after V4 unless a real run exposes a concrete missing gate.
