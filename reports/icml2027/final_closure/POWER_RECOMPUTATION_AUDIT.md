# True-alternative power recomputation

After excluding NULL, invariance, and reference-design controls, the existing quick synthetic production runs contain `68` true-alternative cases. Correct resolution is `2.9412%` and unresolved fraction is `97.0588%`.

Minimum-utility planning gate: `EXPECTED_RESOLUTION_PLANNING_ONLY=RED`. This RED result is prominent: transport is closed, but statistical power remains the main scientific risk.

Per-scenario output includes mean paired-MMD effect, between-run descriptive SD, standardized effect when defined, terminal CS radius, approximate fixed-N Hoeffding requirement, power, and unresolved behavior. The quick profile has one replicate per scenario/dimension/budget and is planning-only, not a power guarantee.

See `reports/icml2027/production_mmd/POWER_RECOMPUTED_TRUE_ALTERNATIVES.csv`. `claim_allowed=false`.
