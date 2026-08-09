# Partial Order Assumptions

- `statement_id`: `T-PO-1`
- `formal_objects`: filtered bounded streams, stopping times, family allocations, and directed comparison graphs
- `assumptions`: edge direction is antisymmetric; cycles are invalid rather than silently removed
- `dependencies`: frozen study, sample identities, feature/preprocessing hashes, multiplicity registry
- `what_code_assumes`: fail-closed bounded values and prospective configuration
- `what_simulations_validate`: implementation behavior and finite-grid calibration only
- `what_remains_unproven`: population-level transitivity across representations
- `counterexamples`: naive repeated testing, outcome-adaptive prefixes, undeclared reuse, cyclic directions
- `proof_status`: `NOT_MARKED_COMPLETE`
- `claim_allowed`: `false`
