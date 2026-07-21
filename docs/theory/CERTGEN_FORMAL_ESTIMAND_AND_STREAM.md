# CertGen Formal Estimand and Implemented Stream

Status: `CONDITIONAL_METHOD_VALIDITY_ONLY`

Evidence boundary: `synthetic_validation_only`, `not_model_evidence`, `claim_allowed=false`.

This document matches the repaired implementation in `certgen.metrics.streams` and `certgen.stats.cs`. It does not describe FID, polynomial KID, a quadratic U-statistic, or an idealized future method.

## Conditional estimand

Fix before observing the certificate stream:

- populations (P_A), (P_B), and (P_R);
- feature extractor and immutable weights (phi);
- preprocessing and row-wise L2 normalization;
- a positive finite RBF parameter `gamma`;
- pairing/blocking rule, permutation seed, horizon, alpha, and comparison family.

For the fixed kernel

\[
k(x,y)=\exp\{-\gamma\|\bar\phi(x)-\bar\phi(y)\|_2^2\},\qquad 0<k(x,y)\le 1,
\]

the implemented target is

\[
\Delta_{AB}=\operatorname{MMD}_k^2(P_A,P_R)-\operatorname{MMD}_k^2(P_B,P_R).
\]

Negative `Delta_AB` means A is closer to the reference under this exact metric protocol; positive means B is closer. It is not a statement about perceptual quality, utility, all metrics, or model superiority in general.

## Raw stream unit

For unit (i), use disjoint pairs ((A_{i1},A_{i2})), ((B_{i1},B_{i2})), and ((R_{i1},R_{i2})). The code computes

\[
Z_i = k(A_{i1},A_{i2})-k(B_{i1},B_{i2})
-k(A_{i1},R_{i2})-k(A_{i2},R_{i1})
+k(B_{i1},R_{i2})+k(B_{i2},R_{i1}).
\]

This is the difference of two linear-time unbiased MMD-squared contributions. The shared (k(R_{i1},R_{i2})) term cancels algebraically. Under mutually independent IID draws from (P_A,P_B,P_R),

\[
\mathbb E[Z_i]=\Delta_{AB}.
\]

There are three nonnegative kernel terms and three subtracted kernel terms, so

\[
-3\le Z_i\le 3.
\]

The earlier `[-4,4]` range was safe but unnecessarily loose. The implementation now records `[-3,3]` and rejects non-finite or non-positive RBF gamma.

## Blocking and sample accounting

With preregistered block size (b), stream unit (t) is the mean of the next nonoverlapping (b) raw contributions. A final short block may contain fewer contributions. Averaging preserves the `[-3,3]` support and expected value.

- one raw contribution consumes two samples from each of A, B, and R;
- one full block consumes `2*b` samples per distribution and `6*b` feature rows total;
- a decision at block unit `t` ordinarily consumes `2*b*t` samples per distribution, adjusted for a final partial block;
- `samples_to_decision` is right-censored at the maximum budget when no boundary is crossed.

The repaired metadata records contribution count, per-distribution consumption, total feature-row consumption, pairing, filtration, kernel, and bandwidth protocol.

## Filtration and stopping

Let `F_t` contain the fixed design plus the first `t` disjoint stream units. The claim-capable code requires

\[
\mathbb E[Z_t\mid\mathcal F_{t-1}]=\Delta_{AB},\qquad Z_t\in[-3,3].
\]

For block means, replace (Z_t) by the corresponding nonoverlapping block average. The code's union-Hoeffding radius is

\[
r_t=(U-L)\sqrt{\frac{\log(\pi^2t^2/(3\alpha))}{2t}}.
\]

At a fixed time, the two-sided Hoeffding error is at most (6\alpha/(\pi^2t^2)); summing over all positive integers gives alpha. Therefore

\[
C_t=[\bar Z_t-r_t,\bar Z_t+r_t]
\]

is time-uniform under the stated conditional-mean/boundedness contract. The stopping rule is the first `t` with `upper_t < 0` or `lower_t > 0`. Equality with zero is undecided. The certificate now records that first crossing; if there is no crossing, it records the final budget and a censored undecided outcome.

## What is and is not adaptive

Allowed: stop at the first crossing of the valid confidence sequence.

Not covered:

- selecting gamma, extractor, preprocessing, model pair, dataset, or metric after seeing any certificate-stream value;
- restarting and reporting only a favorable run;
- choosing a global stopping time from several dependent e-processes without a global-filtration theorem;
- overlapping pairs or reusing a row across stream units under an IID-stream claim;
- treating a fixed finite cache, shuffled without replacement after inspection, as conditionally IID;
- choosing only favorable kernels or budgets without multiplicity accounting.

## Finite reference-pool blocker

The current code permutes available rows without replacement. If those rows are genuinely IID draws and the cache/order/design were fixed before inspection, the superpopulation argument can apply unconditionally. A fixed benchmark such as the complete CIFAR-10 test set is instead a finite population. Its successive without-replacement reference draws do not automatically satisfy the displayed constant conditional-mean property for this nonlinear paired statistic.

The audit implemented the first option as an executable design gate:

- `certgen.stats.reference_sampling` builds and validates a seed-fixed draw plan over ordered source sample IDs;
- every draw records a unique draw ID, source ID/index, seed, source-manifest hash, draw hash, and plan hash;
- real-like certificate statuses now hard-block unless a validated plan is supplied and materialized against the exact reference-cache sample-ID order;
- the metric-reproduction specification must bind the same draw-plan hash.

Build a plan only after the reference manifest order is frozen and before any certificate value is inspected:

```bash
python3 -m certgen.cli.build_reference_draw_plan \
  --manifest <validated-reference-manifest.jsonl> \
  --population-id cifar10_test_empirical \
  --num-draws <2-times-budget-times-block-size> \
  --seed <predeclared-seed> \
  --out <reference-draw-plan.json>
```

This operationally targets the fixed empirical reference distribution. Repeated source rows are valid independent draws; draw IDs, not source IDs, identify stream observations. No real plan has been generated in this audit, and model A/B rows still require their own IID/precommitment evidence.

The alternative remains:

1. a proved and tested finite-population confidence sequence directly applicable to the implemented paired statistic.

Until a real plan, reference cache, model-cache sampling contract, and hash-bound metric reproduction all pass, CIFAR certificates remain blocked even if arrays exist.

## Implemented bandwidth default

For L2-normalized features, the repaired default is the data-independent `gamma=0.5`, labeled `fixed_unit_sphere_gamma_0.5_v1`. A custom gamma is recorded as `explicit_gamma_preregistration_not_verified` unless an external design lock proves it was fixed prospectively. Median-heuristic or grid-selected bandwidths from the certificate stream are not supported.

## Experimental objects

The finite-grid betting interval remains deterministic and useful as a synthetic diagnostic, but it is marked `time_uniform=false` because continuum inversion is not proved. The historical empirical-Bernstein-style formula is also diagnostic-only. A point-null betting e-value has a narrower valid scope described in the multiplicity protocol; it does not itself provide a direction.
