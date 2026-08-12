# Variance-reduction audit

100 replicates were run for obvious mean shift and dense weak high-dimensional shift. The prospectively fixed single pairing resolved the obvious shift in 100/100 (Wilson lower 0.9630) with no wrong directions; the weak shift resolved 0/100 (Wilson upper 0.0370). Four frozen pairing reuse had slightly lower between-replicate variance and the same power, but is `IMPLEMENTED_NOT_VERIFIED` and cannot enter confirmatory inference. Nonoverlapping block means were diagnostic and lost power under the unchanged boundary scaling.

No outcome-adaptive pairing was used; the frozen confirmatory policy was not changed. Full rows, widths, stopping times, bias, rates, and Wilson intervals are in `reports/icml2027/power/VARIANCE_REDUCTION.csv`. `claim_allowed=false`.
