# Prompt 05 — Clean Metric Certificate API

## Role

You are packaging the V2 MMD/KID/CMMD stream and CS logic into a stable certificate API that future pilots can call.

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

Create a high-level API and CLI for clean-core metric certificates over feature arrays.

## Required files

Create or update:

```text
certgen/certs/api.py
certgen/certs/io.py
certgen/cli/certify_clean_metric.py
tests/test_certify_clean_metric_cli.py
```

If the project uses a different CLI pattern, follow the existing pattern.

## Required API

Implement:

```python
certify_clean_metric_comparison(
    features_a_path: str,
    features_b_path: str,
    features_r_path: str,
    metric_label: str,
    kernel_config: dict,
    cs_config: dict,
    comparison_id: str,
    evidence_status: str,
    out_path: str,
) -> DecisionCertificate
```

Supported feature formats in V2:

- `.npz` with key `features`
- `.npy`
- optionally `.jsonl` only for tiny fixtures

Rules:

- Validate shapes.
- Validate finite values.
- Use deterministic sampling/streaming with seed.
- Require bounds/clipping config for CS.
- Refuse `evidence_status='real_evidence'` unless registry and provenance gates exist and pass. In V2, this should usually be blocked.

## Required CLI

Example:

```bash
python3 -m certgen.cli.certify_clean_metric   --features-a data/smoke/v2/features/model_a.npz   --features-b data/smoke/v2/features/model_b.npz   --features-r data/smoke/v2/features/reference.npz   --metric kid_polynomial   --comparison-id smoke_pair_001   --alpha 0.05   --budget-units 100   --clip-lower -10   --clip-upper 10   --out data/smoke/v2/certificates/smoke_pair_001_kid_certificate.json   --evidence-status smoke_only
```

## Required certificate output

Certificate JSON must include:

- all fields from Prompt 03;
- feature hashes;
- stream hash;
- command provenance;
- software version if available;
- `claim_allowed: false` unless real gates pass.

## Tests

Add tests for:

- CLI smoke success;
- missing feature path failure;
- shape mismatch failure;
- NaN/Inf failure;
- refusal to mark smoke data as real evidence;
- output certificate schema;
- deterministic hash output.

## Documentation

Create:

```text
docs/V2_CLEAN_METRIC_CERTIFICATE_API.md
```

Include command examples and output explanation.

## Done criteria

- API and CLI work on tiny feature fixtures.
- Certificates are deterministic.
- Claim gates remain conservative.
