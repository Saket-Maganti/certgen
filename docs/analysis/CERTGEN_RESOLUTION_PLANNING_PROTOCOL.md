# Synthetic Resolution Planning Protocol

The planner uses deterministic bounded Bernoulli-difference streams to compare 1k, 10k, and 50k budgets over a fixed effect grid. It records resolution curves, first-crossing summaries, and unresolved rates with Monte Carlo standard errors. Every output is labeled `planning_simulation_only`, `not_model_evidence`, `not_empirical_power`, and `claim_allowed=false`. It can reject obviously weak spending plans but cannot predict real model performance.
