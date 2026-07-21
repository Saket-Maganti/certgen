# CertGen Claim and Contribution Contract

Contract state: `VERIFIED_CURRENT`, `claim_allowed=false`, empirical slots `MISSING`.

## Scientific object

For prospectively fixed feature map $\phi$, normalization rule, RBF bandwidth $\gamma$, reference distribution $P_R$, and generator distributions $P_A,P_B$, the implemented target is

$$
\Delta_{A,B;R}=\operatorname{MMD}_{k_\gamma}^2(P_A,P_R)-\operatorname{MMD}_{k_\gamma}^2(P_B,P_R).
$$

“A is better than B” means only $\Delta_{A,B;R}<0$: A is closer to the declared reference under this exact feature/kernel protocol. It does not mean A is perceptually, socially, or universally better.

## Claim-capable stream and guarantee

- Observation unit: one non-overlapping disjoint pair from each of A, B, and R, used to form a difference of two linear-time RBF-MMD-squared contributions.
- Required sampling: mutually independent IID samples within and across A, B, and R before deterministic stream construction; no cross-unit sample reuse.
- Fixed before observation: model pair, reference population/split, extractor and revision, preprocessing, normalization, kernel/bandwidth, alpha, family, maximum budget, exclusion rules, and stopping rule.
- Primary inference: time-uniform union-Hoeffding confidence sequence using the declared finite support.
- Directional decision: A better only when the upper bound is below zero; B better only when the lower bound is above zero; otherwise undecided at budget.
- Error statement: per-pair time-uniform coverage under the assumptions above. For a predeclared family, the primary protocol uses Bonferroni-adjusted alpha for family-wise control.

The finite-grid betting interval, empirical-Bernstein implementation, and e-BH path are diagnostic and `claim_allowed=false` until their open proof obligations are resolved. A point-null e-value is not by itself a directional certificate.

## Samples to decision

Samples-to-decision is the first stream unit at which the primary interval excludes zero. Image/sample cost must be reported separately because one unit consumes disjoint pairs from three roles. An undecided comparison is right-censored at its maximum budget. Reports must include the full decidedness curve or survival-style summary; they must not report a mean only among decided comparisons as though it described the whole family.

## Primary contribution

> Under a prospectively fixed bounded-kernel feature protocol, CertGen turns generative-model point-estimate comparisons into reproducible anytime-valid directional decisions or honest censored unresolved outcomes, and audits how those outcomes change the conclusions of a predeclared real comparison family.

This sentence is a proposed paper claim. Its method clause becomes allowed only after the final statistical audit passes. Its empirical clause remains blocked until the preregistered study produces validated real artifacts and the claim gate approves them.

## Method claims currently allowed

- The repository implements a non-overlapping disjoint-pair RBF-MMD difference stream.
- The conservative union-Hoeffding route is time-uniform under the documented bounded conditional-mean assumptions.
- FID and polynomial KID are blocked from the anytime-certificate path.
- The software can represent decided and undecided-at-budget outcomes without promoting fixtures to evidence.

## Empirical claims currently blocked

- any real model ordering or winner;
- any measured undecided fraction;
- any measured samples-to-decision or compute saving;
- any claim that a published comparison reverses or is unresolved;
- any checkpoint load, generation, feature, runtime, or metric-reproduction result;
- any ranking graph, benchmark generalization, or main-track empirical conclusion.

## Scope and non-claims

- FID is descriptive unless a separate valid functional procedure is implemented and audited.
- Polynomial KID does not inherit the bounded RBF guarantee.
- “Undecided” does not mean equivalent.
- “Decided” does not imply a practically meaningful gap.
- One CIFAR-10 pilot cannot establish domain generality.
- Pairwise decisions do not imply a valid global total ranking.
- Results are conditional on the declared reference, extractor, preprocessing, kernel, populations, and randomness.
- The current implementation is not metric-agnostic at the inferential level.

## Stop condition for claim promotion

No empirical claim may be promoted unless provenance, source/license, sample identity, feature/cache, metric reproduction, assumptions, statistical validity, multiplicity, and paper injection gates all pass on the same immutable artifact lineage. Passing unit tests or simulations is never sufficient.
