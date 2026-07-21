# Prompt 01 — V3 Project-State Intake Audit

Implement a V3 intake audit that checks the repository is actually in the expected post-V2 state before V3 upgrades proceed.

## Goal

Create a lightweight audit command:

```bash
python3 -m certgen.cli.v3_intake_audit \
  --out docs/V3_INTAKE_AUDIT.md \
  --json-out data/results/v3_intake_audit.json
```

The command should verify V1/V2 readiness without doing heavy work.

## Checks

The audit should check:

1. Package import works.
2. V2 clean metric modules exist.
3. V2 certificate API/CLI exists.
4. V2 feature-cache validator exists.
5. V2 registry validator exists.
6. V2 dry-run pilot planner exists.
7. V2 FID policy doc exists.
8. V2 command index exists.
9. V2 handoff doc exists.
10. Smoke certificate artifacts, if present, are non-evidence.
11. `pytest` can be invoked in a subprocess unless disabled by flag.
12. No known forbidden paper-claim strings appear in docs/results from smoke artifacts.
13. `data/results/v2_final_audit.json`, if present, says passed.
14. The repo has no required heavy/GPU import at package import time.
15. The audit itself emits `claim_allowed=false`.

## Important behavior

- If optional V2 outputs are absent, report warning, not always failure.
- If core modules are absent, fail.
- The audit must be deterministic.
- The audit must not recursively call itself in a way that hangs.
- If it runs pytest, allow a skip of recursive audit self-tests.

## Outputs

Markdown report should include:

- title;
- timestamp;
- pass/fail summary;
- table of checks;
- warnings;
- blockers;
- final status;
- explicit statement: `NO_REAL_EVIDENCE_FROM_INTAKE_AUDIT`.

JSON should include:

```json
{
  "audit_name": "v3_intake_audit",
  "passed": true,
  "checks_passed": 15,
  "checks_total": 15,
  "warnings": [],
  "blockers": [],
  "evidence_status": "dry_run_only",
  "claim_allowed": false
}
```

## Tests

Add tests that:
- run the audit in a temp directory or with fixtures;
- verify JSON schema;
- verify claim_allowed is false;
- verify missing core module detection can fail gracefully via monkeypatch.

## Verification

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q
python3 -m certgen.cli.v3_intake_audit --out docs/V3_INTAKE_AUDIT.md --json-out data/results/v3_intake_audit.json
```
