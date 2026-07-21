# Kaggle runtime assumptions

Every duration is `PLANNING_ESTIMATE_NOT_MEASURED`, not a measured CertGen result. Ranges assume Kaggle GPU T4 x2, one worker per GPU, pinned dependencies, warm private caches after preflight, resumable deterministic shards, and no queue or restart delay. Real diagnostic and preflight artifacts replace planning assumptions only in typed runtime records; they never become empirical model evidence. `claim_allowed=false`.
