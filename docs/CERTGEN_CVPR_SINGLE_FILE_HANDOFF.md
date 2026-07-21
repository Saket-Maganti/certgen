# CertGen CVPR Single-File Handoff

Authoritative operational source: `CERTGEN_CVPR_RUN_READY_EXECUTION_HANDBOOK.md`.

Current status: `CVPR_RUN_READY_BLOCKED_BY_REFERENCE_INPUT`. Code, notebooks, schemas, importers, cache-v2 merge, recovery, and portable release are locally contract-tested. The root CIFAR archive is only an unvalidated candidate. Real reference manifests, model/extractor preflights, generation, feature caches, metrics, certificates, and rankings are absent. No paper evidence exists.

One next command:

```bash
python3 -m certgen validate reference --source cifar-10-python.tar.gz --explain
```

Then follow stages 3–27 of the handbook without skipping validators. Stop after the first partial ranking and interpret it before new build work. `claim_allowed=false`.
