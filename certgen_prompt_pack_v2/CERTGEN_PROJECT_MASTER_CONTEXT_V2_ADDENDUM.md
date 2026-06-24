# CertGen Project Master Context — V2 Addendum

# CertGen V2 Prompt Pack Context

Project: CertGen / Certified Generative-Model Comparison
Current title: CertGen: Anytime-Valid, Metric-Agnostic Decision Certificates for Generative-Model Comparison
Target venue: CVPR 2027 Main Conference

V1 status supplied by user:
- Full V1 prompt pack implemented end to end.
- V1 final audit passed: 15/15 audit checks.
- Tests: 33 passed, 0 failed via `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q`.
- Full V1 command sequence passed: config validation, smoke artifact generation, registry validation, first-pilot plan generation, and final audit.
- V1 foundation exists across `certgen/`, `configs/`, `docs/`, `registry/`, `tests/`, and generated smoke/audit outputs in `data/`.
- Current V1 limitations are intentional: no real feature extraction, no real benchmark audit, no decidedness fraction, no ranking movement claim, FID/FD-DINOv2 descriptive-only, and the clean certificate is a V1 smoke scaffold using a labeled Hoeffding-style bound, not the final V2 statistical implementation.

V2 mission:
Upgrade V1 from a claim-safe scaffold into a technically meaningful clean-core certificate implementation for KID/MMD/CMMD-style metrics, while keeping every empirical claim blocked until real gates pass.

The central V2 output is not a paper result. It is a reusable clean-core statistical engine plus a dry-run-safe first-pilot path.

V2 must deliver:
1. Clean MMD/KID/CMMD contribution streams.
2. Anytime-valid confidence-sequence/e-process implementation for bounded per-unit comparison streams.
3. Optional-stopping validity lab that demonstrates naive peeking inflation versus CertGen control.
4. Certificate API that produces `decided`, `not_decided_at_budget`, or `invalid_input` outcomes.
5. Feature-cache and preprocessing contracts, but no mandatory heavy GPU extraction in tests.
6. Registry upgrade for released-sample availability and reproducibility checks.
7. First-pilot dry-run route for one verified benchmark/model-pair registry entry.
8. Final V2 audit and single-file handoff.

Hard scientific boundary:
V2 must not claim any real published gap is undecided, any real model is better, any ranking changed, or any audit headline exists. Smoke/synthetic/demo data remain non-evidence.

## V2 directional update

V2 should be understood as the first real technical upgrade after V1. V1 created a conservative repository foundation. V2 must make the clean-core statistical certificate meaningful enough that V3 can run a first benchmark pilot.

The clean-core metrics are:

- KID / MMD with a polynomial or RBF kernel.
- CMMD as MMD on CLIP-like feature embeddings.
- Optional FD-DINOv2/FID descriptive point estimates, not rigorous certificates.

The core comparison estimand is:

```text
Delta_AB = d(A, R) - d(B, R)
```

Lower distance is better. A is better than B when `Delta_AB < 0`; B is better than A when `Delta_AB > 0`.

V2 should operate on feature arrays, not raw images. Raw feature extraction may be scaffolded but must not become required for tests.

## V2 non-negotiable scientific position

The strongest paper version is not “FID is bad.” It is:

> CertGen gives a metric-agnostic, optional-stopping-valid decision certificate for deciding whether one generative model is better under a chosen metric, and later audits how many reported wins clear that bar.

Before real pilot runs, only infrastructure claims are allowed.
