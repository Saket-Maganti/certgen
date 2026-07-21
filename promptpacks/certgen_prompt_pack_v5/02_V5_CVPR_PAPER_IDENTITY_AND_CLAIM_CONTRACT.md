# 02 — V5 CVPR Paper Identity and Claim Contract

## Goal

Lock the paper identity and create a strict machine-readable claim contract.

CertGen must read as:

> a metric-agnostic decision/certificate layer for generative-model comparison, not a new metric, not a leaderboard replacement, not a "FID is bad" paper.

## Add Documents

Create:

- `docs/paper/CVPR_PAPER_IDENTITY.md`
- `docs/paper/CLAIM_CONTRACT.md`
- `docs/paper/FORBIDDEN_CLAIMS.md`
- `docs/paper/ALLOWED_PRE_RUN_CLAIMS.md`
- `data/contracts/claim_contract_v5.json`
- `certgen/audit/claim_contract.py`
- `tests/test_v5_claim_contract.py`

## Locked Title Candidates

Use these title candidates:

1. **How Many Samples Until You Know? Anytime-Valid Certificates for Generative Model Comparison**
2. **CertGen: Anytime-Valid, Metric-Agnostic Decision Certificates for Generative-Model Comparison**
3. **Are Generative-Model Wins Statistically Decided? A Peeking-Safe Audit of Visual Generation Metrics**

The default project title can remain CertGen, but the paper-facing preferred title should be candidate 1 unless the user later changes it.

## Required Claim Categories

Create a claim schema with:

- `claim_id`
- `claim_text`
- `claim_type`: `method|protocol|statistical|empirical|reproducibility|limitation`
- `allowed_before_real_runs`: boolean
- `required_artifact_types`
- `required_evidence_status`
- `blocked_reason_if_pre_run`
- `fid_sensitive`: boolean
- `requires_citation`: boolean
- `citation_status`: `not_needed|needed_unverified|verified`

## Allowed Pre-Run Claims

Allowed before real runs:

- CertGen implements a design/scaffold for metric-agnostic decision certification.
- Clean-core KID/MMD/CMMD-style certificates are implemented or planned, depending on actual code state.
- FID is descriptive-only unless rigorously handled.
- Smoke/dry-run artifacts are non-evidence.
- The project is zero-cost/released-samples-oriented by design.

## Forbidden Pre-Run Claims

Forbidden before real runs:

- any undecided-fraction value;
- any claim that published wins are undecided;
- any ranking movement claim;
- any compute-savings number;
- any real benchmark result;
- any rigorous FID certificate claim unless audited;
- any claim that CertGen is a new metric;
- any claim that FID is useless/wrong;
- any claim that most papers are wrong.

## Claim Audit

Implement a claim-contract checker that scans:

- `docs/`
- `paper/`
- `data/results/`
- generated report cards

for forbidden phrases and unsupported numbers. It should fail on:

- fake percentages;
- fake metric values;
- unsupported `claim_allowed=true`;
- `FID certified` language not routed through policy;
- broad claims like "most published wins are wrong".

## Output

Generate:

- `docs/paper/CLAIM_CONTRACT.md`
- `data/results/v5_claim_contract_audit.json`

with clear pass/fail status.
