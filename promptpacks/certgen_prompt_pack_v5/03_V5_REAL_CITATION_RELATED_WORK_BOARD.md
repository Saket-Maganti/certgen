# 03 — V5 Real-Citation Related Work Board

## Goal

Create a related-work board that prevents fabricated citations and prepares the CVPR paper's related-work section.

## Important Rule

Do not fabricate citations, authors, venues, years, DOIs, or URLs. If a citation has not been verified manually or through a real source, mark it:

- `citation_status=needs_verification`
- `paper_claim_allowed=false`

## Suggested Files

Create:

- `registry/related_work/related_work_board_v5.csv`
- `docs/related_work/RELATED_WORK_BOARD_V5.md`
- `docs/related_work/CITATION_VERIFICATION_PROTOCOL.md`
- `docs/related_work/RELATED_WORK_SECTION_SCAFFOLD.md`
- `certgen/audit/related_work_audit.py`
- `tests/test_v5_related_work_audit.py`

## Required Related-Work Buckets

1. Generative image metrics:
   - FID
   - KID
   - precision/recall, density/coverage
   - CMMD
   - FD-DINOv2 or feature-distribution alternatives

2. Generative video metrics:
   - FVD
   - FVD bias/reliability work

3. Metric reproducibility and preprocessing sensitivity:
   - resizing/interpolation sensitivity
   - feature extractor sensitivity
   - sample-size sensitivity

4. Sequential inference / anytime-valid methods:
   - confidence sequences
   - e-processes / betting martingales
   - sequential kernel two-sample tests
   - optional stopping validity

5. Evaluation reliability and benchmark auditing:
   - leaderboard uncertainty
   - ranking stability
   - fixed-n error bars vs sequential testing

6. Preference/arena evaluation, only as contrast:
   - Bradley-Terry/Elo style ranking
   - why CertGen targets distributional metrics instead of human preference ranking

## CSV Columns

Use columns:

- `work_id`
- `title`
- `authors`
- `year`
- `venue`
- `url_or_doi`
- `bucket`
- `verified`
- `verification_source`
- `how_certgen_uses_it`
- `reviewer_attack_it_supports_or_defuses`
- `citation_status`
- `notes`

## Audit Rules

Fail if:

- a citation appears in paper-facing text but is missing from the board;
- a citation is marked verified without URL/DOI/source;
- a paper-facing paragraph cites unverified citations as if final;
- a related-work bucket is empty;
- fake placeholder citations like `[Author2024]` appear outside scaffold areas.

## Output

Generate:

- a markdown board sorted by bucket;
- a citation verification TODO list;
- a related-work scaffold with placeholders clearly marked.

## No Web Assumption

If the implementation agent lacks browsing, it must not invent citations. It should create the board schema and known-to-user citation placeholders marked `needs_verification`.
