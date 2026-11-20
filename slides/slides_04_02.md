---
title: Aprendizagem Aplicada à Segurança
subtitle: "Class 10: Malware Detection II, dynamic analysis"
author: Mário Antunes
institute: Universidade de Aveiro
date: November 13, 2026
toc: true
toc-title: Outline
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

## Last class in one frame

<!-- defines: static detection, passive detection -->

```{=latex}
\begin{adjustbox}{max width=\linewidth,max totalheight=0.30\textheight,center}
\begin{tikzpicture}
  \node[neu, text width=2.0cm] (f) {file};
  \node[dfn, text width=3.0cm, right=9mm of f] (s) {\textbf{static model}\\headers, imports};
  \node[ok, text width=2.4cm, right=9mm of s] (b) {benign or malware};
  \node[dfn, text width=2.6cm, right=9mm of b] (h) {family (stage 2)};
  \draw[arr] (f) -- (s); \draw[arr] (s) -- (b); \draw[arr] (b) -- (h);
\end{tikzpicture}
\end{adjustbox}
```

* **Static** (passive) detection reads the file and never runs it.
* Class 9: binary stage AUC 0.999 on headers; families macro-F1 0.65; base rate decides precision.

## Why static is not enough

* Packers and encryption change the bytes, not the behaviour.
* Header fields are metadata: an attacker rewrites them (Class 11).
* A worm is ordinary code; its harm is *what it does* (Class 9, replicator).
* So we need a second opinion that cannot be rewritten for free: behaviour.

## Active malware detection

<!-- defines: active detection, dynamic analysis, sandbox, trace -->

```{=latex}
\begin{adjustbox}{max width=\linewidth,max totalheight=0.30\textheight,center}
\begin{tikzpicture}
  \node[neu, text width=2.0cm] (s) {unknown sample};
  \node[dfn, text width=3.2cm, right=10mm of s] (b) {\textbf{execute} in a controlled environment};
  \node[dfn, text width=3.0cm, right=10mm of b] (t) {\textbf{trace}: calls, files, network};
  \node[ok, text width=2.2cm, right=10mm of t] (m) {model: verdict};
  \draw[arr] (s) -- (b); \draw[arr] (b) -- (t); \draw[arr] (t) -- (m);
\end{tikzpicture}
\end{adjustbox}
```

* **Active** (dynamic) detection **runs** the sample and decides from what it does.
* The controlled environment is a **sandbox**; its record of the run is the **trace**.

## Static against active

```{=latex}
\begin{adjustbox}{max width=\linewidth,max totalheight=0.1\textheight,center}
\begin{tikzpicture}[font=\footnotesize]
  \node[neu, text width=2.0cm] (n0) {static: bytes};
  \node[dfn, text width=2.0cm, right=6mm of n0] (n1) {fast, fakeable};
  \node[neu, text width=2.0cm, right=6mm of n1] (n2) {active: run, trace};
  \node[ok, text width=2.0cm, right=6mm of n2] (n3) {slow, harder to fake};
  \draw[arr] (n0) -- (n1); \draw[arr] (n1) -- (n2); \draw[arr] (n2) -- (n3);
\end{tikzpicture}
\end{adjustbox}
```


| | Static (passive) | Active (dynamic) |
|:----------------|:-------------------|:---------------------------|
| input | the bytes | the trace of one run |
| cost per sample | milliseconds | minutes, one machine slot |
| easy to fake | yes, metadata | no, behaviour must happen |
| blind spots | packers, no row | sandbox detection, delays |

* Detection on a user's machine (EDR) is also active; we study the analysis lab.

# Sandboxes

## What a sandbox must do

```{=latex}
\begin{adjustbox}{max width=\linewidth,max totalheight=0.34\textheight,center}
\begin{tikzpicture}
  \node[dfn, text width=1.9cm] (r) {1 restore clean state};
  \node[dfn, text width=1.9cm, right=6mm of r] (d) {2 drop sample, start agent};
  \node[atk, text width=1.9cm, right=6mm of d] (x) {3 run for a fixed window};
  \node[dfn, text width=1.9cm, right=6mm of x] (c) {4 collect trace and files};
  \node[ok, text width=1.9cm, right=6mm of c] (m) {5 report, then discard};
  \draw[arr] (r) -- (d); \draw[arr] (d) -- (x); \draw[arr] (x) -- (c); \draw[arr] (c) -- (m);
\end{tikzpicture}
\end{adjustbox}
```

* **Contain** the sample, **observe** it, **reset** the machine, and do it thousands of times a day.

## Types of sandbox (1/2): isolation and speed

```{=latex}
\begin{adjustbox}{max width=\linewidth,max totalheight=0.1\textheight,center}
\begin{tikzpicture}[font=\footnotesize]
  \node[neu, text width=2.0cm] (n0) {emulator};
  \node[neu, text width=2.0cm, right=6mm of n0] (n1) {container};
  \node[dfn, text width=2.0cm, right=6mm of n1] (n2) {microVM};
  \node[dfn, text width=2.0cm, right=6mm of n2] (n3) {virtual machine};
  \node[ok, text width=2.0cm, right=6mm of n3] (n4) {bare metal};
  \draw[arr] (n0) -- (n1); \draw[arr] (n1) -- (n2); \draw[arr] (n2) -- (n3); \draw[arr] (n3) -- (n4);
\end{tikzpicture}
\end{adjustbox}
```


<!-- defines: container, microVM, virtual machine, emulator -->

| Type | What it is | Isolation | Start (assumption) |
|:---------------|:-----------------------------|:--------------|:------------|
| **Emulator** | software CPU and OS model (QEMU, Qiling) | strong | seconds |
| **Container** | shares the host kernel (Docker, Podman) | weakest | about 1 s |
| **microVM** | tiny VM, own kernel (Firecracker, gVisor) | strong | about 1 s |
| **Virtual machine** | full guest, snapshot revert (KVM, VirtualBox) | strong | 10 to 60 s |
| **Bare metal** | real PC, disk re-imaged | strongest | minutes |

## Types of sandbox (2/2): fidelity and evasion

```{=latex}
\begin{adjustbox}{max width=\linewidth,max totalheight=0.1\textheight,center}
\begin{tikzpicture}[font=\footnotesize]
  \node[neu, text width=2.0cm] (n0) {Linux only: container};
  \node[neu, text width=2.0cm, right=6mm of n0] (n1) {partial: emulator};
  \node[dfn, text width=2.0cm, right=6mm of n1] (n2) {Windows: VM};
  \node[ok, text width=2.0cm, right=6mm of n2] (n3) {real PC: bare metal};
  \draw[arr] (n0) -- (n1); \draw[arr] (n1) -- (n2); \draw[arr] (n2) -- (n3);
\end{tikzpicture}
\end{adjustbox}
```


| Type | Windows samples | Hard to detect? | Typical use |
|:---------------|:--------|:-----------------|:-----------------------------|
| Emulator | partly | no: timing and CPU quirks | first behaviour, packers |
| Container | no (Linux) | no: shared kernel visible | Linux, lab demos |
| microVM | no | partly | cloud-scale Linux |
| Virtual machine | yes | partly: artefacts | analysis labs |
| Bare metal | yes | yes | evasive samples |

## Speed: the window dominates

![](plots/04/d04_sandbox_throughput.pdf){width=100%}

* Restore is a few percent of the run, except on bare metal; 120 s gives about 30 runs an hour per slot.

## Limits of every sandbox

* *Coverage*: one run, one input; code behind a missing condition never executes.
* *Time*: a fixed window; slow or delayed behaviour is not seen.
* *Fidelity*: the sandbox is not a real user machine.
* *Cost*: each run needs a licence, a machine slot and minutes.
* *Safety*: an escape from a weak sandbox infects the lab.

## Cuckoo Sandbox

<!-- defines: Cuckoo -->

```{=latex}
\begin{adjustbox}{max width=\linewidth,max totalheight=0.34\textheight,center}
\begin{tikzpicture}
  \node[neu, text width=1.7cm] (u) {submit sample};
  \node[dfn, text width=2.0cm, right=7mm of u] (h) {host: scheduler};
  \node[atk, text width=2.6cm, right=7mm of h] (g) {guest VM + agent, API hooks};
  \node[dfn, text width=2.0cm, right=7mm of g] (p) {processing, signatures};
  \node[ok, text width=1.6cm, right=7mm of p] (r) {JSON report};
  \draw[arr] (u) -- (h); \draw[arr] (h) -- (g); \draw[arr] (g) -- (p); \draw[arr] (p) -- (r);
\end{tikzpicture}
\end{adjustbox}
```

* Open source (2010), automates the five steps on a Windows guest; **monitor hooks** log every API call.
* The datasets of this class are Cuckoo traces; Cuckoo 2.x is no longer maintained.

## CAPEv2

<!-- defines: CAPEv2 -->

* **CAPEv2** (Config And Payload Extraction) is a maintained fork of Cuckoo.
* It adds automatic **unpacking**, YARA classification of unpacked payloads, and malware **configuration extraction**.
* Its reports keep a Cuckoo-like structure, so feature code carries over.
* Successor project: Cuckoo3 (CERT-EE), a rewrite, not yet production ready.

## Online platforms

```{=latex}
\begin{adjustbox}{max width=\linewidth,max totalheight=0.1\textheight,center}
\begin{tikzpicture}[font=\footnotesize]
  \node[neu, text width=2.0cm] (n0) {your sample};
  \node[dfn, text width=2.0cm, right=6mm of n0] (n1) {platform: engines + sandbox};
  \node[ok, text width=2.0cm, right=6mm of n1] (n2) {report and verdict};
  \draw[arr] (n0) -- (n1); \draw[arr] (n1) -- (n2);
\end{tikzpicture}
\end{adjustbox}
```


| Platform | What it adds | Note |
|:-----------------|:------------------------------------------|:-------------------|
| **VirusTotal** | 70+ antivirus engines, sandboxes, community | crowd verdicts |
| **ANY.RUN** | interactive VM in the browser | analyst clicks |
| **Hybrid Analysis** | free reports (CrowdStrike Falcon Sandbox) | public samples |
| **Joe Sandbox**, **VMRay** | deep behaviour reports; hypervisor-based | commercial |

* Uploading a sample **shares it**: never upload confidential files.

## AI in the platforms

:::: {.columns}
::: {.column width="55%"}
![VirusTotal blog, 24 Apr 2023](clips/sandbox/virustotal-codeinsight-2023-clip.png){width=100%}
:::
::: {.column width="45%"}
* **Code Insight**: a large language model summarises what a script does.
* Sandboxes add machine-learning scores on traces.
* Vendor claims: no independent benchmark covers all of them; verify on your data.
:::
::::

# Sandbox Evasion

## A sample that checks who is watching

<!-- defines: sandbox evasion, evasive sample -->

```{=latex}
\begin{adjustbox}{max width=\linewidth,max totalheight=0.34\textheight,center}
\begin{tikzpicture}
  \node[neu, text width=1.6cm] (s) {sample starts};
  \node[dfn, text width=2.4cm, right=8mm of s] (c) {\textbf{check}: sandbox or user machine?};
  \node[ok, text width=2.6cm, above right=2mm and 10mm of c] (b) {sandbox: stay quiet, look benign};
  \node[atk, text width=2.6cm, below right=2mm and 10mm of c] (m) {user machine: run payload};
  \draw[arr] (s) -- (c); \draw[arr] (c) -- (b); \draw[arratk] (c) -- (m);
\end{tikzpicture}
\end{adjustbox}
```

* An **evasive sample** detects the analysis and behaves like a benign program.
* Its trace looks benign: the detector is not wrong about the trace, the trace is wrong about the sample.

## Taxonomy of evasion

```{=latex}
\begin{adjustbox}{max width=\linewidth,max totalheight=0.1\textheight,center}
\begin{tikzpicture}[font=\footnotesize]
  \node[atk, text width=2.0cm] (n0) {environment};
  \node[atk, text width=2.0cm, right=6mm of n0] (n1) {timing};
  \node[atk, text width=2.0cm, right=6mm of n1] (n2) {human};
  \node[atk, text width=2.0cm, right=6mm of n2] (n3) {targeting};
  \node[atk, text width=2.0cm, right=6mm of n3] (n4) {kill switch};
  \draw[arr] (n0) -- (n1); \draw[arr] (n1) -- (n2); \draw[arr] (n2) -- (n3); \draw[arr] (n3) -- (n4);
\end{tikzpicture}
\end{adjustbox}
```


| Family | What the sample checks | Sandbox defence |
|:---------------|:----------------------------------|:---------------------|
| Environment | VM artefacts, tiny disk, few CPUs | realistic guest |
| Timing | sleeps minutes; short window | skip or fast-forward sleeps |
| Human | mouse moves, recent files, clicks | simulated user |
| Targeting | language, domain, country | several profiles |
| Kill switch | a domain that answers or not | careful network model |

* Survey: [@afianian:2019].

## Example 1: Rombertik (2015)

:::: {.columns}
::: {.column width="55%"}
![Silicon UK, 5 May 2015](clips/sandbox/rombertik-2015-clip.png){width=100%}
:::
::: {.column width="45%"}
* Cisco Talos: checks for analysis before it acts.
* Floods memory with about 960 million writes: a full log would exceed 100 GB.
* If it thinks it is watched, it wipes the boot record.
* Under it: a browser credential stealer.
:::
::::

## Example 2: Lumma stealer (2023)

:::: {.columns}
::: {.column width="55%"}
![Infosecurity Magazine, 20 Nov 2023](clips/sandbox/lumma-2023-clip.png){width=100%}
:::
::: {.column width="45%"}
* Waits for **human** mouse movement before running.
* Samples five cursor positions, 50 ms apart; angles under 45 degrees mean a person.
* An automated cursor fails the test: the sandbox sees a harmless idle program.
:::
::::

## Example 3: WannaCry kill switch (2017)

:::: {.columns}
::: {.column width="55%"}
![CNBC, 2017: attribution story](clips/malware/wannacry-2017-clip.png){width=100%}
:::
::: {.column width="45%"}
* WannaCry first asked for an unregistered domain and **exited if it answered**.
* Sandboxes that answer every DNS query made it stop: a false "benign".
* A researcher registered the domain in May 2017 and halted the spread.
:::
::::

## What the evasive trace looks like

```{=latex}
\begin{adjustbox}{max width=\linewidth,max totalheight=0.30\textheight,center}
\begin{tikzpicture}
  \node[neu, text width=2.0cm] (f) {payload run: 100 calls};
  \node[dfn, text width=2.6cm, right=8mm of f] (e) {\textbf{early exit}: 10 calls then stop};
  \node[dfn, text width=2.9cm, right=8mm of e] (t) {\textbf{stalling}: one call repeated 90 times};
  \draw[arr] (f) -- (e); \draw[arr] (e) -- (t);
\end{tikzpicture}
\end{adjustbox}
```

* Both leave a **short** or **repetitive** trace; we simulate them on real malware traces (Demo D5).

# Traces as Data

## Which data? Real traces, not synthetic

| Corpus | Traces | Labels | Calls |
|:--------------------|--------:|:----------------|:------------------|
| MalBehavD-V1 [@maniriho:2023] | 2,570 | benign / malware | API names, one pipeline |
| Mal-API-2019 [@catak:2019] | 7,107 | 8 families | API names, first 200 |
| Oliveira 2019 | 43,876 | benign / malware | integer ids, 100 calls |

* All three: real samples run in **Cuckoo**; no script writes these traces.

## Where the labels come from

* Malware: VirusTotal submissions (MalBehavD) and VirusTotal engine consensus (Mal-API families).
* Benign: downloads from a software site, each checked on VirusTotal.
* Weak points: family names disagree between engines; benign and malware come from different sources, so part of the signal can be *where the file came from*.

## Behaviour classes

<!-- defines: behaviour class -->

![](plots/04/d04_category_mix.pdf){width=100%}

* A **behaviour class** groups API names by prefix (file, registry, process, network, ...); Mal-API traces are loops of library loading.

## What one trace looks like

![](plots/04/d04_trace_strip.pdf){width=100%}

* One column per call, coloured by behaviour class; malware A probes first (`getcursorpos`, `enumwindows`).

## DEMO D1

\begin{center}
\Huge \textbf{DEMO D1}\\[4mm]
\Large \texttt{notebooks/03-malware/notebook\_03.ipynb}
\end{center}

# Representing a Trace

## Four representations

```{=latex}
\begin{adjustbox}{max width=\linewidth,max totalheight=0.1\textheight,center}
\begin{tikzpicture}[font=\footnotesize]
  \node[neu, text width=2.0cm] (n0) {trace};
  \node[dfn, text width=2.0cm, right=6mm of n0] (n1) {bag or n-grams};
  \node[dfn, text width=2.0cm, right=6mm of n1] (n2) {ids};
  \node[dfn, text width=2.0cm, right=6mm of n2] (n3) {strip};
  \draw[arr] (n0) -- (n1); \draw[arr] (n1) -- (n2); \draw[arr] (n2) -- (n3);
\end{tikzpicture}
\end{adjustbox}
```


<!-- defines: bag of calls, n-gram, embedding -->

| Representation | Keeps order? | Size per trace | For |
|:--------------------|:----------|:--------------|:-------------------|
| **Bag of calls** | no | 291 counts | linear model, forest |
| **$n$-grams** | locally | 7,712 counts | linear model, forest |
| **Sequence of ids** | all | 100 ids | neural networks |
| **Behaviour strip** | all, coarse | 11 symbols | quick views |

## From a trace to bigrams

:::: {.columns}
::: {.column width="50%"}
![](plots/04/d04_bigram_toy.pdf){width=100%}
:::
::: {.column width="50%"}
* A bigram counts a call followed by another; the toy trace has 8 calls and 5 distinct bigrams.
* Trigrams add one more call of context; the set grows to 7,712 features.
:::
::::

## Graphs

* Calls as nodes, transitions as edges: a **graph** keeps process trees and data flow.
* A graph neural network reads it; cost and tuning are higher.
* Use it when the process tree matters, not for a first baseline.

## The usual models

```{=latex}
\begin{adjustbox}{max width=\linewidth,max totalheight=0.1\textheight,center}
\begin{tikzpicture}[font=\footnotesize]
  \node[ok, text width=2.0cm] (n0) {linear, forest};
  \node[dfn, text width=2.0cm, right=6mm of n0] (n1) {convolution};
  \node[dfn, text width=2.0cm, right=6mm of n1] (n2) {GRU, LSTM};
  \node[atk, text width=2.0cm, right=6mm of n2] (n3) {transformer};
  \draw[arr] (n0) -- (n1); \draw[arr] (n1) -- (n2); \draw[arr] (n2) -- (n3);
\end{tikzpicture}
\end{adjustbox}
```


<!-- defines: GRU -->

| Model | Input | Cost | Remark |
|:------------------------|:---------------|:-------|:-----------------------------|
| Logistic regression, forest, boosting | bag, $n$-grams | tiny | strong baseline |
| 1-D convolution | ids | small | local patterns |
| GRU, LSTM [@pascanu:2015] | ids | medium | reads the trace |
| Transformer | ids | high | needs large corpora |
| Graph network | graph | high | process trees |

* A **gated recurrent unit (GRU)** is a recurrent layer that reads the trace call by call.

## Six models, one split

![](plots/04/d04_models_auc.pdf){width=100%}

* Test AUC 0.983 to 0.993 on 771 traces; the intervals overlap.
* Order of the models is not reliable: we need a paired test (below).

## DEMO D2

\begin{center}
\Huge \textbf{DEMO D2}\\[4mm]
\Large \texttt{notebooks/03-malware/notebook\_03.ipynb}
\end{center}

# Sequence Models as Encoders

## A GRU is a layer; the idea is an encoder

<!-- defines: sequence model, encoder -->

```{=latex}
\begin{adjustbox}{max width=\linewidth,max totalheight=0.30\textheight,center}
\begin{tikzpicture}
  \node[neu, text width=2.0cm] (i) {trace: call ids};
  \node[dfn, text width=2.0cm, right=8mm of i] (e) {embedding};
  \node[dfn, text width=2.4cm, right=8mm of e] (g) {\textbf{encoder}: GRU layer};
  \node[ok, text width=2.0cm, right=8mm of g] (z) {vector $z$ (64)};
  \node[neu, text width=2.2cm, right=8mm of z] (h) {any classifier};
  \draw[arr] (i) -- (e); \draw[arr] (e) -- (g); \draw[arr] (g) -- (z); \draw[arr] (z) -- (h);
\end{tikzpicture}
\end{adjustbox}
```

* A **sequence model** reads a trace of any length and **compresses** it into a fixed vector $z$.
* The **gated recurrent unit (GRU)** is one such layer; LSTM and convolution are others.

## The encoder as a feature extractor

:::: {.columns}
::: {.column width="50%"}
![](plots/04/d04_embed_pca.pdf){width=100%}
:::
::: {.column width="50%"}
* Encoder state of the GRU, two principal components: malware and benign separate.
* Logistic regression on $z$: AUC 0.983, the same as the GRU's own head.
* Train once; reuse $z$ with any model.
:::
::::

## Training the encoder

:::: {.columns}
::: {.column width="50%"}
![](plots/04/d04_gru_loss.pdf){width=100%}
:::
::: {.column width="50%"}
* Embedding 32, GRU 64, sigmoid output, 12 epochs on 1,800 traces.
* Validation loss stops improving early: small data, small network.
:::
::::

## Temporal autoencoder

<!-- defines: temporal autoencoder -->

```{=latex}
\begin{adjustbox}{max width=\linewidth,max totalheight=0.30\textheight,center}
\begin{tikzpicture}
  \node[neu, text width=1.8cm] (i) {benign trace};
  \node[dfn, text width=2.2cm, right=8mm of i] (e) {encoder GRU};
  \node[ok, text width=1.6cm, right=8mm of e] (z) {code $z$ (16)};
  \node[dfn, text width=2.2cm, right=8mm of z] (d) {decoder GRU};
  \node[neu, text width=2.0cm, right=8mm of d] (o) {rebuilt trace};
  \draw[arr] (i) -- (e); \draw[arr] (e) -- (z); \draw[arr] (z) -- (d); \draw[arr] (d) -- (o);
\end{tikzpicture}
\end{adjustbox}
```

* Trained on **benign** traces only; reconstruction error is the anomaly score.
* A trace it cannot rebuild is unlike what it saw.

## Autoencoder scores

:::: {.columns}
::: {.column width="50%"}
![](plots/04/d04_ae_scores.pdf){width=100%}
:::
::: {.column width="50%"}
* Mean error: benign 4.91, malware 5.45; AUC 0.76 without a malware label.
* Weaker than a supervised model; useful when labels are missing or new families appear.
:::
::::

## DEMO D3

\begin{center}
\Huge \textbf{DEMO D3}\\[4mm]
\Large \texttt{notebooks/03-malware/notebook\_03.ipynb}
\end{center}

# The Shuffle Test

## Does the model use the order?

<!-- defines: shuffle test -->

```{=latex}
\begin{adjustbox}{max width=\linewidth,max totalheight=0.30\textheight,center}
\begin{tikzpicture}
  \node[neu, text width=3.2cm] (o) {a b c d e f g h};
  \node[dfn, text width=3.2cm, right=10mm of o] (b) {block $w=2$: c d a b g h e f};
  \node[atk, text width=3.2cm, right=10mm of b] (f) {$w=1$: f a h c b g d e};
  \draw[arr] (o) -- (b); \draw[arr] (b) -- (f);
\end{tikzpicture}
\end{adjustbox}
```

* Hypothesis: the model uses only **which** calls occur. Then permuting a test trace must not change its score.
* A sequence model that ties its shuffled score has learned a bag.

## Protocol

* First 100 calls, same for all models; **control**: bag of calls cannot move.
* **Test-only**: train on original order, score shuffled traces.
* **Block widths** $w$ from 1 (all order destroyed) to 100 (intact): how long are the patterns?
* **Train and test shuffled**: retrain; does the model recover?
* Five seeds; report mean and spread.

## Block shuffle on binary detection

![](plots/04/d04_shuffle_blocks.pdf){width=100%}

* n-gram AUC 0.989 falls to 0.981 at $w=1$ and recovers by $w=8$: patterns are short.
* The GRU stays at 0.98: it never used order. Bag: flat by construction.

## Retraining on shuffled data

:::: {.columns}
::: {.column width="50%"}
![](plots/04/d04_shuffle_bars.pdf){width=100%}
:::
::: {.column width="50%"}
* n-gram: 0.989, 0.981 test-only, 0.985 retrained on shuffled traces.
* Order is worth under one AUC point for **binary** detection of this corpus.
:::
::::

## It depends on the task

![](plots/04/d04_shuffle_tasks.pdf){width=100%}

* Families: n-gram macro-F1 0.55 falls to 0.26; 43,876 traces: bigrams 0.990 fall to 0.784. The bags do not move.

## DEMO D4

\begin{center}
\Huge \textbf{DEMO D4}\\[4mm]
\Large \texttt{notebooks/03-malware/notebook\_03.ipynb}
\end{center}

# Machine Learning Against Evasion

## The model against the evasion

![](plots/04/d04_evasion_recall.pdf){width=100%}

* Bag of calls plus logistic regression, trained on complete traces.
* Early exit: recall 0.96 falls to 0.73 at 10 calls.
* Stalling with the call the model trusts most: recall 0.00.

## DEMO D5

\begin{center}
\Huge \textbf{DEMO D5}\\[4mm]
\Large \texttt{notebooks/03-malware/notebook\_05.ipynb}
\end{center}

## Roadmap of mitigations

```{=latex}
\begin{adjustbox}{max width=\linewidth,max totalheight=0.1\textheight,center}
\begin{tikzpicture}[font=\footnotesize]
  \node[atk, text width=2.0cm] (n0) {evasive trace};
  \node[dfn, text width=2.0cm, right=6mm of n0] (n1) {partial traces};
  \node[dfn, text width=2.0cm, right=6mm of n1] (n2) {collapse repeats};
  \node[ok, text width=2.0cm, right=6mm of n2] (n3) {unknown};
  \node[ok, text width=2.0cm, right=6mm of n3] (n4) {second run};
  \draw[arr] (n0) -- (n1); \draw[arr] (n1) -- (n2); \draw[arr] (n2) -- (n3); \draw[arr] (n3) -- (n4);
\end{tikzpicture}
\end{adjustbox}
```


| Mitigation | Idea | Tested here |
|:------------------------|:----------------------------------|:----------|
| Train on partial traces | short traces become normal | yes |
| Collapse repeats | a loop is one call | yes |
| Abstain: **unknown** | quiet or odd trace is not benign | yes |
| Second environment | compare two runs | concept |
| Unsupervised on benign | flag what is not normal | yes |
| Static first, then active | cascade (below) | yes |

## Partial traces and repeats

![](plots/04/d04_mitigation_recall.pdf){width=100%}

* Prefix augmentation: early-exit recall 0.73 to 0.86; false alarms 5% to 9%.
* Collapsing repeats: stalling recall 0.00 to 0.65.
* Each fix costs something; the demo prints both sides.

## Abstain: unknown is not benign

:::: {.columns}
::: {.column width="50%"}
![](plots/04/d04_abstain.pdf){width=100%}
:::
::: {.column width="50%"}
* Rule: fewer than 15 calls, one call above 50%, or a score in 0.3 to 0.7.
* Early exit and stalling: 100% unknown, sent to a second environment.
* Cost: 22% of benign traces are also unknown.
:::
::::

## Second environment and unsupervised

* **Differential run**: execute on a VM and on bare metal; a large trace difference is the signal.
* **Temporal autoencoder** (below) learns normal benign traces; AUC 0.76 with no malware label.
* Detect the **behaviour**, not the check (next frame).

## A failure case: counting probes

:::: {.columns}
::: {.column width="50%"}
![](plots/04/d04_probes.pdf){width=100%}
:::
::: {.column width="50%"}
* Evasive samples must look before they hide, so count environment probes in the first 10 calls?
* Benign programs probe too: 37% with two or more, against 22% for malware.
:::
::::

## DEMO D6

\begin{center}
\Huge \textbf{DEMO D6}\\[4mm]
\Large \texttt{notebooks/03-malware/notebook\_05.ipynb}
\end{center}

# Comparing Close Models

## Same test set, two models

<!-- defines: McNemar test -->

* Test set of 771 traces: bag + logistic regression (37 errors) against bag + random forest (21 errors).
* Accuracy 0.952 against 0.973: is the forest really better, or lucky?
* Most traces are right or wrong **for both**; they say nothing about the difference.

## Only disagreements count

:::: {.columns}
::: {.column width="50%"}
![](plots/04/d04_mcnemar_pair.pdf){width=100%}
:::
::: {.column width="50%"}
* $b$ = logistic right, forest wrong: 7 traces.
* $c$ = logistic wrong, forest right: 23 traces.
:::
::::

## McNemar's test

* Under H0 (equal error rates) each disagreement is a fair coin: $\min(b,c) \sim \mathrm{Binomial}(b+c, \tfrac12)$.
* For $b+c \ge 25$: $\chi^2 = \dfrac{(|b-c|-1)^2}{b+c}$ with one degree of freedom [@mcnemar:1947].
* Worked: $b=7$, $c=23$: $(16-1)^2/30 = 7.5$, $p = 0.006$ (exact $0.005$).
* Reject H0: the forest is better on this set.

## Which pairs differ?

:::: {.columns}
::: {.column width="50%"}
![](plots/04/d04_mcnemar_matrix.pdf){width=100%}
:::
::: {.column width="50%"}
* Exact $p$ per pair. Logistic against $n$-gram: $p = 0.75$, no difference.
* Same GRU, two seeds: $p = 0.09$: seed noise.
:::
::::

## Limits of the test

* One split, one test set: it measures this sample, not the training noise [@dietterich:1998].
* Fewer than 25 disagreements: use the exact binomial.
* Many pairs: correct for multiple tests (Holm), or compare to a reference only.
* Significant is not large: report the error counts too.

## DEMO D7

\begin{center}
\Huge \textbf{DEMO D7}\\[4mm]
\Large \texttt{notebooks/03-malware/notebook\_05.ipynb}
\end{center}

# The Full System

## Static first, active when unsure

<!-- defines: cascade -->

```{=latex}
\begin{adjustbox}{max width=\linewidth,max totalheight=0.45\textheight,center}
\begin{tikzpicture}[font=\footnotesize, node distance=8mm]
  \node[neu, text width=1.3cm] (f) {file};
  \node[dfn, text width=2.6cm, right=of f] (s1) {\textbf{1 static binary}\\milliseconds};
  \node[ok, text width=2.6cm, right=of s1] (b) {confident benign: stop};
  \node[dfn, text width=2.6cm, below=5mm of b] (s2) {\textbf{2 static family}\\confident malware};
  \node[atk, text width=2.6cm, below=12mm of s1] (d1) {\textbf{3 sandbox + dynamic binary}\\unsure files};
  \node[dfn, text width=2.6cm, right=of d1] (d2) {\textbf{4 dynamic family}\\malware only};
  \draw[arr] (f) -- (s1); \draw[arr] (s1) -- (b); \draw[arr] (s1.east) -- ++(4mm,0) |- (s2.west);
  \draw[arratk] (s1) -- (d1); \draw[arr] (d1) -- (d2);
\end{tikzpicture}
\end{adjustbox}
```

* Class 9 gave stages 1 and 2; today adds 3 and 4 for the files stage 1 cannot decide.

## How much sandbox do we need?

![](plots/04/d04_cascade.pdf){width=100%}

* Queue with 10% malware. Static alone: F1 0.892, 2.7% false alarms.
* Band 0.3 to 0.7 (3% to the sandbox): F1 0.932; sandbox for every file: F1 0.785.

## Why the cascade wins

* Stage 1 is almost perfect where it is confident; stage 3 is wrong at random.
* Sending only the grey band keeps the static precision and adds behaviour where it counts.
* Assumption: PE rows and traces are paired by class, so the two errors are independent; real hard files are hard for both, so expect less.

## Family stages

:::: {.columns}
::: {.column width="50%"}
![](plots/04/d04_family_confusion.pdf){width=100%}
:::
::: {.column width="50%"}
* Static families (Class 9): macro-F1 0.65 flat, 0.63 hierarchical.
* Dynamic families here (8 classes, $n$-gram + logistic): macro-F1 0.55.
* Trojan, backdoor and virus overlap.
:::
::::

## DEMO D8

\begin{center}
\Huge \textbf{DEMO D8}\\[4mm]
\Large \texttt{notebooks/03-malware/notebook\_05.ipynb}
\end{center}

# Takeaways

## What to remember

* **Active detection** runs the sample in a sandbox and reads the trace; choose the sandbox by system and isolation.
* Evasive samples fake a benign trace: train on partial traces, collapse repeats, answer *unknown*.
* A sequence model is an encoder; run the shuffle test per task before claiming order.
* Compare close models with McNemar; use the cascade: static first, sandbox for the grey band.
* Next class: break these detectors without breaking the malware.

<!-- refs:begin -->
