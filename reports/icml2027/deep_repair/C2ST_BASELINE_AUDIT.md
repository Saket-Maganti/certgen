# C2ST baseline audit

The original simple classifier is now explicitly `c2st_centroid`. The new
`c2st_logistic` fits `StandardScaler` inside each training fold, uses seeded
regularized logistic regression, deterministic stratified folds, and seeded
label-permutation p-values. The high-dimensional CPU benchmark contains
12 rows across [64, 768] dimensions and six scenarios.
Both remain non-sequential descriptive/comparator baselines. `claim_allowed=false`.
