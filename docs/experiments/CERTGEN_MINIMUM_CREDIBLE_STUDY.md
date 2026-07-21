# CertGen Minimum Credible Study

Artifact status: `PLANNING_ONLY`
Evidence status: `not_empirical_evidence`
`claim_allowed=false`

All sample budgets, scale tiers, and effort statements below are planning decisions. They are not measurements, runtime evidence, or evidence that any checkpoint, dataset, feature cache, or comparison is available.

## Verdict

A CIFAR-10 certificate pilot is necessary to open the execution path, but it is not a credible paper by itself. The minimum paper study is a prospectively frozen two-family image audit:

1. CIFAR-10 as the low-resolution, repository-supported execution family; and
2. AFHQ v2 as the provisional non-human, higher-resolution family, selected only if source terms, held-out reference capacity, and at least three independent model/sample sources pass feasibility checks before any CIFAR metric or certificate result is inspected.

If AFHQ v2 fails that feasibility-only gate, FFHQ is the sole planned fallback. That substitution must be logged before feature inspection and must pass privacy, attribution, non-commercial-use, and redistribution review. A result-driven benchmark substitution is forbidden.

## Statistical boundary

The only claim-capable route in this study is:

- estimand
  \[
  \Delta_{A,B;R}=\operatorname{MMD}_{k_\gamma}^{2}(P_A,P_R)-
  \operatorname{MMD}_{k_\gamma}^{2}(P_B,P_R);
  \]
- non-overlapping disjoint pairs from mutually independent IID rows from `A`, `B`, and `R`;
- a fixed extractor, preprocessing rule, L2 feature normalization, seeded order, and positive finite RBF `gamma` before the stream is inspected;
- data-independent default `gamma=0.5` unless an alternative is frozen prospectively;
- raw contributions in `[-3, 3]` under the bounded RBF construction;
- the union-Hoeffding time-uniform confidence sequence; and
- Bonferroni correction over the full predeclared claim-bearing family.

The finite-grid betting interval, empirical-Bernstein diagnostic, directional e-BH use, adaptive bandwidth selection, FID/FD, and polynomial KID are excluded from confirmatory claims. They may be shown only as clearly labeled diagnostics where the evidence firewall permits them.

One raw stream contribution consumes two samples from each distribution: six feature rows in total. A block of `b` non-overlapping contributions consumes `2b` samples per distribution. Every result table must report confidence-sequence units and samples per distribution separately.

## Minimum design

| Component | Required design | Paper role | Current status |
|---|---|---|---|
| CIFAR-10 sources | The three repository-declared candidates are preflight candidates, not validated models: `google/ddpm-cifar10-32`, `FrankCCCCC/ddpm_ema_cifar10`, and `FrankCCCCC/cfm-cifar10-32` | Low-resolution contestable family | `BLOCKED`: reference, license, real-load, generation, and feature gates are incomplete |
| Higher-resolution sources | At least three exact AFHQ v2 model/sample sources, or the frozen FFHQ fallback | Domain-breadth contestable family | `TBD_REQUIRED_PRE_EXECUTION` |
| Null controls | Reference-split versus reference-split and same-checkpoint independent seed pools | Check direction/type-I behavior without calling controls model evidence | `TBD_REAL_RUN_REQUIRED` |
| Obvious-gap controls | Fixed severe corruption on independent base rows versus uncorrupted or mildly corrupted independent rows | Direction sanity and failure detection | `TBD_REAL_RUN_REQUIRED` |
| Intermediate-gap controls | A fully frozen corruption ladder using disjoint base rows | Censoring and effect-scale calibration | `TBD_REAL_RUN_REQUIRED` |
| Contestable pairs | All unordered pairs among the three frozen sources in each family | Primary real-model audit | `TBD_REAL_RUN_REQUIRED` |
| Repeated extraction | Same immutable manifest through two batch/shard schedules | Deterministic cache reproduction only; not an IID directional certificate | `TBD_REAL_RUN_REQUIRED` |
| Protocol sensitivity | One predeclared alternate extractor or RBF gamma | Diagnostic by default; directional only if included in the full Bonferroni Cartesian family | `TBD_REQUIRED_PRE_EXECUTION` |

The exact prospective rows live in [CERTGEN_PROSPECTIVE_COMPARISON_REGISTRY.csv](CERTGEN_PROSPECTIVE_COMPARISON_REGISTRY.csv). A row with a missing source, license, checkpoint revision, extractor revision, or reference lineage cannot enter the confirmatory family.

## Sample-budget plan

| Lane | Planned samples per distribution | Raw CS units at block size 1 | Purpose | Permission |
|---|---:|---:|---|---|
| Pilot | 1,000 | at most 500 | Validate the complete real artifact path and estimate whether further scale is useful | `planning_only`; no automatic claim promotion |
| Minimum scale | up to 10,000 | at most 5,000 | Primary minimum-study horizon when an independent held-out reference pool supports it | `planning_only`; gated |
| Existing 50k generation lane | 50,000 | at most 25,000 | Generation capacity only | not claim-capable until model-row provenance and a sufficiently long precommitted reference draw plan pass |

The actual maximum for each comparison is constrained by accepted independent A/B rows and by the length of the validated reference draw plan. Reference draw IDs are sampled with replacement from a frozen empirical reference population; a source image may therefore recur, but each recurrence must be a distinct precommitted draw. Ad hoc row reuse, unique without-replacement traversal, or cycling through the cache is prohibited.

## Confirmatory families

The primary headline family, `F_PRIMARY_CONTESTABLE`, contains every contestable model pair across both frozen benchmark families under the single primary extractor/kernel protocol. If three sources pass per family, the family contains the three unordered pairs per family. This count is a design consequence, not an observed result.

Null controls and gap controls are separately predeclared calibration families. They cannot be used to remove difficult primary pairs. Any directional sensitivity result across additional extractors, kernels, datasets, or metrics expands the relevant Bonferroni family to the full Cartesian set actually tested. An exploratory display can avoid that expansion only by remaining explicitly non-directional and `claim_allowed=false`.

No e-BH or point-null e-value output may orient an edge. No family may be enlarged after inspecting values without an amendment that makes the new comparisons exploratory.

## Outcomes

### Primary

For every valid contestable comparison and every registered budget `b`:

- `decided_by_b`: the union-Hoeffding interval first excluded zero at or before `b`;
- `undecided_at_b`: no valid directional crossing occurred at or before `b`;
- `invalid_or_rejected`: the artifact or assumption gates failed; and
- `T_i`: first crossing time in CS units, right-censored at the comparison-specific maximum budget when no crossing occurs.

The primary audit reports the decided and undecided fractions over all valid preregistered contestable comparisons. Invalid comparisons remain visible in a separate denominator audit. They are not silently removed after outcomes are known.

### Secondary

- the full administrative-censoring curve, not a mean among decided comparisons;
- samples per distribution at decision and at censoring;
- false-direction and unexpected-decision events in predeclared controls;
- early-stopping sample use relative to each comparison's fixed maximum sample budget;
- completeness of the Bonferroni-certified partial-order graph;
- disagreement between the primary protocol and explicitly diagnostic alternatives; and
- source, preprocessing, reference-split, and block-size sensitivity.

Wall-clock runtime and GPU time require measured run logs and remain absent until then. A samples-saved calculation is not a runtime claim.

## Minimum credibility gates

All of the following must pass on the same immutable lineage:

1. source, license, and redistribution review;
2. accepted reference manifest and held-out split contract;
3. checkpoint or released-sample identity, exact revision, and integrity checks;
4. independent model seed/sample identities with no within-stream reuse, plus a hash-bound with-replacement reference draw plan;
5. frozen extractor and preprocessing lock;
6. cache schema, order, role, finiteness, and hash validation;
7. metric reproduction against an independent implementation or a declared trusted target;
8. null and obvious-gap controls;
9. exact union-Hoeffding and support checks;
10. a frozen Bonferroni family and analysis-plan hash;
11. right-censoring-aware aggregation; and
12. paper result-injection and claim-trace approval.

Passing software tests, dry runs, synthetic simulations, or the 1k lane alone is not paper evidence.

## Pivot logic

- If the preregistered undecided fraction at the maximum budget is below `0.05`, the proposed “many comparisons remain unresolved” headline is blocked. Report the registered outcome and emphasize only validated early-decision or reproducibility findings; do not search for harder pairs.
- If it is between `0.05` and `0.25`, treat decidedness as a mixed result and retain the full censored distribution.
- If it is at least `0.25`, an uncertainty-audit headline may be considered only after uncertainty, multiplicity, breadth, and claim gates pass.
- If controls contradict their expected direction, stop result promotion and audit provenance, stream construction, and metric orientation.
- If every pair remains undecided, do not assert model equivalence. Scale only when additional independent model rows, a longer prospectively fixed reference draw plan, and the no-cost execution policy permit it.

These thresholds are prospective analysis rules inherited from the existing plan. They are not observed values and do not guarantee a publishable conclusion.

## What this study can and cannot support

If fully executed, this design can support a bounded-kernel, two-image-family audit of directional decisions and unresolved outcomes under continuous monitoring. It cannot support metric-agnostic claims, universal generator rankings, rigorous FID/KID conclusions, text-to-image conditional conclusions, practical-equivalence claims, or claims about the literature at large.

Current verdict: `MINIMUM_STUDY_DESIGNED_NOT_EXECUTED`.
