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

## What a trace contains

* **Kernel calls**: system calls such as open, write, connect, execve.
* **Library calls**: Windows functions that open files, edit keys, allocate memory.
* **Files and registry**: what is created, changed, deleted.
* **Processes and memory**: children spawned, code injected into other processes.
* Network: domain names, connections, protocols, bytes sent.

## Anatomy of one sandbox run

```{=latex}
\begin{adjustbox}{max width=\linewidth,max totalheight=0.34\textheight,center}
\begin{tikzpicture}
  \node[dfn, text width=1.9cm] (r) {1 restore clean snapshot};
  \node[dfn, text width=1.9cm, right=6mm of r] (d) {2 drop sample, start agent};
  \node[atk, text width=1.9cm, right=6mm of d] (x) {3 run for a fixed time};
  \node[dfn, text width=1.9cm, right=6mm of x] (c) {4 collect trace and files};
  \node[ok, text width=1.9cm, right=6mm of c] (m) {5 report to the model};
  \draw[arr] (r) -- (d); \draw[arr] (d) -- (x); \draw[arr] (x) -- (c); \draw[arr] (c) -- (m);
\end{tikzpicture}
\end{adjustbox}
```

* Cuckoo and CAPEv2 automate these five steps; the run is then thrown away.

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

## Container, microVM or virtual machine

| | Container | microVM | Full VM |
|:------------|:--------------|:--------------|:--------------|
| kernel | shared with host | own, minimal | own, complete |
| Windows samples | no | no | yes |
| start time | very fast | fast | slow |
| isolation | weakest | strong | strong |

* Docker and Podman are containers; rootless Podman limits an escape.

## Five questions to choose a sandbox

1. Which operating system does the sample need?
2. How strong must isolation be if the sample escapes?
3. How many samples per hour must it analyse?
4. Can the sample detect the environment?
5. Who restores the clean state after each run?

## Sandbox evasion by malware

* **Environment checks**: hypervisor bit, virtual network card, guest tools.
* **Timing**: sleep for minutes; the sandbox stops watching first.
* **Human checks**: no mouse movement, no recent documents, tiny disk: probably a sandbox.
* A sample that detects the sandbox stays quiet, and its trace looks benign.

## Countering sandbox evasion

* Harden the guest: realistic hardware names, installed software, user files.
* Accelerate sleeps and simulate a user (mouse, keys, clicks).
* Run suspicious samples on bare metal, restored from a disk image.
* Treat a quiet trace as **unknown**, not as benign.

# Sequences of Calls

## The data

* 43,876 sandbox runs, 100 API calls each, vocabulary 307, 97.5% malware.
* "Always malware" scores 97.5% accuracy: use area under the curve (AUC), average precision and F1.
* A bag of calls is a sparse count matrix.

## Representing a trace

* Bag of calls: how often each call occurs; order lost.
* **$n$-grams**: counts of call pairs and triples; keeps local order.
* **Sequence of ids**: the full trace through an embedding; keeps all order.
* **Graph**: calls as nodes and transitions as edges; for process trees and data flow.

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

## Models for traces

| Model | Reads order? | Cost | Use when |
|:---------------|:--------|:------|:------------------------------|
| bag of calls + linear | no | tiny | first baseline, interpretable |
| $n$-grams + forest | locally | small | short traces |
| 1-D convolution | locally | medium | repeated call patterns |
| GRU, LSTM | yes | medium | long traces |
| transformer | yes | high | large corpora |

## Cheap first, expensive second

```{=latex}
\begin{adjustbox}{max width=\linewidth,max totalheight=0.34\textheight,center}
\begin{tikzpicture}
  \node[neu, text width=1.8cm] (f) {file};
  \node[dfn, text width=2.4cm, right=8mm of f] (s) {static model, milliseconds};
  \node[ok, text width=1.9cm, above right=2mm and 9mm of s] (a) {confident: decide};
  \node[atk, text width=2.6cm, below right=2mm and 9mm of s] (d) {uncertain: sandbox, then dynamic model};
  \draw[arr] (f) -- (s); \draw[arr] (s) -- (a); \draw[arr] (s) -- (d);
\end{tikzpicture}
\end{adjustbox}
```

* Send only the files the static model cannot decide to the costly sandbox.

## The price of behavioural features

* Behaviour is **representative** but expensive: minutes per sample.
* Labels are scarce; the set is imbalanced; traces are truncated.
* The sandbox can be fooled: a quiet trace proves little.

# Takeaways

## What to remember

* Behaviour is harder to fake, and costs minutes per sample.
* A sequence model is justified only if the shuffle test hurts it.
* Choose the sandbox by the sample's system and isolation.
* Next class: break these detectors without breaking the malware.

<!-- refs:begin -->
