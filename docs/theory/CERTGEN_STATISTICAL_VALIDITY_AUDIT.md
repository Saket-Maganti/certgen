# CertGen Statistical Validity Audit

Status: `LOCAL_CORE_CONDITIONALLY_VALID_REAL_PILOT_BLOCKED`

Evidence boundary: `synthetic_validation_only`, `not_model_evidence`, `claim_allowed=false`.

## Verdict

CertGen now has one defensible claim-capable statistical path: a union-Hoeffding confidence sequence over nonoverlapping, bounded, disjoint-pair RBF-MMD difference contributions, with Bonferroni allocation over a fully predeclared family. Its validity is conditional on an IID/conditional-mean stream and all metric choices being frozen before observation.

The repository does not yet establish that the planned fixed CIFAR reference cache satisfies that stream contract. It also lacks a hash-bound real metric-reproduction artifact and an executed canonical cache identity contract. There is no paper evidence: current smoke, synthetic, cache, and pilot-labeled artifacts do not qualify.

## Component verdicts

| Component | Verdict | Scope |
|---|---|---|
| Estimand | `VERIFIED_CURRENT` | Difference of two fixed-protocol RBF MMD-squared population distances. |
| Disjoint-pair algebra | `VERIFIED_CURRENT` | Shared reference self-kernel cancels; expectation equals the difference estimand under IID triples. |
| Boundedness | `VERIFIED_CURRENT` | RBF kernel in `(0,1]`; raw difference in `[-3,3]`; block averages preserve bounds. |
| Union-Hoeffding CS | `VERIFIED_CURRENT_CONDITIONAL` | Time-uniform for bounded conditionally mean-stationary units. |
| First-crossing stopping | `VERIFIED_CURRENT_CONDITIONAL` | Valid under the same CS assumptions; repaired certificate records first crossing. |
| Fixed finite CIFAR reference | `REPAIRED_GATE_NOT_EXECUTED` | Real-like runs now require a deterministic IID-with-replacement draw plan targeting the empirical reference distribution; no real plan/cache has passed. |
| Bandwidth | `REPAIRED_CONDITIONAL` | Default is fixed `gamma=0.5` after L2 normalization; custom prospective lock is not yet artifact-verified. |
| Betting grid interval | `SYNTHETIC_ONLY_BLOCKED_FOR_CLAIMS` | Candidate-mean e-processes are evaluated on a finite grid; continuum CS coverage is unresolved. |
| Empirical-Bernstein-style interval | `SYNTHETIC_ONLY_BLOCKED_FOR_CLAIMS` | No pinned theorem matches the implemented radius; now marked non-time-uniform. |
| Point-null betting e-value | `VERIFIED_CURRENT_NARROW_SCOPE` | Valid for a fixed null conditional mean with declared bounds and a local/fixed analysis time. |
| e-BH | `VERIFIED_ALGORITHM_BLOCKED_FOR_DIRECTION` | Fixed-time FDR for valid marginal e-values under arbitrary dependence; equality rejection only. |
| Bonferroni | `VERIFIED_CURRENT` | Directional simultaneous pairwise CS path; family size repaired to pairs times metrics. |
| Polynomial KID/MMD | `DESCRIPTIVE_ONLY` | Unbounded polynomial kernel does not inherit RBF bounds. |
| FID/FD-DINOv2 | `DESCRIPTIVE_ONLY` | No anytime-valid stream is implemented. |

## Repairs made in this audit

1. Demoted the finite-grid betting interval and unproved empirical-Bernstein formula from time-uniform certificate methods.
2. Made union-Hoeffding the default certificate method in typed config, CLI, batch, and pilot orchestration.
3. Prevented a non-time-uniform method from issuing a directional decision.
4. Repaired first-crossing accounting and hashes to cover only the consumed stream prefix.
5. Tightened the implemented shared-reference stream range from `[-4,4]` to `[-3,3]` by coding the algebraic cancellation directly.
6. Rejected invalid RBF gamma and replaced the near-constant post-normalization `1/d` default with fixed `gamma=0.5`.
7. Added explicit stream-unit, filtration, sample-consumption, independence, and bandwidth metadata.
8. Rejected out-of-bounds e-process inputs instead of silently clipping them.
9. Corrected e-value/e-BH language to point-null rejection, not directional certification.
10. Corrected Bonferroni family size to include every comparison-metric test.
11. Failed the real certificate gate closed unless metric reproduction is bound to the exact metric specification and all three feature hashes.
12. Demoted V6 R1D cache sanity so it cannot set `within_tolerance=true` or authorize a certificate.
13. Separated the future primary undecided-fraction denominator from null/corruption sanity certificates and made incomplete families report a null fraction.
14. Corrected samples-to-decision accounting to distinguish stream units, samples per distribution, and total feature rows.
15. Added a deterministic, hash-bound with-replacement reference draw-plan builder/validator/materializer and made real-like certificate paths reject an absent plan.

## Optional-stopping verdict

The union-Hoeffding sequence uses an explicit summable error schedule, so monitoring every time and stopping at first exclusion of zero is covered under its assumptions. Multiple displayed budgets do not require another correction when they are points on the same valid confidence sequence.

This guarantee does not survive arbitrary restarts, post hoc pair/kernel selection, or selection of the most favorable run. Resume must preserve the exact stream order, prefix, alpha, method, and design hash. Offline replay over an already generated cache estimates a counterfactual stopping time; it is not evidence that generation compute was actually saved.

## Dependence verdict

Within a unit, sharing the reference pair between A and B is intentional and handled by the paired difference. Across units, the proof needs disjoint IID triples or another directly proved sampling law. Sharing a reference cache across different model comparisons makes certificates dependent, but Bonferroni simultaneous coverage does not require cross-comparison independence.

The real-like API now requires the v2 cache identity contract and the reference draw plan, so duplicate IDs, reordered rows, hash drift, and unregistered reference reuse fail closed. Duplicate image content, A/B generation independence, overlapping source lineage, post-inspection cache selection, and a unique without-replacement finite-population traversal still require run-level provenance checks. These are artifact/design obligations, not prose limitations.

## Multiplicity verdict

The primary current protocol is Bonferroni over the complete predeclared family: every model pair multiplied by every certified metric, extractor, dataset, and kernel actually tested. The batch implementation now counts pairs times metrics; higher axes still require the run manifest to enumerate the complete family.

The e-BH implementation matches the standard descending e-value threshold at a fixed analysis time and can control FDR under arbitrary dependence when each input is a valid e-value. Current point-null e-values test exact zero only. They do not control directional false discoveries, justify ranking edges, or establish FDR at a globally adaptive stopping time across dependent streams.

## Synthetic validation boundary

All current method simulations and fixtures are `synthetic_validation_only`, `not_model_evidence`, and `claim_allowed=false`. Passing deterministic tests establishes code behavior; it is not empirical evidence about CIFAR models, undecided fractions, power, or samples to decision.

## Primary references for the theorem boundary

- Hoeffding, W. (1963), “Probability Inequalities for Sums of Bounded Random Variables,” *JASA*, DOI `10.1080/01621459.1963.10500830`.
- Gretton et al. (2012), “A Kernel Two-Sample Test,” *JMLR* 13:723–773, https://www.jmlr.org/papers/v13/gretton12a.html.
- Waudby-Smith and Ramdas (2024), “Estimating Means of Bounded Random Variables by Betting,” *JRSS B* 86(1):1–27, DOI `10.1093/jrsssb/qkad009`.
- Wang and Ramdas (2022), “False Discovery Rate Control with E-values,” *JRSS B* 84(3):822–852, DOI `10.1111/rssb.12489`.

These references support bounded-mean confidence-sequence/e-value and e-BH concepts. They do not automatically discharge CertGen's finite-grid inversion, finite-reference-pool, preprocessing, or artifact-provenance obligations.
