# CertGen Maximum-Ceiling Single-File Handoff

Status target: `CERTGEN_MAX_CEILING_PRE_RUN_READY` / `BLOCKED_ONLY_BY_REAL_INPUTS_AND_REAL_EXECUTION`.

The fixed ZIP hash matched exactly and replaced the old repository. Git branch and HEAD were preserved; no user-owned runtime inputs existed to copy. Replacement verification earned `CVPR_100_PERCENT_PRE_RUN_READY` before upgrades.

Current reality: no real reference, preflight, generated images, features, gates, certificates, rankings, cross-feature result, or paper evidence exists. Five Kaggle notebooks are locally contract-ready but require real Kaggle validation.

Canonical controls:

- `python3 -m certgen readiness`
- `python3 -m certgen doctor`
- `python3 -m certgen provenance verify --study <study>`
- `python3 -m certgen audit maximum-ceiling --explain --json`

Singular next command:

```bash
python3 -m certgen validate reference --source data/sources/cifar-10-python.tar.gz --explain
```

Do not start another infrastructure build. After local verification passes, further progress requires real inputs or real execution.
