# CertGen Single-File Handoff

Evidence boundary: `NO_REAL_EVIDENCE`; `not paper evidence`; `claim_allowed=false`.

## Current truth

Top status: `LOCAL_RESEARCH_CORE_VALID_BLOCKED_BY_REFERENCE_INPUT`.

CertGen now has one conditional claim-capable route: fixed-protocol L2-normalized RBF-MMD difference contributions from non-overlapping A/B/reference pairs, direct shared-reference cancellation giving support `[-3,3]`, a union-Hoeffding time-uniform confidence sequence, first-crossing decisions, and Bonferroni family control. The guarantee requires a bounded constant-conditional-mean stream, prospectively fixed choices, verified A/B sampling, an IID-with-replacement reference draw plan over a frozen empirical population, cache-v2 identity, exact metric reproduction, and a complete multiplicity family.

Finite-grid betting and the historical empirical-Bernstein formula are diagnostic only. Point-null e-values/e-BH do not certify direction or a globally stopped ranking. FID/FD-DINOv2 and polynomial KID are descriptive.

## Evidence state

There is no validated CIFAR source or nonempty reference/generated manifest; no real checkpoint preflight, generated samples, feature cache, metric reproduction, sanity control, certificate, undecided fraction, samples-to-decision curve, or paper result. All 32 NPZ files are smoke fixtures. The single generation ZIP is a code/config package, not data. No machine-readable artifact grants paper permission.

## What was repaired

- corrected the statistical estimand/stream, bound, default method, first crossing, sample accounting, bandwidth lock, and multiplicity denominator;
- demoted unsupported betting/empirical-Bernstein/e-BH/FID/KID claims;
- added reference draw-plan and feature-cache-v2 gates;
- made metric reproduction bind exact specifications and input hashes;
- strengthened evidence classification and paper firewall regression tests;
- hardened CIFAR archive/pickle/privacy handling and inaccessible-path reporting;
- repaired notebook two-GPU concurrency, revisions, preflight dependency, resume, atomic statuses, ZIP integrity, and non-evidence labels;
- hardened copied-back ZIP import and added an append-only artifact registry;
- introduced one canonical CLI and release/archive manifests; and
- rewrote manuscript claims as explicit conditional method statements and missing-evidence placeholders.

## Exact next action

Place the official CIFAR archive at `data/sources/cifar-10-python.tar.gz`, then run:

```bash
python3 -m certgen validate reference \
  --source data/sources/cifar-10-python.tar.gz \
  --explain
```

Success is exit 0 with `READY_FOR_LOCAL_CIFAR_REFERENCE_MATERIALIZATION`. See `docs/CERTGEN_EXACT_NEXT_ACTION.md` for accepted forms, searches, rejected candidates, and outputs.

## Next stages

Reference materialization and draw plan -> real checkpoint preflight -> generation -> safe import -> feature extraction -> safe import/cache-v2 -> hash-bound metric reproduction -> real controls -> frozen Bonferroni family -> first pilot -> censored aggregation -> paper claim gate.

Never skip a stage because a later ZIP or old V9 status exists.

## Research ceiling

Primary identity: prospective generative-model evaluation audit. Secondary: reproducibility/evidence protocol. A 1k CIFAR result is a pilot. A minimum paper needs two meaningful image families, controls, contestable pairs, closest-method comparison, sensitivity, censoring, and independent reproduction. A strong main-track attempt requires broader consequential evidence and possibly a real theory advance. Do not restore “metric-agnostic.”

## Start commands for the next researcher

```bash
python3 -m certgen status
python3 -m certgen next-action
python3 -m certgen audit notebooks
python3 -m certgen audit paper
python3 -m certgen audit artifact-registry
PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES='' python3 -m pytest -q
```

## Safety

The worktree was heavily dirty before this audit. Treat all existing and new artifacts as user-owned. Do not reset, clean, overwrite raw ZIPs, download large data/models, run Kaggle, upload, commit, or push without explicit authority. Keep `claim_allowed=false` unless a separate real-data claim gate passes the exact immutable lineage.

## Detailed sources

- Baseline: `reports/CERTGEN_BASELINE_REPRODUCTION.md`
- Current machine state: `reports/CERTGEN_CURRENT_STATE.json`
- Evidence: `reports/CERTGEN_EVIDENCE_BOUNDARY_AUDIT.md`
- Theory: `docs/theory/CERTGEN_STATISTICAL_VALIDITY_AUDIT.md`
- Metrics/cache: `docs/metrics/CERTGEN_FEATURE_PIPELINE_AUDIT.md`
- Engineering/notebooks: `docs/engineering/CERTGEN_ARCHITECTURE_AUDIT.md`
- Study design: `docs/experiments/CERTGEN_PREREGISTRATION_PROTOCOL.md`
- Paper ceiling: `paper/CERTGEN_PAPER_REDESIGN_PLAN.md`
- Full report: `CERTGEN_FORENSIC_AUDIT_AND_MAXIMUM_CEILING_REPORT.md`
