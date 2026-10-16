---
title: "Practice Guide 03_01: Classic Anomaly Detectors on Network Connections"
subtitle: Aprendizagem Aplicada à Segurança
author: Mário Antunes
institute: Universidade de Aveiro
date: October 16, 2026
colorlinks: true
highlight-style: tango
geometry: a4paper,margin=2cm
mainfont: Noto Sans
header-includes:
 - \usepackage{longtable,booktabs}
 - \usepackage{etoolbox}
 - \AtBeginEnvironment{longtable}{\normalsize}
 - \AtBeginEnvironment{Shaded}{\normalsize}
 - \setmonofont[Contextuals={Alternate}]{FiraCode Nerd Font Mono}
---

# Objective

Build the statistical core of an anomaly detector **yourself**: the z-score, the Mahalanobis distance, a threshold set on normal data only, and average precision; compare each with its scikit-learn twin. Then run the classic detectors of the lecture on KDD Cup 99 and measure why a classifier is not enough for attacks it has never seen.

* **Lecture:** `slides/slides_03_01.pdf`; **demos:** `notebooks/02-anomaly/` 00 to 03.
* **Notebook to complete:** `guide_03_01.ipynb` (this folder). Cells marked `TODO` are yours; `check` cells tell you whether you are right. The shared helpers come from `notebooks/02-anomaly/anomlib.py`.
* **Data:** Example 1 (generated) and `datasets/KDDCup99.csv.gz` (10% file, deduplicated to 145,585 connections).
* **Time:** about 2 hours (suggested: A 5 min, B 20, C 20, D 25, E 10, F 25, questions 15).
* **Environment:** `make venv` at the root of the repository; no GPU needed.

# Background in one page

**Setting.** Train on normal rows only (*novelty detection*); a detector returns a score $s(\mathbf{x})$, higher = more anomalous, and alarms when $s(\mathbf{x})>t$.

**z-score and Mahalanobis.** $z_j=(x_j-\mu_j)/\sigma_j$ and $s=\max_j|z_j|$ looks at one feature at a time. The Mahalanobis distance uses the covariance:

$$
d_M(\mathbf{x})^2=(\mathbf{x}-\boldsymbol\mu)^\top C^{-1}(\mathbf{x}-\boldsymbol\mu)
$$

For Gaussian data $d_M^2\sim\chi^2_d$. With many one-hot features $S$ is singular: shrink it, $\hat C=(1-\lambda)S+\lambda\frac{\text{tr}(S)}{d}I$ (Ledoit-Wolf chooses $\lambda$ from the data).

**Threshold.** $t$ = the $(1-\alpha)$ quantile of the scores of **normal validation** rows: about $\alpha$ false alarms, no attack needed.

**Base rate.** With a share $b$ of attacks, $P(\text{attack}\mid\text{alarm})=\frac{\text{TPR}\,b}{\text{TPR}\,b+\text{FPR}\,(1-b)}$.

**Average precision (AUPRC).** Rank the rows by score; at the rank of each attack, compute the precision of the rows ranked above it (inclusive); average. A random score has AP equal to the attack share.

**Isolation Forest.** $s=2^{-E[h]/c(n)}$, $c(n)=2H(n-1)-2(n-1)/n$, $H(i)\approx\ln i+0.5772$; $h$ = number of random cuts to isolate the point.

# Tasks

| Part | What you do | Check |
|:--|:------------------------------------------------------|:--------------------|
| **A** | Load Example 1 and KDD99, split (given) | |
| **B** | Implement `zmax` and `mahalanobis2` | lecture numbers, scikit-learn twin |
| **C** | Implement `threshold`, `average_precision`, `precision_at_base_rate` | `average_precision_score` |
| **D** | Implement `fit_shrunk`; compare with `LedoitWolf`; run the zoo (given) | table |
| **E** | Implement `c(n)` and `iforest_score` | $c(256)=10.245$ |
| **F** | Implement `train_without(category)`: a random forest that never saw one attack kind | table vs PCA |

**Tips.** Use matrix operations (`np.einsum`) instead of loops over rows. Run the `check` cell after each part. If a check fails, print shapes and a few values before changing code.

# Questions

1. **(B1)** Which of A and B does each score flag, and why? Sketch the contour $\max|z|=2$ and the ellipse $d_M=3$ over Example 1.
2. **(C1)** For TPR 0.95, how many of 100 alarms are real at a base rate of 1/10,000 and FPR 1%? And at FPR 0.1%? What does this mean for a security operations centre?
3. **(C2)** Why can the threshold be set without any attack? What is the risk if the validation rows contain attacks?
4. **(D1)** Which category is hard for every detector, and why? Which detector misses most DoS rows, and why does a flood fool it?
5. **(D2)** How does the shrinkage $\lambda$ change the Mahalanobis result? Why might the $\lambda$ chosen by Ledoit-Wolf not be the best for detection?
6. **(E1)** What score does a point get when it is isolated after 2 cuts, and after 20? Why do the trees use small subsamples?
7. **(F1)** For which unseen category does the forest fail? What does that say about deploying only a classifier?
8. **(F2)** Propose a combination of a classifier and a one-class detector for a real network, and say who labels the alarms.

| Detector | AUPRC | dos | probe | r2l | u2r |
|:------------------|------:|----:|------:|----:|----:|
| Mahalanobis (your $\lambda=0.01$) | | | | | |
| Mahalanobis (Ledoit-Wolf) | | | | | |
| best of the zoo | | | | | |
| random forest without r2l | | | | | |

# Optional challenges

* **Robust covariance:** fit `MinCovDet` on 5,000 training rows of the numeric features only. Does it beat Ledoit-Wolf? Add 1% of attacks from the pool to the training rows and compare again.
* **Contamination:** repeat part D with 1% and 5% of the pool mixed into the training rows. Which detector degrades least (notebook 02, part C)?
* **GMM size:** sweep the number of components of the Gaussian mixture (2 to 40). Is there a best value, and how would you choose it without labelled attacks?

# Reference solution

The solved notebook, with the answers to the questions and the numbers of a full run, is `solution/guide_03_01.ipynb`.
