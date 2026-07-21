# Reference Draw-Plan Protocol

`certgen prepare reference-draw` consumes a named profile, its frozen study, and the materialized reference manifest. It freezes the population hash, IID-with-replacement PCG64 draw order, draw IDs, time index, control allocations, non-overlap constraints, and configuration hash before results exist. Repeating identical inputs is idempotent; changed inputs require a new study artifact. The plan is a claim-ineligible input record.
