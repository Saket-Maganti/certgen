# Prompt 08 — Final V1 Audit and Handoff

## Objective

Run a final V1 audit of the CertGen basics. Confirm that the repository is ready for V2 certificate refinement and first-pilot preparation, while still making no real empirical claims.

## Required context

Read:

- `CERTGEN_PROJECT_MASTER_CONTEXT.md`
- `00_GLOBAL_RULES_FOR_ALL_PROMPTS.md`
- Prompt 01–07 outputs

## Final audit checklist

Implement a CLI:

```bash
python -m certgen.cli.v1_audit --out docs/V1_FINAL_AUDIT.md --json-out data/results/v1_final_audit.json
```

The audit should check:

1. package imports;
2. smoke config exists and validates;
3. schemas serialize/deserialize;
4. evidence statuses are enforced;
5. claim gate catches forbidden phrases;
6. FID policy gate blocks clean-CS FID claims;
7. smoke metrics can run on toy arrays;
8. clean-core certificate can run on toy delta streams;
9. reports pass claim gate;
10. `NO_RESULTS_YET.md` exists;
11. registry templates exist;
12. no generated artifact is marked real evidence;
13. no docs claim real audit findings;
14. command index exists;
15. pytest passes, if the audit can call it safely or parse a provided test log.

If any item fails, audit status must be `failed`. Do not produce `passed` unless the checks actually pass.

## Handoff document

Create:

```text
docs/V1_SINGLE_FILE_HANDOFF.md
```

It should include:

- what CertGen is;
- what V1 built;
- what V1 did not build;
- exact commands to run;
- evidence status policy;
- FID limitation;
- next step for V2;
- the first-pilot go/no-go number;
- current status: no real results.

## Final command sequence

Run:

```bash
python -m pytest -q
python -m certgen.cli.validate_config --config configs/certgen_v1_smoke.yaml
python -m certgen.cli.make_smoke_artifacts --config configs/certgen_v1_smoke.yaml --out-dir data/smoke/v1 --compute-metrics --make-certificate
python -m certgen.cli.validate_registry --benchmarks registry/candidate_benchmarks_template.csv --pairs registry/candidate_model_pairs_template.csv
python -m certgen.cli.plan_first_pilot --pairs registry/candidate_model_pairs_template.csv --out docs/FIRST_PILOT_PLAN.md
python -m certgen.cli.v1_audit --out docs/V1_FINAL_AUDIT.md --json-out data/results/v1_final_audit.json
```

If a command is not implemented yet, either implement it or explicitly record it as missing in the audit.

## Required final response from the agent

Return:

1. V1 audit status;
2. total tests run and pass/fail count;
3. files created/modified;
4. commands available;
5. current limitations;
6. exact next prompt for V2.

Do not claim CertGen is paper-ready. It is only V1 foundation-ready.
