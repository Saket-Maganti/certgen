# CertGen Prompt Pack V1

**Project:** CertGen / Certified Generative-Model Comparison  
**Target venue:** CVPR 2027 Main Conference  
**Pack purpose:** Give an implementation agent enough context to build the **basic project foundation first** without fabricating results, overbuilding infrastructure, or weakening the statistical framing.

## What this pack is for

This V1 pack is not asking the agent to write the final paper, run full experiments, or claim empirical results. It asks the agent to build the first usable repository skeleton for CertGen:

1. package scaffold;
2. configuration system;
3. schemas for datasets, models, metrics, feature manifests, comparison records, and decision certificates;
4. feature-cache contracts;
5. metric implementations or safe stubs for FID, KID/MMD, CMMD, and FD-DINOv2;
6. clean-core certificate scaffold for MMD-style metrics;
7. strict FID policy guard;
8. claim gates that block mock/smoke/planned outputs from becoming evidence;
9. reporting and audit skeletons;
10. tests proving the basic contracts work.

## Use order

Feed the prompts in this order:

1. `00_GLOBAL_RULES_FOR_ALL_PROMPTS.md`
2. `01_BOOTSTRAP_REPO_SCAFFOLD.md`
3. `02_SCHEMAS_MANIFESTS_AND_CLAIM_GATES.md`
4. `03_FEATURES_AND_METRICS_FOUNDATION.md`
5. `04_CERTIFICATE_CORE_CLEAN_METRICS.md`
6. `05_FID_POLICY_AND_DESCRIPTIVE_HANDLING.md`
7. `06_PILOT_REGISTRY_AND_AUDIT_SCAFFOLD.md`
8. `07_REPORTING_DOCS_REPRODUCIBILITY.md`
9. `08_FINAL_V1_AUDIT_AND_HANDOFF.md`

Use `09_ONE_SHOT_MEGAPROMPT_V1.md` only if you want to ask one agent to do all of V1 in a single run.

## Non-negotiable behavior

- No fake numbers.
- No empirical claims.
- No heavy downloads in tests.
- No GPU work in tests.
- No paid API or paid compute.
- No automatic large dataset/model downloads.
- No rigorous FID certificate claim unless the FID handling is mathematically watertight.
- All mock/smoke/planned artifacts must be clearly marked **non-evidence**.

## V1 success criterion

At the end of V1, the repo should be able to run local CPU tests and produce a **non-evidence smoke decision-certificate artifact** for a toy MMD-style stream. The artifact must explicitly say it is smoke/non-evidence.

V1 is successful if the project has strong contracts and gates. It is **not** successful because it reports any real generative-model result.
