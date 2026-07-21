# 10 — V5 Result Injection and Claim Trace System

## Goal

Prepare a safe mechanism for later real results to be injected into paper tables/figures only if they pass provenance, reproduction, certificate, and claim gates.

## Add Files

Create:

- `certgen/paper/result_injection.py`
- `certgen/audit/claim_trace_audit_v5.py`
- `data/contracts/result_injection_contract_v5.json`
- `docs/paper/RESULT_INJECTION_PROTOCOL.md`
- `docs/paper/CLAIM_TRACE_PROTOCOL.md`
- `tests/test_v5_result_injection.py`

## Claim Trace Object

Each paper claim must trace to:

- `claim_id`
- `paper_location`
- `result_artifact_id`
- `source_provenance_id`
- `feature_cache_id`
- `preprocessing_lock_id`
- `metric_reproduction_id`
- `certificate_id`
- `audit_id`
- `evidence_status`
- `claim_allowed`

## Injection Rules

Result injection must fail unless:

- evidence status is at least `evidence_candidate` for draft internal reports;
- evidence status is `claim_eligible` for paper claims;
- claim contract allows the claim type;
- analysis plan hash matches;
- proof/metric limitation requirements are satisfied;
- FID-sensitive claims pass FID policy;
- all cited result artifacts exist.

## Placeholder Behavior

Before real runs, injection should produce paper files with:

- placeholders retained;
- a clear report saying no real result was injected;
- `claim_allowed=false`.

## Result Card

Create a canonical result card schema:

```json
{
  "result_card_id": "...",
  "benchmark": "...",
  "model_pair": "...",
  "metric": "...",
  "verdict": "TBD_REAL_RUN_REQUIRED|A_certified|B_certified|not_decided|invalid",
  "samples_to_decision": "TBD_REAL_RUN_REQUIRED",
  "undecided_fraction_contribution": "TBD_REAL_RUN_REQUIRED",
  "claim_allowed": false,
  "evidence_status": "template_only"
}
```

## Tests

Test that:

- placeholder injection works;
- fake real numbers fail;
- missing claim trace fails;
- FID-sensitive claim fails unless policy-approved;
- analysis-plan hash mismatch blocks injection.
