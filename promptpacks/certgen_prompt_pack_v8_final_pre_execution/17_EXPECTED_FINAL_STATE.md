# V8 Expected Final State

After successful V8 implementation, the repo should be in this state:

## Built

- CIFAR-10 local/reference onramp is robust.
- Kaggle T4x2 generation bookrun is robust and resumable.
- Kaggle T4x2 feature extraction bookrun is robust and resumable.
- Input/output ZIP handoff is validated with fake fixtures.
- Run ledger/dashboard gives exact next command.
- Scale lanes exist with hard gates.
- Checkpoint preflight exists.
- Metric sanity and certificate pilot are prepared but gated.
- Paper firewall prevents result leakage.
- Devops snapshot is non-destructive.

## Not built / not allowed

- No V9.
- No generic infrastructure expansion.
- No fake results.
- No paper evidence from planning/smoke/pilot-only outputs.
- No FID certificate claim.
- No certified polynomial KID by default.

## Acceptable final statuses

Best:

- `READY_FOR_KAGGLE_GENERATION` if CIFAR reference was found/materialized.

Acceptable honest blocker:

- `BLOCKED_USER_MUST_PROVIDE_CIFAR_REFERENCE` if no local CIFAR data or archive is available.

Unacceptable:

- fake readiness;
- fake empirical result;
- `claim_allowed=true` without real gates;
- paper result injection.

## Actual next action after V8

Run the real execution chain. Do not ask for another prompt pack.
