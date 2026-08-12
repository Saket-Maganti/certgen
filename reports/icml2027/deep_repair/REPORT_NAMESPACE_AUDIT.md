# Report namespace audit

`registry/icml2027/report_namespaces.yaml` and its report-facing mirror assign
one non-overlapping canonical root to every current producer. A pairwise
collision test rejects equal or nested roots. The legacy scalar simulator is
explicitly reclassified as bounded-stream validation. `claim_allowed=false`.
