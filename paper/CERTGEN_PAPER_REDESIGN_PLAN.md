# CertGen Paper Redesign Plan

Status: `PAPER_SCAFFOLD_ONLY`; empirical evidence: `MISSING`; `claim_allowed=false`.

## Identity and title

Primary identity: a prospective generative-model evaluation methodology and audit. Secondary identity: a reproducibility protocol for anytime-valid bounded-kernel comparisons.

Working title:

> Are Generative-Model Improvements Statistically Decided? A Prospective Anytime-Valid Evaluation Audit

The method-forward fallback is *CertGen: Anytime-Valid Decision Certificates for Bounded-Kernel Generative-Model Comparison*. “Metric-agnostic” is prohibited because FID/FD and polynomial KID are descriptive-only and the only claim-capable route is the bounded RBF-MMD difference stream.

## One-sentence paper thesis

Under a prospectively locked bounded-kernel evaluation protocol, many apparent model comparisons may be better represented by simultaneous anytime-valid directions or honest censored unresolved edges than by a forced point-estimate ranking.

The sentence is a hypothesis and proposed framing, not a current empirical finding.

## Main-paper structure

1. **Introduction:** decision question, evidence gap, and exact contribution boundary.
2. **Why point estimates are not decisions:** finite-sample variation, preprocessing sensitivity, optional monitoring, and multiplicity.
3. **Problem and certificate contract:** conditional estimand, direction, unresolved outcome, censoring, and non-claims.
4. **Anytime-valid bounded-kernel method:** disjoint-pair stream, `[-3,3]` support, union-Hoeffding CS, first crossing, and assumptions.
5. **Multiplicity-aware partial rankings:** predeclared Bonferroni family, direct versus transitive edges, no forced total order.
6. **Reproducibility and evidence gates:** cache v2, reference draw plan, metric reproduction, immutable lineage, and claim firewall.
7. **Prospective experimental protocol:** controls, contestable pairs, budgets, failure handling, and pivot rules.
8. **Controlled validation:** real null and obvious-gap controls; synthetic validation remains separate.
9. **Real-model audit:** decidedness, censored stopping, partial order, and protocol sensitivity.
10. **Related work:** direct comparison with Gao–Sun–Su, sequential two-sample testing, CSs, CMMD/KID/FID, and evaluation audits.
11. **Limitations and ethics:** metric conditionality, reference choice, access/licensing, energy, and no equivalence interpretation.
12. **Conclusion:** only claims supported by approved artifacts.

## Main versus supplement

Main paper keeps the estimand, raw stream, support argument, union-Hoeffding guarantee, primary family definition, core protocol, real results, and limitations. The supplement holds the full derivation, assumption ledger, reference-sampling contract, cache schema, all registered comparisons, sensitivity cells, failure logs, reviewer-facing claim trace, and additional trajectories.

## Baselines required

- fixed-budget point estimate under the identical feature/kernel protocol;
- fixed-sample uncertainty using the same stream where appropriate;
- an established sequential/betting two-sample baseline at the theorem-compatible level;
- Gao, Sun, and Su's relative generative-comparison method where density access or an honest approximation makes the comparison meaningful;
- descriptive FID/FD-DINOv2/CMMD context only under exact reproduced conventions; and
- no “baseline” fabricated from unavailable checkpoints or paper tables.

## Evidence required before results prose

Every result sentence must trace to a frozen registry member and an immutable chain:

```text
source/license -> raw manifest -> checkpoint/preflight -> samples -> feature-cache v2
-> metric reproduction -> reference draw plan -> family/alpha ledger
-> certificate trajectory -> aggregation -> claim gate -> paper cell
```

Null and obvious-gap controls must pass before a contestable comparison can be interpreted. Invalid and failed registered members remain in an audit table; they are not silently removed from the denominator.

## Current manuscript repairs

The LaTeX scaffold now uses the bounded-kernel title, states the conditional estimand and `[-3,3]` stream, makes union-Hoeffding/Bonferroni primary, demotes betting-grid/e-BH and FID/KID claims, removes the false statement that real benchmarks were already answered, and keeps result tables as explicit missing-evidence placeholders. It compiles locally but is not a submission draft.

## Advancement gates

- **Pilot report:** one complete 1k lineage plus real controls; no breadth claim.
- **Minimum paper:** two image families, at least three prospectively selected systems per family where feasible, all registered pairs, controls, censoring, and independent artifact audit.
- **Strong main-track attempt:** three meaningful families or one deep modern-domain extension, mandatory closest-method baselines, protocol sensitivity, consequential findings, and a public reproducibility capsule.
- **Stop:** if the empirical outcome is weak, report it honestly or target a narrower methodology venue; do not add benchmarks after seeing results to manufacture unresolved cases.

## Current verdict

`PAPER_DESIGN_COHERENT_RESULTS_AND_BREADTH_MISSING`.
