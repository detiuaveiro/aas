---
title: Aprendizagem Aplicada à Segurança
subtitle: "Class 1: Using AI/ML to Break Security"
author: Mário Antunes
institute: Universidade de Aveiro
date: September 18, 2026
toc: true
toc-title: "Table of Contents"
bibliography: "references.bib"
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

# The Theme of This Year

## AI for security: defence and offence

```{=latex}
\begin{adjustbox}{max width=\linewidth,center}
\begin{tikzpicture}
  \node[neu, minimum width=30mm, minimum height=14mm, font=\normalsize] (ml) {AI / ML};
  \node[dfn, right=34mm of ml, yshift=11mm, minimum width=56mm] (d) {\textbf{Defence}\\detect spam, malware,\\intrusions, fraud};
  \node[atk, right=34mm of ml, yshift=-11mm, minimum width=56mm] (o) {\textbf{Offence}\\attack traditional systems\\\emph{and} ML-based detectors};
  \draw[arr, aasblue] (ml) -- node[above, note, sloped] {learn to detect} (d);
  \draw[arratk] (ml) -- node[below, note, sloped] {learn to attack} (o);
\end{tikzpicture}
\end{adjustbox}
```

* **Class 1:** the toolbox (models, gradients, optimisation) and the map of what ML does for both sides.
* **Classes 2-4:** build a **spam detector**, then **break** it; later: anomaly and malware detectors.
* *Out of scope this year:* securing the AI pipeline (data provenance, model signing).

## Rules of the game

* **Lab only.** Own models, own data, and targets we are authorised to test.
* **Dual use.** Every technique works for both sides; we ask *who benefits and at what cost*.
* **State the threat model** before any attack: goal, knowledge, capability, stage. *No threat model, no security claim.*
* **Measure the attack:** success rate **and** cost (edits, queries, time, compute).
* **Format:** each 3-hour class is **1 hour** of lecture and **2 hours** of guided lab (notebooks and practice guides).

## Security meets ML: a short timeline

```{=latex}
\begin{adjustbox}{max width=\linewidth,center}
\begin{tikzpicture}[x=1.3cm, font=\scriptsize]
  \draw[thick, aasgrey] (-0.4,0) -- (9.5,0);
  \foreach \i/\y/\t in {
    0/1987/Denning: anomaly-\\based intrusion\\detection,
    1/2002/Graham: Bayesian\\spam filters,
    2/2005/Good-word attacks\\on spam filters,
    3/2014/Adversarial\\examples on\\deep nets,
    4/2017/PassGAN: GAN\\password guessing,
    5/2018/RL evades PE\\malware classifiers,
    6/2024/LLM agents exploit\\known CVEs,
    7/2025/AIxCC agents\\find and patch bugs}
  {
    \fill[aasred] (\i*1.3,0) circle (2pt);
    \pgfmathparse{mod(\i,2)==0 ? 1 : 0}
    \ifnum\pgfmathresult=1
      \node[above=3pt, align=center, text width=2.3cm] at (\i*1.3,0) {\textbf{\y}\\\t};
    \else
      \node[below=3pt, align=center, text width=2.3cm] at (\i*1.3,0) {\textbf{\y}\\\t};
    \fi
  }
\end{tikzpicture}
\end{adjustbox}
```

* Defence: Denning [@denning:1987], Graham [@graham:2002]. Attacks on detectors: [@lowd:2005; @szegedy:2014; @anderson:2018].
* Attacks with ML: PassGAN [@hitaj:2019], exploiting CVEs [@fang:2024], AIxCC [@zhang:2026].

# Machine Learning in Ten Minutes

## What is machine learning?

**Traditional program:** *rules + data $\to$ answers.* **Learning:** *data + answers $\to$ rules (a model).*

```{=latex}
\begin{adjustbox}{max width=\linewidth,center}
\begin{tikzpicture}
  \node[neu] (d) {Data\\(examples)};
  \node[neu, right=10mm of d] (f) {Features\\$\mathbf{x}\in\mathbb{R}^d$};
  \node[neu, right=10mm of f] (m) {Model\\$f_\theta(\mathbf{x})$};
  \node[neu, right=10mm of m] (p) {Prediction\\$\hat y$};
  \draw[arr] (d) -- (f); \draw[arr] (f) -- (m); \draw[arr] (m) -- (p);
  \node[neu, below=8mm of m] (l) {Loss $\mathcal{L}(\theta)$\\(compare with labels $y$)};
  \draw[arr] (p) |- (l); \draw[arr] (l) -- node[right, note] {update $\theta$} (m);
\end{tikzpicture}
\end{adjustbox}
```

* A model is a **function with parameters $\theta$**; *training* chooses $\theta$ so that the loss is small on the data.
* Everything in this course, from Naive Bayes to LLMs, fits this picture.

## Learning is optimisation, and so is attacking

```{=latex}
\begin{columns}[T]
\begin{column}{0.48\textwidth}
\begin{tikzpicture}
  \node[dfn, text width=5.2cm] {\textbf{Training}\\[2pt] vary the \textbf{weights}\\ $\theta\leftarrow\theta-\eta\,\nabla_{\theta}\mathcal{L}(\theta;\mathbf{x},y)$\\[2pt] \emph{descend} the loss};
\end{tikzpicture}
\end{column}
\begin{column}{0.48\textwidth}
\begin{tikzpicture}
  \node[atk, text width=5.2cm] {\textbf{Evasion}\\[2pt] vary the \textbf{input}\\ $\mathbf{x}\leftarrow\mathbf{x}+\varepsilon\,\mathrm{sign}\big(\nabla_{\mathbf{x}}\mathcal{L}(\theta;\mathbf{x},y)\big)$\\[2pt] \emph{ascend} the loss};
\end{tikzpicture}
\end{column}
\end{columns}
```

* **Same gradient, different variable.** The attacker uses the machinery that trains the model.
* No gradient (black-box API)? Use **derivative-free search**: particle swarms, genetic algorithms, greedy search.
* Details, maths and code: the **appendix** of this deck and `notebooks/00-intro/` (02 to 05, then 11).

## Learning paradigms, and who uses them

| Paradigm | Learns from | Defence | Offence |
|:------------------|:---------------|:------------------------|:------------------------|
| **Supervised** | labelled examples | spam, malware classifiers | surrogate models of a victim |
| **Unsupervised** | unlabelled data | anomaly detection | profiling targets |
| **Generative** | data distribution | synthetic training data | phishing text, passwords |
| **Reinforcement** | reward | adaptive response | pentest agents, evasion |
| **Self-supervised** (LLMs) | text itself | alert triage | general-purpose agents |

* Labels in security are **scarce, late and noisy**: practice leans on semi- and unsupervised methods and on pre-trained models.

## Generalisation: the enemy of memorisation

```{=latex}
\begin{adjustbox}{max width=\linewidth,center}
\begin{tikzpicture}
\begin{axis}[aasplot, height=0.5\textheight, width=0.66\linewidth, xlabel={model complexity}, ylabel={error}, xtick=\empty, ytick=\empty,
  domain=0.4:4, samples=60, legend pos=north east, ymin=0, ymax=1.3]
  \addplot[thick, aasblue] {0.15 + 1.1*exp(-1.4*x)};
  \addlegendentry{training error}
  \addplot[thick, aasred] {0.25 + 0.9*exp(-1.4*x) + 0.05*x^2.4/2};
  \addlegendentry{error on new data}
  \node[note] at (axis cs:0.9,0.15) {underfit};
  \node[note] at (axis cs:3.5,0.25) {overfit};
\end{axis}
\end{tikzpicture}
\end{adjustbox}
```

*(Schematic.)* A model that **memorises** the attacks it has seen is excellent in the lab and blind to the next variant.

## Why generalisation matters in security

* **New variants:** attackers repack and rewrite; a detector must recognise what it has *not* seen.
* **Gaps between training points** are where a detector is unreliable: the attacker moves the input there.
* **Spurious correlations:** the model learns artefacts (data source, file size, HTML escapes), not the real cause [@arp:2022].
* **Evaluation traps:** duplicates across train and test, random splits of time-ordered data, tuning on the test set.
* An evaluation with **no adaptive adversary** says nothing about security.

## Metrics: the base-rate fallacy

A detector with **99%** detection rate and **1%** false-alarm rate. Attacks are **1 in 1,000** events.

```{=latex}
\begin{adjustbox}{max width=\linewidth,center}
\begin{tikzpicture}[level distance=13mm, sibling distance=52mm, font=\footnotesize,
  edge from parent/.style={draw, -{Stealth[length=2mm]}, aasgrey}]
  \node[neu] {1,000,000 events}
    child {node[atk] {1,000 attacks}
      child {node[ok, sibling distance=25mm] {990 alarms\\(caught)}}
      child {node[neu, sibling distance=25mm] {10 missed}}}
    child {node[neu] {999,000 benign}
      child {node[atk, sibling distance=25mm] {9,990 alarms\\(false)}}
      child {node[neu, sibling distance=25mm] {989,010 quiet}}};
\end{tikzpicture}
\end{adjustbox}
```

$P(\text{attack}\mid\text{alarm})=\dfrac{990}{990+9990}\approx 9\%$: **91% of the alarms are false** [@axelsson:2000].

## Consequences of the base rate

* Real attacks hide in a **flood of alarms**: analysts stop looking at a detector that cries wolf.
* **Defender:** tune the operating point to analyst capacity; report precision and recall at the true prevalence.
* **Attacker:** noise is cover; more benign-looking junk means more alarms to ignore.
* **Rule for all our labs:** precision, recall, PR-AUC and MCC on a *leak-free* split, as mean $\pm$ spread over folds.

# AI/ML for Defence

## Where ML helps defenders

| Problem | Data | Typical models | Where in this course |
|:-------------------|:-------------------|:-------------------|:---------------|
| **Spam, phishing** | message text, URLs | Naive Bayes, linear, embeddings | **classes 2-4** |
| **Malware** | PE headers, API calls, bytes | trees, ensembles, nets | malware module |
| **Intrusion, anomaly** | flows, logs | isolation forest, autoencoders | anomaly module |
| **Fraud, UEBA** | transactions, user behaviour | boosting, one-class | anomaly module |
| **Triage, threat intel** | alerts, reports | LLMs, retrieval | discussion |

* **Why learning:** it generalises to *variants*, adapts to drift and scales to millions of events per day.

## Signatures and rules versus learning

| | Signature / rule based | Learning based |
|:----------|:---------------------------------|:---------------------------------|
| **Spam** | keyword and blocklist rules | statistical text classifiers |
| **Malware** | hashes, byte patterns | classifiers on static and dynamic features |
| **Intrusion** | Snort/Suricata-style rules | anomaly detection on flows and logs |
| **Strength** | precise, explainable, cheap | generalises to variants |
| **Weakness** | blind to anything new; one changed byte evades it | needs data, harder to explain, statistical errors |

* Defenders **combine both**: rules for the known, learning for the unknown.

## Why security ML is different

Sommer and Paxson: detection in the lab is not detection on a real network [@sommer:2010].

* **Costly errors:** a false negative is a breach, a false positive burns analyst time.
* **Semantic gap:** "anomalous" is not "malicious"; the operator needs *harmful*.
* **Few realistic, shareable, labelled datasets**; sites and threats differ and change.
* **Adversaries adapt** to the detector, so the data reacts to the defence.
* **Evaluation is hard:** one accuracy number hides all of the above.

## Common pitfalls (Arp et al., 2022)

Pitfalls found in *every one* of 30 top-venue papers reviewed [@arp:2022]:

| Pitfall | Example in security |
|:--------------------------------|:------------------------------------------------|
| **Sampling bias, label noise** | benign and malicious samples from different sources |
| **Data snooping** | tuning or selecting features with the test set |
| **Spurious correlations** | model keys on artefacts, not on behaviour |
| **Wrong metrics** | accuracy on balanced data, not PR at real prevalence |
| **Temporal bias** | random splits mix past and future |

# AI/ML for Offence: Traditional Targets

## The offensive AI landscape

| Task | Classic technique | With ML / AI |
|:----------------|:------------------------|:------------------------------------------|
| **Passwords** | dictionaries, rules (hashcat) | generative models of leaked passwords [@hitaj:2019] |
| **Phishing** | templates, mass mailing | LLM-written, personalised, fluent text |
| **Bug finding** | fuzzers, manual audit | LLM-guided fuzzing, autonomous find-and-patch [@zhang:2026] |
| **Pentesting** | scripts, scanners | LLM agents that plan and use tools [@deng:2024] |
| **Exploitation** | manual | agents exploiting known CVEs [@fang:2024] |
| **Malware** | packers, polymorphism | RL and generators that evade AV [@anderson:2018] |
| **CAPTCHA, biometrics** | brute force, replay | CNNs solve them; deepfakes |

## Case 1: password guessing with generative models

A password is a *string with structure*; a language model assigns it a **probability**:

$$
P(c_1\dots c_n)=\prod_{i=1}^{n}P(c_i\mid c_1\dots c_{i-1})
$$

```{=latex}
\begin{adjustbox}{max width=\linewidth,center}
\begin{tikzpicture}
  \node[neu] (l) {Leaked\\passwords};
  \node[atk, right=9mm of l] (g) {Generative model\\Markov / GAN / GPT};
  \node[neu, right=9mm of g] (c) {Candidates in\\decreasing probability};
  \node[neu, right=9mm of c] (h) {Hash\\check};
  \draw[arr] (l) -- (g); \draw[arratk] (g) -- (c); \draw[arr] (c) -- (h);
\end{tikzpicture}
\end{adjustbox}
```

* Rules (`p4ssw0rd!`) are hand-written; a model **learns the habits** of real users from data [@hitaj:2019].
* *Offline* attack: only a leaked hash and compute.

## Case 2: social engineering at scale

* Classical phishing has tell-tale signs: **generic greeting, typos, odd phrasing, one template** for a million victims.
* An LLM removes them: **fluent, personalised, multilingual** text produced from public information about the target, at almost zero marginal cost.
* Voice and video cloning add a second channel (fake calls from a "manager").
* Content signals weaken; the spam filter of classes 2-4 will be attacked with exactly such texts (notebook `01-spam/07`).

## Case 3: finding and exploiting vulnerabilities

```{=latex}
\begin{adjustbox}{max width=\linewidth,center}
\begin{tikzpicture}
  \node[neu] (t) {Target\\program};
  \node[atk, right=10mm of t] (p) {LLM proposes\\inputs / harness};
  \node[neu, right=10mm of p] (r) {Run\\(fuzz)};
  \node[neu, right=10mm of r] (c) {Crash?\\triage};
  \draw[arr] (t) -- (p); \draw[arr] (p) -- (r); \draw[arr] (r) -- (c);
  \draw[arratk] (c.south) -- ++(0,-6mm) -| node[pos=0.25, below, note] {feedback: coverage, crashes} (p.south);
\end{tikzpicture}
\end{adjustbox}
```

* In DARPA's **AIxCC** (2023-2025) seven finalist *cyber reasoning systems* used LLMs to **discover, confirm and patch** bugs in real open-source software [@zhang:2026].
* LLM agents can exploit **known** (one-day) vulnerabilities when given the CVE description [@fang:2024].

## Case 4: LLM agents as penetration testers

```{=latex}
\begin{adjustbox}{max width=\linewidth,center}
\begin{tikzpicture}
  \node[atk] (o) {Observe\\tool output};
  \node[atk, right=12mm of o] (t) {Think / plan\\(LLM)};
  \node[atk, right=12mm of t] (a) {Act\\scan, exploit, shell};
  \draw[arratk] (o) -- (t); \draw[arratk] (t) -- (a);
  \draw[arratk] (a.south) -- ++(0,-7mm) -| (o.south);
  \node[neu, above=6mm of t] (g) {Goal: "get a shell on host X"};
  \draw[arr] (g) -- (t);
\end{tikzpicture}
\end{adjustbox}
```

* Systems such as PentestGPT [@deng:2024] chain reconnaissance, exploitation and reporting.
* **Limits:** hallucinated findings, long-horizon planning, no proof of exploit: serious tools *demand a validated proof* before reporting.
* Trust in agent output rests on **validation**: a working proof of exploit, not a fluent report.

## Why ML changes the economics of attacks

* **Scale:** thousands of personalised messages, millions of candidate passwords, continuous scanning.
* **Cost:** the skilled labour of a few experts is replaced by compute and prompts.
* **Adaptivity:** an attack that *learns from the defender's responses* (a score, a block, an error message).
* **Asymmetry:** the attacker needs one success; the defender must stop every attempt.
* Natural next question: what if the **defence is itself a model**? See the last section, and the spam lab.

# AI/ML for Offence: Breaking ML-Based Detectors

## Threat model: who attacks what, and when?

| Axis | Options |
|:------------------|:--------------------------------------------------------------------|
| **Goal** | evade (a malicious input is accepted), degrade (raise errors), learn the model |
| **Capability** | change test-time inputs; contribute training data or labels; query the detector |
| **Knowledge** | white-box (weights), grey-box, **black-box** (scores or labels only) |
| **Stage** | training time or inference time |

* **Targets in this course:** the spam filter (classes 2-4), the anomaly detector, the malware classifier.
* A detector is "robust" only against a *stated* adversary [@nist:2025].

## Where can a detector be attacked?

```{=latex}
\begin{adjustbox}{max width=\linewidth,center}
\begin{tikzpicture}[node distance=7mm]
  \node[neu] (d) {Training\\data};
  \node[neu, right=of d] (t) {Training};
  \node[neu, right=of t] (m) {Model};
  \node[neu, right=of m] (a) {Detector\\API};
  \node[neu, right=of a] (o) {Decision};
  \draw[arr] (d) -- (t); \draw[arr] (t) -- (m); \draw[arr] (m) -- (a); \draw[arr] (a) -- (o);
  \node[atk, above=10mm of d] (p) {Poisoning\\backdoors};
  \node[atk, below=10mm of o] (e) {Evasion\\(adversarial inputs)};
  \node[atk, below=10mm of m] (x) {Surrogate\\(query and copy)};
  \draw[arratk] (p) -- (d); \draw[arratk] (e) -- (o); \draw[arratk] (x) -- (a);
\end{tikzpicture}
\end{adjustbox}
```

## Evasion: the gradient points the way

Fast Gradient Sign Method [@szegedy:2014; @goodfellow:2015]: one step that increases the loss under an $\ell_\infty$ budget $\varepsilon$.

```{=latex}
\begin{adjustbox}{max width=\linewidth,center}
\begin{tikzpicture}[scale=0.9]
  \fill[aasblue!12] (-3.2,-1.5) rectangle (0.2,1.6);
  \fill[aasred!12] (0.2,-1.5) rectangle (3.4,1.6);
  \draw[thick, aasgrey, decorate, decoration={random steps, segment length=6mm, amplitude=1.2mm}] (0.2,-1.5) -- (0.2,1.6);
  \node[note] at (-1.6,1.3) {class A (benign)}; \node[note] at (1.9,1.3) {class B (malicious)};
  \node[circle, fill=aasblue, inner sep=1.6pt, label={[font=\scriptsize]below:$\mathbf{x}$}] (x) at (-1.3,-0.2) {};
  \draw[arratk] (x) -- (1.0,0.3);
  \node[circle, fill=aasred, inner sep=1.6pt, label={[font=\scriptsize]right:$\mathbf{x}_{adv}$}] at (1.0,0.3) {};
  \node[note, below] at (-0.1,-0.75) {the step $\varepsilon\,\mathrm{sign}(\nabla_{\mathbf{x}}\mathcal{L})$ crosses the boundary};
\end{tikzpicture}
\end{adjustbox}
```

$$
\mathbf{x}_{adv}=\mathbf{x}+\varepsilon\cdot\mathrm{sign}\big(\nabla_{\mathbf{x}}J(\theta,\mathbf{x},y)\big)
$$

## Evasion is not random noise

Small digit classifier (notebook `00-intro/11`); same $\ell_\infty$ budget $\varepsilon$ per pixel (pixels in $[0,1]$).

```{=latex}
\begin{adjustbox}{max width=\linewidth,center}
\begin{tikzpicture}
\begin{axis}[aasplot, height=0.5\textheight, width=0.6\linewidth, xlabel={budget $\varepsilon$}, ylabel={accuracy}, ymin=0, ymax=1.02,
  legend style={at={(1.03,0.5)}, anchor=west}]
  \addplot[thick, aasred, mark=*] coordinates {(0,0.981) (0.05,0.817) (0.1,0.470) (0.15,0.202) (0.2,0.094) (0.3,0.019) (0.4,0.015)};
  \addlegendentry{MLP, FGSM}
  \addplot[thick, aasgold, mark=square*] coordinates {(0,0.967) (0.05,0.857) (0.1,0.643) (0.15,0.369) (0.2,0.106) (0.3,0) (0.4,0)};
  \addlegendentry{logistic regr., FGSM}
  \addplot[thick, aasgrey, dashed, mark=triangle*] coordinates {(0,0.981) (0.05,0.970) (0.1,0.956) (0.15,0.931) (0.2,0.907) (0.3,0.770) (0.4,0.635)};
  \addlegendentry{MLP, random $\pm\varepsilon$}
\end{axis}
\end{tikzpicture}
\end{adjustbox}
```

## In security, the perturbation must still work

* **Images:** any small change is allowed. **Security:** the input must keep its *function* (the malware runs, the spam is readable, the URL resolves).
* The attack becomes a **search over valid edits** ("problem space"), not a step in pixel space.

| Detector | Valid edits | Reference |
|:--------------|:-----------------------------------------|:-------------------|
| **Spam text** | append benign words, obfuscate spelling | [@lowd:2005] |
| **PE malware** | append bytes, add sections, repack | [@anderson:2018] |
| **Anomaly (flows, logs)** | mimic normal statistics, stay below threshold | anomaly module |

## Black-box attacks: queries and transfer

* **Query attack:** ask the detector for a score on inputs you choose; lower it with derivative-free search (PSO, greedy, genetic).
* **Transfer:** train a **surrogate** on labels obtained by querying the victim, attack it with gradients; the examples *transfer* [@papernot:2017; @tramer:2016].

Digits, $\varepsilon=0.2$, 30 test images (notebook `00-intro/11`):

| Attack | Success rate | Cost |
|:-----------------------|------:|:---------------------|
| Random noise | 0.07 | none |
| FGSM (white-box) | 0.90 | 1 gradient |
| PSO (black-box) | 0.97 | about 1,300 queries per image |

## Poisoning and backdoors

* **Poisoning:** contaminate the training data so the detector is wrong in a chosen way [@biggio:2012].
* **Backdoor:** a hidden **trigger** flips the decision only when present; the model looks normal on clean data [@gu:2019].
* **Realistic channels:** "Not spam" buttons, crowdsourced malware feeds and labels.
* The number of poisoned samples needed can stay **small**: about 250 documents backdoored LLMs from 600M to 13B parameters [@souly:2025].
* Spam lab (`01-spam/07`): 50 to 100 relabelled messages (1-2% of the training set) cut the recall of a logistic-regression filter from 0.91 to 0.54 and 0.30.

## Summary: attack, knowledge, cost

| Attack | Knowledge needed | Attacker's cost | Where we practise it |
|:---------------------|:------------------|:-----------------|:---------------------|
| **White-box evasion** (FGSM, PGD) | weights | 1 backward pass | `00-intro/11` |
| **Black-box evasion** | scores | 100s-1000s of queries | `00-intro/11`, `01-spam/07` |
| **Transfer** | labels | queries to train a surrogate | `01-spam/07` |
| **Good-word attack** | weights or scores | a few appended words | `01-spam/07` |
| **Poisoning, backdoors** | write access to data | tens of samples | `01-spam/07` |

# Wrap-up

## Dual use: one technique, two sides

```{=latex}
\begin{adjustbox}{max width=\linewidth,center}
\begin{tikzpicture}
  \matrix[ampersand replacement=\&, row sep=2.5mm, column sep=4mm, nodes={font=\footnotesize, align=center, minimum height=7mm, inner sep=3pt}] {
    \node[dfn, text width=3.6cm] {spam classifier}; \& \node[note] {text models}; \& \node[atk, text width=3.6cm] {LLM phishing writer}; \\
    \node[dfn, text width=3.6cm] {password-strength meter}; \& \node[note] {sequence models}; \& \node[atk, text width=3.6cm] {password guesser}; \\
    \node[dfn, text width=3.6cm] {static analysis, fuzzing}; \& \node[note] {code models, LLMs}; \& \node[atk, text width=3.6cm] {exploit finding}; \\
    \node[dfn, text width=3.6cm] {malware classifier}; \& \node[note] {gradients, search}; \& \node[atk, text width=3.6cm] {evasion of the classifier}; \\
  };
\end{tikzpicture}
\end{adjustbox}
```

* The same model families sit on both sides; what differs is the **objective**, the **error costs** and **who adapts to whom**.


## The labs of class 1

| Notebook (`notebooks/00-intro/`) | Topic |
|:-------------------------|:-----------------------------------------------|
| **00, 01, 02** | probability, linear algebra, calculus (gradients, integration) |
| **03, 04, 05** | PSO, gradient descent, linear regression: *the optimisers* |
| **06** | classifier zoo and decision boundaries |
| **07-10** | learning as compression, evaluation, pitfalls, taxonomies |
| **11** | **attack lab:** FGSM, PGD, transfer, PSO black-box |

**Core path for the 2 hours:** 02 $\to$ 04 $\to$ 11. The others are self-study; 00 and 01 are the maths refresher.

## Take-aways

* ML works for **both sides**: defenders detect (spam, malware, intrusions); attackers guess, phish, find bugs, and **attack the detectors**.
* **Learning is optimisation, and so is attacking:** gradients when available, derivative-free search when not.
* Security ML is **not** ordinary ML: rare positives, costly errors, drift, adaptive opponents. Judge it by **precision at the real base rate** and by **robustness to a stated adversary**, not by accuracy.
* **Next class:** we build a spam detector, from the simplest Naive Bayes to small-language-model embeddings, then break it.

# Appendix: Optimisation Concepts

## Training is optimisation

* **Optimisation** finds the best solution of a problem: the **minimum** (or maximum) of a function.
* Training a model picks the parameters $\theta$ that minimise a **loss** (cost) over the data:

$$
\min_\theta\ \mathcal{L}(\theta)=\frac1n\sum_{i=1}^{n}\ell\big(f_\theta(\mathbf{x}_i),y_i\big)
$$

| Task | Model | Loss $\ell$ |
|:------------------|:-------------------------|:-------------------------------|
| Regression | $\hat y=mx+b$ | squared error $(y-\hat y)^2$ |
| Classification | $\hat p=\sigma(\mathbf{w}\cdot\mathbf{x}+b)$ | log-loss (cross-entropy) |


## Two families of optimisers

```{=latex}
\begin{adjustbox}{max width=\linewidth,center}
\begin{tikzpicture}
  \node[dfn, text width=5.4cm] (g) {\textbf{Gradient-based}\\[2pt] needs $\nabla\mathcal{L}$\\ fast on smooth, convex losses\\ gradient descent, Newton, L-BFGS, Adam};
  \node[neu, text width=5.4cm, right=8mm of g] (b) {\textbf{Derivative-free (blind)}\\[2pt] needs only $\mathcal{L}(\theta)$\\ any function, black boxes, noise\\ PSO, genetic algorithms, random search};
\end{tikzpicture}
\end{adjustbox}
```

* Choose by what you can **observe**: the gradient (white-box) or only the value (black-box, a *query*).

# Gradient-Based Optimisation

## Gradient descent in one dimension

Imagine descending a foggy mountain: feel the slope, step downhill, repeat.

$$
x_{t+1}=x_t-\eta\,f'(x_t)
$$

* $f'(x_t)$ is the slope at the current point; $\eta$ is the **learning rate**.
* **Too small:** very slow. **Too large:** overshoots, oscillates or diverges.
* For $f(x)=x^2$: $x_{t+1}=(1-2\eta)\,x_t$, so it converges only if $\lvert 1-2\eta\rvert<1$, i.e. $0<\eta<1$.

## The learning rate decides everything

$f(x)=x^2$, start at $x_0=4$: $\;x_t=(1-2\eta)^t\,x_0$. For $\eta\ge1$ it **diverges** (not shown).

```{=latex}
\begin{adjustbox}{max width=\linewidth,center}
\begin{tikzpicture}
\begin{axis}[aasplot, height=0.5\textheight, width=0.62\linewidth, xlabel={iteration $t$}, ylabel={$x_t$}, domain=0:12, samples=13, ymin=-5, ymax=5,
  legend style={at={(1.03,0.5)}, anchor=west}]
  \addplot[thick, aasblue, mark=*] {4*(1-2*0.1)^x};
  \addlegendentry{$\eta=0.1$}
  \addplot[thick, aasgreen, mark=square*] {4*(1-2*0.45)^x};
  \addlegendentry{$\eta=0.45$}
  \addplot[thick, aasgold, mark=triangle*] {4*(1-2*0.9)^x};
  \addlegendentry{$\eta=0.9$}
\end{axis}
\end{tikzpicture}
\end{adjustbox}
```

## Many variables: the gradient

For $f:\mathbb{R}^n\to\mathbb{R}$ the gradient is the vector of **partial derivatives**, $\nabla f=(\partial_{x_1}f,\dots,\partial_{x_n}f)$.

```{=latex}
\begin{adjustbox}{max width=\linewidth,center}
\begin{tikzpicture}[scale=0.85]
  \foreach \r in {0.5,1,1.5,2.0} {\draw[aasgrey!70] (0,0) ellipse ({\r*1.6} and {\r*0.9});}
  \fill (0,0) circle (1.5pt) node[below=6pt, note] {minimum};
  \coordinate (p) at (1.6,1.05);
  \fill[aasblue] (p) circle (2pt) node[right=2pt, font=\scriptsize] {$\theta_t$};
  \draw[arratk] (p) -- ++(0.55,0.42) node[right, font=\scriptsize, text=aasred] {$\nabla\mathcal{L}$ (uphill)};
  \draw[arr, aasblue] (p) -- ++(-0.95,-0.72) node[right=3pt, font=\scriptsize, text=aasblue, pos=1] {$-\nabla\mathcal{L}$ (step)};
\end{tikzpicture}
\end{adjustbox}
```

* $\nabla f$ points to the **steepest ascent** and is **perpendicular to the level curves**.
* Update: $\;\boldsymbol\theta_{t+1}=\boldsymbol\theta_t-\eta\,\nabla f(\boldsymbol\theta_t)$.

## The chain rule is backpropagation

$\hat y=\sigma\big(w_2\tanh(w_1x)\big)$, $L=(\hat y-y)^2$: derivatives multiply along the path, from the loss back to each variable.

```{=latex}
\begin{adjustbox}{max width=\linewidth,center}
\begin{tikzpicture}[node distance=7mm]
  \node[neu] (x) {$x$};
  \node[neu, right=of x] (a) {$a$};
  \node[neu, right=of a] (h) {$h$};
  \node[neu, right=of h] (z) {$z$};
  \node[neu, right=of z] (p) {$\hat y$};
  \node[neu, right=of p] (l) {$L$};
  \foreach \s/\t/\d in {x/a/{w_1},a/h/{\tanh},h/z/{w_2},z/p/{\sigma},p/l/{(\hat y-y)^2}} {\draw[arr] (\s) -- node[above, font=\scriptsize] {$\d$} (\t);}
  \draw[arratk] (l.south) to[bend left=25] node[below, font=\scriptsize, text=aasred] {backward: multiply the local derivatives} (x.south);
\end{tikzpicture}
\end{adjustbox}
```


* $\dfrac{\partial L}{\partial w_1}=2(\hat y-y)\,\hat y(1-\hat y)\,w_2\,(1-h^2)\,x$. Continue to $x$: $\partial L/\partial x$ (`00-intro/02`).
* JAX and Keras do this mechanically (*automatic differentiation*).

## Logistic regression: loss and gradient

With $z_i=\mathbf{w}\cdot\mathbf{x}_i+b$:

$$
J(\mathbf{w},b)=-\frac1n\sum_i\Big[y_i\log\sigma(z_i)+(1-y_i)\log\big(1-\sigma(z_i)\big)\Big]
$$

$$
\nabla_{\mathbf{w}}J=\frac1n X^\top\big(\sigma(X\mathbf{w}+b)-\mathbf{y}\big),\qquad
\nabla_{\mathbf{x}}J=(\sigma(z)-y)\,\mathbf{w}
$$

* The first gradient trains the spam filter; the second says which **word** moves a score most: just the weight $\mathbf{w}$. The loss is **convex**.

## Numerical stability matters

Computing `log(sigmoid(z))` naively fails for confident predictions ($\sigma(-800)$ underflows to 0, and $\log 0=-\infty$).

| $z$ | naive $\log\sigma(z)$ | stable (`log_sigmoid`) |
|-----:|-----------:|-----------:|
| $-800$ | $-\infty$ | $-800$ |
| $-30$ | $-30.000$ | $-30.000$ |
| $0$ | $-0.693$ | $-0.693$ |

* Use $\log\sigma(z)=-\operatorname{softplus}(-z)$ and $\log\sum_i e^{\ell_i}=m+\log\sum_i e^{\ell_i-m}$ (*log-sum-exp*).
* Same trick makes Naive Bayes work on long messages (`notebooks/01-spam/01`).

# Derivative-Free Optimisation

## When there is no gradient

Use it when $f(\mathbf{x})$ is:

* **non-smooth** or discontinuous,
* **noisy**,
* **expensive** to evaluate,
* a **black box**: only inputs and outputs are visible (a scoring API).

Examples: genetic algorithms, differential evolution, simulated annealing, **particle swarm optimisation**.

## Particle swarm optimisation (PSO)

Kennedy and Eberhart [@kennedy:1995]: a swarm searches for food; each bird remembers its own best place and knows the best place of the flock.

\begin{align*}
V^i_{t+1}&=w\,V^i_t+c_1r_1\big(\mathrm{pbest}^i-X^i_t\big)+c_2r_2\big(\mathrm{gbest}-X^i_t\big)\\
X^i_{t+1}&=X^i_t+V^i_{t+1}
\end{align*}

```{=latex}
\begin{adjustbox}{max width=\linewidth,center}
\begin{tikzpicture}[scale=0.9]
  \coordinate (x) at (0,0);
  \coordinate (pb) at (2.2,1.6);
  \coordinate (gb) at (3.4,-0.4);
  \fill[aasblue] (x) circle (2pt) node[below left, font=\scriptsize] {$X^i_t$};
  \fill[aasgold] (pb) circle (2pt) node[above, font=\scriptsize] {pbest};
  \fill[aasred] (gb) circle (2pt) node[below right, font=\scriptsize] {gbest};
  \draw[arr, dashed] (x) -- (pb); \draw[arr, dashed] (x) -- (gb);
  \draw[arr, aasgrey] (x) -- (-1.4,0.9) node[above, font=\scriptsize] {inertia $wV^i_t$};
  \draw[arr, thick, aasblue] (x) -- (1.2,0.5) node[right, font=\scriptsize] {$V^i_{t+1}$};
\end{tikzpicture}
\end{adjustbox}
```

## PSO in practice

* **Cost:** $\text{particles}\times\text{iterations}$ evaluations; each particle is independent, so it **parallelises** trivially.
* **Parameters:** inertia $w$ (keep direction), $c_1$ (own memory), $c_2$ (swarm); they trade exploration for exploitation.
* Works on a non-convex "egg-carton" $f(x,y)=(x-3.14)^2+(y-2.72)^2+\sin(3x+1.41)+\sin(4y-1.73)$: PSO found $f=-1.8084$ at $(3.19,3.13)$; the exhaustive grid optimum is $-1.8083$ (`notebooks/00-intro/03`).
* **No guarantee** of the global optimum: run several times.

## Gradient descent versus PSO

| Feature | Gradient descent | PSO |
|:------------------|:---------------------------|:---------------------------|
| **Needs** | the gradient | function values only |
| **Best for** | smooth, convex problems | noisy, non-smooth, non-convex |
| **Search** | deterministic, one path | stochastic, a population |
| **Local minima** | can get stuck | can jump out |
| **Cost** | cheap per step, many steps | many evaluations per step |
| **Analogy** | one hiker downhill | a flock searching |

# Applications

## Linear regression: four solvers, one answer

$h(x)=mx+b$, cost $e(m,b)=\frac1{2n}\sum_i(y_i-h(x_i))^2$. Same data (`notebooks/00-intro/05`):

| Solver | Needs | RMSE |
|:-----------------------|:---------------------|-------:|
| Closed form (`lstsq`) | linear model | 6.930 |
| Gradient descent | gradient | 6.930 |
| Newton | gradient + Hessian | 6.930 |
| PSO | only the loss | 6.930 |

* Same problem, same answer; the solvers differ in **what they require** and what they **cost**.

## Logistic regression for spam

* Features: TF-IDF vector of an SMS; model $\sigma(\mathbf{w}\cdot\mathbf{x}+b)$ with an L2 penalty.
* **Gradient descent** (300 steps) and **L-BFGS** reach the same loss and the same test score (F1 $\approx$ 0.94, `notebooks/01-spam/03`); L-BFGS needs about a tenth of the iterations and no learning rate.
* **Choosing the threshold is optimisation too:** on Naive Bayes, a threshold of 0.9914 gives precision 0.992 and recall 0.930 (`notebooks/01-spam/01`).
* A **cost-sensitive** objective, e.g. $c_{FP}\cdot FP+c_{FN}\cdot FN$, picks the operating point from the analysts' capacity.

## Attacking is optimisation

Same loss, different variable: maximise the loss over the **input** under a budget [@szegedy:2014; @madry:2018].

$$
\max_{\|\boldsymbol\delta\|_\infty\le\varepsilon}\ \mathcal{L}\big(\theta;\mathbf{x}+\boldsymbol\delta,y\big)\quad\Longrightarrow\quad \boldsymbol\delta\approx\varepsilon\,\mathrm{sign}\big(\nabla_{\mathbf{x}}\mathcal{L}\big)\ \text{(FGSM)}
$$

Digits, $\varepsilon=0.2$, 30 images (`notebooks/00-intro/11`):

| Attack | Optimiser | Success | Cost |
|:-------------------|:--------------------|-----:|:----------------------|
| Random noise | none | 0.07 | none |
| FGSM | one gradient step | 0.90 | 1 gradient |
| PSO (black-box) | derivative-free | 0.97 | ~1,300 queries |

## Conclusion

* Optimisation is the engine of ML: a **model** plus a **loss** plus an **optimiser**.
* **Gradient-based** methods need $\nabla\mathcal{L}$ (automatic differentiation provides it); **derivative-free** methods need only evaluations.
* Choosing the solver is choosing **what you can observe** and **what a step costs**: exactly what separates a white-box from a black-box attacker.
* **Next:** apply it, on spam (Naive Bayes, logistic regression, fastText, embeddings), then break the detector.

## Bibliography {.allowframebreaks}

::: {#refs}
:::
