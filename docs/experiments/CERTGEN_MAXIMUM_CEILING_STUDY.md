# CertGen Maximum-Ceiling Study

Artifact status: `PLANNING_ONLY`
Evidence status: `not_empirical_evidence`
`claim_allowed=false`

## Ceiling verdict

The maximum credible paper on the current statistical core is a prospective, multi-benchmark generative-evaluation audit—not a new sequential-inference theorem and not a metric-agnostic certificate system. It would ask whether point-estimate model comparisons remain directionally decided under a locked bounded-kernel protocol, how long decisions take, which edges remain unresolved, and how those conclusions change under declared protocol variations.

The scientific ceiling has two different levels:

1. **Current-core ceiling:** a broad image-generation audit using the disjoint-pair bounded RBF-MMD difference stream, union-Hoeffding confidence sequences, Bonferroni family-wise control, right-censored stopping times, and simultaneous partial rankings.
2. **Expanded-theory ceiling:** conditional text-to-image comparisons, directional e-value procedures, or e-BH rankings. This level is blocked until a new estimand, dependence argument, directional test construction, implementation, and validation are complete. It must not be implied by current code.

The direct 2025 comparator, Gao, Sun, and Su, *Statistical Inference for Generative Model Comparison* (arXiv:2501.18897), already studies uncertainty for comparing two generators, including conditional models and real CIFAR-10/text experiments, through a relative-KL-score route. CertGen's remaining novelty must therefore come from time-uniform optional stopping, the accessible-sample bounded-kernel setting, prospective multiplicity and partial rankings, artifact lineage, and a consequential empirical audit. “Uncertainty for generative-model comparison” is not a sufficient novelty claim.

## Study pillars

### 1. Controlled validity family

For every accepted benchmark:

- reference split versus reference split;
- same checkpoint with independent seed pools;
- repeated extraction and shard-order checks, labeled deterministic reproduction rather than certificate evidence;
- one severe, prospectively fixed corruption contrast; and
- an intermediate corruption ladder with disjoint base rows.

The controls validate direction, censoring behavior, provenance, and the end-to-end measurement path. They do not count as independent real-model breadth.

### 2. Prospective real-model audit

The current-core ceiling uses three image benchmark families selected before any primary result:

1. CIFAR-10 for the existing low-resolution execution lane;
2. one higher-resolution non-human or governed face family, provisionally AFHQ v2 with FFHQ as a predeclared feasibility fallback; and
3. one recognized large-scale or archive-driven natural-image family, selected from ImageNet-compatible or provenance-complete released-sample candidates after source and legal review.

Each family should contain at least three prospectively frozen, independently sourced systems or sample archives. Every unordered pair enters the primary registry. No pair may be added because its point-estimate gap looks interesting. The exact family size is `choose(m_b, 2)` for `m_b` accepted sources and must be computed from the frozen registry before features are inspected.

### 3. Protocol-sensitivity audit

The maximum study separates a single primary inferential protocol from sensitivity analyses:

- exact extractor and revision;
- preprocessing and resize implementation;
- RBF gamma;
- block size;
- held-out reference split; and
- sample budget.

Any sensitivity cell that makes a directional claim enters the full Bonferroni Cartesian family. Otherwise it remains exploratory and cannot be used to select the favorable model direction. FID/FD and polynomial KID may be reported as descriptive context but cannot inherit the RBF certificate.

### 4. Systematic literature and artifact audit

A frozen paper sampling frame records what published generative comparisons report about sample size, uncertainty, seeds, preprocessing, and artifacts. Certificate reanalysis is limited to papers with provenance-complete sample archives or feature inputs that satisfy the same source and independence gates. Point estimates copied from tables are never reverse-engineered into certificates.

The literature audit can establish reporting and artifact-availability facts. It can support claims about directional resolution only for the preregistered reanalysis-eligible subset, with that denominator reported.

## Claim-capable statistical contract

For every real comparison, the primary target remains

\[
\Delta_{A,B;R}=\operatorname{MMD}_{k_\gamma}^{2}(P_A,P_R)-
\operatorname{MMD}_{k_\gamma}^{2}(P_B,P_R).
\]

“A better” means only `Delta < 0`: A is closer to the declared reference under the exact feature and RBF protocol. Each raw disjoint-pair difference contribution lies in `[-3, 3]`; one raw unit consumes two samples per distribution. The interval is union-Hoeffding with per-comparison alpha obtained from the frozen global Bonferroni family. Unresolved comparisons are right-censored.

The following stay blocked:

- finite-grid betting inversion as a confidence sequence;
- the current empirical-Bernstein formula;
- point-null e-values as directional evidence;
- e-BH directional edges or rankings under adaptive stopping;
- adaptive bandwidth or extractor selection;
- overlapping U-statistic terms treated as IID;
- FID/FD and polynomial KID certification; and
- any shared-prompt text-to-image stream without a matching theorem.

## Scale plan

| Stage | Input scale | Scientific purpose | Advancement rule | Status |
|---|---|---|---|---|
| Integrity pilot | 1k images per distribution, at most 500 raw units | Exercise the complete immutable lineage and controls | advance only when every source/cache/metric/control gate passes | `planning_only` |
| Minimum image audit | up to 10k model images per distribution, at most 5k raw units | Execute the two-family minimum study | bounded by independent model rows and a validated reference draw plan | `planning_only` |
| Broad image audit | benchmark-specific registered horizon | Add the third family and complete all registered pairs | advance only if breadth adds a new scientific question | `planning_only` |
| Conditional T2I | `TBD_REQUIRED_PRE_EXECUTION` | Test modern conditional generation | blocked until estimand and dependence proof are implemented | `blocked_by_theory` |
| Literature reanalysis | number determined by the frozen sampling and eligibility protocol | Test external validity | no minimum count may be invented before the sampling frame is frozen | `planning_only` |

The existing 50k generation configuration is not automatically a 25k-unit certificate lane. A valid horizon cannot exceed accepted independent A/B rows or the precommitted reference draw-plan length. Repeated reference source IDs are permitted only as IID-with-replacement draws from the frozen empirical population; ad hoc reuse must not be disguised as scale.

## Primary and secondary outcomes

Primary outcomes:

- decided and undecided fractions at every registered budget;
- the full right-censored samples-to-decision distribution;
- the Bonferroni-certified partial-ranking graph; and
- invalid/rejected comparison rate with reasons and the original denominator.

Secondary outcomes:

- controlled false-direction and unexpected-null-decision events;
- sample use relative to the fixed maximum budget, including censored comparisons;
- model-edge resolution across benchmark families;
- extractor, gamma, block, preprocessing, and reference-split sensitivity;
- point-estimate ranking versus the certified partial order;
- descriptive metric disagreement without claim leakage; and
- reporting and artifact-availability findings from the literature protocol.

Wall-clock and GPU-compute claims require measured logs. “Samples saved” is not automatically “runtime saved.” Practical importance requires a separately preregistered effect margin and is absent from the current method.

## Maximum-ceiling artifact set

The final audit would require, for every run:

- immutable raw sample/reference manifests and source-license records;
- exact model, checkpoint, revision, scheduler, seed, and generation logs;
- frozen extractor weights, preprocessing implementation, and sidecars;
- deterministic feature arrays with row IDs and hashes;
- independent metric-reproduction artifacts;
- per-comparison certificate trajectories, not only final decisions;
- the frozen family registry and alpha ledger;
- administrative-censoring and partial-ranking outputs;
- invalid/rejected run records; and
- claim traces from each paper sentence, figure, and table to approved artifacts.

## Outcome-independent interpretation

- If most contestable pairs decide early, the unresolved-fraction thesis weakens; the valid contribution may instead be early-decision efficiency and protocol reproducibility.
- If many remain unresolved, report that result with its exact registered denominator and budgets; do not generalize beyond the sampled families.
- If directions change across protocols, the conclusion is protocol dependence, not proof that one metric is universally wrong.
- If controls fail, the empirical audit stops. It is not repaired by excluding the failed controls.
- If only CIFAR-10 completes, the project remains a pilot and cannot claim broad evaluation consequences.

## Publication ceiling

With complete current-core execution across three recognized image families, a systematic artifact audit, strong controls, and a result that materially changes evaluation practice, the realistic ceiling is a strong evaluation/benchmark venue or a full TMLR-style methodology study. A NeurIPS/ICML/ICLR/CVPR main-track paper is possible only at the maximum empirical ceiling and remains high risk because the underlying confidence-sequence and MMD ingredients are prior art and Gao et al. already address generative comparison uncertainty.

Conditional text-to-image breadth would materially improve relevance, but it cannot be bought by violating the current independence proof. A new valid conditional method would be a separate research contribution, not a sensitivity option.

Current verdict: `MAXIMUM_CEILING_DESIGNED_NOT_EXECUTED`.
