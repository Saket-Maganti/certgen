# CertGen Adversarial Reviewer Simulation

Status: `PLANNING_ONLY`; scores are scenario judgments, not venue predictions or evidence.

## Reviewer 1 — Sequential inference

**Summary.** A bounded-mean CS is specialized to a paired RBF-MMD difference and embedded in an evaluation pipeline.

**Strengths.** The estimand, support, first-crossing rule, and censored outcomes can be unusually explicit; the evidence gate is valuable.

**Major weaknesses.** The core union-Hoeffding result is established machinery; model/reference sampling assumptions are demanding; the old betting-grid and e-BH language was invalidly broad.

**Minor weaknesses.** The bound may be conservative, and block-size choices need prospective treatment.

**Fatal concern.** Any real certificate whose A/B provenance, reference draw plan, or cache identity fails the constant-conditional-mean contract.

**Required experiment.** Real null/obvious-gap controls plus coverage/power simulations with uncertainty on Monte Carlo error.

**Required clarification.** State the filtration, empirical-reference target, global family, and exact directional error guarantee in one theorem.

**Likely current / maximum-ceiling score.** reject / borderline-to-accept if the empirical audit is consequential; not a forecast.

## Reviewer 2 — Generative-model evaluation

**Summary.** The paper proposes an inference layer over bounded feature-kernel discrepancies rather than a new metric.

**Strengths.** It could expose when familiar point-estimate comparisons are not directionally resolved and enforce preprocessing/source reproducibility.

**Major weaknesses.** Current evidence is empty; CIFAR-only results would be dated; conclusions are conditional on an extractor and reference distribution; Gao–Sun–Su directly overlaps the problem.

**Minor weaknesses.** CMMD naming and FD-DINOv2 reproduction must match source conventions exactly.

**Fatal concern.** A claim of general model superiority or metric-agnosticism from one RBF protocol.

**Required experiment.** Prospectively selected recognizable systems across at least two meaningful image families, closest-method comparison, and protocol sensitivity.

**Required clarification.** Explain why time-uniform sample-only inference changes scientific practice beyond fixed-sample relative-KL inference.

**Likely current / maximum-ceiling score.** reject / possible accept at an evaluation-focused venue; not a forecast.

## Reviewer 3 — Computer vision

**Summary.** The idea is understandable, but the present repository is an execution scaffold with no figures or real results.

**Strengths.** A clear decided/unresolved visualization and partial-ranking graph could be useful to practitioners.

**Major weaknesses.** No current benchmark breadth, no modern high-resolution or conditional generation result, and no measured compute benefit.

**Minor weaknesses.** The manuscript must reduce process terminology and foreground the scientific result.

**Fatal concern.** A 1k three-checkpoint CIFAR pilot presented as a main-track vision contribution.

**Required experiment.** Strong real-model families, sensitivity across at least one semantic extractor protocol, and cases where inference materially changes a point ranking.

**Required clarification.** Separate model quality, metric proximity, practical importance, and statistical direction.

**Likely current / maximum-ceiling score.** reject / high-risk borderline for CVPR main even at ceiling; not a forecast.

## Reviewer 4 — Reproducibility and benchmarks

**Summary.** The strongest aspect may be the immutable artifact lineage and refusal to promote incomplete runs.

**Strengths.** Registry, safe import, cache contract, paper firewall, and explicit invalid denominator can make the study auditable.

**Major weaknesses.** Large historical V1–V9 duplication obscures the canonical path; source licenses and public release scope remain to be verified; passing static checks is not reproducibility.

**Minor weaknesses.** The repository needs a clean release capsule and short user path.

**Fatal concern.** Raw ZIP overwrite, unregistered repair, hidden failed comparisons, or a paper cell without a traceable approved lineage.

**Required experiment.** Independent clean-machine reproduction of one full pilot import/analysis from copied-back immutable artifacts.

**Required clarification.** Define which historical reports are excluded from the public release and how schema migration preserves originals.

**Likely current / maximum-ceiling score.** reject / strong evaluation-track candidate if independently reproduced; not a forecast.

## Consensus

All four reviewers would reject the current state because there is no empirical contribution. The paper becomes credible only if the real audit is broad, prospectively frozen, closest-work-aware, assumption-valid, and consequential. More scaffolding does not answer these objections.
