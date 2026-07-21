# V8 One-Shot Mega Prompt — Use Only If You Cannot Run Staged


You are working on **CertGen** in `/Users/saketmaganti/Projects/certGen`.

Hard rule: this is **V8 Final Pre-Execution Hardening**, not V8 generic infrastructure.
Do not create V9. Do not add vanity scaffolding. Do not fabricate results. Do not promote anything to paper evidence.
All smoke/template/planning outputs must keep `claim_allowed=false`, `NO_FAKE_RESULTS`, and `not paper evidence`.

Current known state:
- V7 execution-development audit passed.
- Tests reached 169 passed after V7.
- Final execution audit remains `BLOCKED_MISSING_REFERENCE_SAMPLES`.
- Kaggle generation and feature-extraction bookruns exist.
- CPU/Kaggle ZIP handoff exists.
- No generation, feature extraction, metric sanity, certificate pilot, undecided fraction, or paper evidence exists.
- The immediate real blocker is missing CIFAR-10 reference samples.

V8 goal:
> Remove avoidable execution blockers, harden the CPU/Kaggle handoff, make CIFAR reference onboarding almost impossible to mess up, and end with a hard stop: after V8, only real execution.


Execute every operational prompt from 00 through 15 in order. Do not execute this one-shot if you are already running staged prompts.

Final output must include:

1. Tests passed/failed.
2. V8 final audit status.
3. Final execution audit status.
4. Current blocker.
5. Exact next CPU command.
6. Exact next Kaggle notebook step.
7. Which `.ipynb` files were created/updated.
8. Which ZIP builders/importers were created/updated.
9. Estimated runtimes.
10. Confirmation:
   - no fake empirical results;
   - no paper evidence;
   - no `claim_allowed=true`;
   - no FID certificate;
   - no certificates unless real gates pass.

Hard final instruction: Do not create V9. After this, run real CIFAR execution.
