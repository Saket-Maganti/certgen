# CertGen Metric Reproduction Protocol

Status: `PROTOCOL_ONLY_NOT_EXECUTED`

Evidence boundary: `synthetic_validation_only`, `not_model_evidence`, `claim_allowed=false`.

No real CIFAR-10 metric has been reproduced in the current repository state. This protocol separates cache sanity, internal implementation agreement, and reproduction against a trusted target so that a finite point estimate cannot be mislabeled as reproduction.

## Definition

A metric is reproduced only when all of the following are frozen and matched:

- exact ordered input samples or feature arrays and their hashes;
- extractor name, resolved weights/revision, package versions, and output layer;
- preprocessing and feature-normalization convention;
- metric estimator, kernel, bandwidth, sample count, dtype, and numerical convention;
- a trusted target value or independent reference implementation;
- an absolute/relative tolerance declared before computing the comparison.

Cache validity alone is not metric reproduction. A null split, obvious-gap fixture, finite output, or agreement with the same function called twice is a sanity result only.

## Current metric capabilities

| Metric label | Point estimate | Fixed-sample descriptive use | Anytime certificate | Current reproduction ceiling |
|---|---:|---:|---:|---|
| `mmd_rbf` | Implemented | Yes | Implemented only for the bounded linear-time stream under its stated assumptions | Internal synthetic agreement after cache and kernel repair; no real target reproduced. |
| `cmmd_clip_mmd` | Implemented as L2-normalized CLIP-feature RBF MMD | Yes | Same bounded-stream path | Must not be called canonical CMMD reproduction until matched to a named reference implementation and exact CLIP/kernel convention. |
| `kid_polynomial` / polynomial MMD | Implemented | Yes | No | Descriptive-only; polynomial kernels do not inherit the bounded-RBF guarantee. |
| `fid_inception` | Implemented | Yes | No | Descriptive-only; current torchvision features are not automatically canonical FID features. |
| `fd_dinov2` | Implemented | Yes | No | Descriptive-only. |

## Repaired convention mismatch

The metric-reproduction audit previously computed `mmd_rbf` on raw features, while the certificate path L2-normalized every row. The audit now calls the same L2-normalized RBF convention, and `tests/test_metric_reproduction_v3.py::test_mmd_rbf_reproduction_matches_certificate_l2_convention` prevents regression. This is a code-consistency repair, not a real metric-reproduction result.

## Required execution protocol

### Gate 1 — canonical cache validation

Both caches must pass `certgen.feature_cache.v2` validation with strict hashes, unique and ordered sample IDs, exact extractor/preprocessing identity, compatible roles, and no unresolved warnings that affect metric semantics. Validation failures stop the audit before a metric is computed.

### Gate 2 — freeze the metric specification

Write a canonical specification containing:

- `metric_label` and implementation version;
- estimator form (`linear_time_paired`, `quadratic_unbiased`, or descriptive Frechet);
- feature normalization;
- kernel name and every parameter;
- bandwidth value and selection policy;
- sample count and ordered sample-ID hashes;
- random seed/permutation policy where applicable;
- expected source, value, tolerance, and source hash or citation locator.

Hash this specification. The audit and every later certificate must record the same specification hash.

### Gate 3 — independent calculation

For a trusted target, recompute on the same inputs and compare to the preregistered tolerance. If no trusted published target exists, compare against an independently coded formula or reputable reference library on fixed synthetic arrays and label the result `internal_implementation_agreement`, not `published_metric_reproduction`.

Minimum deterministic checks are symmetry, identity/null behavior with the chosen estimator convention, permutation invariance, non-negativity only where mathematically applicable, dtype sensitivity, batching invariance, and shard-merge invariance.

### Gate 4 — bind the result to its inputs

The audit output must include:

- `passed` and `errors`;
- `reproduction_class` (`trusted_target`, `independent_implementation`, or `sanity_only`);
- metric-specification hash;
- feature NPZ and sidecar hashes for both inputs;
- ordered sample-ID hashes;
- preprocessing-lock and source-manifest hashes;
- computed value, expected value, tolerance, and discrepancy;
- implementation/package versions;
- `claim_allowed=false` until the separate evidence and paper gates pass.

A certificate gate must reject a missing field, an input-hash mismatch, a metric mismatch, any cache error, `sanity_only`, or an audit produced from synthetic fixtures when real-pilot inputs are requested.

## Repaired P0 gate defect

The inspected baseline let `certgen.pipeline.v6_execution.run_r1d_metric_reproduction_gate` set `within_tolerance=true` from cache sanity and let the certificate API accept a minimal two-field JSON. The repaired R1D path now emits `READY_FOR_METRIC_REPRODUCTION`, forces `within_tolerance=false`, and cannot authorize a certificate. The real-like certificate gate now requires trusted-target or independent-implementation status, an exact metric match, a valid metric-specification hash, exact A/B/R feature hashes, and the same reference draw-plan hash. No current real artifact satisfies that contract, so execution remains blocked honestly.

## P0/P1 pilot accounting defects

- R1E currently appends a reference null split, a synthetic `+5` corruption check, and the preregistered model comparisons to one certificate list, then computes `undecided_fraction` over the entire list. The primary fraction must use only eligible real model-pair/metric comparisons. Sanity outcomes need a separate denominator and artifact.
- If certificate generation fails after some certificates have been written, the current function can still serialize a numeric partial fraction while marking the pilot blocked. A blocked or incomplete family must expose `undecided_fraction=null` and preserve partial rows only as run-log diagnostics.
- One null split is a sanity check, not null calibration. Calibration requires a preregistered repeated synthetic/statistical-validation lane with Monte Carlo uncertainty and remains non-model evidence.
- One linear-time stream contribution consumes two raw samples from each role. For a block of `b` contributions, a decision at stream unit `t` consumes `2*b*t` raw samples per role (subject to the final partial block), not `b*t`. The repaired block-sensitivity output now states stream units, per-distribution samples, and total feature rows separately.

## Bandwidth protocol

The inspected baseline used `gamma = 1 / feature_dim` after L2 normalization. Unit vectors have squared distance at most four, so that confined the kernel to `[exp(-4/d), 1]`: approximately `[0.99805, 1]` for 2048-dimensional Inception features and `[0.99481, 1]` for 768-dimensional CLIP features. This is a mathematical consequence of the old code, not an empirical measurement. The repaired certificate convention uses the data-independent `gamma=0.5` after L2 normalization and records `fixed_unit_sphere_gamma_0.5_v1`.

Before a pilot, use exactly one of these policies:

1. the repaired positive finite fixed default `gamma=0.5`; or another benchmark/extractor-specific value fixed and hash-locked before the certificate stream; or
2. a median-distance bandwidth selected on an independent pilot split whose sample IDs and hash are excluded from the certificate stream.

Record the selected value, formula, split hash, and selection timestamp in the metric specification. Do not optimize a grid on the certificate stream. A sensitivity grid may be reported only without choosing the most favorable certificate. Reject non-finite, zero, or negative gamma values.

## Reference empirical-population draw contract

Real-like certificate statuses now require a deterministic IID-with-replacement draw plan over the ordered reference-cache sample IDs. The plan targets the fixed empirical reference distribution and records every draw ID/source ID, seed, manifest hash, draw hash, and plan hash. A unique without-replacement cache traversal is not accepted as an IID stream. No current real plan has passed this gate.

## FID and Frechet checks

The current Frechet helper returns `NaN` for one-sample and non-finite inputs rather than failing early, and it silently discards the imaginary component returned by `sqrtm`. Before any descriptive real-data use, require at least two finite rows per input, use a numerically documented PSD square-root convention, bound acceptable imaginary residuals, and compare against a named reference implementation.

## Acceptance taxonomy

- `REPRODUCED_TRUSTED_TARGET`: exact inputs and convention matched a trusted target within a frozen tolerance.
- `INTERNAL_IMPLEMENTATION_AGREEMENT`: independent implementation/reference-library agreement passed; suitable only for a non-claim technical pilot unless a stronger gate says otherwise.
- `SANITY_ONLY`: cache checks, finite output, synthetic identity/direction tests, or same-code repeatability only.
- `BLOCKED`: missing/mismatched inputs, metadata, target, tolerance, or implementation agreement.

The current real-data state is `BLOCKED`. Existing smoke outputs are `SANITY_ONLY` and remain non-evidence.
