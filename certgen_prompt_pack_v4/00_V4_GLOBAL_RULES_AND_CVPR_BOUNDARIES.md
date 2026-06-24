# 00 — V4 Global Rules and CVPR Boundaries

You are implementing **CertGen V4**, a broad CVPR-range upgrade pack.

## Current state assumed

V1 passed with the repo scaffold and claim-safe smoke artifacts.  
V2 passed with clean MMD/KID/CMMD stream/certificate scaffolding and a conservative bounded CS core.  
V3 passed with provenance ledger validation, real feature-cache contracts, dry-run feature extraction adapters, metric reproduction audit, first-pilot orchestrator, certificate replay, pilot report cards, upgraded optional-stopping lab, and V3 docs.

Your job in V4 is not to add random infrastructure. Your job is to make the project **empirical-run ready and paper-facing**, while preserving strict no-fake-evidence discipline.

## Non-negotiable constraints

Absolutely no:

- paid APIs,
- paid cloud GPUs,
- paid datasets,
- paid annotation,
- paid inference,
- mandatory heavyweight dependencies,
- automatic large downloads in tests,
- fabricated claims,
- fake benchmark results,
- smoke/synthetic artifacts becoming evidence,
- rigorous FID-certification claims unless mathematically justified.

Allowed:

- local CPU tests,
- small synthetic fixtures,
- dry-run paths,
- generated notebooks that the user may run later on Kaggle/Colab,
- public/free dataset/sample/feature references,
- strict provenance and license validation,
- non-claim report scaffolds.

## Evidence status taxonomy

Every artifact created by V4 that resembles a result must carry one of:

- `smoke_only`
- `synthetic_only`
- `dry_run_only`
- `planned_only`
- `real_unverified`
- `real_verified_nonclaim`
- `real_claim_candidate`
- `claim_allowed`

Only `claim_allowed` artifacts may be used for paper claims, and V4 should normally produce **zero** `claim_allowed` artifacts unless real provenance, feature-cache, metric-reproduction, and certificate gates are all satisfied.

## Core scientific boundary

The paper is not:

- a new metric,
- a FID-is-bad paper,
- a leaderboard replacement,
- an anytime-valid theory paper,
- or a dataset paper.

The paper is:

> a metric-agnostic decision/certificate layer for generative-model comparison, plus a decidedness audit of reported generative-model wins.

## FID policy

FID and FD-DINOv2 are nonlinear plug-in distances. Do not claim rigorous anytime-valid FID certificates unless a valid V4/V5 method is added and audited. In V4:

- clean rigorous core: KID/MMD/CMMD-style metrics;
- FID: descriptive, reproduction, block-sensitivity, preprocessing audit;
- block-FID experiments: explicitly approximate/descriptive unless proven otherwise.

## V4 implementation rules

- Start by reading the V1–V3 handoff docs if present.
- Keep imports lazy.
- Preserve existing CLI entry points.
- Add tests for every new gate.
- Make every audit machine-readable JSON and human-readable Markdown.
- Ensure commands work with `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q`.
- Prefer small deterministic fixtures.
- Do not initialize git or commit.

## Required end state

Create or update:

- V4 audit modules,
- real-run provenance pipeline,
- feature extraction notebook generators,
- preprocessing lock validator,
- metric reproduction gate,
- multiple-comparison/ranking audit tools,
- first-real-pilot controller,
- literature claim trace registry,
- figure/table generators,
- CVPR paper scaffold docs,
- reviewer attack harness,
- reproducibility capsule validator,
- final V4 handoff.

End with:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q
python3 -m certgen.audit.v4_audit --out docs/V4_FINAL_AUDIT.md --json-out data/results/v4_final_audit.json
```

If module names differ, document the exact commands in `docs/COMMAND_INDEX_V4.md`.
