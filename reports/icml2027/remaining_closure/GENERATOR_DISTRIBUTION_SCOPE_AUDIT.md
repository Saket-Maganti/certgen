# Generator-distribution scope audit

Result: **PLANNING_ONLY / NOT_CONFIRMATORY_ELIGIBLE**.

`docs/icml2027/theory/GENERATOR_DISTRIBUTION_RANDOMIZED_DESIGN.md` defines `icml2027_generator_randomized_inference_v1`: seed/randomization law, independent precommitted draws, model output map, reference law, paired-MMD estimand, filtration, precommitment, and the union-Hoeffding optional-stopping event.

The frozen legacy and 10k studies were not changed. A fixed realized seed manifest supports exact reproducibility and its already-declared probability-space target; it does not silently justify a broader generator-population claim. The new design requires a separately frozen prospective version and completed theorem mapping before eligibility. `claim_allowed=false`.
