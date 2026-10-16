---
title: Aprendizagem Aplicada à Segurança
subtitle: "Class 6: Anomaly Detection II, autoencoders, time, space and the state of the art"
author: Mário Antunes
institute: Universidade de Aveiro
date: October 23, 2026
bibliography: "references.bib"
suppress-bibliography: true
colorlinks: true
highlight-style: tango
mainfont: Noto Sans
header-includes:
 - \usetheme[sectionpage=none,numbering=fraction,progressbar=frametitle]{metropolis}
 - \usepackage{longtable,booktabs}
 - \usepackage{etoolbox}
 - \AtBeginEnvironment{longtable}{\small}
 - \AtBeginEnvironment{cslreferences}{\small}
 - \AtBeginEnvironment{Shaded}{\tiny}
 - \AtBeginEnvironment{verbatim}{\tiny}
 - \setmonofont[Contextuals={Alternate}]{FiraCode Nerd Font Mono}

---

# Where We Are

## Class 03_01 in one frame

* Model **normal**, score the departure $s(\mathbf{x})$, set $t$ at 1% false alarms on normal validation data.
* KDD99, 1.8% attacks: ten classic detectors reach AUPRC 0.33 to 0.68; the GMM is best, PCA has the best F1.
* r2l looks like normal traffic: every detector struggles; a classifier misses attack kinds it never saw.
* Today: can **learned representations** do better, and what about anomalies in **time** and across **sensors**?

## Why neural detectors?

* Hand-made features work for tables like KDD99; they are poor for raw **sequences**, **images**, **many sensors**.
* A neural network learns the features from normal data; the price: tuning, training time, less transparency. Deep and shallow detectors share a few principles [@ruff:2021]:

```{=latex}
\begin{adjustbox}{max width=\linewidth,max totalheight=0.46\textheight,center}
\begin{tikzpicture}[node distance=5mm]
  \node[note] (h1) {classic (class 03\_01)};
  \node[note, right=30mm of h1] (h2) {neural (today)};
  \node[neu, text width=3.2cm, below=2mm of h1] (a1) {reconstruction: PCA};
  \node[dfn, text width=4cm, below=2mm of h2] (b1) {autoencoder, conv / LSTM AE};
  \node[neu, text width=3.2cm, below=3mm of a1] (a2) {density: Gaussian, GMM};
  \node[dfn, text width=4cm, below=3mm of b1] (b2) {variational AE};
  \node[neu, text width=3.2cm, below=3mm of a2] (a3) {boundary: one-class SVM};
  \node[dfn, text width=4cm, below=3mm of b2] (b3) {Deep SVDD};
  \foreach \i in {1,2,3} {\draw[arr] (a\i) -- (b\i);}
\end{tikzpicture}
\end{adjustbox}
```

# Autoencoders

## The autoencoder: squeeze, then rebuild

```{=latex}
\begin{adjustbox}{max width=\linewidth,max totalheight=0.30\textheight,center}
\begin{tikzpicture}[node distance=6mm]
  \node[neu, minimum height=26mm, text width=1.2cm] (x) {$\mathbf{x}$\\71};
  \node[dfn, minimum height=18mm, text width=1.2cm, right=of x] (h1) {32\\ReLU};
  \node[ok, minimum height=9mm, text width=1.2cm, right=of h1] (z) {$\mathbf{h}$\\8};
  \node[dfn, minimum height=18mm, text width=1.2cm, right=of z] (h2) {32\\ReLU};
  \node[neu, minimum height=26mm, text width=1.2cm, right=of h2] (y) {$\hat{\mathbf{x}}$\\71};
  \node[atk, text width=2cm, right=8mm of y] (s) {score $s(\mathbf{x})$\\= error};
  \foreach \a/\b in {x/h1,h1/z,z/h2,h2/y,y/s} {\draw[arr] (\a) -- (\b);}
  \node[note, below=2mm of h1] {encoder $f$};
  \node[note, below=2mm of h2] {decoder $g$};
\end{tikzpicture}
\end{adjustbox}
```

* Train $\hat{\mathbf{x}}=g(f(\mathbf{x}))$ on **normal** rows to minimise $\frac1n\sum_i\lVert\mathbf{x}_i-\hat{\mathbf{x}}_i\rVert^2$.
* The 8-unit **code** $\mathbf{h}$ cannot copy 71 numbers: it keeps the structure of normal data only.

## Normal rebuilds well, attacks do not

![](plots/03/ae_scores.pdf)

* Test set, 1.8% attacks: the score is the reconstruction error; attacks sit to the right of the threshold.
* The threshold is the 99% quantile of the validation scores of normal rows.

## A linear autoencoder is PCA

![](plots/03/ae_vs_pca.pdf)

* Without activations, $\hat{\mathbf{x}}=W_2W_1\mathbf{x}$ and the best rank-$k$ map is the PCA projection $V_kV_k^\top$ [@baldi:1989].
* The ReLU or tanh layers bend the subspace into a curved surface: the only gain over PCA.

## Terminology: four variations on the autoencoder

| Model | Change | Why |
|:--------------|:-------------------------------------------------|:---------------------------|
| sparse AE | $+\lambda\lVert\mathbf{h}\rVert_1$ on the code | few active units, less copying |
| denoising AE | input $\mathbf{x}+\boldsymbol\epsilon$, target $\mathbf{x}$ [@vincent:2008] | learns the shape, not the points |
| variational AE | code is a distribution [@kingma:2014] | a density, not only a surface |
| Deep SVDD | no decoder; pull $\phi(\mathbf{x})$ to a centre [@ruff:2018] | one-class boundary in learned space |

* All four use the same protocol: train on normal rows, threshold on normal validation rows.

## Variational AE: a code with uncertainty

```{=latex}
\begin{adjustbox}{max width=\linewidth,max totalheight=0.30\textheight,center}
\begin{tikzpicture}[node distance=7mm]
  \node[neu, text width=0.9cm] (x) {$\mathbf{x}$};
  \node[dfn, text width=1.3cm, right=of x] (enc) {encoder};
  \node[ok, text width=1.2cm, above right=1mm and 9mm of enc] (mu) {$\boldsymbol\mu$};
  \node[ok, text width=1.2cm, below right=1mm and 9mm of enc] (sg) {$\log\boldsymbol\sigma^2$};
  \node[ok, text width=2.6cm, right=22mm of enc] (h) {$\mathbf{h}=\boldsymbol\mu+\boldsymbol\sigma\odot\boldsymbol\epsilon$};
  \node[dfn, text width=1.3cm, right=of h] (dec) {decoder};
  \node[neu, text width=0.9cm, right=of dec] (y) {$\hat{\mathbf{x}}$};
  \node[note, below=5mm of h] (eps) {$\boldsymbol\epsilon\sim\mathcal{N}(0,I)$};
  \draw[arr] (x) -- (enc); \draw[arr] (enc) -- (mu); \draw[arr] (enc) -- (sg);
  \draw[arr] (mu) -- (h); \draw[arr] (sg) -- (h); \draw[arr] (eps) -- (h);
  \draw[arr] (h) -- (dec); \draw[arr] (dec) -- (y);
\end{tikzpicture}
\end{adjustbox}
```

* The encoder outputs a mean $\boldsymbol\mu$ and a log-variance; the code is **sampled** around the mean.
* Score: the reconstruction error. In practice clip $\log\sigma^2$ and the gradient norm, or a seed can diverge (it did here).

## Variational AE: definition of the loss

* Loss = reconstruction + $\beta$ times the distance of the code distribution from $\mathcal{N}(0,I)$:
$$
\mathcal{L}=\lVert\mathbf{x}-\hat{\mathbf{x}}\rVert^2+\beta\,\mathrm{KL}
$$
$$
\mathrm{KL}=-\frac{1}{2}\sum_j\big(1+\log\sigma_j^2-\mu_j^2-\sigma_j^2\big)
$$
* The sum runs over the code units $j$. Why the sampling is differentiable: appendix.

## Deep SVDD: a sphere in a learned space

```{=latex}
\begin{adjustbox}{max width=\linewidth,max totalheight=0.30\textheight,center}
\begin{tikzpicture}[node distance=8mm]
  \node[neu, text width=0.9cm] (x) {$\mathbf{x}$};
  \node[dfn, text width=1.5cm, right=of x] (phi) {network $\phi$};
  \begin{scope}[shift={(7.6,0)}]
    \draw[aasblue, thick, fill=aasblue!8] (0,0) circle (0.95);
    \foreach \p in {(-0.3,0.2),(0.2,-0.3),(0.1,0.35),(-0.4,-0.2),(0.4,0.1),(0,0.05)} {\fill[aasgrey] \p circle (0.05);}
    \node[font=\scriptsize] at (0,0.62) {$\mathbf{c}$};
    \fill[aasred] (1.7,0.5) circle (0.08);
    \node[note, text=aasred, anchor=west] at (1.8,0.5) {attack: far from $\mathbf{c}$};
    \node[note, anchor=north] at (0,-1.05) {normal rows: close to $\mathbf{c}$};
  \end{scope}
  \draw[arr] (x) -- (phi); \draw[arr] (phi) -- (5.9,0);
\end{tikzpicture}
\end{adjustbox}
```

* A network $\phi$ maps normal rows close to a fixed centre $\mathbf{c}$; the score is the distance to it.
* Deep SAD adds a few labelled anomalies that are pushed *away* from $\mathbf{c}$ [@ruff:2020].

## Deep SVDD: definition and collapse

$$
\min_\phi\ \frac1n\sum_i\lVert\phi(\mathbf{x}_i)-\mathbf{c}\rVert^2,\qquad s(\mathbf{x})=\lVert\phi(\mathbf{x})-\mathbf{c}\rVert^2
$$

* $\mathbf{c}$ is the mean of the initial outputs, then fixed.
* **Collapse:** if $\phi$ may output a constant, $\phi(\mathbf{x})=\mathbf{c}$ for every $\mathbf{x}$ is a perfect, useless solution.
* Remedies of the paper: no bias terms, no bounded activations [@ruff:2018].

# Results on KDD99

## DEMO

\begin{center}
\Huge \textbf{DEMO 04}\\[4mm]
\Large \texttt{notebooks/02-anomaly/notebook\_04.ipynb}
\end{center}

## Deep detectors land in the same band

![](plots/03/deep_band.pdf)

* Mean of 3 seeds, default sizes (code 8), 20 epochs, 2-3 s each on a CPU. The mixture still leads; the AE equals its linear twin.
* PCA keeps the best F1 (0.637) and r2l recall (0.45). Depth is no free lunch on hand-made features [@han:2022].

## How big should the code be?

![](plots/03/code_size.pdf)

* Too small: normal traffic does not fit. Too large: the AE starts to copy attacks too.
* **Who chose 32?** We looked at the test attacks. The validation MSE of normal rows prefers 64.

## Tuning without anomalies is guessing

* A one-class detector has no labelled anomalies to tune code size, epochs, $\nu$, $k$ on.
* A gain from tuning on the test attacks is **not** a gain: report the default, or tune on a separate labelled set.
* Options: a few labelled anomalies (semi-supervised), a simulated attack set, or robust defaults over seeds.

## Explaining an alarm: error per feature

![](plots/03/explain_alarm.pdf)

* The reconstruction error is a sum over features: the largest terms name the reason.
* A triage hint: SYN-error rates for floods, failed logins and shells for intrusions.

# Anomalies in Time

## A value can be normal and still wrong *now*

<!-- defines: contextual -->

![](plots/03/nab_series.pdf)

* A **contextual** anomaly (80 requests/s: normal at noon, not at 3 a.m.) needs a **window**. Four NAB series [@lavin:2015], 14 days, red = the labelled anomaly.
* Only jumpsup leaves the normal range; jumpsdown, nojump (no daily rise) and flatmiddle stay inside it.
* Protocol: train on days 1-8, threshold = max score of day 9 + 10%.

## Three one-liners, one autoencoder

![](plots/03/nab_scores.pdf)

* One-liners: $|x_t|$; **seasonal difference** $|x_t-x_{t-288}|$; moving std (1 h). **Conv AE** over one-day windows (288 steps).
* AE score of step $t$: the squared error **at $t$**, averaged over the windows holding it. Plot: the seasonal difference (top) echoes a day later, the conv AE does not.

## DEMO

\begin{center}
\Huge \textbf{DEMO 05}\\[4mm]
\Large \texttt{notebooks/02-anomaly/notebook\_05.ipynb}
\end{center}

## Found, and at what price

![](plots/03/nab_found.pdf)

* Each cell: found or missed, then false alarms outside the NAB window.
* The seasonal difference finds all four but echoes (~110 false alarms); the conv AE finds all four with 1 to 35.
* An LSTM AE over 8-hour windows **misses** nojump: the window must hold the context.

## The benchmarks are telling us something

* Several popular time-series benchmarks are solvable by one-liners, and their labels have errors [@wu:2021].
* TSB-AD (40 data sets, 40 methods): simple and statistical methods are often as good as deep ones [@liu:2024].
* Time-series **foundation models** (pre-trained on many series, used zero-shot): no better than moving-window one-liners for anomaly detection.
* Lesson: always run the one-liners first; a deep model must beat them on *your* data.

# Space and Time: Many Sensors

## Example 2: a small water plant

![](plots/03/plant_events.pdf)

* 8 sensors, two hidden processes: **demand** (daily cycle) and **heat** (slow wander); correlated with each other (**space**) and with their own past (**time**).
* Three events in the second half (red): **spike** on level (+1.2, 30 min), **freeze** of the valve (stale value, 6 h: every value normal), **drift** of pressure (slow ramp, 10 h).

## Graphs of sensors: predict each one from the others

<!-- defines: graph -->

* Graph-based detectors learn which sensors depend on which and alarm when one departs from what its neighbours predict (GDN [@deng:2021]).

```{=latex}
\begin{adjustbox}{max width=\linewidth,max totalheight=0.22\textheight,center}
\begin{tikzpicture}[node distance=9mm]
  \node[neu, text width=2.2cm] (o) {the 7 other sensors};
  \node[dfn, text width=2cm, right=of o] (r) {linear regression};
  \node[ok, text width=2cm, right=of r] (p) {predicted $\hat{x}_{t,i}$};
  \node[neu, text width=2cm, below=4mm of p] (m) {measured $x_{t,i}$};
  \node[atk, text width=2cm, right=of p] (e) {residual $|x-\hat{x}|$};
  \draw[arr] (o) -- (r); \draw[arr] (r) -- (p); \draw[arr] (p) -- (e); \draw[arr] (m) -| (e);
\end{tikzpicture}
\end{adjustbox}
```

$$
s_t=\max_i\ \big|x_{t,i}-\hat{x}_{t,i}(\mathbf{x}_{t,-i})\big|
$$

* A frozen valve reports a normal value, but not the one its neighbours predict.

## DEMO

\begin{center}
\Huge \textbf{DEMO 06}\\[4mm]
\Large \texttt{notebooks/02-anomaly/notebook\_06.ipynb}
\end{center}

## Space beats per-sensor checks

![](plots/03/space_beats.pdf)

* The freeze and the drift break **relations**, not ranges: only models of the relations see them.
* With smooth, strongly correlated sensors the linear model wins; time pays off when the anomaly is in the *shape* (NAB).

## The point-adjust trap

<!-- defines: point-adjusted -->

* **Point-adjusted** F1 (many papers): one flagged point counts the whole anomalous segment as found.

![](plots/03/point_adjust.pdf)

* A random score looks almost as good as the best detector [@kim:2022].
* Report point-wise metrics, events found, delay, false alarms, baselines.

# The State of the Art, Honestly

## A map of the newer tools

| Tool | Idea | Note |
|:--------------------|:------------------------------------|:----------------------------------|
| Kitsune [@mirsky:2018] | online ensemble of small AEs on packet statistics | trains on live traffic: assumes it is clean |
| GDN [@deng:2021] | graph of sensor dependencies | names the sensor |
| TranAD [@tuli:2022] | transformer reconstruction | reported gains on benchmarks with known flaws |
| foundation models | pre-trained forecasters, zero-shot | ~ one-liners |

* Each brings a real idea; none removes the base rate, the threshold, or the need for baselines.

## What to take from the literature

* No detector wins everywhere, on tables [@han:2022] or on series [@liu:2024].
* Evaluation choices (duplicates, point adjust, tuning on the test set) move results more than architectures.
* A good deep detector is a good **representation** plus the same protocol as class 03_01.
* Next class: the same detectors as **targets**. What an attacker can change decides what they are worth.

# Wrap-up

## Labs and practice guide

| Notebook | Content |
|:--------------|:----------------------------------------------------------------------------|
| **04** | AE, sparse, denoising, variational, Deep SVDD on KDD99; code size; explanations |
| **05** | NAB: one-liners vs conv AE vs LSTM AE; per-step scores |
| **06** | Example 2: per-sensor vs space vs space + time; point-adjust; attribution |

* All neural models: Keras 3 on the JAX backend, CPU is enough (each notebook under 2 minutes).
* **Guide** `practice/anomaly/guide_03_02`: an AE by hand in Keras, its PCA twin, a windowed conv AE on NAB, one-liner baselines.

## Take-aways

* An autoencoder is PCA with curves; Deep SVDD is a one-class boundary in a learned space.
* On hand-made features, deep detectors match the classic ones; their tuning has no labels to rely on.
* Time: score windows, localise the error per step, and beat the seasonal one-liner first.
* Space: anomalies that break **relations** need a model of the relations (PCA, graphs, AEs over sensors).
* Distrust point-adjusted F1 and benchmark gains without baselines.

# Appendix: The Mathematics

## The reparameterisation trick

* Sampling $\mathbf{h}\sim\mathcal{N}(\boldsymbol\mu,\text{diag}\,\boldsymbol\sigma^2)$ is not differentiable in $\boldsymbol\mu,\boldsymbol\sigma$.
* Write $\mathbf{h}=\boldsymbol\mu+\boldsymbol\sigma\odot\boldsymbol\epsilon$ with $\boldsymbol\epsilon\sim\mathcal{N}(0,I)$: the randomness moves to an input, and $\partial\mathbf{h}/\partial\boldsymbol\mu=I$, $\partial\mathbf{h}/\partial\boldsymbol\sigma=\text{diag}\,\boldsymbol\epsilon$.
* KL of two Gaussians per code unit, closed form: $\mathrm{KL}(\mathcal{N}(\mu,\sigma^2)\Vert\mathcal{N}(0,1))=\tfrac12(\mu^2+\sigma^2-\log\sigma^2-1)$.
* Summed over the units it gives the loss term of the VAE frame.

## Why a linear AE recovers the PCA subspace

* Minimise $\sum_i\lVert\mathbf{x}_i-W_2W_1\mathbf{x}_i\rVert^2$ (centred data): $P=W_2W_1$ has rank at most $k$.
* For a fixed rank-$k$ projection $P$ the error is $\text{tr}(S)-\text{tr}(PS)$, $S$ the scatter matrix.
* $\text{tr}(PS)$ is maximal when $P$ projects onto the top $k$ eigenvectors of $S$ (Ky Fan): $P=V_kV_k^\top$.
* The AE finds the same subspace, not necessarily the same basis: $W_1$ can be any invertible mix of $V_k^\top$ [@baldi:1989].

<!-- refs:begin -->
## References

:::: {.columns}
::: {.column width="50%"}
\fontsize{5.5}{6.4}\selectfont\setlength{\parskip}{2.5pt}

Baldi, Pierre, and Kurt Hornik. 1989. “Neural Networks and Principal Component Analysis: Learning from Examples Without Local Minima.” Neural Networks 2 (1).

Deng, Ailin, and Bryan Hooi. 2021. “Graph Neural Network-Based Anomaly Detection in Multivariate Time Series.” AAAI Conference on Artificial Intelligence.

Han, Songqiao, Xiyang Hu, Hailiang Huang, Minqi Jiang, and Yue Zhao. 2022. “ADBench: Anomaly Detection Benchmark.” Advances in Neural Information Processing Systems (NeurIPS), Datasets and Benchmarks.

Kim, Siwon, Kukjin Choi, Hyun-Soo Choi, Byunghan Lee, and Sungroh Yoon. 2022. “Towards a Rigorous Evaluation of Time-Series Anomaly Detection.” AAAI Conference on Artificial Intelligence.

Kingma, Diederik P., and Max Welling. 2014. “Auto-Encoding Variational Bayes.” International Conference on Learning Representations (ICLR).

Lavin, Alexander, and Subutai Ahmad. 2015. “Evaluating Real-Time Anomaly Detection Algorithms – the Numenta Anomaly Benchmark.” IEEE International Conference on Machine Learning and Applications (ICMLA).

Liu, Qinghua, and John Paparrizos. 2024. “The Elephant in the Room: Towards a Reliable Time-Series Anomaly Detection Benchmark.” Advances in Neural Information Processing Systems (NeurIPS), Datasets and Benchmarks.

:::
::: {.column width="50%"}
\fontsize{5.5}{6.4}\selectfont\setlength{\parskip}{2.5pt}

Mirsky, Yisroel, Tomer Doitshman, Yuval Elovici, and Asaf Shabtai. 2018. “Kitsune: An Ensemble of Autoencoders for Online Network Intrusion Detection.” Network and Distributed System Security Symposium (NDSS).

Ruff, Lukas, Jacob R. Kauffmann, Robert A. Vandermeulen, et al. 2021. “A Unifying Review of Deep and Shallow Anomaly Detection.” Proceedings of the IEEE 109 (5).

Ruff, Lukas, Robert A. Vandermeulen, Nico Görnitz, et al. 2020. “Deep Semi-Supervised Anomaly Detection.” International Conference on Learning Representations (ICLR).

Ruff, Lukas, Robert Vandermeulen, Nico Görnitz, et al. 2018. “Deep One-Class Classification.” International Conference on Machine Learning (ICML).

Tuli, Shreshth, Giuliano Casale, and Nicholas R. Jennings. 2022. “TranAD: Deep Transformer Networks for Anomaly Detection in Multivariate Time Series Data.” Proceedings of the VLDB Endowment 15 (6).

Vincent, Pascal, Hugo Larochelle, Yoshua Bengio, and Pierre-Antoine Manzagol. 2008. “Extracting and Composing Robust Features with Denoising Autoencoders.” International Conference on Machine Learning (ICML).

Wu, Renjie, and Eamonn J. Keogh. 2021. “Current Time Series Anomaly Detection Benchmarks Are Flawed and Are Creating the Illusion of Progress.” IEEE Transactions on Knowledge and Data Engineering.

:::
::::
<!-- refs:end -->
