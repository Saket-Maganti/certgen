# Runtime Calibration Protocol

Planning values are labeled `planning_estimate`, `hardware-dependent`, and `not an empirical project result`. A real checkpoint preflight may generate 4–16 non-evidence smoke images and records measured seconds/image, images/minute, effective batch size, peak VRAM, download/cache time, OOM events and hardware identity.

Recalculate with:

```bash
python3 -m certgen runtime-plan --config <frozen-runtime-plan.yaml> --out <measured-runtime-plan.json> --ingest-preflight <preflight-runtime-report.json>
```

The new plan labels measured inputs separately, derives generation ranges/session assignments, names model/shard membership, defines copy-back ZIPs and resume commands, and retains conservative disk/RAM margins. A measurement is runtime evidence only, never model-quality evidence.
