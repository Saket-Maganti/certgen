# 13 — V4 Final Audit and Handoff

Implement the final V4 audit and handoff document.

## Goal

After V4, the repo should be demonstrably closer to CVPR-range execution, but still honest about what is not done.

## Implement

Create:

- `certgen/audit/v4_audit.py`
- `certgen/cli/v4_audit.py` if project CLI style uses it
- `docs/V4_FINAL_AUDIT.md`
- `data/results/v4_final_audit.json`
- `docs/V4_SINGLE_FILE_HANDOFF.md`
- `docs/COMMAND_INDEX_V4.md`
- tests.

## Required final audit checks

At least 25 checks, including:

1. V4 state intake audit exists.
2. Provenance-to-real-run planner exists.
3. Feature notebook generator exists.
4. Preprocessing lock validator exists.
5. Metric reproduction gate exists.
6. Batch certificate runner exists.
7. Multiple-comparison policy exists.
8. Dependence diagnostics exist.
9. Decidedness audit exists.
10. Ranking stability report exists.
11. First real pilot controller exists.
12. Literature claim ingestion exists.
13. Paper figure/table scaffold exists.
14. CVPR paper scaffold or doc scaffold exists.
15. Claim-language audit exists.
16. Reviewer attack harness exists.
17. Reproducibility capsule validator exists.
18. Release safety scan exists.
19. FID policy remains descriptive unless justified.
20. Smoke/synthetic artifacts remain non-claim.
21. No result claims are present without real evidence.
22. Tests pass or audit records exact failure.
23. Command index updated.
24. Handoff summarizes blockers.
25. Next V5 action is concrete.

## Handoff structure

`docs/V4_SINGLE_FILE_HANDOFF.md` should include:

- project status,
- what V4 added,
- tests/audit status,
- commands,
- evidence boundary,
- current blockers,
- exact next V5 action,
- go/no-go number still needed,
- warning not to build endlessly before first real pilot.

## Final commands

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q
python3 -m certgen.audit.v4_audit \
  --out docs/V4_FINAL_AUDIT.md \
  --json-out data/results/v4_final_audit.json
```

If the audit entrypoint differs, update `docs/COMMAND_INDEX_V4.md`.

## Acceptance criteria

- Final V4 audit passes.
- At least 25 checks implemented.
- Handoff is clear enough for a fresh agent to continue.
- No fake real evidence exists.
- Exact V5 next action is listed.
