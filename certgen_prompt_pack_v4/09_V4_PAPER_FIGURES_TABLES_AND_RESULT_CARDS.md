# 09 — V4 Paper Figures, Tables, and Result Cards

Build paper-facing outputs without creating fake paper claims.

## Goal

CertGen should start looking like a CVPR paper artifact: figures, tables, result cards, and placeholders that can be populated after real gates pass.

## Implement

Create:

- `certgen/reporting/figures.py`
- `certgen/reporting/tables.py`
- `certgen/reporting/result_cards.py`
- `certgen/cli/build_paper_artifacts.py`
- `docs/PAPER_ARTIFACTS_V4.md`
- `paper/figures/README.md`
- `paper/tables/README.md`
- tests that generate toy non-claim outputs.

## Figures to scaffold

1. **Optional-stopping validity figure**  
   naive peeking false-decision rate vs certificate-controlled rate.

2. **Samples-to-decision curve**  
   number of samples vs CS width/decision status.

3. **Ranking stability graph**  
   naive ranking edges vs certified partial order.

4. **Decidedness audit bar chart**  
   decided same direction / opposite / undecided / blocked.

5. **Metric disagreement panel**  
   FID descriptive vs KID/CMMD rigorous status.

If plotting dependencies are unavailable, generate CSV/JSON specs and Markdown summaries; plots can be optional.

## Tables to scaffold

- Main audit table.
- Metric reproduction table.
- Sample availability table.
- Certificate summary table.
- Ranking-stability table.
- Limitations table.

## Result cards

For each comparison, generate a card:

- comparison id,
- source claim,
- sample availability,
- preprocessing lock,
- reproduction status,
- certificate decision,
- samples-to-decision,
- evidence status,
- claim allowed.

## Claim safety

If input artifacts are synthetic/smoke/nonverified, every figure/table must be watermarked or labeled:

> NON-EVIDENCE / TEMPLATE / SYNTHETIC

Do not generate polished fake numbers without labels.

## Acceptance criteria

- Toy inputs generate figure/table specs.
- Non-evidence labels are visible in Markdown and machine-readable outputs.
- Missing real evidence prevents paper-ready status.
- Existing tests remain passing.
