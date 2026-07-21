# CertGen Prompt Pack V1 Changelog

## V1 contents

This pack creates the first implementation prompt set for CertGen basics.

Included prompts:

1. global rules;
2. repo scaffold;
3. schemas/manifests/claim gates;
4. feature and metric foundation;
5. clean-core certificate scaffold;
6. FID policy guard;
7. pilot registry/audit scaffold;
8. reporting/reproducibility docs;
9. final V1 audit/handoff;
10. one-shot megaprompt.

## Design decisions locked in this pack

- CertGen is a metric-agnostic certificate layer, not a metric paper.
- KID/MMD/CMMD are the rigorous clean core for V1/V2.
- FID is descriptive-only in V1 unless later proven watertight.
- Smoke/mock/planned outputs are non-evidence.
- V1 success means contracts and gates, not results.

## Not included in V1

- real feature extraction runs;
- real benchmark/model-pair audit;
- real decidedness fraction;
- real ranking changes;
- final paper writing;
- verified related-work BibTeX;
- video/FVD implementation.
