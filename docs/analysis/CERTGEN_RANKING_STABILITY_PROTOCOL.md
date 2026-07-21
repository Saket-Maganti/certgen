# Ranking Stability Protocol

Ranking stability is evaluated only at registered budgets (1k, 10k, and 50k when present). Each comparison/feature-space row records the first budget at which an edge appears, the first-decision sample count, unresolved budgets, decisions by budget, and whether all protocol hashes match.

An apparent disappearance is flagged. If the protocol differs, it is described as a protocol change; under identical protocol hashes it requires an integrity/statistical audit. No total order is forced, and censored unresolved pairs remain unresolved.
