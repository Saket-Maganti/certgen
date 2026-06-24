# Prompt 12 — V3 Final Audit and Handoff

Implement the final V3 audit and single-file handoff.

## Goal

Create:

- `certgen/cli/v3_audit.py`
- `docs/V3_FINAL_AUDIT.md`
- `data/results/v3_final_audit.json`
- `docs/V3_SINGLE_FILE_HANDOFF.md`

Command:

```bash
python3 -m certgen.cli.v3_audit \
  --out docs/V3_FINAL_AUDIT.md \
  --json-out data/results/v3_final_audit.json
```

## Required audit checks

At minimum, 20 checks:

1. package import works;
2. V1/V2 compatibility checks pass or are not missing;
3. evidence statuses known and enforced;
4. smoke/dry-run artifacts cannot claim evidence;
5. provenance ledger validator exists and passes template;
6. feature-cache validator exists and passes valid fixture;
7. feature-cache validator rejects NaN/mismatch/restricted license;
8. feature extraction planner dry-run works without heavy deps;
9. metric reproduction audit works on synthetic fixture;
10. first-pilot dry-run planner works;
11. first-pilot real mode works on synthetic validated caches only;
12. clean-core certificates are generated for synthetic caches;
13. FID policy blocks rigorous FID claim by default;
14. certificate replay passes for synthetic certificate;
15. pilot report card renders;
16. claim scanner catches overclaim language;
17. V3 registry validator works;
18. availability table renders;
19. optional-stopping lab tiny config runs;
20. command index includes V3 commands;
21. docs exist;
22. pytest passes, allowing intentional audit-subprocess skip;
23. final audit output is non-evidence;
24. no fake real numbers appear in paper-facing docs.

## Audit output

Markdown:
- title;
- summary;
- check table;
- warnings;
- blockers;
- exact commands run;
- next action;
- final verdict.

JSON:
```json
{
  "audit_name": "v3_final_audit",
  "passed": true,
  "checks_passed": 24,
  "checks_total": 24,
  "warnings": [],
  "blockers": [],
  "evidence_status": "dry_run_only",
  "claim_allowed": false,
  "next_action": "fill provenance ledger for one benchmark and validate real feature caches"
}
```

## Handoff doc

`docs/V3_SINGLE_FILE_HANDOFF.md` should include:

- project status after V3;
- implemented modules;
- command list;
- tests result;
- generated artifacts;
- evidence boundary;
- current limitations;
- exact next V4 action.

## Current limitations section must say

- no real benchmark audit yet unless user has supplied validated real features;
- no decidedness fraction yet unless real pilot was run in validated mode;
- no ranking movement claim;
- FID/FD descriptive-only;
- first paper claim remains blocked until real gates pass.

## Verification

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q
python3 -m certgen.cli.v3_audit --out docs/V3_FINAL_AUDIT.md --json-out data/results/v3_final_audit.json
```
