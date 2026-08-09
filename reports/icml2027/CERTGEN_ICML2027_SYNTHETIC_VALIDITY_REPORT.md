# CertGen ICML 2027 — Synthetic Validity Report

All results in this report are engineering or synthetic-validation evidence only. They are not real-generator or empirical paper evidence. `claim_allowed=false`.

Deterministic quick, medium, and overnight grids passed across 28 scenario definitions. The largest run produced 112,000 records.

- Null calibration, reference reuse, finite-reference behavior, stopping time, and power curves completed.
- Naive repeated fixed-z testing produced a 0.2578 simulated false-positive rate over 5000 null replicates; the anytime union-CS fixture produced 0.0000.
- These simulations validate software behavior under registered synthetic assumptions; they do not establish real-generator performance or a universal theorem.
