# Prompt 07 — Certificate Replay and Determinism

Implement certificate replay tools so every certificate can be reproduced from its recorded inputs.

## Goal

Add a replay command:

```bash
python3 -m certgen.cli.replay_certificate \
  --certificate data/results/first_pilot_v3/certificates/modelA_vs_modelB_kid.json \
  --out docs/CERTIFICATE_REPLAY_REPORT.md \
  --json-out data/results/certificate_replay.json
```

## Certificate metadata requirements

Every certificate must include:

- `certificate_id`
- `comparison_id`
- `metric`
- `alpha`
- `seed`
- `max_samples`
- `batch_size`
- `stopping_rule`
- `feature_cache_ids`
- `feature_cache_hashes`
- `preprocessing_ids`
- `certgen_version`
- `code_policy_version`
- `created_at`
- `input_config_hash`
- `contribution_stream_hash` if generated
- `result`
- `evidence_status`
- `claim_allowed`
- `claim_blockers`

## Replay behavior

Replay should:

1. load certificate;
2. verify referenced feature caches or contribution stream if available;
3. recompute certificate result;
4. compare:
   - verdict,
   - stopping sample,
   - final CS lower/upper,
   - undecided status,
   - sample count,
   - warnings/blockers;
5. emit pass/fail.

If required raw inputs are missing:
- replay should emit `replay_status="blocked_missing_inputs"`;
- do not fail with cryptic stack trace.

## Determinism tests

Add tests for:
- same seed same output;
- changed seed changes stream order but remains valid;
- missing input gives blocked status;
- tampered certificate hash gives fail;
- replay report has claim_allowed=false.

## Why this matters

This is a reviewer defense against:
- "your certificates are not reproducible";
- "your pilot result is a one-off";
- "your stopping point was cherry-picked";
- "your code cannot regenerate the reported verdict."

## Verification

Run pytest and replay a synthetic certificate.
