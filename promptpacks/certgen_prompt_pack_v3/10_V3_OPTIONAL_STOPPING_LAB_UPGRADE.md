# Prompt 10 — Optional-Stopping Lab Upgrade

Upgrade the optional-stopping lab from smoke-only into a stronger reviewer-facing diagnostic.

## Goal

Show why CertGen exists:

> naive repeated peeking can inflate false decisions, while the certificate keeps error controlled under the same monitoring.

Files:

- `certgen/stats/optional_stopping_lab.py`
- `certgen/cli/run_optional_stopping_lab.py`
- `docs/OPTIONAL_STOPPING_LAB_V3.md`

## Required scenarios

Implement lightweight CPU simulations:

1. Null case: two models have equal distributional distance.
2. Small-effect case: one model is slightly better.
3. Medium-effect case: one model clearly better.
4. Heavy-tailed bounded-transformed contribution case.
5. Multiple-peek schedule: every batch vs sparse peeks.

## Compare methods

- naive fixed-n interval peek-and-stop;
- naive running mean threshold;
- CertGen bounded CS;
- optional: empirical Bernstein CS if already implemented.

## Outputs

- false decision rate under null;
- stopping time distribution;
- power under alternatives;
- average samples to decision;
- plots as CSV/JSON data, not necessarily images;
- Markdown report.

## Evidence behavior

All optional-stopping lab outputs are **simulation evidence about method behavior**, not generative-model empirical evidence.

Use:

```json
"evidence_status": "synthetic_only",
"claim_allowed": false
```

## Tests

- small deterministic simulation completes fast;
- null false decision rate output exists;
- report includes warning not to use as real benchmark evidence;
- method names correct;
- seeds make outputs deterministic.

## CLI

```bash
python3 -m certgen.cli.run_optional_stopping_lab \
  --config configs/optional_stopping_lab_v3.yaml \
  --out docs/OPTIONAL_STOPPING_LAB_V3.md \
  --json-out data/results/optional_stopping_lab_v3.json
```

## Verification

Run pytest and a tiny lab config.
