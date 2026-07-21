# Prompt 11 — Docs, Commands, and Reproducibility Polish

Polish the codebase so V3 is usable by future-you and reviewer-you.

## Goal

Add coherent documentation and command indexes for V3.

Create/update:

- `docs/COMMAND_INDEX_V3.md`
- `docs/V3_RUNBOOK.md`
- `docs/REPRODUCIBILITY_CAPSULE_V3.md`
- `docs/CLAIM_POLICY_V3.md`
- `docs/FID_POLICY_V3.md`
- `docs/FIRST_REAL_PILOT_CHECKLIST.md`
- `docs/TROUBLESHOOTING_V3.md`
- `README.md` V3 section.

## Command index should include

- V3 intake audit
- validate provenance ledger
- validate feature cache
- plan feature extraction
- audit metric reproduction
- run first pilot
- replay certificate
- render pilot report
- validate V3 registry
- render availability table
- run optional stopping lab
- V3 final audit

For every command include:

- purpose;
- input files;
- output files;
- evidence status;
- whether it can support paper claims;
- example invocation.

## Reproducibility capsule

Must list:
- Python version;
- package dependencies;
- optional heavy dependencies;
- no paid dependencies;
- expected directory layout;
- cache contracts;
- exact order of execution;
- how to reproduce smoke;
- how to reproduce first real pilot when features are provided.

## Claim policy

Make the claim policy explicit:

- what V3 can say;
- what V3 cannot say;
- when a real pilot is claim-eligible;
- how reports must phrase non-claim diagnostics.

## Tests

Add a docs existence test:
- required docs exist;
- command index mentions all V3 CLIs;
- claim policy contains forbidden claims list;
- FID policy says descriptive-only unless rigorous method established.

## Verification

Run pytest.
