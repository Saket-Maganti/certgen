# Normalization-aware synthetic audit

Every production scenario is classified as NULL, INVARIANCE_CONTROL, EASY_ALTERNATIVE, HARD_ALTERNATIVE, REPRESENTATION_SPECIFIC_ALTERNATIVE, or REFERENCE_DESIGN_STRESS. Before/after diagnostics record mean and covariance differences, norm statistics, paired-MMD estimate, and cosine statistics.

`scale_shift` and isotropic `variance_inflation` are positive radial rescalings erased by row-wise L2 normalization. They are invariance controls and are excluded from power. Diagnostics are synthetic checks, not evidence.

See `reports/icml2027/production_mmd/SCENARIO_CLASSIFICATION.csv` and `PREPROCESSING_EFFECT_DIAGNOSTICS.csv`. `claim_allowed=false`.
