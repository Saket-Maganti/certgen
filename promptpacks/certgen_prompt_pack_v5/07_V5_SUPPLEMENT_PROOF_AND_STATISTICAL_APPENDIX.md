# 07 — V5 Supplement, Proof, and Statistical Appendix

## Goal

Prepare a supplement scaffold that makes the statistical contribution reviewable without inventing new theory claims.

## Add Files

Create:

- `paper/supplement.tex`
- `paper/supplement/01_certificate_details.tex`
- `paper/supplement/02_optional_stopping_validity.tex`
- `paper/supplement/03_mmd_kid_cmmd_streams.tex`
- `paper/supplement/04_multiple_comparisons_dependence.tex`
- `paper/supplement/05_fid_fd_policy.tex`
- `paper/supplement/06_reproducibility_details.tex`
- `paper/supplement/07_additional_tables_placeholders.tex`
- `docs/paper/PROOF_OBLIGATION_TRACKER.md`
- `data/contracts/proof_obligations_v5.json`
- `certgen/audit/proof_obligation_audit.py`
- `tests/test_v5_proof_obligations.py`

## Proof Obligation Tracker

Create machine-readable proof obligations:

1. Define comparison estimand `Delta = d(A,R) - d(B,R)`.
2. State assumptions for bounded stream terms.
3. State how stream terms are clipped/bounded.
4. State the confidence sequence validity condition.
5. State optional-stopping theorem or cited theorem.
6. State stopping rule.
7. State multiple-comparison alpha policy.
8. State dependence caveats.
9. State why FID is not part of the rigorous clean-core certificate unless separately handled.
10. State what is empirical validation vs theoretical guarantee.

Each obligation should have:

- `obligation_id`
- `description`
- `status`: `todo|drafted|verified|blocked`
- `requires_external_citation`
- `paper_location`
- `audit_status`

## FID/FD Appendix

The supplement must explicitly say:

- FID is a nonlinear biased functional of sample mean/covariance;
- naive mean-based CS does not directly certify FID;
- CertGen's rigorous clean-core certificate applies to metrics with valid stream/estimator structure;
- FID can be descriptive, block-experimental, or future-work unless made watertight.

## Optional-Stopping Validity Section

Include a result-free explanation of the synthetic validity lab:

- what false-decision rate means;
- how naive peeking is simulated;
- what certificate-controlled monitoring should show;
- why this is methodological validation, not benchmark evidence.

## Tests

Tests should confirm:

- supplement files exist;
- proof obligations load;
- no obligation is falsely marked verified without text location;
- FID caveat exists;
- optional stopping validity section exists;
- no fake theorem/citation is inserted.
