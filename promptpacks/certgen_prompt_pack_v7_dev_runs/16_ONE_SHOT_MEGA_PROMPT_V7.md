You are working on CertGen in `/Users/saketmaganti/Projects/certGen` after V6.

Global non-negotiables:
- Do not fabricate results.
- Do not create `claim_allowed=true` unless a specific real-evidence gate later permits it; for V7, keep `claim_allowed=false`.
- Do not use smoke/template/synthetic outputs as real evidence.
- Do not run certificates unless real feature caches and metric/sanity gates pass.
- Do not claim rigorous FID certification. FID remains descriptive-only.
- Polynomial KID remains descriptive/non-certified by default unless a separate valid bounded/nonasymptotic justification is implemented and audited.
- Rigorous certificate path remains bounded RBF-MMD / bounded CMMD / valid bounded streams.
- Kaggle T4×2 is for sample generation and feature extraction only. CPU/local is for validation, packaging, metric reproduction, certificates, reports, and audits.
- Every output must clearly label whether it is `NO_REAL_EVIDENCE`, `pilot_only`, `not_paper_evidence`, or `run_log_only`.
- Do not build generic V7 fluff. Build execution leverage: commands, notebooks, validators, packaging, recovery, and run lanes that get the first real pilot unstuck and scalable.

# V7 One-Shot Mega Prompt — Developmental Runs + Kaggle Bookruns

Execute all V7 prompts 00–15 in order.

Do not create V8 or any generic infrastructure.

Your mission is to make CertGen practically runnable from current blocked state to first real CIFAR-10 pilot with clean CPU/Kaggle handoff:

- stronger local CIFAR reference onramps;
- Kaggle T4×2 generation bookrun notebook;
- Kaggle T4×2 feature extraction bookrun notebook;
- input ZIP packaging;
- output ZIP import/validation/recovery;
- run ledger;
- stage dashboard;
- scale lanes;
- failure recovery;
- metric/sanity gates;
- certificate pilot upgrades;
- notebook quality validator;
- paper result leakage gate;
- final V7 audit/handoff.

Do not run Kaggle locally. Do not fabricate Kaggle outputs. Do not run certificates unless real feature caches and metric/sanity gates pass.

After implementation, run:

```bash
PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES="" python3 -m pytest -q
PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES="" python3 -m certgen.audit.v7_execution_development_audit --out docs/V7_EXECUTION_DEVELOPMENT_AUDIT.md --json-out data/results/v7_execution_development_audit.json
PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES="" python3 -m certgen.audit.final_execution_audit --out docs/FINAL_EXECUTION_AUDIT.md --json-out data/results/final_execution_audit.json
```

Final response must report:

- tests passed;
- V7 audit status;
- final execution audit status;
- files changed;
- notebooks created;
- CPU commands added;
- ZIP builders/validators added;
- current blocker;
- exact next CPU command;
- exact next Kaggle step;
- estimated runtimes;
- confirmation of no fake results, no paper evidence, no `claim_allowed=true`, no FID certificate, no premature certificate run.
