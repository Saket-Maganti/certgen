# V7 Expected Final State

After V7, the repo should be more execution-capable, not merely bigger.

Expected additions:

- CIFAR-10 auto-detection and guided materialization.
- Kaggle T4×2 generation bookrun notebook with timed/resumable/blocked-safe execution.
- Kaggle T4×2 feature extraction bookrun notebook with role-aware feature cache outputs.
- CPU import/validation/recovery for copied-back Kaggle output ZIPs.
- Run ledger and dashboard.
- 1k/10k/50k scale lane configs and escalation gates.
- Checkpoint adapter preflight and failure playbook.
- Metric/sanity gate enhancements.
- Certificate pilot sensitivity expansion, still gated.
- Multi-benchmark candidate onramp, not execution.
- Kaggle dataset packaging automation.
- Notebook quality validator.
- Paper result leakage gate.
- Final V7 audit and handoff.

Expected status if real data is still absent:

- Final execution audit may remain `BLOCKED_MISSING_REFERENCE_SAMPLES`. That is acceptable if true.
- V7 audit should pass because the execution bridge is stronger.

Expected status after the user provides CIFAR root/archive:

- Reference materialization should pass.
- Next blocker should become generation output ZIP missing.
- Kaggle generation notebook should be the next action.

Expected status after Kaggle 1k generation output is copied back:

- Generation validation should pass or fail honestly.
- Next blocker should become feature input/output stage.

Expected status after feature extraction output is copied back:

- Feature validation should pass or fail honestly.
- Next blocker should become metric/sanity gates.

Expected status after metric/sanity gates pass:

- CPU certificate pilot can run.
- First pilot undecided fraction can be produced as pilot-only, not paper evidence.
