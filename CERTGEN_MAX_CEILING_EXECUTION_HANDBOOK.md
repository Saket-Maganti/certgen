# CertGen Maximum-Ceiling Execution Handbook

This handbook supersedes earlier execution handbooks for current guidance; earlier files remain historical traceability only.

1. Place the official CIFAR archive at `data/sources/cifar-10-python.tar.gz` and run the exact validation command in the readiness report. No command downloads it.
2. Materialize the validated reference, select `cifar_integrity_minimal`, and freeze the study.
3. Run `provenance verify`, `doctor --study`, `scale-plan freeze`, and `sensitivity freeze` before any external outcome exists.
4. Build the private preflight capsule, run the canonical T4x2 preflight notebook, copy back the atomic ZIP, and validate/import it.
5. Repeat the capsule/run/import sequence for generation and feature extraction. Never reuse a completion marker whose study, configuration, asset, preprocessing, worker, or output-schema identity differs.
6. Merge cache-v2 artifacts, freeze metric and sanity gate configs, and require both gates to pass.
7. Freeze the family, build every certificate input through the canonical builder, validate operational coverage, run all family certificates, then build only a certified partial ranking.
8. Run cross-feature analysis, compute accounting, claim validation, paper firewall, provenance verification, and replay verification.
9. Apply the prospective pilot decision. Promotion cannot depend on a favorable metric direction.

Recovery is minimal and lineage-driven: use `python3 -m certgen replay plan --study <study>` and rerun from the first invalidated stage. Public capsules and archives must never contain model weights, credentials, local paths, or real private data.

All pre-run artifacts are non-evidentiary and `claim_allowed=false`.
