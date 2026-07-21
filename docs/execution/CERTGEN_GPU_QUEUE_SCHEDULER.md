# CertGen GPU Queue Scheduler

Default rule: one active subprocess per physical GPU. The parent groups workers into deterministic GPU queues; one queue thread launches its next subprocess only after the prior process exits. The parent does not import PyTorch or initialize CUDA.

Outputs are `queue_assignments.json`, `worker_schedule.json`, `worker_start_end.csv`, `gpu_utilization_summary.json`, `worker_exit_codes.json`, per-worker logs/status, and `orchestration_status.json`. A failed worker cancels later work in the same dependent queue while an independent GPU queue may finish. Completed work remains intact and exact rerun commands are emitted.

Resume accepts only `REUSED_VALID_COMPLETION`. Invalid schemas, versions, identities, missing files, or hash changes are quarantined and reported as `RERUN_INVALID_COMPLETION`, `RERUN_MISSING_OUTPUT`, `RERUN_CONFIG_CHANGED`, or `RERUN_ASSET_CHANGED`.
