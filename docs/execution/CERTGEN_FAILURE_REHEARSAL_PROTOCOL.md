# Failure Rehearsal Protocol

`rehearse failures --all` executes only local fixtures. Sixteen cases cover interruption, partial ZIPs, duplicate/corrupt images, missing shards, revision/preprocessing/study drift, stale markers, worker mismatch, disk/OOM exhaustion, missing certificate inputs, incomplete family coverage, early ranking, and restricted public weights. Each row names the detector, expected typed status, recovery action, and actual fixture result. Outputs are synthetic validation only and not empirical evidence.
