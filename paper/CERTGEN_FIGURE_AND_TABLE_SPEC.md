# CertGen Figure and Table Specification

Status: `PLANNING_ONLY`; final empirical figures do not exist; `claim_allowed=false`.

## Figures

| ID | Scientific question | Required artifacts | Plot and axes | Uncertainty | Claim supported | Failure interpretation | Location |
|---|---|---|---|---|---|---|---|
| F1 | How does a point winner differ from a certificate? | one approved illustrative trajectory or clearly synthetic diagram | two-panel concept schematic | label synthetic if not real | decision contract | a point gap without exclusion is unresolved | main Fig. 1 |
| F2 | When does each comparison first decide? | full approved CS trajectories | x: samples per distribution; y: `Delta` estimate and CS | full time-uniform band, zero line | optional monitoring and direction | no crossing is censored, not equivalent | main Fig. 2 |
| F3 | What fraction decides by budget? | complete registered family and censoring ledger | Kaplan–Meier-style unresolved curve or cumulative incidence; x: budget | simultaneous/bootstrapped descriptive band only if preregistered | decidedness over budget | missing/invalid members shown separately | main Fig. 3 |
| F4 | What ordering is actually certified? | simultaneous Bonferroni certificates | directed graph; nodes models, solid direct edges, dashed logical closure | family alpha in caption | partial ranking | cycles or protocol-mixed edges block the graph | main Fig. 4 |
| F5 | Does protocol choice alter conclusions? | registered extractor/gamma/preprocessing cells | matrix or alluvial comparison; x: protocols, y: edge state | corrected family or explicit exploratory label | protocol sensitivity | favorable-cell selection is forbidden | main/supplement |
| F6 | Are samples actually saved? | online generation/extraction stop logs plus maximum budgets | x: comparison; y: realized samples, optional wall time | censoring and run variability | realized compute benefit | offline replay supports no runtime claim | main only if online logs exist |
| F7 | Where does evaluation fail safely? | invalid/rejected artifacts and controls | failure gallery with reason codes | none | integrity benefit | failures are not silently excluded | supplement |
| F8 | How broad is the result? | approved per-benchmark aggregations | small multiples of decidedness/partial order | identical axis and family disclosure | domain breadth | a single family cannot support universality | main/supplement |

Every plotting script must refuse inputs that lack an affirmative approval record from the separate paper claim gate. Planning schemas and synthetic plots must watermark `NOT MODEL EVIDENCE`.

## Tables

| ID | Contents | Required input | Placement | Permission now |
|---|---|---|---|---|
| T1 | Method capability: fixed/sequential, optional stopping, multiplicity, ranking, assumptions | verified literature matrix | main | prose/table scaffold only |
| T2 | Benchmark, source, license, model revision, sample count, extractor | frozen execution registries | main | planning rows only |
| T3 | Null and obvious-gap controls | approved real control artifacts | main | missing |
| T4 | Primary per-pair direction/unresolved state by budget | complete certificate family | main | missing |
| T5 | Decided fraction and censored samples-to-decision | aggregation ledger | main | missing |
| T6 | Certified partial-order consequences versus point estimates | T4 plus ranking audit | main | missing |
| T7 | Protocol sensitivity | registered sensitivity family | supplement/main | missing |
| T8 | Assumption and limitation ledger | theory audit plus run validations | supplement | method-only rows allowed |
| T9 | Measured runtime and resource use | immutable online logs | supplement | missing; no planning estimate in result cell |
| T10 | Ablations: alpha, block, gamma, reference split | preregistered sensitivity artifacts | supplement | missing |

## Placeholder contract

The current LaTeX result placeholders may name required artifacts and statuses but may not contain plausible-looking numbers, winner labels, colored cells suggesting outcomes, or captions written in the past tense. A failed injection gate leaves the placeholder intact.
