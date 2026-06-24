# Prompt 05 — FID Policy and Descriptive Handling

## Objective

Make the FID limitation explicit in code, docs, and tests. This prompt exists to prevent the most dangerous overclaim in CertGen: pretending FID has a clean anytime-valid certificate when it does not.

## Required context

Read:

- `CERTGEN_PROJECT_MASTER_CONTEXT.md`, especially the FID landmine section
- `00_GLOBAL_RULES_FOR_ALL_PROMPTS.md`
- Prompt 01–04 outputs

## Required policy

FID is allowed in V1 only as:

- fixed-n descriptive point estimate;
- descriptive ranking input;
- optional experimental block-CS placeholder that is explicitly not paper-grade;
- a target for later V2 mathematical resolution.

FID is **not** allowed in V1 as:

- rigorous anytime-valid certificate;
- optional-stopping-safe verdict;
- real evidence candidate;
- paper claim.

## Implement FID policy gate

In `certgen/gates/fid_policy_gate.py`, implement:

```python
validate_fid_certificate_request(metric_record, requested_rigor, mode) -> PolicyDecision
```

Behavior:

- if metric family is not FID, pass through;
- if metric is FID and requested path is `clean_cs`, fail;
- if FID is `descriptive_only`, allow only descriptive reports;
- if FID is `block_cs_experimental`, allow only if status is non-evidence and limitations include `experimental`;
- no V1 path may output `optional_stopping_valid=True` for FID.

## Update metric registry

Ensure every FID-like metric has:

```python
supports_clean_cs = False
fid_rigor_status = "descriptive_only"
```

FD-DINOv2 should be treated similarly unless explicitly implemented as a clean metric later.

## Update certificate logic

If a caller attempts:

```python
make_decision_certificate(... metric_name="fid_inception" ...)
```

then either:

- return a certificate with `status=descriptive_only`, `optional_stopping_valid=False`, and limitations; or
- raise a policy error with a clear message.

Pick one approach and document it. Prefer returning a clear descriptive-only artifact for reports, but never mark it certified.

## Documentation

Write/update:

```text
docs/FID_POLICY.md
```

It should explain:

1. why FID is nonlinear and biased;
2. why naive CS over FID values is invalid;
3. what V1 allows;
4. what future V2 must solve;
5. exact forbidden wording.

Forbidden wording:

- `FID-certified winner`
- `anytime-valid FID result`
- `rigorous FID certificate`
- `FID proves A beats B`

Allowed wording:

- `FID descriptive estimate`
- `FID point estimate`
- `FID block-level exploratory analysis`
- `KID/CMMD certificate with FID shown descriptively`

## Tests

Add tests that:

1. FID cannot enter clean CS path;
2. FID descriptive artifact has `optional_stopping_valid=False`;
3. FID descriptive artifact includes limitations;
4. claim gate blocks forbidden FID certificate phrases;
5. docs contain the FID warning;
6. FD-DINOv2 is not accidentally marked clean-CS supported unless explicitly implemented.

## Acceptance criteria

Run:

```bash
python -m pytest -q
```

Then write `docs/V1_FID_POLICY_REPORT.md`.
