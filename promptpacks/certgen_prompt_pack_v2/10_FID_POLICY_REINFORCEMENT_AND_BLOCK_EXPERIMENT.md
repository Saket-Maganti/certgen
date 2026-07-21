# Prompt 10 — FID Policy Reinforcement and Optional Block-FID Experiment

## Role

You are preventing the most obvious reviewer kill-shot: claiming a rigorous anytime-valid FID certificate when FID is a biased nonlinear functional.

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

Strengthen the FID/FD-DINOv2 descriptive-only policy and optionally add a clearly labeled block-FID experimental module that cannot be used for paper claims without future proof/audit.

## Required files

Create or update:

```text
certgen/metrics/fid.py
certgen/certs/fid_policy.py
certgen/cli/check_fid_policy.py
tests/test_fid_policy_v2.py
docs/V2_FID_POLICY.md
```

## Required policy behavior

By default:

- FID may be computed as a point estimate.
- FD-DINOv2 may be computed as a point estimate.
- FID/FD may appear in descriptive reports.
- FID/FD may not produce `rigorous_anytime_certificate=True`.
- FID/FD may not be used as the sole claim basis.
- Any FID certificate-like output must be labeled `descriptive_only` or `experimental_not_for_claims`.

## Optional block-FID experiment

If implemented, block-FID should:

- split generated/reference features into deterministic blocks;
- compute FID per block;
- produce a rough interval over block estimates;
- mark output `experimental_not_for_paper_claims`;
- document why this is not equivalent to a rigorous anytime-valid FID certificate.

## CLI

```bash
python3 -m certgen.cli.check_fid_policy   --certificate data/smoke/v2/certificates/example_fid_like.json
```

It should fail if a FID/FD output claims rigorous certification.

## Tests

Add tests that:

- FID point estimate can be computed on synthetic features;
- FID certificate claims are blocked;
- block-FID outputs are labeled experimental if present;
- claim gate refuses FID-only rigorous claims.

## Documentation

`docs/V2_FID_POLICY.md` must explain:

- why FID is hard for CS;
- what is allowed in V2;
- what would be required to upgrade it later;
- how to write honest paper language.

## Done criteria

- FID policy tests pass.
- No path can accidentally mark FID rigorous.
