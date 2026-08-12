# Bentkus-based confidence sequence candidate

- Status: `NOT_IMPLEMENTED` and not confirmatory-eligible.
- Primary source: [Kuchibhotla and Zheng, “Near-Optimal Confidence Sequences for Bounded Random Variables”](https://proceedings.mlr.press/v139/kuchibhotla21a.html), Theorem 1 and its bounded-variable construction.
- Exact theorem candidate: the paper's stitched Bentkus confidence sequence for bounded variables.
- Assumptions requiring verification: theorem-specific bounded-variable and centering conditions, epoch/error allocation, numerical binomial-tail evaluation, and applicability to CertGen's conditional-mean sequence.
- Time-uniform, sidedness, and alpha mapping: not yet transcribed or independently verified locally.
- Implementation status: absent.
- Limitation: promising worst-case sharpness does not establish a valid implementation for this stream.
