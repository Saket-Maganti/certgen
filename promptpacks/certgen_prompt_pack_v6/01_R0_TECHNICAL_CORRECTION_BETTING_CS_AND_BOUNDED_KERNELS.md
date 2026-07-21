# 01 — R0 Technical Correction: Betting CS + Bounded Kernels

Implement `CERTGEN_R0_TECHNICAL_CORRECTION_BETTING_CS_AND_BOUNDED_KERNELS`.

This is the only allowed pre-run technical correction before real execution. Do not turn this into V6 infrastructure.

## Why this exists

External audit found:

1. Existing CS is loose union-Hoeffding / heuristic Bernstein while docs imply betting/e-process strength.
2. Polynomial KID kernel is unbounded and conflicts with bounded-stream CS assumptions.
3. Rigorous clean core should use bounded RBF-MMD / bounded CMMD.
4. FID must remain descriptive-only.

## Tasks

### 1. Add/verify git

If the repo is not under git, initialize git locally.

Do not commit unless explicitly asked. The goal is protecting work, not creating publication history.

### 2. Implement betting-style CS for bounded streams

Add a bounded-mean betting CS implementation, e.g.

- `certgen/stats/betting_cs.py`
- or integrate into existing stats module.

Requirements:

- accepts bounded stream values with declared lower/upper bounds;
- supports deterministic replay;
- supports alpha;
- returns time-uniform lower/upper bounds;
- stops when CS excludes zero for comparison deltas;
- has safe fallback if numerical issues occur;
- does not require internet or heavy dependencies.

Keep union-Hoeffding as fallback/descriptive baseline.

### 3. Add bounded RBF-MMD stream

Add bounded-kernel MMD block streams:

- RBF kernel values in `[0, 1]`;
- block-level delta bounds derived and stored;
- no clipping of unbounded values to fake validity;
- support block-size sensitivity.

### 4. Add bounded CMMD stream

For CLIP features:

- normalize features when appropriate;
- use bounded RBF kernel or explicitly bounded kernel;
- store preprocessing/feature-normalization contract;
- declare bounds.

### 5. Demote polynomial KID

Polynomial KID can remain available as descriptive/non-certified.

Default behavior:

- `polynomial_kid_certificate_allowed=false`;
- any attempt to run rigorous certificate with polynomial KID fails with clear message unless a valid proof/config is added later.

### 6. Reinforce FID policy

FID/FD-DINOv2:

- descriptive only;
- no rigorous anytime-valid certificate claim;
- block any config that claims `fid_certificate_allowed=true`.

### 7. Tests

Add tests for:

- betting CS deterministic replay;
- null synthetic stream does not decide too often in smoke conditions;
- obvious-gap synthetic stream decides;
- bounded RBF stream declares valid bounds;
- bounded CMMD stream declares valid bounds;
- polynomial KID rigorous cert blocked by default;
- FID cert blocked;
- no `claim_allowed=true`.

### 8. Audit

Add or update an audit command:

```bash
PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES="" python3 -m certgen.audit.r0_technical_correction_audit \
  --out docs/R0_TECHNICAL_CORRECTION_AUDIT.md \
  --json-out data/results/r0_technical_correction_audit.json
```

It must check:

- betting CS exists;
- bounded RBF-MMD certificate path exists;
- bounded CMMD path exists;
- polynomial KID cert blocked by default;
- FID cert blocked;
- old Hoeffding path not mislabeled as e-process;
- all outputs `claim_allowed=false`.

## Verification

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES="" python3 -m pytest -q
```

Final response:

- tests passed/failed;
- audit passed/failed;
- files changed;
- whether clean-core certificate path is now technically corrected;
- whether R1B execution can continue.
