# 13 — V5 Final Audit and Handoff

## Goal

Create the final V5 audit and handoff documents.

## Add Files

Create:

- `certgen/audit/v5_audit.py`
- `docs/V5_FINAL_AUDIT.md`
- `data/results/v5_final_audit.json`
- `docs/V5_SINGLE_FILE_HANDOFF.md`
- `docs/COMMAND_INDEX_V5.md`
- `docs/V5_STOP_CONDITION.md`
- `tests/test_v5_audit.py`

## Required Audit Checks

The V5 final audit must check at least:

1. V5 state intake exists.
2. All tests pass or test command status is recorded.
3. Claim contract exists.
4. Forbidden-claims audit passes.
5. Related-work board exists.
6. Related-work unverified citations are clearly marked.
7. Analysis-plan lock exists.
8. Analysis-plan hash exists.
9. Result contracts exist.
10. Table manifest exists.
11. Figure manifest exists.
12. Main paper scaffold exists.
13. Results section contains placeholders only.
14. Supplement scaffold exists.
15. Proof obligation tracker exists.
16. FID/FD policy exists and is enforced.
17. Reproducibility capsule exists.
18. Release/anonymity scan passes.
19. V5 command bundle exists.
20. Result injection protocol exists.
21. Claim trace protocol exists.
22. Reviewer attack harness exists.
23. Author response bank exists.
24. CVPR readiness scorecard exists.
25. Kill list exists.
26. No fake real evidence exists.
27. No `claim_allowed=true` for smoke/dry-run/template artifacts.
28. V5 handoff exists.
29. V5 command index exists.
30. Stop condition says next action is real execution, not V6 infrastructure.

## Handoff Contents

`docs/V5_SINGLE_FILE_HANDOFF.md` must include:

- current project status;
- what V1–V5 built;
- exact evidence boundary;
- commands to run tests/audit;
- exact next real execution steps;
- current limitations;
- what not to claim;
- what would justify V6;
- final verdict.

## Final Verdict Template

Use this exact shape:

> CertGen is now CVPR-ready-except-runs: the codebase, paper scaffold, result contracts, claim gates, reproducibility capsule, and reviewer defenses are prepared. It is not CVPR-submission-ready because no real claim-eligible empirical audit has been executed. The next step is real execution: populate one provenance ledger, validate/materialize real feature caches, reproduce one metric point estimate, run the first real clean-core pilot in non-claim mode, and only then evaluate the first-benchmark undecided fraction.

## Tests

Test that:

- final audit can run;
- audit JSON has `passed` and `claim_allowed=false` unless real evidence exists;
- handoff contains the final verdict;
- stop condition blocks generic V6 recommendation.
