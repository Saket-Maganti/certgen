# V1 Certificate Core Report

Implemented:

- A V1 confidence-sequence scaffold using a time-uniform Hoeffding union bound when a fixed value range is supplied.
- Decision-certificate construction for clean KID/MMD/CMMD-style metrics.
- Smoke certificate reporting.

Rigorous in V1:

- The API contract and policy handling are tested.
- The interval method is honestly labeled.

Smoke-only:

- Toy delta streams.
- Generated certificates from smoke artifacts.

Remaining for V2:

- Final empirical-Bernstein/e-process construction.
- Real feature streams.
- Real comparison manifests.
