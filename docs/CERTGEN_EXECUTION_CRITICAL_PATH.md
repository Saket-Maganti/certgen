# CertGen Execution Critical Path

Current status: `LOCAL_RESEARCH_CORE_VALID_BLOCKED_BY_REFERENCE_INPUT`. Every stage remains `claim_allowed=false` until the final paper gate approves a same-lineage result.

## Shortest path to the first real certificate

| Order | Gate | Input | Command/surface | Required output | Advance only if |
|---:|---|---|---|---|---|
| 1 | reference source | official/user-supplied CIFAR source | exact command in `docs/CERTGEN_EXACT_NEXT_ACTION.md` | accepted onramp JSON | structure/hash pass |
| 2 | reference materialization | accepted source | next-action engine's materializer command | 10,000-row deterministic test manifest plus provenance | counts, dimensions, IDs, labels, hashes, source/license pass |
| 3 | reference sampling | frozen manifest/cache order | `certgen.cli.build_reference_draw_plan` | precommitted with-replacement plan | plan regenerates and binds manifest/cache IDs |
| 4 | checkpoint preflight | exact registry/revisions | hardened preflight notebook on Kaggle T4x2 | copied-back preflight ZIP | all three models load and 1–4 images validate; non-evidence only |
| 5 | generation | imported preflight and rebuilt input package | hardened generation notebook | six complete 500-seed shards and integrity ZIP | every model has exact 0–999 seeds, valid images/hashes, no duplicates |
| 6 | safe import | copied-back generation ZIP | `python3 -m certgen import generation <zip>` | run-specific immutable import and registry rows | ZIP/status/integrity/schema checks pass |
| 7 | feature extraction | validated reference and model manifests | hardened two-GPU feature notebook | complete extractor/role shards and integrity ZIP | exact revisions/preprocessing, dimensions, IDs, finite arrays, hashes pass |
| 8 | feature import/cache | copied-back feature ZIP | safe import plus cache-v2 migration/validation | three or more canonical cache-v2 lineages | all metadata and source-manifest identities resolve; no overlaps |
| 9 | metric reproduction | exact A/B/R caches and reference plan | independent/trusted reproduction gate | hash-bound reproduction artifact | same metric spec and all feature/plan hashes match within declared tolerance |
| 10 | controls | preregistered null and obvious-gap rows | CPU certificate pipeline | control trajectories | no direction/orientation/provenance failure |
| 11 | family freeze | prospective comparison registry | family/alpha ledger | immutable Bonferroni manifest | every tested dataset/extractor/kernel/pair axis is counted |
| 12 | pilot | all prior same-lineage artifacts | claim-capable union-Hoeffding path | first real certificate trajectories and censored aggregation | no gate fails; still pilot-only until paper review |

The state engine should expose only the first incomplete row. A later artifact found out of order is preserved but does not bypass prerequisites.

## Minimum credible paper path

After the integrity pilot:

1. freeze the feasibility-selected second image family before inspecting pilot outcomes;
2. execute the two-family comparison registry with real null, gap, and contestable pairs;
3. include every valid/invalid registered row in denominator and censoring audits;
4. compare against fixed-budget inference and the direct Gao–Sun–Su baseline where applicable;
5. run the preregistered protocol-sensitivity family;
6. complete independent clean-machine artifact reproduction; and
7. inject only approved tables/figures through the paper firewall.

CIFAR-only or 1k-only evidence is a pilot, not a minimum paper.

## Strong main-track path

Add a third recognized image/archive family or a theory-valid modern conditional domain, a systematic literature/artifact audit, robust partial-ranking consequences, measured online resource logs, and a public capsule. The outcome must materially change evaluation practice; more comparisons alone are not a contribution.

## Maximum-ceiling path

The current-core ceiling is a multi-family prospective evaluation audit using the bounded RBF route. A higher ceiling requires a genuine theory advance—e.g., a less conservative established CS adapted with proof, a valid conditional/shared-prompt stream, or directional false-discovery control under the relevant filtration—plus corresponding implementation and evidence. Do not imply that expansion before proof.

## Hard stop conditions

- control direction or null behavior fails;
- A/B independence or reference draw-plan contract cannot be established;
- cache or metric reproduction does not bind exact inputs;
- licenses/source terms prevent the planned use;
- a registered family is selected after viewing outcomes;
- paid/long compute is required without user authority; or
- the pilot scientific outcome does not justify scale under the preregistered rule.
