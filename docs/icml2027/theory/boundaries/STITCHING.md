# Stitched boundary candidate

- Status: `NOT_IMPLEMENTED` and not confirmatory-eligible.
- Primary source: [Howard et al.](https://arxiv.org/abs/1810.08240), Theorem 1 (stitched boundary).
- Exact theorem candidate: Theorem 1 applied to a valid sub-gamma process with a predeclared epoch function, minimum intrinsic time, geometric factor, and error-spending function.
- Assumptions requiring verification: a valid CertGen sub-gamma process, predictable intrinsic time, fixed support/scale, and a fully prospective choice of all tuning constants.
- Time-uniform statement: the cited theorem controls uniform boundary crossing over the stated intrinsic-time range.
- One/two-sided and alpha handling: not yet mapped; two one-sided boundaries and cross-hypothesis Bonferroni accounting must be checked exactly.
- Implementation status: no production implementation. The authors' [official `confseq` implementation](https://github.com/gostevehoward/confseq) is a research reference, not a dependency or validation oracle.
- Limitation: no CertGen coverage benchmark may label this confirmatory until theorem mapping and independent reproduction pass.
