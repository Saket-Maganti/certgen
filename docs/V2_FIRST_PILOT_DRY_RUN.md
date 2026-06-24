# V2 First Pilot Dry Run

`NO_REAL_EVIDENCE`

The V2 first-pilot planner checks whether registry metadata is complete enough for a later feature extraction and certification run. It does not run heavy extraction and does not make claims.

Example:

```bash
python3 -m certgen.cli.plan_first_pilot_v2 --registry-dir registry --out-json data/results/v2_first_pilot_plan.json --out-md docs/V2_FIRST_PILOT_PLAN.md --dry-run
```
