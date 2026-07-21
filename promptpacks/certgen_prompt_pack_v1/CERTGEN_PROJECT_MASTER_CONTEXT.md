# CertGen Project Master Context

**Project name:** CertGen / Certified Generative-Model Comparison
**Current directional title:** **CertGen: Anytime-Valid, Metric-Agnostic Decision Certificates for Generative-Model Comparison**
**Target venue:** CVPR 2027 Main Conference
**Primary goal:** Build a zero-cost, reproducible, statistically disciplined tool that decides *when one generative model is certifiably better than another* — with how few samples, under a guarantee that survives continuous monitoring — and audit how many recently reported generative-model wins actually clear that bar.

**Relationship to CertVIC and to the rest of the portfolio:**
CertGen is the deliberate sibling of CertVIC. Same statistical moat (anytime-valid confidence sequences, optional-stopping-safe certification, zero-cost recipe-first reproducibility, hard claim gates). Deliberately different object: CertVIC measures whether VLMs update decisions under controlled edits; CertGen decides whether one generative model beats another under a sample budget. CertGen is intended to be the **safe, high-acceptance-probability** second CVPR submission, while CertVIC remains the **high-ceiling, high-variance** one. It is also kept distinct from the NeurIPS Datasets & Benchmarks anytime-valid evaluation work, which is a *discriminative benchmark-ranking framework*; CertGen is an *applied decision tool + literature audit for generative evaluation*, not a new framework and not a new metric.

---

## 1. One-Sentence Project Summary

CertGen wraps any standard generative-evaluation metric (FID, KID/MMD, CMMD, FD-DINOv2, precision/recall) in an **anytime-valid confidence sequence**, so that a "model A beats model B" verdict stays valid under optional stopping, reports the **minimum number of samples** needed to reach that verdict, and is used to **audit how many recently reported generative-model wins are statistically decided** at the sample sizes the field actually uses.

---

## 2. The Core Research Question

> When is one generative model *certifiably* better than another — with how few samples, under a guarantee that survives continuous monitoring — and how many published comparisons actually clear that bar?

This is not "is FID a good metric." That question is closed (NeurIPS 2023 and others already showed FID's flaws and its unfair treatment of diffusion models, and proposed better feature extractors). CertGen takes the metric *as given by the reviewer* and asks the orthogonal question the entire metric zoo currently leaves unanswered:

> Given whatever metric you trust, when have you sampled enough to declare a winner without your peeking inflating the error?

The desired failure mode CertGen exposes is:

> A reported "model A beats model B" gap that is **not statistically decided** at the sample size used, and that may flip or vanish under a valid sequential test.

---

## 3. Current Correct Framing

CertGen should **not** be framed as:

- a new generative-evaluation metric (the space is crowded: CMMD, FD-DINOv2, FLD, probabilistic precision/recall, etc.)
- a "FID is unreliable" paper (already done, including a large human study at NeurIPS 2023)
- a new anytime-valid statistical theory paper (the machinery is reused, not invented)
- a benchmark or dataset paper
- a leaderboard-replacement paper

The corrected framing is:

> CertGen is a **metric-agnostic decision/certificate layer** that sits *on top of* the existing metric zoo, plus a **forensic audit of decidedness** in the recent generative-evaluation literature.

The central methodological object is the **decision certificate**: a per-comparison artifact that says either "A is certified better than B (decided at n samples, error ≤ α, valid under optional stopping)" or "not decided at budget."

The single most important reframing move: **the crowded metric literature is the substrate, not the competitor.** CertGen does not argue against FID, KID, CMMD, or FD-DINOv2. It makes any of them yield a peeking-safe verdict. This defuses the obvious "why not just use the already-sample-efficient metric?" attack — the answer is "use it; CertGen wraps it too."

---

## 4. Why This Can Be Unique (and an Honest Bound on That Uniqueness)

Many people can compute FID and report a gap. That alone is not unique. CertGen becomes distinctive through the combination of:

1. **Metric-agnostic wrapper** — works with whichever metric the reviewer trusts.
2. **Optional-stopping validity** — the thing the entire metric zoo lacks; verdicts hold under continuous monitoring.
3. **Samples-to-decision certificate** — an explicit sample/compute budget per comparison.
4. **Literature audit** — the empirical headline: the fraction of recently reported wins that are statistically decided.
5. **Image core + video (FVD) stretch** — to ride CVPR's single hottest area without depending on video execution.
6. **Zero-cost, released-samples-only** — operates on already-generated samples/features; no training, no frontier models, no paid anything.

**Honest bound (read this every time hype creeps in):** this is a *narrow methodological wedge inside a crowded reliability space*, and structurally it resembles a 2025–2026 template ("anytime-valid certificate for X") that is currently flooding ML. Its strength is **execution + framing + the audit**, not paradigm novelty. CertGen's safety comes from genre-fit, flawless cheap execution, and being an adoptable tool — *not* from owning empty terrain. If the audit headline is weak and the framing is sloppy, this paper is rejectable as incremental. Treat that as the default risk, not a remote one.

---

## 5. Honest Positioning and Strategic Risk

This section exists so the project never lies to itself.

- **The reliability conversation is established.** "FID is noisy / unfair to diffusion / reproducibility is shaky" was done at scale (NeurIPS 2023, plus reproducibility studies showing the same sample size and interpolation must be matched). Do not re-sell this. Cite it as settled context.
- **The anytime-valid-certificate template is crowded and fast-moving.** Sequential stopping certificates for LLM generation, self-consistency, and risk control all appeared in 2025–2026. CertGen is the generative-vision instantiation. Being first to that instantiation is a real but modest contribution.
- **This would be the third anytime-valid paper in the portfolio** (after CertVIC and the NeurIPS D&B work). For the "auditable certified evaluation" identity that is coherent; strategically it concentrates the bet on one statistical idea at the moment it commoditizes. Accept this consciously. If portfolio *range* matters more than a safe third line, the alternative is a fresh non-anytime-valid vision direction (not yet scoped; would require its own diligence).
- **Net call:** as a safe, gettable second CVPR line under hard zero-cost constraints, CertGen is the best-supported option. It is not the "rare and surprising" unicorn; no single paper is both safe and maximally surprising, and the stated goal is safety.

---

## 6. Core Metric and Statistical Target

### 6.1 Estimands

For each generative model `M` and a reference real set `R`, a discrepancy `d(M, R)`:

- **FID / FD-DINOv2:** `d = ||mu_M - mu_R||^2 + Tr(Sigma_M + Sigma_R - 2*(Sigma_M*Sigma_R)^{1/2})` on Inception or DINOv2 features.
- **KID / MMD:** `d = MMD^2(M, R)` with a polynomial or RBF kernel; unbiased U-statistic estimator with tractable variance.
- **CMMD:** `MMD^2` on CLIP features.

Comparison estimand:

> `Delta_{A,B} = d(A, R) - d(B, R)`, with the **verdict** being a certified sign of `Delta` (lower distance is better, so `A` better ⇔ `Delta < 0`).

### 6.2 Anytime-valid construction

- **Clean core — KID / MMD / CMMD.** The squared MMD has an unbiased (U-statistic or linear-time) estimator, so the *difference* `MMD^2(A,R) - MMD^2(B,R)` is an average of per-unit terms `h_i`. Build an anytime-valid confidence sequence on `E[h_i]` via empirical-Bernstein e-processes / betting confidence sequences. There is existing sequential/anytime-valid kernel two-sample testing to cite and differentiate from. **Stop when the CS on `Delta` excludes 0** (one model certified better) or when the sample budget is exhausted (declare "not decided at budget").
- **Hard case — FID.** FID is a **biased, nonlinear** functional of the empirical mean and covariance — *not* a sample mean — so a naive mean-based CS does **not** directly certify FID. This is the single biggest technical risk and must be resolved in V2. Options:
  1. **Block/batched FID** with a confidence sequence over per-block FID estimates (conservative, loses efficiency).
  2. **Bias-corrected FID** (extrapolation-style correction) plus a CS on the corrected sequence.
  3. **Reframe the FID comparison as an MMD-style paired test**, present FID descriptively, and certify rigorously via MMD/KID/CMMD.
- **Honest recommendation:** certify rigorously on MMD/KID/CMMD/FD-DINOv2; include FID **descriptively** plus via the block-CS approximation; state the limitation explicitly. Do not claim a rigorous anytime-valid FID certificate unless option (1)–(2) is made watertight.

### 6.3 The load-bearing demonstration (optional-stopping validity)

The methodological proof that the tool matters (CertVIC analog: "the validity certificate is load-bearing"):

> Show that naive "peek at the metric as you add samples and stop when A looks better" **inflates the false-decision rate above α** (reproduce the peeking-inflation effect), while the CertGen certificate **holds the false-decision rate ≤ α** under the *same* monitoring.

Without this demonstration, the paper is "KID with error bars." With it, the paper has a reason to exist.

### 6.4 The audit (empirical headline)

- Collect recently reported pairwise claims ("A's FID `X` < B's FID `Y` on dataset `D`") where released samples/checkpoints exist.
- Recompute under **matched preprocessing** (interpolation/resize policy matters and changes FID — document it).
- Run the certificate. Report the fraction of reported directions that are **statistically decided vs. undecided**, both at standard sample sizes and at the sizes the original papers used.

### 6.5 The compute story

For decided pairs, report **samples-to-decision** vs. the 10k/50k convention → a concrete compute-savings narrative (relevant to the GPU-poor era and to CertGen's own constraints).

---

## 7. Non-Negotiable Constraints

Identical in spirit to CertVIC. Do not relax without an explicit decision.

### 7.1 Cost Constraints

Absolutely no: paid APIs, paid cloud GPUs, paid datasets, paid annotation, paid credits, paid experiment tracking, paid inference. Core identity is **zero-cost reproducibility**.

### 7.2 Compute Constraints

Allowed: local M4-class Mac (CPU), free Kaggle GPU (~30 hr/week), free Colab fallback, open-source models only, public/free datasets and **released samples/features** only. Feature extraction is the *only* GPU step and must be cached. Everything downstream (estimators, confidence sequences, certificates, audit) runs on CPU. The project must be executable as **many small runs**, never long monolithic sessions.

Not allowed by default: paid GPU rental, paid hosted inference, paid annotation, automatic large downloads inside tests, mandatory heavy dependencies, generating samples from scratch when released samples exist.

### 7.3 Development Constraints

Do not: fabricate results, insert fake numbers, fabricate citations, weaken claim gates to pass tests, let smoke/mock/synthetic artifacts become evidence, run GPU jobs inside normal tests, initialize/commit git unless explicitly asked.

Do: keep heavy imports lazy/optional, keep tests CPU/local, document every command, mark non-evidence artifacts as non-evidence, keep claim gates conservative, preserve backward compatibility, verify sample/feature availability and license per item before use.

---

## 8. Target Paper Identity

### Recommended Title

**CertGen: Anytime-Valid, Metric-Agnostic Decision Certificates for Generative-Model Comparison**

### Alternate Titles

1. **When Is One Generative Model Certifiably Better? Sample-Bounded, Peeking-Safe Comparison**
2. **How Many Samples Until You Know? A Decision Certificate for Generative Evaluation**
3. **Are Reported Generative-Model Wins Statistically Decided? An Anytime-Valid Audit**

### One-Sentence Thesis

Given any standard generative-evaluation metric, CertGen certifies when one model is better than another under optional stopping, reports the minimum samples to decide, and shows that a meaningful fraction of recently reported wins are not statistically decided at the sample sizes the field uses.

### Main Contributions

Claim contributions only after real evidence exists.

1. **Decision certificate** — a per-comparison, optional-stopping-safe verdict for whether one model beats another under a chosen metric.
2. **Samples-to-decision** — an explicit sample/compute budget per comparison, with a "not decided at budget" outcome.
3. **Optional-stopping validity** — a demonstration that naive peeking inflates error while the certificate controls it.
4. **Literature audit** — the fraction of recently reported generative-model wins that are statistically decided, and where rankings change.
5. **Zero-cost reproducible tool** — released-samples-only, CPU-runnable certificate over multiple metrics (FID descriptive + KID/MMD/CMMD/FD-DINOv2 rigorous).
6. **Image core + video (FVD) extension** — landing the certificate on the hottest CVPR area.

---

## 9. Datasets and Models (Released Samples / Features Only)

Use only public benchmarks and **already-released generated samples / checkpoints / precomputed feature stats**. Verify availability and license per item; no scraping, no paid sources.

### Tier 1 — image core
- **CIFAR-10** (small, fast, many released models).
- **FFHQ / CelebA-HQ 256** (faces, strong released model coverage).
- **ImageNet 256 class-conditional** (the comparisons people actually cite).
- Optional: **LSUN** categories.

Candidate model families with released samples/checkpoints: StyleGAN2/3, BigGAN, ADM/guided-diffusion, EDM, LDM / Stable Diffusion (released samples), DiT. Choose **pairs with small reported gaps** — those are the contestable ones.

### Tier 2 — video stretch (only if Kaggle budget is comfortable)
- Released **text-to-video** sample sets + I3D / VideoMAE features; standard FVD conventions (e.g., UCF-101-style protocols).
- Treat as **upside, not a dependency.** The image core must stand alone.

Rule: four strong, deeply-analyzed comparisons beat ten shallow ones.

---

## 10. Build Roadmap (Nothing Is Built Yet — This Is V0)

CertGen has **no code, no runs, no results.** This document is V0 (design). The roadmap is forward-looking, not a retrospective.

- **V0 — Design (this document).** Framing, constraints, statistical target, kill-list locked.
- **V1 — Feature extraction + metric implementations.** Inception + DINOv2 (+ CLIP) feature extraction on Kaggle, cached. CPU implementations of FID, KID/MMD, CMMD, FD-DINOv2, precision/recall. Reproduce a couple of published point estimates to validate correctness (match sample size and interpolation).
- **V2 — Certificate layer.** Anytime-valid CS / e-process on `Delta` for KID/MMD/CMMD (clean core). Resolve the FID-bias decision (block-CS vs. bias-corrected vs. descriptive-only). Native CS fallback reused from CertVIC; no paid `confseq` dependency.
- **V3 — Single-benchmark pilot (the decisive number).** One benchmark, a handful of contestable model pairs. Compute the fraction of reported gaps that are *not* decided under the certificate. **This is the go/no-go.**
- **V4 — Multi-benchmark + audit.** Scale to 3–4 benchmarks and 6–10 models each. Run the optional-stopping-validity demonstration. Produce the audit table and ranking-stability figure.
- **V5 — Video stretch.** FVD certificate on released text-to-video samples, if budget allows.
- **V6 — Paper.** Figures, tables, related-work positioning, reviewer-attack hardening, reproducibility capsule.

### Stop-building rule (CertVIC analog)
After V2 the tool exists. Only write more infrastructure if a real run crashes, a metric/CS contract mismatches, the FID-bias decision breaks, or a claim gate fails to block invalid evidence. Otherwise: **run the pilot.**

---

## 11. The Decisive Early Number and Go/No-Go Thresholds

The CertVIC equivalent of "tiny-pilot detectability AUC" is:

> **On the first benchmark, the fraction of contestable reported gaps that are NOT statistically decided under the sequential certificate, at the sample sizes commonly used.**

Decision thresholds (tune after the pilot, but anchor here):

- **Undecided fraction ≥ ~0.25–0.30:** strong GO. Clear audit headline; the paper has a reason to exist beyond the tool.
- **~0.05–0.25:** GO, but lean on the *samples-to-decision / compute-savings* and *optional-stopping-validity* angles; broaden the set of model pairs to surface ranking flips.
- **< ~0.05:** weak audit headline. Either pivot the emphasis to the compute-savings and validity story, or reconsider the project. Do not force a headline that the data does not support.

The pilot is a few days of small runs. It will resolve the project's viability before any large commitment.

---

## 12. Experimental Pipeline (Stage by Stage)

- **Stage 1 — Features.** Extract and cache Inception + DINOv2 (+ CLIP) features for released samples and reference real sets. Record exact preprocessing (resize/interpolation), since it changes FID.
- **Stage 2 — Estimators.** CPU implementations of FID, KID/MMD, CMMD, FD-DINOv2, precision/recall, each producing a point estimate and a per-unit contribution stream where applicable.
- **Stage 3 — Certificate.** Anytime-valid CS / betting e-process on `Delta_{A,B}` for the clean-core metrics; FID handled per the V2 decision. Stopping rule: CS excludes 0, or budget exhausted.
- **Stage 4 — Validity demonstration.** Simulate naive peeking vs. certificate monitoring on matched data; show false-decision-rate inflation vs. control.
- **Stage 5 — Audit.** Recompute reported pairwise claims under matched preprocessing; classify decided vs. undecided; record ranking changes.
- **Stage 6 — Compute story.** Samples-to-decision per decided pair vs. convention.
- **Stage 7 — Video (optional).** Repeat Stages 1–6 for FVD on released video samples.

---

## 13. Paper Figures and Tables

- **Main table:** per dataset, per metric — fraction of reported gaps decided vs. undecided; ranking changes after valid testing.
- **Figure 1 (headline):** a gallery of model pairs that are statistically *indistinguishable* despite different reported scores.
- **Figure 2:** samples-to-decision curves per metric per benchmark (the compute-savings story).
- **Figure 3:** the optional-stopping-validity plot — naive peeking false-decision rate vs. certificate-controlled rate.
- **Figure 4:** ranking-stability — leaderboard before vs. after valid testing.

---

## 14. Related Work and Landmines (Position as a Layer, Not a Competitor)

Cite and differentiate from each. These are the reviewer's weapons; disarm them in related work.

- **"Exposing flaws of generative metrics" (NeurIPS 2023)** — large human study, FID unfair to diffusion, FD-DINOv2 leaderboard, documented reproducibility issues. *Position:* this is the settled "metrics are flawed / new leaderboard" work; CertGen is orthogonal (decision validity, not a new metric or leaderboard).
- **CMMD / "Rethinking FID" (CVPR 2024)** — metric replacement. *Position:* CertGen wraps CMMD too.
- **FVD content bias (CVPR 2024)** — video-metric reliability. *Position:* motivates the video extension; CertGen certifies decisions for FVD rather than diagnosing it.
- **KID / unbiased estimators with variance** — the closest "error bars" prior art. *Position:* KID gives a fixed-n standard error, not optional-stopping validity; peeking at KID still inflates error.
- **FID bias correction (effectively-unbiased FID)** — informs the V2 FID handling.
- **Sequential / betting kernel two-sample testing** — the legitimate statistical ancestor of the certificate. *Position:* CertGen applies and packages it for generative-model *comparison and audit*, with a samples-to-decision certificate and a literature study; it does not claim new sequential-testing theory.
- **Arena / Bradley-Terry + bootstrap (Chatbot Arena lineage)** — the preference-evaluation analog. *Position:* explains why CertGen targets distributional metrics (vision-native, free released samples) rather than human-preference ranking; the preference-sequential space is crowded, largely text, and partly done.
- **Anytime-valid certificate template flood (LLM generation stopping, self-consistency, risk control, 2025–2026)** — template-fatigue risk. *Position:* acknowledge the template; the contribution is the generative-vision instantiation plus the empirical audit, not the template itself.
- **Reproducibility-of-GAN-research / preprocessing-sensitivity work (e.g., aliased-resizing GAN-evaluation subtleties, CVPR 2022)** — *Position:* motivates matched-preprocessing discipline in the audit.

---

## 15. Reviewer Attack Points and Defenses

- **"This is just KID/CMMD with a stopping rule."** → Optional-stopping validity is exactly what those lack; the validity demonstration (Stage 4) shows naive peeking fails. It is metric-agnostic and includes an empirical audit, not a single estimator.
- **"FID isn't a mean, your CS is invalid for it."** → Agreed; certify rigorously on MMD/KID/CMMD; treat FID descriptively / via block-CS; state the limitation. Do not overclaim.
- **"Dataset bias / metric flaws are already known."** → CertGen does not re-litigate metric quality; it certifies decisions under whatever metric you trust.
- **"Anytime-valid certificates are a known template."** → True; the contribution is the generative-vision instantiation plus the literature audit and compute story.
- **"Only toy datasets."** → CIFAR-10, FFHQ/CelebA-HQ, ImageNet, plus a video extension on standard FVD protocols; audited claims are ones people actually cite.
- **"Where's the vision?"** → Operates on image/video feature distributions, produces galleries of indistinguishable model pairs, and changes real generative-model rankings.

---

## 16. Acceptance Targets

### Weak-accept target
- 3 image benchmarks, 6+ model pairs each, certificate over ≥3 metrics, a real undecided fraction, clean optional-stopping-validity plot, reproducible capsule.

### Strong-accept target
- 3–4 benchmarks, ranking changes after valid testing, samples-to-decision savings demonstrated, the FID-bias handling made watertight, polished headline gallery, rigorous related work.

### Highlight-level possibility
- A striking undecided fraction that reorders a recognizable leaderboard, a clean compute-savings result, and a landing video (FVD) extension. Under strict zero-cost and "tool, not paradigm" framing, the realistic ceiling is a solid accept rather than highlight unless the audit result is unusually sharp.

---

## 17. What Can Still Kill the Paper

1. **FID-bias handling botched** — a CS presented as rigorous for FID when FID is not a mean.
2. **Undecided fraction ~0** — no audit headline (mitigated only partly by the compute/validity story).
3. **Novelty rejection** — "incremental / KID with a stopping rule," if the validity demonstration and audit are weak.
4. **Template fatigue** — reviewers tired of "anytime-valid certificate for X."
5. **Sample/feature unavailability** — the model pairs you want to audit lack released samples.
6. **Preprocessing confound** — failing to match interpolation/resize makes recomputed scores contestable.
7. **Video execution overrun** — letting the optional FVD stretch jeopardize the safe image core.
8. **Audit overclaim** — conflating "not decided at small n" with "the original paper was wrong"; must show it changes real conclusions/rankings, stated carefully.
9. **Reads as a stats paper** — insufficiently vision-native figures/framing.

---

## 18. What Would Make the Paper Strong

- Metric-agnostic certificate across ≥3 metrics with the FID limitation handled honestly.
- A non-trivial fraction of reported wins shown undecided, with at least one ranking reorder.
- A clean optional-stopping-validity demonstration (peeking inflation vs. control).
- A concrete samples-to-decision / compute-savings result.
- A beautiful headline gallery of statistically indistinguishable model pairs.
- A landing video (FVD) extension.
- Related work that positions CertGen as a layer on the metric zoo, not a competitor.
- Recipe-first, released-samples-only reproducibility.

---

## 19. Forbidden Claims

Never claim:

- FID is wrong / useless (not the claim).
- CertGen proposes a better metric (it does not).
- New anytime-valid sequential-testing theory (the theory is reused).
- A rigorous anytime-valid FID certificate, unless the FID-bias handling is made watertight.
- "Most published generative-model comparisons are wrong" (overclaim; report decidedness carefully).
- Certification from fixed-n bootstrap alone.
- Results from non-released or unverifiable samples.
- Paper evidence from smoke / mock / synthetic / planned artifacts.

---

## 20. Allowed Claims Before Runs

Before real runs, CertGen may claim only:

- the design and framing exist;
- the certificate construction is planned and rests on established anytime-valid machinery;
- the FID-bias subtlety is identified and a resolution path is specified;
- smoke/mock artifacts are non-evidence;
- no empirical result, no audit number, and no decidedness claim is available yet.

It must not claim a real undecided fraction, a real ranking change, a real compute saving, or paper-ready evidence.

---

## 21. Project Philosophy

CertGen should be: honest, zero-cost, reproducible, conservative, claim-safe, metric-agnostic, optional-stopping-rigorous, audit-driven, reviewer-aware, and skeptical of its own outputs.

It should not be: overclaiming, metric-replacing, leaderboard-replacing, paid-API-dependent, FID-bias-naive, fake-number-driven, statistically loose, or visually sloppy.

---

## 22. Final Stop Rule

After V2, the tool exists. Stop building general infrastructure. Write new code only if a real run crashes, a metric/CS contract mismatches, the FID-bias decision breaks, the audit ingestion breaks, or a claim gate fails to block invalid evidence. Otherwise: **run the pilot.**

---

## 23. Final Current Verdict

CertGen is currently a **design with no code, no runs, and no results** — a claim-safe master plan for a zero-cost, CVPR-native, executable second submission that reuses the CertVIC statistical moat on a deliberately different object.

It becomes a strong paper only if:

1. the certificate is rigorous on the clean-core metrics and honest about FID;
2. the optional-stopping-validity demonstration is clean and load-bearing;
3. a non-trivial fraction of reported wins is shown undecided, ideally reordering a recognizable ranking;
4. the framing holds it as a layer on the metric zoo, not a competitor;
5. it is reproducible from released samples at zero cost.

The next decisive action is not more design. It is to **extract features for one benchmark, run the certificate on a handful of contestable model pairs, and measure the undecided fraction.**

---

## 24. Single Most Important Sentence

CertGen is not trying to prove that FID is bad; it is trying to certify, under optional stopping and at minimum sample cost, *when one generative model is actually better than another* — and to show how often the field's reported wins do not clear that bar.

---

## 25. Next Action

```bash
# V1 first step: extract and cache features for one image benchmark,
# then reproduce one published point estimate to validate correctness
# (match sample size and interpolation), before building the certificate.
```

Critical go/no-go number:

> first-benchmark undecided fraction (Section 11)

Final status:

> Design settled. Next phase is V1 feature extraction and the V3 pilot number, not more planning.