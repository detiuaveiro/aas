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

# Malware in Context

## Why detection is a learning problem

* **Malware** is any program built to harm a device, network, server or user.
* The harm ranges from a prank to a continental outage.
* Today's classes: detect it **without** running it, then **with** running it, then break both.

## Learning objectives of Class 9

* Name malware types and place incidents on a timeline.
* Compare ten ways to recognise malware; place machine learning among them.
* Build a static detector from file headers and API imports.
* Explain how malware share and data drift limit a detector.

## Malware types (1/2)

<!-- defines: virus, worm, trojan, ransomware, botnet, wiper -->

```{=latex}
\begin{adjustbox}{max width=\linewidth,max totalheight=0.12\textheight,center}
\begin{tikzpicture}[font=\footnotesize]
  \node[dfn, text width=5.2cm] (a) {\textbf{how it spreads}\\virus, worm, trojan};
  \node[atk, text width=5.8cm, right=8mm of a] (b) {\textbf{what it does}\\ransomware, botnet, wiper};
\end{tikzpicture}
\end{adjustbox}
```

| Type | Defining trait | Example |
|:-----------|:---------------------------------------|:-----------------|
| Virus | infects other files; runs when the host runs | Elk Cloner (1982) |
| Worm | copies itself over the network, no host file | Morris, Stuxnet |
| Trojan | looks useful, hides its payload | Gameover Zeus |
| Ransomware | encrypts files, demands payment | CryptoLocker |
| Botnet | many infected machines, one controller | Mirai |
| Wiper | destroys data; no key exists | NotPetya |

* One program mixes both axes: WannaCry is a worm that carries ransomware.

## Malware types (2/2): roles in our datasets

<!-- defines: RAT, downloader, spyware, infostealer -->

| Role | What it does |
|:------------|:-------------------------------------------------|
| RAT | remote-access trojan: the attacker controls the machine |
| Downloader | small first stage; fetches the real payload |
| Banking trojan | steals bank credentials and redirects payments |
| Spyware | watches the user: screen, keys, files |
| Infostealer | collects saved passwords and cookies (RedLine) |

* Class 9 labels files with these roles (family detection).

## Timeline (1/3): 1971 to 1999

```{=latex}
\begin{adjustbox}{max width=\linewidth,max totalheight=0.45\textheight,center}
\begin{tikzpicture}[font=\small]
  \draw[arr] (-0.4,0) -- (11.8,0);
  \foreach \x/\y/\n/\t/\p in {0.00/1971/Creeper/prank/a, 2.75/1982/Elk Cloner/boot virus/b, 5.50/1986/Brain/PC virus/a, 8.25/1988/Morris/worm/b, 11.00/1999/Melissa/Word worm/a} {
    \fill[aasblue] (\x,0) circle (2pt);
    \if\p a
      \node[above=3pt, align=center] at (\x,0) {\textbf{\y}\\\n\\{\scriptsize\textcolor{aasgrey}{\t}}};
    \else
      \node[below=3pt, align=center] at (\x,0) {\textbf{\y}\\\n\\{\scriptsize\textcolor{aasgrey}{\t}}};
    \fi
  }
\end{tikzpicture}
\end{adjustbox}
```

* Not to scale. The decades: experiments, floppy-disk viruses, then the first internet worm.

## Timeline (2/3): 2000 to 2012

```{=latex}
\begin{adjustbox}{max width=\linewidth,max totalheight=0.45\textheight,center}
\begin{tikzpicture}[font=\small]
  \draw[arr] (-0.4,0) -- (11.8,0);
  \foreach \x/\y/\n/\t/\p in {0.00/2000/ILOVEYOU/mail worm/a, 2.20/2001/Code Red/server worm/b, 4.40/2003/Slammer/fast worm/a, 6.60/2007/Zeus/banking trojan/b, 8.80/2008/Conficker/botnet worm/a, 11.00/2010/Stuxnet/ICS worm/b} {
    \fill[aasblue] (\x,0) circle (2pt);
    \if\p a
      \node[above=3pt, align=center] at (\x,0) {\textbf{\y}\\\n\\{\scriptsize\textcolor{aasgrey}{\t}}};
    \else
      \node[below=3pt, align=center] at (\x,0) {\textbf{\y}\\\n\\{\scriptsize\textcolor{aasgrey}{\t}}};
    \fi
  }
\end{tikzpicture}
\end{adjustbox}
```

* The decade of worms: speed, botnets and the first state-grade weapon.

## Timeline (3/3): 2013 to 2023

```{=latex}
\begin{adjustbox}{max width=\linewidth,max totalheight=0.45\textheight,center}
\begin{tikzpicture}[font=\small]
  \draw[arr] (-0.4,0) -- (11.8,0);
  \foreach \x/\y/\n/\t/\p in {0.00/2013/CryptoLocker/ransomware/a, 1.57/2014/Emotet/loader/b, 3.14/2016/Mirai/IoT botnet/a, 4.71/2017/WannaCry/ransom worm/b, 6.29/2017/NotPetya/wiper/a, 7.86/2020/SolarWinds/supply chain/b, 9.43/2021/Colonial/ransomware/a, 11.00/2023/Clop/data theft/b} {
    \fill[aasblue] (\x,0) circle (2pt);
    \if\p a
      \node[above=3pt, align=center] at (\x,0) {\textbf{\y}\\\n\\{\scriptsize\textcolor{aasgrey}{\t}}};
    \else
      \node[below=3pt, align=center] at (\x,0) {\textbf{\y}\\\n\\{\scriptsize\textcolor{aasgrey}{\t}}};
    \fi
  }
\end{tikzpicture}
\end{adjustbox}
```

* Crime becomes a business: ransomware, loaders, supply chains and extortion.

## Creeper (1971): the first self-copying program

* Bob Thomas, at a Boston research firm, wrote it for an early research network.
* It hopped between mainframes and printed "I'm the creeper, catch me if you can".
* Ray Tomlinson made it copy itself, then wrote **Reaper** to delete it: the first antivirus.
* Source: Exabeam, "Creeper: The World's First Computer Virus".

## Elk Cloner (1982) and Brain (1986): the first viruses

* Elk Cloner: an Apple II virus by a 15-year-old; it printed a poem on the 50th boot.
* Brain: the first virus for personal computers, written in Lahore.
* Both spread only when people **shared floppy disks**: slow and local.

## Morris worm (1988): the first internet outage

:::: {.columns}
::: {.column width="52%"}
![Lawrence Livermore National Laboratory](clips/malware/morris-1988-clip.png){width=100%}
:::
::: {.column width="48%"}
* Student experiment: guessed passwords, used a mail-server flaw.
* A bug made it re-copy itself: machines crawled.
* First conviction under the 1986 computer-crime law of the United States.
:::
::::

## ILOVEYOU (2000): the mail worm

:::: {.columns}
::: {.column width="52%"}
![Cybercrime Magazine](clips/malware/iloveyou-2000-clip.png){width=100%}
:::
::: {.column width="48%"}
* A mail with a script attachment: users **ran it themselves**.
* It mailed itself to the address book and overwrote files.
* Tens of millions of Windows machines; Melissa (1999) did the same inside a Word file.
:::
::::

## Code Red (2001) and Slammer (2003): worms at network speed

* Code Red: a flaw in Microsoft's web server (IIS); 359,000 hosts in 14 hours.
* Slammer: one 376-byte packet, no file on disk; 75,000 hosts in 10 minutes.
* Slammer's patch was six months old: patching failed, not detection.

## Zeus (2007): crime-ware as a product

* A banking trojan sold as a **kit**: buyers built their own variants.
* It stole bank logins from the browser and redirected payments.
* Its descendants (Gameover Zeus) carried the first mass ransomware.

## Conficker (2008): the worm botnet

:::: {.columns}
::: {.column width="52%"}
![HKCERT, 2 Feb 2009](clips/malware/conficker-2008-clip.png){width=100%}
:::
::: {.column width="48%"}
* Used a Windows flaw (patched weeks earlier) and weak passwords.
* Millions of computers joined one botnet.
* It generated 250 fresh domain names a day to hide its controller.
:::
::::

## Stuxnet (2010): malware that breaks machines

:::: {.columns}
::: {.column width="52%"}
![IEEE Spectrum, 26 Feb 2013](clips/malware/stuxnet-2010-clip.png){width=100%}
:::
::: {.column width="48%"}
* Spread by memory sticks and Windows flaws.
* Acted only on certain Siemens controllers (PLCs).
* Changed centrifuge speeds at Natanz, Iran; replayed normal readings.
* Attributed to the United States and Israel; never confirmed.
:::
::::

## CryptoLocker (2013): ransomware at scale

:::: {.columns}
::: {.column width="52%"}
![Europol, 2 Jun 2014](clips/malware/cryptolocker-2014-clip.png){width=100%}
:::
::: {.column width="48%"}
* Encrypted files with a public key.
* Spread by the Gameover Zeus botnet: about 234,000 infections.
* Police seized its servers; victims later got free keys.
:::
::::

## Emotet (2014 to 2021): the loader business

* Began as a banking trojan; became a service that **rented** infected machines to other gangs.
* It delivered ransomware such as Ryuk.
* Police took over its servers in January 2021; it returned months later.

## Mirai (2016): a botnet of cameras

:::: {.columns}
::: {.column width="52%"}
![CNBC, 22 Oct 2016](clips/malware/mirai-2016-clip.png){width=100%}
:::
::: {.column width="48%"}
* Logged in with **factory-default passwords**.
* Source published; a copy flooded Dyn, a provider of the domain-name system (DNS).
* Twitter, Reddit, Spotify unreachable for many users.
:::
::::

## WannaCry (2017): a worm with ransomware

:::: {.columns}
::: {.column width="52%"}
![CNBC, 27 Oct 2017](clips/malware/wannacry-2017-clip.png){width=100%}
:::
::: {.column width="48%"}
* 12 May 2017: over 200,000 computers, 150 countries.
* Windows flaw patched two months before.
* Hospitals diverted ambulances.
:::
::::

## NotPetya (2017): a wiper disguised as ransomware

:::: {.columns}
::: {.column width="52%"}
![CNBC, 16 Aug 2017](clips/malware/notpetya-2017-clip.png){width=100%}
:::
::: {.column width="48%"}
* Entered through a poisoned accounting-software update.
* Ransom note, but the disk was unrecoverable: a **wiper**.
* Maersk: up to 300 million dollars lost.
:::
::::

## SolarWinds (2020): a signed backdoor

:::: {.columns}
::: {.column width="52%"}
![TechTarget, 3 Nov 2023](clips/malware/solarwinds-2020-clip.png){width=100%}
:::
::: {.column width="48%"}
* A backdoor (Sunburst) hidden in a signed update of the Orion monitoring software.
* About 18,000 customers received it; fewer than 100 were hacked.
* US government attributed it to Russian intelligence.
:::
::::

## Colonial Pipeline (2021): ransomware meets infrastructure

* DarkSide encrypted billing systems; the operator shut 5,500 miles of pipeline.
* It paid 4.4 million US dollars; the pipeline restarted on 12 May.
* The gang announced its shutdown within weeks.

## Clop (2019 to present): extortion without encryption

:::: {.columns}
::: {.column width="52%"}
![Kaspersky](clips/malware/clop-2019-clip.png){width=100%}
:::
::: {.column width="48%"}
* First encrypted files; later campaigns mostly **stole** data and threatened to publish it.
* In 2023 it exploited a flaw in the MOVEit file-transfer product against hundreds of organisations.
* Lesson: backups alone no longer end an incident.
:::
::::

## What the timeline teaches

* Goals moved from curiosity to money, politics and physical damage.
* Spread moved from shared disks to updates, default passwords and unpatched servers.
* A detector must see the **file** (static) and the **behaviour** (dynamic): the next classes.

# How To Recognize Malware

## Ten ways to recognize malware (1/2)

```{=latex}
\begin{adjustbox}{max width=\linewidth,max totalheight=0.10\textheight,center}
\begin{tikzpicture}[font=\footnotesize]
  \node[neu, text width=3.3cm] (a) {before it runs\\1, 2, 5, 6, 8, 9};
  \node[dfn, text width=3.3cm, right=6mm of a] (b) {while it runs\\3, 4, 7};
  \node[ok, text width=3.3cm, right=6mm of b] (c) {learns from both\\10};
  \draw[arr] (a) -- (b); \draw[arr] (b) -- (c);
\end{tikzpicture}
\end{adjustbox}
```

<!-- defines: static analysis -->

| Approach | Idea | Weak point |
|:--------------|:--------------------------|:--------------------------|
| 1 Signature | match a known hash or byte pattern | a repacked sample changes it |
| 2 Static analysis | read headers, strings, imports; no execution | packing hides content |
| 3 Dynamic analysis | run in a sandbox, log behaviour | slow; evasive code detects it |
| 4 File watching | alarm on mass renames or deletes | fires after damage starts |
| 5 Blocklist | refuse dangerous file types | attackers switch type |

## Ten ways to recognize malware (2/2)

<!-- defines: entropy -->

```{=latex}
\begin{adjustbox}{max width=\linewidth,max totalheight=0.10\textheight,center}
\begin{tikzpicture}[font=\footnotesize]
  \node[neu, text width=3.3cm] (a) {before it runs\\1, 2, 5, 6, 8, 9};
  \node[dfn, text width=3.3cm, right=6mm of a] (b) {while it runs\\3, 4, 7};
  \node[ok, text width=3.3cm, right=6mm of b] (c) {learns from both\\10};
  \draw[arr] (a) -- (b); \draw[arr] (b) -- (c);
\end{tikzpicture}
\end{adjustbox}
```

| Approach | Idea | Weak point |
|:--------------|:--------------------------|:--------------------------|
| 6 Allowlist | only approved programs run | heavy upkeep |
| 7 Honeypot | decoy; any touch is suspect | may be avoided |
| 8 Checksum | hash differs from trusted one | no intent shown |
| 9 Entropy | packed bytes look random | archives look random |
| 10 ML | learn from labelled files | needs data; drifts |

* Items 1 to 9 are fixed rules; item 10 learns from items 2 and 3.

## File entropy as a feature

* **Entropy** of a byte histogram: $H=-\sum_{i=0}^{255} p_i \log_2 p_i$.
* $p_i$ is the share of bytes equal to $i$: constant file 0 bits, random bytes 8 bits.

```{=latex}
\begin{adjustbox}{max width=\linewidth,max totalheight=0.22\textheight,center}
\begin{tikzpicture}[font=\scriptsize]
  \draw[arr] (0,0) -- (10.4,0) node[right] {$H$ (bits)};
  \foreach \x/\l in {0/0, 5/4, 10/8} {\draw (\x,0.07) -- (\x,-0.07) node[below] {\l};}
  \node[neu, text width=1.6cm] at (0.2,0.9) {constant padding};
  \node[dfn, text width=1.6cm] at (4.4,0.9) {text, code};
  \node[atk, text width=2.6cm] at (8.9,0.9) {packed, encrypted, compressed};
\end{tikzpicture}
\end{adjustbox}
```

* A packed section sits near 8 bits, but so does a zip inside a clean installer.
* Attackers pad files with low entropy: use one value **per section**.

# Detection Pipeline

## Pre-execution and post-execution data

* **Pre-execution**: what the file shows without running: format, headers, byte statistics, strings.
* **Post-execution**: what the running process does: API calls, files, network traffic.
* Emulation sits in between: a safe, simplified run that records the first behaviour.
* A scanner may use one phase or both; Class 10 covers the second phase.

## From hand-written rules to learning

* Early malware was rare: an analyst wrote one rule (signature) per sample.
* Labs now receive hundreds of thousands of new samples a day.
* Machine learning scores host, network and cloud data and generalises.

## Unsupervised and supervised learning

* **Unsupervised**: find structure in unlabelled data, such as clusters; labels are costly.
* **Supervised**: files carry the answer (benign, malware, family); fit a model for new files.
* Two stages: **training** the model, then **applying** it; parameters no longer change.

## The learning pipeline

![](figures/malware00.png){width=75%}

* $X$ = features of content or behaviour; $Y$ = benign, malware, or a family.

# Requirements of a Detector

## Metrics of a binary detector

<!-- defines: recall, precision, TPR, FPR, F1, AUC -->

* **True positive rate** (TPR), or recall: share of malware caught.
* **Precision**: share of alarms that are malware.
* **False positive rate** (FPR): share of clean files that alarm.
* **F1**: harmonic mean of precision and recall.
* **Area under the curve** (AUC) of the receiver operating characteristic: chance a random malware file outscores a random benign one.
* AUC ignores the threshold; precision also depends on the malware share.

## Deep learning is one option, not a requirement

* Deep networks learn high-level features from raw data (images, text, bytes).
* One model trained end to end: more data needed, harder to explain.
* The next four frames are requirements that **any** model must meet.

## Large representative datasets

* The approach is **data-driven**: the model is as good as its data.
* Training data must match the real conditions: a **representative dataset**.

## Interpretability (XAI)

* Deep networks are **black boxes**: input $X$, output $Y$, no human-readable steps.
* After a false alarm we ask: bad training set or bad model?
* **Interpretability** decides how easy it is to manage, assess and correct a model.

## False positives must be rare

* A false positive flags a clean file: a blocked program, a stopped server.
* An FPR of 1% on a million clean files a day gives 10,000 false alarms.
* Optimise for a low FPR: the base-rate frame shows why.

## Adaptability: data drift

* Usual machine learning assumes a **fixed distribution**; malware does not allow it.
* Adversaries release new versions that differ from training data.
* Software vendors keep producing new benign programs the model must accept.

## Drift in one picture

![](figures/malware01.png){width=75%}

* Retrain on schedule; watch the alarm rate.

# Multi-Class and Multi-Label

## Multi-class classification

* One of three or more classes; binary classification has two.

![](figures/multiclass.png){width=60%}

## One-versus-rest

<!-- defines: one-versus-rest -->

* One binary classifier per class: red vs rest, blue vs rest, green vs rest.
* Predict with the most confident classifier.
* $K$ classes need $K$ models.

## One-versus-one

<!-- defines: one-versus-one -->

* One binary classifier per pair of classes; each votes, the most votes win.
* The number of models is $K(K-1)/2$: 21 for $K=7$ classes.

## Multi-label classification

<!-- defines: multi-label -->

* A file can carry **several** labels at once.
* One sigmoid output per label; each has its own threshold.
* Multi-class has exactly one label per file; multi-label has zero or more.

## Metrics for many classes

* The $K \times K$ confusion matrix shows which families get mixed up.
* **Macro** F1 averages classes equally; **micro** pools all decisions; **weighted** follows class sizes.
* With rare families report macro F1: accuracy hides them.

# Static Detection

## Detect malware without running it


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

## The data: a malware-heavy benchmark

* 19,611 files, 74.4% malware: the **reverse** of a real queue.
* Random forest on 77 header fields: AUC 0.9992, F1 0.9941.
* Does this score survive a queue where malware is rare?

## Same detector, rarer malware: AUC hides the damage

![](plots/04/d04_imbalance.pdf){width=47%}

* Stratified resamples of the test files; model and threshold fixed.
* AUC and recall never move; precision: 0.991 at $b=74\%$, 0.270 at 1%.

## Notation: scanner metrics

<!-- defines: base rate -->

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

* TPR 0.9975, FPR 0.0271, $b=0.001$: precision 0.0355.
* At $b=1\%$ the best threshold is 0.95: tune on the real queue.

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

* Macro-F1 0.647, accuracy 0.675 on 5,000 held-out files.
* Downloader F1 0.982; Snake 0.177 and Spyware 0.460.
* Snake and Spyware call about 13 and 10 functions: generic calls hide them.

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

![](plots/04/d04_flat_vs_hier.pdf){width=62%}

* End-to-end macro-F1: hierarchy 0.629, flat 0.647: a small loss.
* Stage 1: AUC 0.702, F1 0.979; what it calls benign is lost.
* Snake and Spyware swap roles: the pair stays confused.

## Beyond this dataset

* Raw-byte networks learn from the whole file [@raff:2018].
* EMBER2024: files for several platforms, with evasive samples [@joyce:2025].
* Use it for homework; our demos stay small and fast.

# Limits of Static Analysis

## A replicator has no features

* Morris, WannaCry and Stuxnet spread by **behaviour**: connect, copy, repeat.
* A worm-like program is ordinary code: a header scan finds nothing odd.
* Lab: four containers send **data-only** beacons (fan-out 2, hop limit 4).
* The flow log shows depth 4; the file scan shows nothing.

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
