# Paired-MMD memory audit

The repaired primitive computes six aligned RBF vectors in `O(ND)` time and
`O(chunk*D + N)` extra memory. It never materializes a Gram matrix. The
performance grid contains 32 cases through `N=10000` and
`D=2048`; all were finite and small-case parity drift stayed
below tolerance. At `N=10,000`, a float64 Gram matrix alone would require
800,000,000 bytes per kernel call, while the registered chunk bound is listed
per case in `PAIRED_MMD_PERFORMANCE_AUDIT.csv`. The integration lane also
executes memory-mapped `10k x 768` and `10k x 2048` fixtures. `claim_allowed=false`.
