# 11 — V5 Reviewer Simulator and Author Response Bank

## Goal

Build a reviewer-attack harness and response bank that prepares CertGen for CVPR review.

## Add Files

Create:

- `docs/review/REVIEWER_ATTACKS_V5.md`
- `docs/review/AUTHOR_RESPONSE_BANK_V5.md`
- `docs/review/REVIEWER_SCORE_SIMULATOR_V5.md`
- `certgen/review/reviewer_simulator.py`
- `certgen/audit/reviewer_harness_audit.py`
- `tests/test_v5_reviewer_harness.py`

## Required Reviewer Attacks

Include at least these attacks:

1. This is just KID/CMMD with a stopping rule.
2. Anytime-valid CS is known; where is the vision contribution?
3. FID is not certifiable by your method.
4. You do not propose a new metric.
5. The audit is small / only toy datasets.
6. Released samples are biased or cherry-picked.
7. Preprocessing differences invalidate comparisons.
8. Multiple comparisons inflate false discoveries.
9. Dependence between comparisons invalidates your inference.
10. Results are obvious: small gaps are uncertain.
11. The paper is a statistics paper, not CVPR.
12. The contribution overlaps with recent anytime-valid evaluation work.
13. No human preference validation.
14. No video results.
15. Your result does not prove prior papers are wrong.

## Response Bank Rules

Responses must be:

- honest;
- result-aware only after real results exist;
- not overclaiming;
- tied to paper sections or planned artifacts;
- clear about limitations.

## Score Simulator

Create a simple scorecard with axes:

- novelty;
- technical correctness;
- empirical strength;
- CVPR fit;
- reproducibility;
- clarity;
- risk of incremental rejection;
- risk of stats-only rejection.

Before real runs, empirical strength must be low or blocked.

## Tests

Test that:

- attack bank has all required attacks;
- no response includes fake numbers;
- score simulator marks no-results state appropriately;
- FID attack response mentions the FID policy.
