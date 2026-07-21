# CertGen Multiplicity Protocol

Status: `BONFERRONI_DIRECTIONAL_PATH_IMPLEMENTED_CONDITIONALLY`

Evidence boundary: `synthetic_validation_only`, `not_model_evidence`, `claim_allowed=false`.

## Primary protocol: simultaneous pairwise confidence sequences

Before any outcome is inspected, construct a family manifest containing every hypothesis actually eligible for reporting:

```text
benchmark x reference population x model pair x extractor x metric x kernel/bandwidth protocol
```

Budgets along one valid confidence sequence do not create new hypotheses. Alternate seeds, reruns, preprocessing variants, bandwidths, and post hoc pairs do create additional analyses unless they are sensitivity-only and cannot be selected for the primary result.

If the family contains `K` directional comparisons, allocate `alpha_i = alpha_family / K` (or preregister weights summing to one). Run the claim-capable union-Hoeffding CS for every member. Because each pair's entire sequence covers its scalar difference with probability at least `1-alpha_i`, a union bound gives simultaneous family-wise coverage at least `1-alpha_family`. Cross-comparison independence is not required.

The batch runner now uses `K = number_of_pairs * number_of_metrics`; a production manifest must also include extractor, dataset, bandwidth, preprocessing, and rerun axes rather than hiding them outside the denominator.

## Direction and partial rankings

An edge `A -> B` may be emitted only when the simultaneous interval for `d(A,R)-d(B,R)` is strictly below zero under one shared metric/reference protocol. Zero-touching intervals are unresolved. “Unresolved” is not equivalence.

A graph is a partial order only when all edges target the same scalar model score and protocol, no directional cycle exists, and every displayed edge is in the corrected family. Transitive closure may be shown as logical consequence only when those conditions hold and must be distinguished from directly tested edges. No total ranking should be forced through unresolved pairs.

## Point-null e-values and e-BH

`certgen.stats.e_values.betting_e_value` mixes fixed legal bets at one null mean. It is a valid terminal/local-stopping e-value only if the bounded stream satisfies the null conditional-mean contract. The repaired code rejects support violations rather than clipping them.

`certgen.certs.multiple_comparisons.e_bh` implements the descending threshold

\[
e_{(k)} \ge K/(\alpha k).
\]

For valid marginal e-values at a fixed predeclared analysis time, e-BH controls FDR under arbitrary cross-hypothesis dependence. Current outputs are explicitly limited to rejection of the point null `Delta=0`.

Current e-BH non-claims:

- no directional false-discovery guarantee;
- no ranking edge from point-null rejection alone;
- no claim that a global stopping time selected by watching dependent streams preserves marginal e-values;
- no post hoc family, metric, or kernel selection;
- no claim permission from synthetic FDR simulations.

Accordingly, Bonferroni simultaneous directional CSs are the primary protocol. e-BH remains an exploratory fixed-time equality-rejection analysis until directional and global-filtration obligations are proved and tested.

## Required family artifact

A future run must record:

```text
family_id
family_manifest_sha256
alpha_family
allocation_method
member_id
pair/model IDs
benchmark/reference population
extractor/preprocessing lock
metric/kernel/gamma protocol
stream seed/block/horizon
reference draw-plan hash
metric-specification hash
status and exclusion reason
```

Missing/failed members remain visible. Dropping a failed or unfavorable member and recomputing the denominator is prohibited.
