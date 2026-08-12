# Union-Hoeffding boundary

- Status: `VERIFIED_CONFIRMATORY_ELIGIBLE` for the CertGen bounded conditional-mean stream.
- Primary source: Hoeffding, “Probability inequalities for sums of bounded random variables,” JASA 1963, combined with a countable union bound.
- Exact construction: at time `n`, allocate `alpha_n = 6 alpha / (pi^2 n^2)` and use the two-sided fixed-time Hoeffding interval for support `[-3,3]`; summing `alpha_n` gives at most `alpha` over all integer times.
- Assumptions: adapted independent or martingale-difference bounded increments around the declared conditional means; fixed support; no outcome-adaptive changes to stream construction.
- Time-uniform statement: simultaneous coverage for every integer `n >= 1` by the summable error allocation.
- Two-sided/alpha handling: the implementation uses the two-sided radius and Bonferroni allocation across confirmatory hypotheses.
- CertGen mapping: paired RBF contributions are bounded in `[-3,3]` after the frozen unit-sphere preprocessing and bounded kernel.
- Implementation: `certgen.stats.bounds.hoeffding_union_radius` and `certgen.stats.cs`.
- Limitation: conservative; it does not adapt to observed variance.
