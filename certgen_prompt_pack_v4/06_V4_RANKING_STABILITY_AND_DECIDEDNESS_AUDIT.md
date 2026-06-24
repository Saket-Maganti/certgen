# 06 — V4 Ranking Stability and Decidedness Audit

Build the analysis layer that turns certificates into the paper's core empirical story.

## Goal

CertGen’s headline is not individual p-values. It is:

> Which reported generative-model wins are decided, undecided, or ranking-unstable under valid certificate rules?

V4 should add ranking-stability and decidedness audit tools.

## Implement

Create:

- `certgen/analysis/decidedness.py`
- `certgen/analysis/ranking_stability.py`
- `certgen/analysis/samples_to_decision.py`
- `certgen/cli/build_decidedness_audit.py`
- `certgen/cli/build_ranking_stability_report.py`
- `docs/DECIDEDNESS_AND_RANKING_STABILITY_V4.md`
- tests.

## Decidedness categories

For every reported claim:

- `decided_same_direction`
- `decided_opposite_direction`
- `undecided_at_reported_n`
- `undecided_at_budget`
- `blocked_reproduction_failed`
- `blocked_provenance_missing`
- `blocked_metric_policy`
- `descriptive_only`

## Ranking stability

Given metric scores/certificates for multiple models:

- produce naive ranking by point estimate;
- produce partial order by certified decisions;
- flag pairs whose ordering is undecided;
- compute ranking confidence summary;
- detect ranking movement under preprocessing locks/metrics if available.

Do not claim a leaderboard replacement. Phrase as:

> “Under the CertGen certificate, this leaderboard position is decided/undecided at the available budget.”

## Samples-to-decision

For decided pairs, compute:

- samples needed to decide;
- fraction of full budget used;
- savings vs fixed 10k/50k convention if applicable;
- sensitivity to metric and alpha.

For undecided pairs:

- budget used;
- final CS width;
- projected sample need if using a conservative extrapolation, clearly labeled as heuristic.

## Report outputs

Generate:

- `data/results/v4/decidedness_audit.csv`
- `data/results/v4/decidedness_audit.json`
- `docs/V4_DECIDEDNESS_AUDIT.md`
- `docs/V4_RANKING_STABILITY.md`

All reports must be claim-safe if based on synthetic/nonverified data.

## Acceptance criteria

- Synthetic batch certificate file produces decidedness audit.
- Ranking report produces a partial order with undecided edges.
- Blocked rows are counted separately from undecided rows.
- Reports include clear evidence status.
