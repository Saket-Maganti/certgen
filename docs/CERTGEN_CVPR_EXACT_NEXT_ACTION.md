# CertGen CVPR Exact Next Action

Status: `CVPR_RUN_READY_BLOCKED_BY_REFERENCE_INPUT`.

A 170,498,071-byte candidate exists at `cifar-10-python.tar.gz`. It has not been opened, hashed, layout-validated, or treated as official data during this local-safe repair pass.

Run exactly from the repository root:

```bash
python3 -m certgen validate reference --source cifar-10-python.tar.gz --explain
```

Success means the validator identifies a supported official layout and emits one materialization command. If it fails, replace the candidate with the official CIFAR-10 Python archive and rerun the same command. Until materialization and later real stages complete: no empirical evidence, no paper claim, `claim_allowed=false`.
