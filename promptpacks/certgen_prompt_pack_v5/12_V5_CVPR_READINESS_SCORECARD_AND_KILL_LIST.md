# 12 — V5 CVPR Readiness Scorecard and Kill List

## Goal

Create a brutally honest CVPR-readiness scorecard that separates infrastructure readiness from empirical readiness.

## Add Files

Create:

- `docs/CVPR_READINESS_SCORECARD_V5.md`
- `docs/CVPR_KILL_LIST_V5.md`
- `data/results/cvpr_readiness_scorecard_v5.json`
- `certgen/audit/cvpr_readiness.py`
- `tests/test_v5_cvpr_readiness.py`

## Score Categories

Score each from 0–10:

1. Paper framing.
2. Statistical correctness.
3. Clean-core metric implementation.
4. FID/FD policy honesty.
5. Provenance/release readiness.
6. Reproducibility.
7. Related-work preparedness.
8. Result-contract readiness.
9. Reviewer-defense readiness.
10. Empirical evidence readiness.
11. Empirical evidence actual status.
12. CVPR submission readiness.

Before real runs, `Empirical evidence actual status` must remain low and clearly marked.

## Kill List

Include hard killers:

- no released samples for meaningful pairs;
- unable to reproduce point estimates;
- FID policy overclaimed;
- undecided fraction near zero and no compute-savings story;
- reviewer sees it as incremental KID with stopping rule;
- related work misses obvious papers;
- paper reads like stats-only;
- no ranking or audit consequence;
- claim gates allow fake evidence;
- paper contains unsupported result numbers.

## Status Labels

Use:

- `blocked`
- `not_started`
- `in_progress`
- `ready_except_runs`
- `ready_with_real_results`
- `submission_ready`

Expected after V5:

- infrastructure: `ready_except_runs`
- empirical evidence: `not_started` or `blocked_until_real_runs`
- submission: `not_submission_ready`

## Tests

Test that:

- no-results state cannot receive high empirical score;
- unsupported result numbers fail readiness;
- kill-list contains all required killers;
- readiness JSON and markdown agree.
