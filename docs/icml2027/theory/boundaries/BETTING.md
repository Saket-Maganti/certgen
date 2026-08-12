# Betting-based bounded-mean candidate

- Status: `NOT_IMPLEMENTED` and not confirmatory-eligible.
- Primary source: [Waudby-Smith and Ramdas, “Estimating means of bounded random variables by betting”](https://arxiv.org/abs/2010.09686), Theorem 1 and the with-replacement bounded-mean constructions in Sections 3–5.
- Exact theorem candidate: Theorem 1's supermartingale-confidence-set inversion instantiated with a predictable, support-valid betting strategy for observations rescaled from `[-3,3]` to `[0,1]`.
- Assumptions requiring verification: common or time-varying conditional-mean target as used by the selected theorem, predictable bets, nonnegative wealth for every candidate mean, and no future-data tuning.
- Time-uniform statement: inversion of the cited nonnegative supermartingale construction.
- One/two-sided and alpha handling: the hedged two-sided construction and cross-hypothesis alpha split require exact local derivation.
- CertGen mapping status: not completed; the current stream targets a prefix average of potentially varying conditional means.
- Limitation: strong empirical performance reported by the primary source is not proof that a particular CertGen mapping is valid.
