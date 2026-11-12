---
title: Aprendizagem Aplicada à Segurança
subtitle: "Class 11: Malware Detection III, evasion that keeps the malware working"
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

# Useful Evasion

## What makes an evasion useful

<!-- defines: functionality-preserving -->

```{=latex}
\begin{adjustbox}{max width=\linewidth,max totalheight=0.32\textheight,center}
\begin{tikzpicture}
  \node[neu, text width=2.4cm] (p) {malware file};
  \node[atk, text width=3.0cm, right=10mm of p] (e) {edit \textbf{metadata}\\header fields};
  \node[ok, text width=3.0cm, right=10mm of e] (r) {same payload, still valid};
  \node[dfn, text width=2.2cm, right=10mm of r] (d) {detector: \textbf{benign}};
  \draw[arr] (p) -- (e); \draw[arratk] (e) -- (r); \draw[arratk] (r) -- (d);
\end{tikzpicture}
\end{adjustbox}
```

* **Functionality-preserving**: the file keeps its payload and stays a valid executable.
* Changing what the payload needs does not count [@kolosnjaji:2018; @demetrio:2021].

## Threat model

| Element | In this class |
|:-------------|:---------------------------------------------|
| goal | evasion at test time |
| capability | 22 malleable fields present of 34 candidates |
| knowledge | white-box field list, or query access only |
| cost | edits, or `predict` queries per file |

* Our model, public data, **feature space**; the aim is defence.

# Three Attacks

## Attack A: rewrite the malleable fields

* Set every malleable field to the benign median.
* Evasion **1.000**, malware F1 0.0000, from a baseline recall of 0.9975.
* A perfect rate shows the benchmark rests on metadata.

## Attack B: benign mimicry

![](plots/04/d04_mimicry.pdf){width=42%}

* Keep $k$ payload fields, copy the benign profile elsewhere.
* Evasion: 0.219 at $k=40$, 0.753 at 20, 0.949 at 10.
* Small $k$ risks breaking the file; this test cannot see it.

## Attack C: greedy black-box

<!-- defines: black-box -->

* Queries only: apply the field change that lowers the score most.
* Evasion **1.000** on 60 files with queries only, no gradients [@anderson:2018].
* One batched query per step: at most 30 steps. Rate-limit scanner APIs.

## Summary of the three attacks

![](plots/04/d04_evasion_summary.pdf){width=70%}

* Baseline evasion without attack: 0.002.

# Defence

## Adversarial retraining

* Add attacked samples labelled **malware** and retrain.
* Attack A evasion falls to **0.000**, recall stays 0.9973.
* Greedy C falls to 0.017; mimicry B still evades (0.928).

## Defended model against all three

| Attack | Undefended | Retrained on A |
|:------------------|------:|------:|
| A malleable rewrite | 1.000 | 0.000 |
| B mimicry, $k=10$ | 0.949 | 0.928 |
| C greedy black-box | 1.000 | 0.017 |

* Retraining on A also closes C; mimicry lands elsewhere.

## Check your attack before you quote it

* No-attack evasion must stay near 0 (0.002).
* Score the **same rows** you rewrote: an index slip fooled our own demo.
* Report malware F1 too: 0.0000 under A and C.

## Further reading

* Query-efficient black-box attacks on Windows malware [@demetrio:2020].
* A survey of PE evasion and defences [@ling:2021].
* EMBER2024 includes evasive files for evaluation [@joyce:2025].

## An arms race with finite resources

```{=latex}
\begin{adjustbox}{max width=\linewidth,max totalheight=0.30\textheight,center}
\begin{tikzpicture}
  \node[atk, text width=2.6cm] (a) {new attack};
  \node[dfn, text width=2.6cm, right=14mm of a] (d) {retrain};
  \node[ok, text width=2.8cm, right=14mm of d] (r) {robust features, behaviour};
  \draw[arratk] (a) -- (d); \draw[arr] (d) -- (a); \draw[arr] (d) -- (r);
\end{tikzpicture}
\end{adjustbox}
```

* Exit the loop with features the attacker cannot change: behaviour.

## Takeaways

* Header metadata gives about 100% evasion at no cost to the payload.
* Retraining closes the attack it saw; mimicry still evades (0.928).
* Defend with behaviour, robust features and monitoring, not a single static model.

<!-- refs:begin -->
## References

:::: {.columns}
::: {.column width="50%"}
\fontsize{5.5}{6.4}\selectfont\setlength{\parskip}{2.5pt}

Anderson, Hyrum S., Anant Kharkar, Bobby Filar, David Evans, and Phil Roth. 2018. Learning to Evade Static PE Machine Learning Malware Models via Reinforcement Learning. arXiv:1801.08917.

Demetrio, Luca, Battista Biggio, Giovanni Lagorio, Fabio Roli, and Alessandro Armando. 2020. Functionality-Preserving Black-Box Optimization of Adversarial Windows Malware. arXiv:2003.13526.

Demetrio, Luca, Scott E. Coull, Battista Biggio, Giovanni Lagorio, Alessandro Armando, and Fabio Roli. 2021. “Adversarial EXEmples: A Survey and Experimental Evaluation of Practical Attacks on Machine Learning for Windows Malware Detection.” ACM Transactions on Privacy and Security 24 (4).

:::
::: {.column width="50%"}
\fontsize{5.5}{6.4}\selectfont\setlength{\parskip}{2.5pt}

Joyce, Robert J. et al. 2025. EMBER2024: A Benchmark Dataset for Holistic Evaluation of Malware Classifiers. arXiv:2506.05074.

Kolosnjaji, Bojan, Ambra Demontis, Battista Biggio, et al. 2018. “Adversarial Malware Binaries: Evading Deep Learning for Malware Detection in Executables.” EUSIPCO.

Ling, Xiang et al. 2021. Adversarial Attacks Against Windows PE Malware Detection: A Survey of the State-of-the-Art. arXiv:2112.12310.

:::
::::
<!-- refs:end -->
