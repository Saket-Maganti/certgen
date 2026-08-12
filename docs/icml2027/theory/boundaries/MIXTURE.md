# Mixture boundary candidate

- Status: `NOT_IMPLEMENTED` and not confirmatory-eligible.
- Primary source: [Howard et al.](https://arxiv.org/abs/1810.08240), Lemma 2 and Propositions 4–9 for conjugate-mixture boundaries.
- Exact theorem candidate: a conjugate mixture boundary matching the correct CertGen sub-Bernoulli or sub-gamma process; the family cannot be chosen after seeing confirmatory outcomes.
- Assumptions requiring verification: correct supermartingale family, intrinsic-time process, support/scale mapping, mixture parameters, and predictable inputs.
- Time-uniform statement: Ville-style crossing control for the selected nonnegative mixture supermartingale.
- One/two-sided and alpha handling: official software distinguishes one- and two-sided forms; the exact CertGen conversion is not yet verified.
- Implementation status: absent. [The authors' implementation](https://github.com/gostevehoward/confseq) identifies proposition-to-function mappings but is not silently vendored.
- Limitation: tuning can materially alter power; it must be frozen prospectively.
