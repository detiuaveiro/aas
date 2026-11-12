---
title: Aprendizagem Aplicada à Segurança
subtitle: "Class 10: Malware Detection II, dynamic analysis"
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

# From Files to Behaviour

## Run it, and watch

<!-- defines: dynamic analysis, sandbox -->

```{=latex}
\begin{adjustbox}{max width=\linewidth,max totalheight=0.30\textheight,center}
\begin{tikzpicture}
  \node[neu, text width=2.0cm] (s) {sample};
  \node[dfn, text width=3.0cm, right=10mm of s] (b) {\textbf{sandbox}\\isolated, snapshot};
  \node[dfn, text width=2.8cm, right=10mm of b] (t) {trace\\API calls, files, network};
  \node[ok, text width=2.0cm, right=10mm of t] (m) {model};
  \draw[arr] (s) -- (b); \draw[arr] (b) -- (t); \draw[arr] (t) -- (m);
\end{tikzpicture}
\end{adjustbox}
```

* **Dynamic analysis**: run the sample in a **sandbox**, record it.

## Static against dynamic

| | Static | Dynamic |
|:----------------|:-------------------|:---------------------------|
| cost per sample | milliseconds | minutes, one machine |
| features | header, imports | call sequence, files, network |
| easy to fake | yes, metadata | no, behaviour must happen |
| blind spots | packers, no row | sandbox detection, delays |

## Which sandbox?

* **Container** (Docker, Podman): fast, shares the host kernel, no Windows.
* **Virtual machine** with snapshot: real system, strong isolation, restored every run.
* Decision: virtual machines on a throwaway network (Cuckoo, CAPEv2); containers for Linux only.

## A sandbox that works in the lab

<!-- defines: disposable container -->

```{=latex}
\begin{adjustbox}{max width=\linewidth,max totalheight=0.34\textheight,center}
\begin{tikzpicture}
  \node[neu, text width=2.0cm] (s) {sample (script)};
  \node[dfn, text width=3.6cm, right=9mm of s] (b) {\textbf{fresh container}\\no network, read-only, 256 MB, \texttt{strace}};
  \node[dfn, text width=2.4cm, right=9mm of b] (t) {syscall sequence};
  \node[ok, text width=2.4cm, right=9mm of t] (m) {bag of syscalls + logistic};
  \draw[arr] (s) -- (b); \draw[arr] (b) -- (t); \draw[arr] (t) -- (m);
\end{tikzpicture}
\end{adjustbox}
```

* One **disposable container** per run: 24 runs in 28 s.
* Checked: connect fails (*Network unreachable*); root is read-only.

## What the sandbox sees

| Sample (unseen seeds) | Truth | P(worm-like) |
|:------------------|:---------|------:|
| benign calculator | benign | 0.00 |
| benign file writer | benign | 0.00 |
| benign polite client | benign | 0.00 |
| scan-and-spawn script | worm-like | 1.00 |

* Top syscalls: socket, connect, execve, write: **behaviour**.
* Limits: Linux only, toy training set.

# Sequences of Calls

## The data

* 43,876 sandbox runs, 100 API calls each, vocabulary 307, 97.5% malware.
* "Always malware" scores 97.5% accuracy: use area under the curve (AUC), average precision and F1.
* A bag of calls is a sparse count matrix.

## Bag of calls

* Logistic regression: AUC 0.939, average precision 0.9974, F1 0.9695.
* Cheap, sparse, interpretable.

## A GRU over the sequence

<!-- defines: GRU -->

```{=latex}
\begin{adjustbox}{max width=\linewidth,max totalheight=0.30\textheight,center}
\begin{tikzpicture}
  \node[neu, text width=2.4cm] (i) {100 call ids};
  \node[dfn, text width=2.4cm, right=9mm of i] (e) {embedding, 32};
  \node[dfn, text width=2.2cm, right=9mm of e] (g) {GRU, 64};
  \node[ok, text width=2.2cm, right=9mm of g] (o) {softmax, 2};
  \draw[arr] (i) -- (e); \draw[arr] (e) -- (g); \draw[arr] (g) -- (o);
\end{tikzpicture}
\end{adjustbox}
```

* The **gated recurrent unit (GRU)** reads calls in order: F1 0.9891.

## Training curve

![](plots/04/d04_gru_loss.pdf){width=65%}

* Validation loss falls slowly; training loss falls faster.

## Does order matter?

![](plots/04/d04_order_matters.pdf){width=60%}

* Shuffled: F1 0.9914 (was 0.9891), AUC 0.855 (was 0.893).
* Order adds a **small ranking signal**; *which* calls occur matters more.

## Architectures for behaviour

* Bag of calls plus a linear model: the strong baseline.
* Recurrent nets: order; 1-D convolution: local patterns.
* Transformers need more data and longer traces.
* Run the shuffle test before claiming "learned order".

# Takeaways

## What to remember

* Behaviour is harder to fake, and costs minutes per sample.
* A sequence model is justified only if the shuffle test hurts it.
* Choose the sandbox by the sample's system and isolation.
* Next class: break these detectors without breaking the malware.

<!-- refs:begin -->
