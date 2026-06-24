# Table Manifest V5

`NO_REAL_EVIDENCE`

Every table entry is a contract slot. Numeric entries remain `TBD_REAL_RUN_REQUIRED` before real runs.

## Table 1 - Audit Summary

Columns: benchmark, metric, number_of_model_pairs, decided_A_better, decided_B_better, not_decided_at_budget, invalid_or_rejected, undecided_fraction, claim_status.

## Table 2 - Samples to Decision

Columns: benchmark, model_A, model_B, metric, reported_sample_size, budget, samples_to_decision, verdict, alpha_policy, preprocessing_lock_id.

## Table 3 - Metric Agreement / Disagreement

Columns: benchmark, model_pair, FID_direction_descriptive, KID_certificate_verdict, CMMD_certificate_verdict, DINO_or_other_verdict, disagreement_flag, claim_status.

## Table 4 - Ranking Stability

Columns: benchmark, metric, naive_rank_order, certified_partial_order, number_of_rank_changes, undecided_edges, claim_status.

