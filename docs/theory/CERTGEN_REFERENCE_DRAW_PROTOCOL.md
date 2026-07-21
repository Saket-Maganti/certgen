# CertGen Reference Draw Protocol

Freeze the validated reference manifest and its SHA-256. Then run `python3 -m certgen.cli.build_reference_draw_plan` before inspecting certificate values. The canonical target is the fixed empirical reference distribution with deterministic PCG64 IID-with-replacement draws. The plan records population ID/hash, seed, draw IDs, source IDs/indices, pairing order, and a plan hash. Repeats are allowed by design; unregistered reuse, reordered caches, changed populations, or post-outcome redraws fail closed. A finite without-replacement design needs a separate proof and family lock.

The materialized execution view pairs draw indices `(0,1)`, `(2,3)`, and so on. A/B sample identities remain non-overlapping and role-disjoint.
