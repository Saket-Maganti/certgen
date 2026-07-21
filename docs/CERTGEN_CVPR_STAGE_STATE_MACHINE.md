# CertGen CVPR Stage State Machine

The authoritative machine contract is `certgen.cvpr.contracts.STAGE_TRANSITIONS`. It enumerates all 18 stages from `REFERENCE_SOURCE_MISSING` through `CVPR_EVIDENCE_GATES_PENDING`, with required inputs, validator, outputs, failure status, next action, evidence class, and claim permission. Every current transition sets claim permission false; paper promotion is a separate future gate.
