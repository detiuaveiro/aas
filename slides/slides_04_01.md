---
title: Aprendizagem Aplicada à Segurança
subtitle: "Class 9: Malware Detection I, static analysis"
author: Mário Antunes
institute: Universidade de Aveiro
date: November 13, 2026
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

# Static Detection

## Detect malware without running it

<!-- defines: static analysis -->

```{=latex}
\begin{adjustbox}{max width=\linewidth,max totalheight=0.30\textheight,center}
\begin{tikzpicture}
  \node[neu, text width=2.2cm] (f) {file on disk};
  \node[dfn, text width=2.6cm, right=10mm of f] (x) {features\\header fields, API imports};
  \node[dfn, text width=2.2cm, right=10mm of x] (m) {classifier};
  \node[ok, text width=2.2cm, right=10mm of m] (d) {benign / malware};
  \draw[arr] (f) -- (x); \draw[arr] (x) -- (m); \draw[arr] (m) -- (d);
\end{tikzpicture}
\end{adjustbox}
```

* **Static analysis**: score a file without running it.
* Features: 77 Portable Executable (PE) header fields; imported API counts [@ember:2018].

## The data and the metric trap

* 19,611 files, 74.4% malware: the **reverse** of reality.
* Random forest: AUC (area under the receiver operating characteristic curve) 0.9992, F1 0.9941.

| Benign share kept | AUC | F1@.5 |
|:--------------|------:|------:|
| 100% (3,759) | 0.9992 | 0.9941 |
| 20% | 0.9953 | 0.9888 |
| 5% | 0.9893 | 0.9784 |
| 1% (50) | 0.9854 | 0.9584 |

## Imbalance: report an operating point

![](plots/04/d04_imbalance.pdf){width=47%}

* AUC barely moves; precision and the threshold do.
* Best threshold 0.95: precision and recall 0.976.

## Notation: scanner metrics

| Symbol | Meaning | Example |
|:----------------|:---------------------------------|:----------|
| $b$ | share of malware in the queue | 74.4% in the data |
| $\text{TPR}$ | share of malware that raises an alarm | scalar |
| $\text{FPR}$ | share of benign files that raises an alarm | scalar |
| $P(\text{malware}\mid\text{alarm})$ | share of alarms that are malware (precision) | scalar |

## The base rate decides precision

:::: {.columns}
::: {.column width="50%"}
<!-- derivation: the-base-rate-decides-precision-definition -->
$$
\begin{aligned}
P(\text{malware}\mid\text{alarm}) \\
=\frac{\text{TPR}\,b}{\text{TPR}\,b+\text{FPR}\,(1-b)}
\end{aligned}
$$
:::
::: {.column width="50%"}
![](plots/04/d04_threshold.pdf)
:::
::::

* Precision falls with $b$, AUC does not: tune on the real queue.

## What the header model looks at

![](plots/04/d04_importance.pdf){width=65%}

* Top fields: operating-system and subsystem versions, stack size, linker version.
* These are **metadata the author controls**: class 04_03 rewrites them.

# Families and the Two-Stage Hierarchy

## 20,000 files, 21,918 API columns

* 7 classes: benign and six families (RedLine, Downloader, remote-access trojan (RAT), Banking, Snake, Spyware).
* Density 0.0032: keep it **sparse** (CSR); a dense copy needs gigabytes.
* Spyware and Snake import about 10 to 13 functions, RATs about 79.

## Flat multi-class baseline

* Macro-F1 0.638, accuracy 0.684 on 5,000 held-out files.
* Downloader F1 0.984; **Spyware F1 0.072**: generic calls hide it.

## Two-stage hierarchy

<!-- defines: two-stage hierarchy -->

```{=latex}
\begin{adjustbox}{max width=\linewidth,max totalheight=0.34\textheight,center}
\begin{tikzpicture}
  \node[neu, text width=1.8cm] (f) {API counts};
  \node[dfn, text width=2.6cm, right=9mm of f] (s1) {\textbf{stage 1}\\binary: benign or malware};
  \node[ok, text width=2.0cm, above right=3mm and 9mm of s1] (b) {benign: stop};
  \node[dfn, text width=2.8cm, below right=3mm and 9mm of s1] (s2) {\textbf{stage 2}\\family, only on flagged files};
  \draw[arr] (f) -- (s1); \draw[arr] (s1) -- (b); \draw[arr] (s1) -- (s2);
\end{tikzpicture}
\end{adjustbox}
```

* Stage 2 trains on malware only.

## Flat or hierarchical?

![](plots/04/d04_flat_vs_hier.pdf){width=85%}

* End-to-end macro-F1: hierarchy 0.635, flat 0.638: no loss.
* Stage 1: AUC 0.879, F1 0.979.
* Its recall caps the pipeline.

## Making it fast enough to demo

* Read the file in chunks; keep a **sparse** 20,000-file sample.
* Demo times: headers 11 s, families 32 s, sequences 73 s, evasion 32 s.
* **Batching** the forest queries made the evasion demo 6x faster.

## Beyond this dataset

* Raw-byte networks learn from the whole file [@raff:2018].
* EMBER2024: files for several platforms, with evasive samples [@joyce:2025].
* Use it for homework; our demos stay small and fast.

# Limits of Static Analysis

## A replicator has no features

* A worm-like program is ordinary code: no header row.
* Lab: four containers send **data-only** beacons (fan-out 2, hop limit 4).
* Static scan: nothing. Flow log: depth 4. **Behaviour** is the signal.

## Takeaways

* Static header detection is almost solved on benchmarks and fragile in practice.
* Report precision and recall at an operating point.
* Use a two-stage hierarchy for diagnosis; protect stage-1 recall.
* Next class: execute the sample and read its behaviour.

<!-- refs:begin -->
## References

:::: {.columns}
::: {.column width="50%"}
\fontsize{5.5}{6.4}\selectfont\setlength{\parskip}{2.5pt}

Anderson, Hyrum S., and Phil Roth. 2018. EMBER: An Open Dataset for Training Static PE Malware Machine Learning Models. arXiv:1804.04637.

Joyce, Robert J. et al. 2025. EMBER2024: A Benchmark Dataset for Holistic Evaluation of Malware Classifiers. arXiv:2506.05074.

:::
::: {.column width="50%"}
\fontsize{5.5}{6.4}\selectfont\setlength{\parskip}{2.5pt}

Raff, Edward, Jon Barker, Jared Sylvester, Robert Brandon, Bryan Catanzaro, and Charles Nicholas. 2018. “Malware Detection by Eating a Whole EXE.” AAAI Workshop on Artificial Intelligence for Cyber Security.

:::
::::
<!-- refs:end -->
