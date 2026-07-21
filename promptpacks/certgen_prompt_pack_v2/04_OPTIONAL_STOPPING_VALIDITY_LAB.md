# Prompt 04 — Optional-Stopping Validity Lab

## Role

You are building the load-bearing demonstration for CertGen: naive peeking can inflate false decisions, while the CertGen confidence sequence controls decisions under the same monitoring.

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

Implement a CPU-only simulation lab that compares naive repeated peeking against the V2 confidence-sequence certificate on synthetic bounded streams.

## Required files

Create or update:

```text
certgen/experiments/optional_stopping_lab.py
certgen/reporting/optional_stopping_report.py
tests/test_optional_stopping_lab.py
```

Add a CLI if project conventions allow:

```bash
python3 -m certgen.experiments.optional_stopping_lab   --out-dir data/results/v2_optional_stopping_lab   --num-replicates 200   --budget 200   --alpha 0.05   --seed 0   --evidence-status smoke_only
```

Tests should use tiny replicate counts only.

## Required simulation settings

At minimum include:

1. Null stream: true mean 0.
2. Negative stream: A genuinely better.
3. Positive stream: B genuinely better.
4. Near-zero stream: hard undecided case.

For each, compare:

- naive fixed-width CI peeked every step;
- naive running mean threshold;
- V2 conservative CS;
- V2 empirical-Bernstein/e-process variant if implemented.

## Required outputs

Output JSON:

```text
data/results/v2_optional_stopping_lab/summary.json
```

Output Markdown:

```text
docs/V2_OPTIONAL_STOPPING_LAB.md
```

The report must include:

- false-decision rate under the null;
- decision rate under alternatives;
- average sample units to decision;
- explicit label: `SMOKE_SIMULATION_ONLY_NOT_REAL_EVIDENCE`;
- warning that this is not a benchmark result.

## Claim gate requirement

The optional-stopping lab may claim only:

> In synthetic smoke simulations, the monitoring path behaves as expected.

It may not claim any real generative-model result.

## Tests

Tests should verify:

- deterministic output with seed;
- summary JSON schema;
- smoke-only labels present;
- naive and CS methods are both reported;
- report refuses to write if evidence status is not smoke/demo for synthetic inputs.

## Done criteria

- Lab command runs on CPU in a few seconds for small settings.
- Tests pass.
- Report clearly states no real evidence.
