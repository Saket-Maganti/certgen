# Operational Family Gate

A metadata-frozen family is not executable until `certgen validate family-operational` finds exactly one valid bundle for every unique hypothesis, every frozen feature space/control/budget, exact Bonferroni allocation, no extra bundle, matching frozen extractor declarations, and `claim_allowed=false` throughout. Only then is `FAMILY_OPERATIONALLY_READY` returned.
