# 14 — One-Shot Megaprompt V5

Use this only if staged execution is not possible. Staged execution is strongly preferred.

---

You are implementing CertGen V5 in `/Users/saketmaganti/Projects/certGen`.

V4 is reported as implemented and verified: V4 final audit passed 27/27, tests 92 passed, `claim_allowed=false`, `evidence_status=dry_run_only`. Do not trust this blindly; verify repository state first.

Your mission: bring CertGen to **CVPR-ready-except-runs**.

This means adding paper-readiness, result contracts, claim tracing, supplement/proof scaffold, related-work board, reproducibility capsule, reviewer harness, command bundles, and a final V5 audit — without executing real heavy runs and without promoting fake empirical evidence.

Implement the following V5 components:

1. V5 state intake and gap audit.
2. CVPR paper identity and machine-readable claim contract.
3. Forbidden/allowed claim scanner.
4. Real-citation related-work board with verification status.
5. Preregistration and analysis-plan lock with hash.
6. Result contracts for all planned tables/figures.
7. Main CVPR paper scaffold with result placeholders only.
8. Supplement/proof/statistical appendix scaffold.
9. FID/FD policy appendix and enforcement.
10. Reproducibility/artifact/anonymity capsule.
11. V5 command bundles for real pilot execution, safe by default.
12. Result injection and claim trace protocol.
13. Reviewer attack harness and author response bank.
14. CVPR readiness scorecard and kill list.
15. Final V5 audit and single-file handoff.

Rules:

- Do not fabricate citations.
- Do not fabricate results.
- Do not make smoke/synthetic/dry-run artifacts evidence.
- Do not set `claim_allowed=true` unless real gates pass.
- Do not claim rigorous FID certification unless the FID policy says it is solved and audited.
- Keep V1–V4 compatibility.
- Keep heavy dependencies optional.
- Add tests for all new gates.
- Update command index and README.

Expected final state:

- tests pass;
- V5 audit passes;
- `docs/V5_FINAL_AUDIT.md` exists;
- `data/results/v5_final_audit.json` exists;
- `docs/V5_SINGLE_FILE_HANDOFF.md` exists;
- `docs/COMMAND_INDEX_V5.md` exists;
- paper scaffold exists;
- supplement scaffold exists;
- result contracts exist;
- analysis-plan lock exists;
- claim trace exists;
- release scan passes;
- no fake real evidence exists;
- final handoff says next action is real execution, not more infrastructure.

After implementation, run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q
python3 -m certgen.audit.v5_audit \
  --out docs/V5_FINAL_AUDIT.md \
  --json-out data/results/v5_final_audit.json
```

Then summarize:

- test count;
- audit status;
- files added;
- claim boundary status;
- exact next real execution step.
