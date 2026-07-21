# CertGen Literature and Artifact Audit Protocol

Status: `PLANNING_ONLY`; `not_empirical_evidence`; `claim_allowed=false`.

## Question

The audit will estimate, within a prospectively sampled publication frame, how often generative-model comparisons disclose enough information and artifacts to assess uncertainty, and—only for a separately eligible subset—how often a frozen CertGen protocol yields a certified direction or an unresolved edge. It will not infer certificates from published point estimates.

## Sampling frame

Freeze before coding any eligible paper:

- venue years and tracks;
- search strings and bibliographic databases;
- inclusion/exclusion rules;
- unit of analysis (paper, benchmark table, or model pair);
- duplicate/preprint policy;
- target sample or census rule;
- reviewer assignment and adjudication; and
- protocol version and SHA-256.

Candidate venues are CVPR, ICCV, ECCV, NeurIPS, ICML, ICLR, and TMLR. Exact years and search strings are `TBD_REQUIRED_PRE_EXECUTION`; no population count is claimed by this repository audit.

## Paper-level schema

```text
paper_id, title, authors, year, venue, persistent_id, selection_source,
inclusion_status, exclusion_reason, generative_task, benchmarks,
metrics, preprocessing_reported, extractor_version_reported,
sample_count_reported, seeds_reported, uncertainty_reported,
multiplicity_reported, released_samples_url, released_features_url,
checkpoint_url, license_status, archive_hash, two_reviewer_agreement,
adjudication_status, evidence_status, claim_allowed
```

## Comparison-level schema

```text
comparison_id, paper_id, benchmark, model_a, model_b, reference,
reported_metric, reported_gap, sample_count_a, sample_count_b,
reported_uncertainty, preprocessing, extractor, source_artifacts,
artifact_provenance, independence_assessment, reanalysis_eligibility,
ineligibility_reason, certgen_family_id, certgen_result_artifact
```

Published numeric values may be transcribed only with a page/table locator and independent second review. Transcription establishes what was reported, not that the number is reproducible or statistically valid.

## Reanalysis eligibility

A comparison is eligible only when immutable A/B sample archives or hash-bound feature inputs, a compatible reference source, complete sample identities, licenses, extractor/preprocessing identity, and independence/precommitment facts pass. The registered bounded-RBF protocol, cache-v2 contract, metric-reproduction gate, reference draw plan, and multiplicity family must all bind the same lineage.

Ineligible comparisons remain in the reporting-practice denominator with an exact reason. Missing artifacts cannot be imputed. FID, FD-DINOv2, and polynomial KID values remain descriptive and are never converted into bounded-RBF certificates.

## Outcomes

Primary reporting-practice outcomes:

- fraction reporting evaluation sample size;
- fraction reporting any uncertainty;
- fraction reporting seeds or independent sample sources;
- fraction fixing extractor/preprocessing details;
- fraction releasing provenance-complete reusable artifacts; and
- distribution of ineligibility reasons.

Reanalysis-subset outcomes:

- decided and unresolved fraction at registered budgets;
- right-censored samples-to-decision;
- point-estimate order versus certified partial order; and
- protocol sensitivity under prospectively registered alternatives.

Every fraction reports its numerator, denominator, missingness, and selection stage. The reanalysis subset is not generalized to all papers without a documented selection-bias analysis.

## Quality control

Two reviewers independently code every claim-bearing field. Disagreements are adjudicated without viewing CertGen results. A pilot coding set may refine field definitions, but pilot papers are either excluded from the confirmatory frame or recoded under the frozen schema. Changes after freeze require a dated amendment and cannot retroactively rescue a preferred conclusion.

## Stop and pivot rules

- If artifact eligibility is too rare for a defensible reanalysis, publish only the reporting/artifact-availability audit; do not lower provenance gates.
- If the sampling frame cannot be reproduced, block literature-wide claims.
- If inter-reviewer agreement is unacceptable under the frozen criterion, revise the coding manual and recode before analysis.
- If the direct Gao–Sun–Su comparison or a newer primary source subsumes a proposed claim, narrow the contribution rather than excluding it.

No literature values were extracted or coded during this repository pass.
