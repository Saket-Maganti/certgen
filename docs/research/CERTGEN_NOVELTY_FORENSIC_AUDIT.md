# CertGen Novelty Forensic Audit

Status: `VERIFIED_CURRENT` for repository claims and `PRIMARY_SOURCE_CHECKED` for the sources listed below. This is a literature audit, not empirical model evidence. `claim_allowed=false`.

## Verdict

CertGen does not currently contain a new sequential-inference theorem. Its valid local core is a conservative specialization of established bounded-mean confidence-sequence machinery to a non-overlapping RBF-MMD-squared difference stream. Sequential kernel two-sample testing, betting confidence sequences, e-values, and e-BH all predate this repository. More importantly, Gao, Sun, and Su's 2025 *Statistical Inference for Generative Model Comparison* already studies uncertainty-quantified relative generative-model performance and reports real image and text comparisons. The defensible novelty is therefore narrower than the historical repository claims, and it exists only if a prospective real-model audit demonstrates something the field does not already know.

The strongest supportable primary identity is **a generative-model evaluation methodology and audit paper**. The secondary identity is **a reproducibility protocol for anytime-valid bounded-kernel comparisons**. It is not currently a new-metric paper, a general metric-agnostic method paper, or a validated leaderboard-ranking method.

Recommended working title:

> **Are Generative-Model Improvements Statistically Decided? A Prospective Anytime-Valid Evaluation Audit**

A method-first alternative supported by the implementation is:

> **CertGen: Anytime-Valid Decision Certificates for Bounded-Kernel Generative-Model Comparison**

The historical “metric-agnostic” title is too broad: only the bounded RBF-MMD difference stream has a claim-capable path, FID and polynomial KID are descriptive, and CMMD support is conditional on a fully locked feature/kernel protocol.

## Exact novelty delta

What prior work already supplies:

- MMD two-sample estimators and linear-time disjoint-pair constructions;
- fixed-sample generative MMD/KID and CMMD evaluation;
- time-uniform confidence sequences for bounded means;
- sequential kernel two-sample tests based on betting;
- e-value multiple testing under arbitrary dependence;
- evidence that preprocessing and finite-sample variation destabilize reported benchmark differences;
- sample-efficient generative evaluation methods with a different objective.
- fixed-sample uncertainty-quantified relative generative-model comparison using a relative KL score, including CIFAR-10 and conditional-model extensions.

What CertGen can still contribute:

1. A prospectively registered estimand for comparing two generators against the same declared reference distribution using a locked feature and kernel protocol.
2. A reproducibility gate that refuses certification when provenance, preprocessing, cache alignment, or metric reproduction fails.
3. An empirical audit of decided, unresolved, and censored comparisons across common budgets, with controlled null and obvious-gap cases.
4. A multiplicity-aware partial order that refuses to force a total ranking.
5. An evidence-bounded public artifact package tying every conclusion to immutable inputs and validation records.

Items 1, 2, 4, and 5 are currently engineering/protocol contributions. Item 3 is the scientific contribution and is entirely missing until real experiments run. Without it, the project is a careful implementation scaffold rather than a paper result.

The most dangerous novelty overlap is Gao, Sun, and Su (2025). CertGen must compare against that method and state the difference precisely: their fixed-sample relative-KL inference assumes accessible model density or an approximation; CertGen targets sample-only generators through a bounded feature-kernel discrepancy and adds time-uniform stopping, prospective multiplicity, censored decision time, and partial-ranking/audit outputs. Those differences are plausible, but no comparative experiment or theorem currently establishes their value.

## Primary-source record

| Work | Authors | Year / venue | Persistent identifier | Relevance |
|---|---|---|---|---|
| A Kernel Two-Sample Test | Arthur Gretton, Karsten M. Borgwardt, Malte J. Rasch, Bernhard Schölkopf, Alexander Smola | 2012, JMLR 13 | [JMLR v13/25](https://jmlr.org/papers/v13/gretton12a.html) | MMD testing and linear-time approximations |
| Demystifying MMD GANs | Mikołaj Bińkowski, Danica J. Sutherland, Michael Arbel, Arthur Gretton | 2018, ICLR | [OpenReview paper](https://openreview.net/pdf/5308a4739abf6c4d149c09c21a4c52e29538f914.pdf) | KID/MMD generative evaluation and kernel choice |
| Effectively Unbiased FID and Inception Score and Where to Find Them | Min Jin Chong, David Forsyth | 2020, CVPR | [CVF proceedings](https://openaccess.thecvf.com/content_CVPR_2020/html/Chong_Effectively_Unbiased_FID_and_Inception_Score_and_Where_to_Find_CVPR_2020_paper.html) | Model-dependent finite-sample bias |
| On Aliased Resizing and Surprising Subtleties in GAN Evaluation | Gaurav Parmar, Richard Zhang, Jun-Yan Zhu | 2022, CVPR | [CVF proceedings](https://openaccess.thecvf.com/content/CVPR2022/html/Parmar_On_Aliased_Resizing_and_Surprising_Subtleties_in_GAN_Evaluation_CVPR_2022_paper.html) | Preprocessing sensitivity |
| Rethinking FID: Towards a Better Evaluation Metric for Image Generation | Sadeep Jayasumana et al. | 2024, CVPR | [CVF proceedings](https://openaccess.thecvf.com/content/CVPR2024/html/Jayasumana_Rethinking_FID_Towards_a_Better_Evaluation_Metric_for_Image_Generation_CVPR_2024_paper.html) | CMMD with CLIP and Gaussian RBF MMD |
| Exposing Flaws of Generative Model Evaluation Metrics and Their Unfair Treatment of Diffusion Models | George Stein et al. | 2023, NeurIPS | [NeurIPS proceedings](https://papers.neurips.cc/paper_files/paper/2023/hash/0bc795afae289ed465a65a3b4b1f4eb7-Abstract-Conference.html) | DINOv2-feature Fréchet distance and metric failure analysis |
| Time-uniform, nonparametric, nonasymptotic confidence sequences | Steven R. Howard, Aaditya Ramdas, Jon McAuliffe, Jasjeet Sekhon | 2021, Annals of Statistics 49(2) | [doi:10.1214/20-AOS1991](https://doi.org/10.1214/20-AOS1991) | Time-uniform inference |
| Estimating Means of Bounded Random Variables by Betting | Ian Waudby-Smith, Aaditya Ramdas | 2023, JRSS B 86(1) | [Oxford Academic](https://academic.oup.com/jrsssb/article/86/1/1/7043257) | Bounded-mean betting CSs |
| Nonparametric Two-Sample Testing by Betting | Shubhanshu Shekhar, Aaditya Ramdas | 2024, IEEE Transactions on Information Theory 70(2) | [doi:10.1109/TIT.2023.3305867](https://doi.org/10.1109/TIT.2023.3305867) | Closest sequential kernel two-sample work |
| Sequential Kernelized Independence Testing | Aleksandr Podkopaev, Patrick Blöbaum, Shiva Kasiviswanathan, Aaditya Ramdas | 2023, ICML | [PMLR 202](https://proceedings.mlr.press/v202/podkopaev23a.html) | Kernel betting and continuous monitoring |
| False Discovery Rate Control with E-values | Ruodu Wang, Aaditya Ramdas | 2022, JRSS B 84(3) | [doi:10.1111/rssb.12489](https://doi.org/10.1111/rssb.12489) | e-BH under arbitrary dependence |
| Accounting for Variance in Machine Learning Benchmarks | Xavier Bouthillier et al. | 2021, MLSys | [MLSys proceedings](https://proceedings.mlsys.org/paper_files/paper/2021/hash/0184b0cd3cfb185989f858a1d9f5c1eb-Abstract.html) | Benchmark uncertainty and comparison variance |
| Deep Reinforcement Learning at the Edge of the Statistical Precipice | Rishabh Agarwal et al. | 2021, NeurIPS | [NeurIPS proceedings](https://proceedings.neurips.cc/paper/2021/hash/f514cec81cb148559cf475e7426eed5e-Abstract.html) | Uncertainty-aware evaluation consequences |
| The Ladder: A Reliable Leaderboard for Machine Learning Competitions | Avrim Blum, Moritz Hardt | 2015, ICML | [PMLR 37](https://proceedings.mlr.press/v37/blum15.html) | Repeated adaptive leaderboard access |
| FlashEval: Towards Fast and Accurate Evaluation of Text-to-image Diffusion Generative Models | Lin Zhao et al. | 2024, CVPR | [CVF proceedings](https://openaccess.thecvf.com/content/CVPR2024/html/Zhao_FlashEval_Towards_Fast_and_Accurate_Evaluation_of_Text-to-image_Diffusion_Generative_CVPR_2024_paper.html) | Closest compute-reduction contrast |
| Statistical Inference for Generative Model Comparison | Zijun Gao, Yan Sun, Han Su | 2025, arXiv:2501.18897 | [arXiv HTML](https://arxiv.org/html/2501.18897) | Direct prior work on relative performance gaps, uncertainty, conditional models, and real image/text evaluation |

## Reviewer-grade novelty questions

1. **What becomes possible only because CertGen exists?** Nothing has yet been empirically shown. At maximum ceiling, it would become possible to distinguish point-estimate winners from prospectively certified directions and unresolved edges under a reproducible protocol.
2. **Why is this not ordinary confidence intervals?** Time-uniform bounds allow valid continuous monitoring, while the artifact and preregistration contract prevents protocol drift. The statistical principle itself is established prior art.
3. **Why not use existing sequential two-sample tests or Gao et al.'s relative-KL inference?** Both are mandatory baselines. CertGen’s case depends on sample-only bounded-kernel access, time-uniform directional inference, multiplicity bookkeeping, censored decisions, and empirical audit—not on owning uncertainty-quantified generator comparison.
4. **Is “samples-to-decision” new?** No. Expected sample size and stopping time are standard sequential-analysis concepts. CertGen’s contribution can be their censored, evaluation-budget interpretation across real generator comparisons.
5. **Is the method metric-agnostic?** No at the claim level. Compatibility must be granted metric by metric.

## Unresolved literature work

- Freeze a real bibliography file and replace author-year prose anchors with compiled citations.
- Map every repository `fd_dinov2` convention to Stein et al.'s exact feature and Fréchet protocol before claiming numerical reproduction; the primary source is now identified, but no local reproduction artifact exists.
- Add the strongest recent work on sequential predictive two-sample testing after theorem-level comparison.
- Search for post-2024 generative-evaluation audits before submission; this July 2026 scan is targeted, not a systematic review.
