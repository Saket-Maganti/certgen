# Final Run-Ready Handoff Audit

- Final status: `CVPR_RUN_READY_BLOCKED_ONLY_BY_REFERENCE_INPUT`.
- Canonical handbook: `CERTGEN_CVPR_FINAL_RUN_READY_EXECUTION_HANDBOOK.md`.
- Selected profile: `cifar_integrity_minimal`.
- Selected models: Google DDPM CIFAR candidate and Frank DDPM EMA CIFAR candidate.
- Selected extractors: Inception and projected-image-embedding CLIP.
- Registered but excluded: CFM and DINO expansion lanes; explicit selection fails closed.
- Study/family continuity: minimal study freeze feeds the canonical six-hypothesis family.
- Portable release: preseal archive passed import, non-Git tests, notebook audit, and synthetic runtime.
- Evidence boundary: local software and synthetic fixture validation only; no model or paper evidence.
- Claim permission: false everywhere.
- Known local defects: none.
- External blocker: `BLOCKED_USER_MUST_PROVIDE_CIFAR_REFERENCE`; the official CIFAR archive/reference input is not present.
- Exact next command: `python3 -m certgen validate reference --source data/sources/cifar-10-python.tar.gz --explain`.
- Stop-building rule: only an observed real-execution defect justifies a further patch.
