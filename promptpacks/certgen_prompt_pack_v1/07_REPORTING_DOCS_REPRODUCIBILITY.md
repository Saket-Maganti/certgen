# Prompt 07 — Reporting, Docs, and Reproducibility Capsule Skeleton

## Objective

Create the V1 reporting and reproducibility skeleton so every future CertGen run is auditable, claim-safe, and easy to reproduce. Do not add real results.

## Required context

Read:

- `CERTGEN_PROJECT_MASTER_CONTEXT.md`
- `00_GLOBAL_RULES_FOR_ALL_PROMPTS.md`
- Prompt 01–06 outputs

## Reporting modules

Implement:

```text
certgen/reporting/certificate_report.py
certgen/reporting/audit_summary.py
```

### Certificate report

Given a certificate JSON, output a markdown report with:

- comparison id;
- metric;
- alpha;
- status;
- sample budget;
- n at decision if applicable;
- optional-stopping validity flag;
- evidence status;
- FID rigor status if relevant;
- limitations;
- provenance.

For non-evidence smoke reports, the title must include:

```text
NON-EVIDENCE SMOKE REPORT
```

### Audit summary

For V1, produce only a placeholder summary with no results. It should say:

- no literature audit has been run;
- templates exist;
- no decidedness fraction is available;
- no ranking change is claimed.

## Reproducibility docs

Create/update:

```text
docs/REPRODUCIBILITY_CAPSULE_V1.md
docs/COMMAND_INDEX_V1.md
docs/NO_RESULTS_YET.md
docs/RELATED_WORK_TODO.md
docs/REVIEWER_ATTACKS_V1.md
docs/ANONYMITY_AND_RELEASE_POLICY.md
```

### REPRODUCIBILITY_CAPSULE_V1.md

Include:

- environment assumptions;
- CPU test commands;
- optional future Kaggle feature-extraction note;
- artifact directories;
- evidence status policy;
- how to regenerate smoke outputs.

### COMMAND_INDEX_V1.md

List all commands added so far, with one-line purpose and evidence status.

### NO_RESULTS_YET.md

This is a claim-safety document. It must say:

> CertGen currently has no real empirical results, no audit number, no decidedness fraction, no ranking changes, and no paper evidence.

### RELATED_WORK_TODO.md

List categories to cite later without fabricating citations:

- FID flaws and generative metrics;
- CMMD / Rethinking FID;
- FVD content bias;
- KID/MMD;
- FID bias correction;
- sequential kernel two-sample testing;
- anytime-valid confidence sequences / e-processes;
- preprocessing sensitivity;
- generative evaluation reproducibility.

Do not invent BibTeX entries unless verified.

### REVIEWER_ATTACKS_V1.md

Include attacks and defenses:

- just KID with stopping rule;
- FID certificate invalid;
- stats paper not vision;
- no real audit headline;
- template fatigue;
- sample availability;
- preprocessing mismatch.

## Tests

Add tests that:

1. generated reports pass claim gate;
2. `NO_RESULTS_YET.md` exists and contains the required no-results statement;
3. command index includes every CLI command;
4. related-work TODO contains no fake citation placeholders like `[1]` without source;
5. reproducibility capsule mentions evidence status.

## Acceptance criteria

Run:

```bash
python -m pytest -q
python -m certgen.cli.make_smoke_artifacts --config configs/certgen_v1_smoke.yaml --out-dir data/smoke/v1 --compute-metrics --make-certificate
```

Then write `docs/V1_REPORTING_REPRODUCIBILITY_REPORT.md`.
