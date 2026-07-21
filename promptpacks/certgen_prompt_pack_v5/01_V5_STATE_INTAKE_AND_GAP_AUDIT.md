# 01 — V5 State Intake and Gap Audit

Implement a V5 intake audit that verifies the V4 state before adding new work.

## Goal

Create a module and CLI that reads the current repository state and produces a V5 gap report:

- what V4 artifacts exist;
- which commands exist;
- which tests pass;
- which paper-facing elements are missing;
- which execution-facing elements remain blocked;
- what V5 must add.

## Suggested Files

Add or update:

- `certgen/audit/v5_state_intake.py`
- `certgen/cli/v5_state_intake.py`
- `docs/V5_STATE_INTAKE.md`
- `data/results/v5_state_intake.json`
- `tests/test_v5_state_intake.py`

## Required Checks

The intake audit should check for:

1. `docs/V4_FINAL_AUDIT.md`
2. `data/results/v4_final_audit.json`
3. `docs/V4_SINGLE_FILE_HANDOFF.md`
4. `docs/COMMAND_INDEX_V4.md`
5. V4 final audit has `passed=true` if JSON is present.
6. V4 artifacts do not claim real evidence.
7. No `claim_allowed=true` appears in smoke/dry-run result directories.
8. V4 known warning about unknown-license template rows is documented, not silently ignored.
9. Core package imports.
10. Pytest command works.
11. Paper scaffold either missing or present but incomplete.
12. Supplement scaffold either missing or present but incomplete.
13. Result contracts either missing or present but incomplete.
14. Related-work board either missing or present but citation verification incomplete.
15. V5 worklist is emitted.

## Output JSON Schema

The JSON should include:

```json
{
  "v5_state_intake_version": "0.5.0",
  "timestamp_utc": "...",
  "v4_detected": true,
  "v4_audit_passed": true,
  "tests_status": "passed|failed|not_run",
  "claim_boundary_status": "clean|warning|failed",
  "missing_cvpr_ready_items": [],
  "required_v5_actions": [],
  "passed": true
}
```

## Report

Generate `docs/V5_STATE_INTAKE.md` with:

- detected state;
- missing pieces;
- risk list;
- recommended V5 implementation order.

## Tests

Add tests that:

- mock or use fixture V4 JSON;
- verify missing critical files fail intake;
- verify unsupported claim artifacts fail intake;
- verify generated worklist includes paper/supplement/result contracts when absent.
