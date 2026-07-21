# 11 — V4 Reviewer Attack Harness and Response Bank

Build a reviewer-facing stress test for the CertGen paper direction.

## Goal

CertGen's biggest risk is incrementalism: reviewers may say it is KID with a stopping rule, stats not vision, or invalid for FID. V4 should add an attack harness and response bank so the project is hardened before writing.

## Implement

Create:

- `certgen/review/attacks.py`
- `certgen/review/score_simulator.py`
- `certgen/cli/run_reviewer_attack_harness.py`
- `docs/REVIEWER_ATTACKS_V4.md`
- `docs/AUTHOR_RESPONSE_BANK_V4.md`
- tests.

## Required attacks

Include at least these attack cards:

1. “This is just KID with error bars.”
2. “Anytime-valid inference is known; what is new?”
3. “FID is nonlinear, so your certificate is invalid.”
4. “This is a statistics paper, not CVPR.”
5. “No new metric.”
6. “Only toy datasets.”
7. “Published metric gaps are already known to be noisy.”
8. “You selected only small gaps to make papers look bad.”
9. “Preprocessing mismatch invalidates your audit.”
10. “Multiple comparisons inflate false discoveries.”
11. “Reference samples are reused; independence is violated.”
12. “Video extension is too shallow.”
13. “Zero-cost constraint limits scope too much.”
14. “No human preference validation.”
15. “The tool does not change conclusions.”

## For each attack, include

- severity,
- likelihood,
- what evidence would answer it,
- required artifact,
- current status,
- response draft,
- blocker status.

## Score simulator

Create a simple heuristic CVPR scorecard:

- novelty,
- technical correctness,
- empirical strength,
- reproducibility,
- clarity,
- significance,
- limitations honesty.

Do not pretend this predicts acceptance. It is an internal triage tool.

## Acceptance criteria

- Attack harness outputs Markdown and JSON.
- At least 15 attacks exist.
- At least 5 attacks are marked as blockers before real evidence.
- Response bank does not overclaim.
