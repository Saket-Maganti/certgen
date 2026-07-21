# CertGen Preregistration Protocol

Registration state: `DRAFT_UNSEALED`
Evidence status: `planning_only; not_empirical_evidence`
`claim_allowed=false`

This protocol must be completed, hashed, and timestamped before any real feature values, metric values, confidence-sequence trajectories, or model directions are inspected. Existing smoke, fixture, and planning artifacts do not seal it.

## 1. Question and estimand

Primary question: among a prospectively declared family of generative-model comparisons, what fraction is directionally decided or unresolved at common sample budgets under continuous monitoring?

For a fixed reference population, feature map, preprocessing rule, L2 normalization, and RBF kernel,

\[
\Delta_{A,B;R}=\operatorname{MMD}_{k_\gamma}^{2}(P_A,P_R)-
\operatorname{MMD}_{k_\gamma}^{2}(P_B,P_R).
\]

`A_certified_better` means the upper confidence bound is below zero. `B_certified_better` means the lower bound is above zero. Otherwise the comparison is `not_decided_at_budget`. “Better” is conditional on this exact discrepancy protocol; it is not perceptual, universal, or practically significant superiority.

## 2. Decisions already fixed

| Field | Preregistered value |
|---|---|
| Global directional error level | `alpha=0.05` |
| Claim-capable metric | Difference of two linear-time disjoint-pair RBF-MMD-squared contributions only |
| Feature normalization | L2 row normalization |
| Default bandwidth | data-independent `gamma=0.5` |
| Raw contribution support | `[-3, 3]` |
| Confidence sequence | union-Hoeffding |
| Stopping rule | first valid interval excluding zero, or administrative censoring at the fixed maximum budget |
| Multiplicity | Bonferroni over the complete confirmatory Cartesian family |
| Censoring | right-censor every unresolved comparison at its comparison-specific maximum budget |
| Primary registry | `CERTGEN_PROSPECTIVE_COMPARISON_REGISTRY.csv` |
| Descriptive-only methods | FID/FD and polynomial KID |
| Blocked methods | betting-grid CS, current empirical-Bernstein interval, directional e-BH/point-null e-values, adaptive bandwidth |

One raw contribution consumes two samples per distribution. For non-overlapping blocks of `b` raw contributions, one CS unit consumes `2b` samples per distribution. Both quantities must be reported.

## 3. Required pre-execution decisions

The registration cannot be sealed while any of these remains `TBD_REQUIRED_PRE_EXECUTION`:

- accepted benchmark source, split, license/terms record, and immutable reference manifest;
- exact model/sample sources, checkpoint revisions, licenses, schedulers, and seed ranges;
- exact feature extractor identifier, weights/revision hash, output dimension read from the artifact, and preprocessing implementation;
- every claim-bearing benchmark, pair, extractor, kernel, gamma, and block size;
- maximum unique sample budget per comparison, bounded by the smallest accepted A/B/R pool;
- corruption transforms and severities;
- the higher-resolution benchmark choice and any feasibility fallback;
- exclusion-code vocabulary and registry lock hash; and
- practical-effect margin, if any practical-significance claim is intended. Without one, only statistical direction is analyzed.

These choices must be based on access, license, provenance, scientific coverage, and adapter feasibility—not observed metric gaps.

## 4. Sampling and filtration

- A and B rows must be mutually independent IID/precommitted model draws with no duplicate generation identity. R uses distinct draw IDs from a seed-fixed IID-with-replacement plan over the frozen empirical reference population; a reference source ID may recur only through that plan.
- Models, checkpoints, sampling configuration, seed sequence, sample order, reference split, extractor, preprocessing, gamma, block size, alpha, family, and budget are fixed before inspection.
- The seeded permutation and its hash are recorded before the first confidence bound is computed.
- Each raw unit uses one disjoint pair from A, B, and R. Non-overlapping blocks may average adjacent raw units; a final short block must be handled according to one frozen rule.
- Cross-comparison reuse may induce dependence and must be logged. Bonferroni does not require cross-test independence, but every marginal stream must still satisfy its own assumptions.
- Generation or extraction may stop after a valid crossing only if seed order and preprocessing were precommitted. Restarting does not reset alpha or create a new confirmatory comparison.

Any unique without-replacement finite-pool traversal, unregistered reference reuse, shared-prompt design, overlapping U-statistic, or adaptively tuned design is non-claim-capable until separately justified.

## 5. Confirmatory family and multiplicity

Let `F_CONFIRMATORY` be every registered directional cell in the Cartesian product of:

`benchmark x comparison x extractor x kernel/gamma x other claim-bearing protocol variants`.

The per-cell level is `0.05 / |F_CONFIRMATORY|`. The family is counted after feasibility exclusions but before any feature or metric value is inspected. Controls can be assigned a separate family only if the paper makes no experiment-wide error statement spanning controls and real pairs; the safer default is one combined confirmatory family.

Exploratory alternatives are excluded from the family only when they remain `claim_allowed=false`, are never used to choose a reported direction, and are labeled diagnostic in every output. Point-null e-values and e-BH cannot orient edges.

## 6. Budgets and stopping

Planned scale lanes are 1,000 and up to 10,000 model samples per distribution, corresponding to at most 500 and 5,000 raw units at block size one. These are `planning_only`. The exact maximum is frozen separately from accepted independent A/B rows and the precommitted reference draw-plan length.

At time `n`, stop and record the first crossing if the Bonferroni-adjusted union-Hoeffding interval excludes zero. If it never crosses, record an event indicator of zero and censor at the maximum budget. Continue no stream merely to obtain a desired direction. A 50k generated-sample archive is not a valid 25k-unit certificate unless equally large independent A/B/R pools pass all gates.

## 7. Outcomes

Primary:

- decided fraction by budget among all valid preregistered contestable comparisons;
- undecided fraction by budget among the same fixed denominator;
- full administrative-censoring curve for first crossing; and
- Bonferroni-certified partial-ranking graph.

Secondary:

- invalid/rejected rate and reasons using the original registry denominator;
- false-direction or unexpected decision events in controls;
- samples consumed relative to the fixed maximum, including censored comparisons;
- extractor/kernel/reference/block sensitivity;
- descriptive point-estimate ranking versus the simultaneous partial order; and
- disagreement with descriptive FID/FD or polynomial KID, without certification language.

Do not report a mean stopping time only among decided comparisons. Report event counts, risk-set/administrative-censoring curves, and the restricted mean or median only if its definition and horizon were frozen. Wall-clock savings require measured logs and are separate from sample savings.

## 8. Ranking rule

Create an oriented edge only from a claim-capable Bonferroni-adjusted interval. Preserve unresolved edges and protocol-specific contradictions. Transitive implications may be displayed only within an identical estimand/protocol and under the simultaneous-coverage event; label them as derived rather than directly crossed. Do not force a total order or interpret unresolved as tied/equivalent.

## 9. Exclusions and failures

Predeclared exclusion codes include: unverifiable provenance; unresolved license/terms; checkpoint load failure; partial or duplicate samples; seed overlap; reference/model overlap; cache schema/order/role/hash failure; extractor or preprocessing mismatch; non-finite values; metric reproduction failure; support violation; independence violation; plan-hash mismatch; and incomplete run.

- Exclusions are decided without viewing the affected comparison's direction.
- Preserve raw ZIPs, logs, and failed artifacts; never overwrite them with a repair.
- An exact-config rerun receives a new run ID and retains its parent hash.
- A failed source may be replaced only by a pre-result feasibility amendment. The removed source and all affected planned pairs stay visible.
- Interrupted runs resume from verified shards without reseeding or alpha reset.
- An assumption failure makes the result invalid, not merely “undecided.”

## 10. Controls

Null, obvious-gap, and intermediate-gap transforms are frozen before extraction. Base rows are disjoint across A/B/R roles. Repeated extraction of the same images is a deterministic reproduction test and must not be fed to an IID certificate.

Any wrong-direction obvious-gap decision triggers a stop-and-audit. A null crossing is possible under the declared error rate, but it triggers lineage and implementation review before result promotion. Failure to decide an obvious gap is a power/implementation diagnostic, not permission to tune the protocol post hoc.

## 11. Scale and pivot rules

- Advance from 1k only after all integrity, reproduction, null, and gap gates pass.
- Stop scaling a comparison at its valid crossing.
- Do not exceed the registered reference draw-plan horizon or the no-cost compute policy.
- If the maximum-budget undecided fraction is below `0.05`, block the “many unresolved” headline; do not mine harder pairs.
- Values from `0.05` to below `0.25` support only a mixed decidedness account.
- A value at or above `0.25` can motivate an unresolved-comparisons headline only after all breadth and claim gates pass.
- These are prospective interpretation rules, not observed results.

## 12. Amendments and sealing

Every amendment records timestamp, author, reason, fields changed, old/new hashes, whether any real feature/metric/certificate value was visible, and `posthoc=true|false`. Post-inspection additions are exploratory by default.

Seal only after:

1. resolving every required pre-execution field;
2. validating the registry and artifact contracts;
3. computing immutable hashes for the protocol, registry, configs, and source manifests;
4. writing a UTC timestamp and repository commit/worktree snapshot; and
5. confirming that no real result was inspected.

Current status: `BLOCKED_UNSEALED_REQUIRED_FIELDS_AND_INPUTS`.
