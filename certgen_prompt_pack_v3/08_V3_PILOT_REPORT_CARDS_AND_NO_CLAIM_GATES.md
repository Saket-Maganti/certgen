# Prompt 08 — Pilot Report Cards and No-Claim Gates

Upgrade reporting so V3 can summarize real or dry-run pilots without overclaiming.

## Goal

Create polished pilot report cards that are reviewer-readable but claim-safe.

Files:

- `certgen/reporting/pilot_cards.py`
- `certgen/cli/render_pilot_report.py`
- `docs/PILOT_REPORT_CARD_TEMPLATE.md`
- tests.

## Report card sections

Each pilot report should include:

1. Pilot ID and mode.
2. Evidence status.
3. Claim allowance.
4. Blockers.
5. Benchmark/model pair table.
6. Feature-cache validation table.
7. Metric reproduction status.
8. Certificate summary.
9. Decided/undecided counts, if eligible.
10. FID/FD descriptive-only section.
11. Optional-stopping validity status.
12. Reproducibility checklist.
13. Exact commands.
14. Forbidden interpretations.

## Language rules

If `claim_allowed=false`, the report must say:

> This artifact is not paper evidence and must not be used to claim a decidedness fraction, ranking movement, model superiority, or published-result error.

If no real validated features:

> NO_REAL_VALIDATED_FEATURES. This report is a planning/dry-run artifact only.

If real validated features but claim policy blocks claims:

> REAL_FEATURES_USED_IN_NON_CLAIM_MODE. Results may be used for debugging and go/no-go planning only.

## Claim gate scanner

Upgrade claim scanner to reject phrases in report artifacts when claim is not allowed:

Forbidden under claim_allowed=false:
- "we show that"
- "our results demonstrate"
- "model A is better"
- "published wins are undecided"
- "X% of claims fail"
- "ranking changes"
- "statistically decided" unless preceded by explicit non-claim/smoke context.

Allow neutral phrasing:
- "computed in non-claim mode"
- "pilot diagnostic"
- "not paper evidence"
- "claim blocked"

## Tests

- render dry-run card;
- render synthetic real non-claim card;
- claim scanner catches overclaim phrases;
- claim scanner permits allowed disclaimers;
- report includes exact command section.

## Verification

Run pytest and generate a template report.
