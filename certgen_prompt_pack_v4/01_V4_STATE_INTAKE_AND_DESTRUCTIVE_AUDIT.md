# 01 — V4 State Intake and Destructive Audit

Implement a V4 intake audit that aggressively checks the integrity of the V1–V3 repo before broader upgrades.

## Goal

Before adding new V4 functionality, verify that:

- V1–V3 audits exist or are gracefully marked missing;
- smoke/synthetic artifacts are still non-evidence;
- FID/FD-DINOv2 remain descriptive-only;
- V2 clean metric certificates are not mislabeled as real evidence;
- V3 pilot artifacts are not claim-promoted;
- command docs match CLI availability;
- no hardcoded user-specific absolute paths are used in release-facing docs;
- no fake numbers appear in paper-facing docs as claims.

## Implement

Create:

- `certgen/audit/v4_state_intake.py`
- CLI entry point if the project uses CLI modules, e.g. `python3 -m certgen.audit.v4_state_intake`
- `docs/V4_STATE_INTAKE_AUDIT.md`
- `data/results/v4_state_intake_audit.json`
- tests under `tests/`.

## Checks

The audit should include at least these checks:

1. Required core package directories exist.
2. V1/V2/V3 handoff docs exist or are reported as missing with nonfatal status.
3. Every artifact under `data/smoke/` has non-claim evidence status.
4. Every certificate-like JSON found under smoke/synthetic folders has `claim_allowed=false`.
5. Any string such as `undecided fraction`, `ranking changed`, `real audit result`, or `published wins` in docs is guarded by “planned,” “template,” “no real result,” or an equivalent non-claim label.
6. FID policy docs contain “descriptive” and do not contain a claim that FID is rigorously certified.
7. Registry templates are templates, not evidence.
8. Any absolute local path is either in a user-local run note or excluded from release docs.
9. `docs/NO_RESULTS_YET.md` or an equivalent result-boundary doc still exists.
10. Tests can be discovered without requiring external data.

## Destructive tests

Add tests that deliberately create temporary invalid artifacts and confirm the audit fails:

- smoke certificate with `claim_allowed=true`;
- FID certificate marked rigorous;
- paper draft with fake undecided fraction;
- real cache row missing provenance;
- registry claim with no sample availability.

Use temporary directories or monkeypatching; do not corrupt real project files.

## Output

The Markdown report should contain:

- summary table,
- pass/fail count,
- warnings,
- blockers,
- exact next repair command if available.

The JSON should contain:

```json
{
  "audit_name": "v4_state_intake",
  "passed": true,
  "num_checks": 0,
  "num_passed": 0,
  "num_failed": 0,
  "checks": [],
  "blockers": [],
  "warnings": []
}
```

## Acceptance criteria

- Intake audit runs locally without external data.
- At least 10 checks are implemented.
- At least 3 destructive regression tests exist.
- Failure messages are clear and action-oriented.
- Existing V1–V3 tests remain passing.
