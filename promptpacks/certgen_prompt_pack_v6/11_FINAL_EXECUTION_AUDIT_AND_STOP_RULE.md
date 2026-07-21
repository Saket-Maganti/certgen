# 11 — Final Execution Audit and Stop Rule

Implement `CERTGEN_FINAL_EXECUTION_AUDIT_AND_STOP_RULE`.

Goal:

> Determine whether CertGen should scale, pivot venue, or stop based on real empirical outputs.

## Inputs

- R1E first pilot results;
- R2 scale results if any;
- multi-benchmark availability;
- runtime measurements;
- audit logs;
- evidence gate reports.

## Audit questions

1. Does a real pilot undecided fraction exist?
2. Did null calibration behave correctly?
3. Did obvious-gap sanity behave correctly?
4. Did metric reproduction/sanity pass?
5. Are all feature caches provenance-validated?
6. Is the clean-core certificate technically valid?
7. Are there recognizable model comparisons affected?
8. Is the story CVPR-native enough?
9. Is NeurIPS/ICML/AISTATS a better venue?
10. Should scaling continue?

## Output

Create:

- `docs/FINAL_EXECUTION_AUDIT.md`
- `data/results/final_execution_audit.json`

Statuses:

- `SCALE_TO_10K`
- `SCALE_TO_50K`
- `EXPAND_TO_SECOND_BENCHMARK`
- `PIVOT_TO_NEURIPS_ICML`
- `STOP_OR_MERGE_INTO_CERTEVAL`
- `FIX_TECHNICAL_CORE_FIRST`

## Stop rules

Stop or pivot if:

- undecided fraction near zero and no compute-savings story;
- null calibration falsely decides;
- obvious-gap sanity fails;
- metric reproduction cannot be matched;
- sources/license remain blocked;
- the paper reads as pure stats with no vision consequence;
- no recognizable comparison is affected after scaling.

## Continue rules

Continue if:

- pilot undecided fraction meaningful;
- sanity gates pass;
- feature pipeline works;
- evidence gates remain clean;
- at least one comparison produces a compelling decided/undecided story.

## Final response required

- current project status;
- real evidence status;
- CVPR readiness estimate;
- venue recommendation;
- next exact command;
- whether to continue, scale, pivot, or stop.
