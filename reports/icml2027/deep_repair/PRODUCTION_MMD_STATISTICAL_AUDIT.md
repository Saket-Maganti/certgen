# Production MMD statistical audit

The simulator generates real feature matrices and calls the same
`mmd_difference_stream` paired contribution path plus the same
`certgen.stats.cs.hoeffding_cs` path as certificates. Quick validation ran
130 cases over dimensions [2, 16, 64, 256, 768, 2048] and budgets
[100, 250, 500, 1000, 2000, 5000, 10000]; bounded stress ran 432 cases. The
scenario inventory includes nulls, mean/covariance/higher-moment/mode,
contamination, manifold, sparse/dense high-dimensional, tail, and reference
design changes.

The dedicated 100-replicate null calibration observed Type-I `0.0`, with 95%
Wilson interval `[0.0, 0.03699349820698568]` and anytime-null
coverage `1.0`. Quick empirical power was
`0.02631578947368421` and unresolved fraction `0.9846153846153847`;
the mean stopping time was `2233.476923076923` paired units and mean
samples saved was `63.06153846153846`. These results
show a valid but strongly conservative boundary; they do not establish model
quality or ICML evidence. All raw Monte Carlo records are ignored local run
artifacts; compact JSON/CSV summaries are canonical. `claim_allowed=false`.
