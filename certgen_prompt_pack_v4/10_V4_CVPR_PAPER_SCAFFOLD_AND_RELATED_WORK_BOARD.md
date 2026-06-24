# 10 — V4 CVPR Paper Scaffold and Related-Work Board

Create a CVPR-facing paper scaffold and related-work task board.

## Goal

V4 should prepare the writing structure early, but keep all empirical claims blocked until real evidence exists.

## Implement

Create or update:

- `paper/main.tex` or `paper/README.md` if LaTeX is not desired yet;
- `paper/sections/abstract_placeholder.tex`
- `paper/sections/introduction.tex`
- `paper/sections/method.tex`
- `paper/sections/experiments_placeholder.tex`
- `paper/sections/limitations.tex`
- `paper/sections/ethics_reproducibility.tex`
- `docs/RELATED_WORK_TASK_BOARD_V4.md`
- `docs/CVPR_PAPER_SCAFFOLD_V4.md`
- `docs/CLAIM_LANGUAGE_POLICY_V4.md`
- tests/audit checks for fake empirical claims.

## Paper framing

The paper should say:

> CertGen provides metric-agnostic, optional-stopping-valid decision certificates for generative-model comparisons, reports samples-to-decision, and audits whether reported wins are decided under valid testing.

The paper should not say:

- FID is useless;
- CertGen proposes a better metric;
- most papers are wrong;
- frontier models fail;
- real undecided fraction before the pilot exists.

## Related-work buckets

Create a board with citation tasks for:

1. FID/KID/MMD/CMMD and generative metrics.
2. FID flaws and reproducibility/preprocessing sensitivity.
3. CVPR 2024 CMMD / Rethinking FID.
4. FVD/video metric reliability.
5. Sequential/anytime-valid inference and e-processes.
6. Kernel two-sample testing.
7. Generative model evaluation audits.
8. Leaderboard/ranking uncertainty.

Do not fabricate BibTeX entries. Use TODO placeholders until citations are verified.

## Claim-language audit

Add a checker that flags forbidden unguarded phrases in paper/docs:

- “we show that X%” unless a real evidence artifact is linked;
- “most reported wins” unless backed;
- “FID is invalid/useless”;
- “certified FID” unless policy allows;
- “paper-ready result” on smoke/synthetic artifacts.

## Acceptance criteria

- Paper scaffold compiles if LaTeX tooling exists, or docs clearly say not compiled yet.
- Claim-language audit catches fake result language.
- Related-work board exists with verified/unverified status fields.
- No fake citations are inserted.
