# Prompt 11 — Reporting and Certificate Cards

## Role

You are making CertGen's outputs reviewer-readable without allowing fake paper claims.

## Global rules that apply to this prompt

- Preserve V1 behavior and backward compatibility unless the prompt explicitly asks for a breaking change.
- Do not fabricate real results, benchmark numbers, model rankings, citations, sample availability, or claim language.
- Do not promote smoke, mock, synthetic, fixture, planned, or dry-run outputs into evidence.
- Keep tests CPU-only and small. No GPU job may run inside normal tests.
- Keep heavy imports lazy and optional. The repo must remain usable without torch/torchvision/transformers unless a command explicitly requests feature extraction.
- FID and FD-DINOv2 remain descriptive unless a mathematically valid FID/FD certificate is explicitly implemented and audited. Do not weaken this policy.
- No paid APIs, no paid cloud, no paid datasets, no paid annotation, no hosted inference.
- Mark every generated artifact with evidence status: `smoke_only`, `dry_run_only`, `planned`, `descriptive_only`, or `eligible_after_real_run` as appropriate.
- Every new command must have docs, help text, tests, and an example invocation.
- Every claim-producing path must pass through claim gates.
- If a real run is not executed, output files must explicitly say `NO_REAL_EVIDENCE` or equivalent.
- Do not initialize git, commit, tag, or push.

## Task

Create reporting utilities that convert V2 certificates and pilot plans into clear Markdown/JSON reports.

## Required files

Create or update:

```text
certgen/reporting/certificate_card.py
certgen/reporting/v2_summary.py
certgen/cli/render_certificate_card.py
tests/test_certificate_reporting.py
docs/V2_REPORTING.md
```

## Required certificate card sections

A certificate card must show:

1. Comparison ID.
2. Metric label.
3. Feature/provenance hashes.
4. Evidence status.
5. Method label and theory status.
6. Alpha and budget.
7. Number of sample units seen.
8. Estimate and interval.
9. Decision.
10. Whether claim is allowed.
11. Limitations.
12. FID/FD policy warning if relevant.

## Required output behavior

If evidence status is smoke/demo/dry-run:

- prominent label: `NOT PAPER EVIDENCE`.
- `claim_allowed: false`.
- no language like “published wins are undecided.”

If future real evidence is eventually allowed, the report should still distinguish:

- decided;
- not decided at budget;
- invalid input;
- descriptive-only.

## CLI example

```bash
python3 -m certgen.cli.render_certificate_card   --certificate data/smoke/v2/certificates/smoke_pair_001_kid_certificate.json   --out docs/SMOKE_CERTIFICATE_CARD.md
```

## Tests

Add tests for:

- report contains not-evidence warning for smoke certificate;
- FID warning appears for FID-like outputs;
- report refuses malformed certificate;
- no forbidden claim language appears in smoke report.

## Documentation

`docs/V2_REPORTING.md` must explain how reports are used in V2 and why they are not paper results.

## Done criteria

- Certificate cards render for smoke/demo certificates.
- Claim language remains conservative.
