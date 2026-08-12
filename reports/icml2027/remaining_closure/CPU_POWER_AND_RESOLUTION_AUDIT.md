# CPU power and resolution audit

Result: **RED minimum-utility gate**.

Corrected true-alternative denominator: 374 runs after excluding null/reference stress and invariance controls. Correct resolutions: 11; power `0.0294117647` with Wilson 95% interval `[0.016500948105892376, 0.05189138475601643]`. Unresolved fraction `0.9705882353` with Wilson 95% interval `[0.9481086152439835, 0.9834990518941076]`.

`reports/icml2027/power/RESOLUTION_EFFECT_MAP.csv` contains 170 scenario/budget/dimension rows with stream mean/SD, standardized effect, terminal radii, approximate fixed-N requirement, observed stopping, and unresolved status. Prior quick, bounded-stress, null-100, 10k×768/2048 feasibility, boundary, multiplicity, C2ST, and overnight synthetic artifacts remain reusable. These are synthetic/planning results, not generator evidence. `claim_allowed=false`.
