# CertGen Theorem and Proof Obligations

Status: `PARTIALLY_DISCHARGED_REAL_CLAIMS_BLOCKED`

Evidence boundary: `synthetic_validation_only`, `not_model_evidence`, `claim_allowed=false`.

| ID | Obligation | Current disposition | Completion test | Claim impact |
|---|---|---|---|---|
| PO-01 | Show the coded raw stream is unbiased for `MMD^2(A,R)-MMD^2(B,R)`. | `DISCHARGED_CONDITIONAL` by direct expansion under mutually independent IID triples. | Symbolic/code formula match plus independent Monte Carlo diagnostic. | Required for any metric-direction claim. |
| PO-02 | Establish exact support. | `DISCHARGED`: direct shared-R cancellation leaves three positive and three negative `[0,1]` RBF terms, hence `[-3,3]`. | Randomized bound tests and invalid-gamma rejection pass. | Required for Hoeffding/e-values. |
| PO-03 | Establish time-uniform coverage of union-Hoeffding formula. | `DISCHARGED_CONDITIONAL`: fixed-time two-sided error `6 alpha/(pi^2 t^2)` sums to alpha. | Deterministic formula test; slow Monte Carlo with binomial uncertainty. | Claim-capable only if stream contract passes. |
| PO-04 | Establish A/B row IID and precommitment. | `OPEN_P0`; arrays alone cannot establish generator randomness, duplicates, or prior inspection. | Valid provenance/seed ledger, unique generation IDs, frozen order/design hash, no selection audit. | Blocks real certificates. |
| PO-05 | Give fixed CIFAR reference rows a valid sequential sampling law. | `IMPLEMENTED_GATE_NOT_EXECUTED`: deterministic IID-with-replacement draw plans target the fixed empirical distribution and are mandatory for real-like API status. | Build plan from validated manifest; reproduce seed/hash; bind cache sample-ID order; metric spec records plan hash. | Blocks current real pilot until real artifacts pass. |
| PO-06 | Prove finite-grid betting interval covers every continuum mean. | `OPEN_P0`; finite candidate e-process validity does not prove the filled grid hull. Code is diagnostic and `time_uniform=false`. | Direct theorem plus conservative numerical inversion proof/tests, or replace with an established implementation. | No betting directional certificate. |
| PO-07 | Pin empirical-Bernstein radius to an applicable theorem. | `OPEN_P1`; historical formula lacks a checked theorem mapping. Code is diagnostic and `time_uniform=false`. | Theorem citation, parameter mapping, edge-case proof, coverage tests. | No EB certificate. |
| PO-08 | Validate point-null betting e-value. | `DISCHARGED_CONDITIONAL` for fixed/local stopping under exact null conditional mean and bounds; support clipping removed. | Martingale-factor derivation and null simulations. | Equality rejection only. |
| PO-09 | Justify e-BH. | `DISCHARGED_NARROW_SCOPE` at fixed predeclared analysis time for valid marginal e-values under arbitrary dependence. | Known examples and invalid-input tests pass. | No direction/ranking/global stopping. |
| PO-10 | Establish globally stopped dependent e-BH validity. | `OPEN_P0`; local e-process validity need not survive a stopping time from the global dependent filtration. | Prove a global e-process/causal condition and test logging/stopping implementation. | Blocks anytime FDR claim. |
| PO-11 | Establish directional FDR/ranking validity from e-values. | `OPEN_P0`; two-sided point-null rejection has no sign-error guarantee. | Directional e-values/one-sided family procedure with proof and graph contract. | Blocks e-BH ranking claims. |
| PO-12 | Freeze bandwidth prospectively. | `PARTIAL`: default L2 RBF gamma `0.5` is fixed; custom gamma has an unverified label. | Immutable metric specification and independent-pilot exclusion hash where applicable. | Blocks custom/adaptive kernel claims. |
| PO-13 | Define complete multiplicity family. | `PARTIAL`: pair-times-metric bug repaired; all higher analysis axes need a manifest. | Family ledger includes every eligible/failed member and hash. | Blocks family/ranking claims. |
| PO-14 | Bind metric reproduction to certificate inputs. | `REPAIRED_GATE_NOT_EXECUTED`: minimal JSON no longer passes. | Independent/trusted agreement, spec hash, A/B/R hashes, reference draw-plan hash all match. | Blocks real pilot. |
| PO-15 | Establish cache/sample identity and nonoverlap. | `IMPLEMENTED_GATE_NOT_EXECUTED`; the canonical v2 validator/migrator and certificate gate reject duplicate/reordered IDs, hash drift, role/schema mismatch, and incomplete metadata. No real cache has passed. | Validate all three real caches and their source manifests; separately audit duplicate image hashes and cross-role lineage. | Blocks current real pilot until executed. |
| PO-16 | Justify polynomial KID/MMD anytime support. | `REJECTED_CURRENT_SCOPE`; no bounded polynomial stream/theorem. | New bounded transform or separate theorem and implementation. | Descriptive-only. |
| PO-17 | Justify FID/FD anytime support. | `REJECTED_CURRENT_SCOPE`; global plug-in statistic is not the implemented bounded stream. | Separate sequential method and proof. | Descriptive-only. |
| PO-18 | Interpret retrospective samples to decision. | `PARTIAL`: first crossing/sample counts repaired, but precomputed-cache replay does not prove realized resource reduction. | Online run ledger records actual generation/extraction stop and censored outcomes. | Blocks resource-reduction claims. |

## Proof-safe theorem statement

The strongest current theorem-shaped statement is conditional:

> For one predeclared comparison and fixed RBF metric protocol, suppose the implemented nonoverlapping block contributions are bounded in `[-3,3]` and have constant conditional mean `Delta_AB` with respect to the sequential filtration. Then the union-Hoeffding intervals emitted by `time_uniform_hoeffding_union_bound_v3` cover `Delta_AB` simultaneously over all monitored times with probability at least `1-alpha`. Stopping at the first interval strictly above or below zero therefore controls the probability of a wrong directional certificate at at most `alpha` for that pair. Bonferroni allocation extends this to a predeclared finite family without cross-pair independence.

This is not yet a real-data result. The antecedent must be verified from sampling, cache, metric, and family artifacts for every run.

## Explicitly blocked theorem statements

- “CertGen is metric agnostic.”
- “The betting grid interval is an anytime-valid CS for every bounded mean.”
- “A point-null e-value crossing certifies which model is better.”
- “e-BH gives an anytime-valid partial ranking under shared-reference global monitoring.”
- “Polynomial KID and FID inherit the RBF stream theorem.”
- “A shuffled fixed CIFAR cache is IID merely because its order is random.”
- “Synthetic coverage/power validation is model evidence.”
