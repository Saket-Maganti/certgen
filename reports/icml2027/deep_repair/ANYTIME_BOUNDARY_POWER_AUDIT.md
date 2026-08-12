# Anytime-boundary power audit

The canonical boundary is union-Hoeffding with terminal radius
`0.27639731927408734` at 5,000 paired units on support `[-3,3]`. A
100-replicate/effect comparison against fixed-n Hoeffding is recorded in
`artifacts/icml2027/boundary_benchmark/ANYTIME_BOUNDARY_COMPARISON.csv`. The
production study remains unchanged because sharper boundaries are not verified:
empirical Bernstein and finite-grid betting are `NOT_PROVEN`; stitched and
mixture boundaries are `NOT_IMPLEMENTED_NOT_VERIFIED`. `claim_allowed=false`.
