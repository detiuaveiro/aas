---
title: Aprendizagem Aplicada à Segurança
subtitle: "Practical Project 2 (resit): rules and the ten topics"
author: Mário Antunes
institute: Universidade de Aveiro
date: January 2027
colorlinks: true
highlight-style: tango
mainfont: Noto Sans
header-includes:
 - \usetheme[sectionpage=none,numbering=fraction,progressbar=frametitle]{metropolis}
 - \usepackage{longtable,booktabs}
 - \usepackage{etoolbox}
 - \AtBeginEnvironment{longtable}{\small}
 - \AtBeginEnvironment{Shaded}{\tiny}
 - \AtBeginEnvironment{verbatim}{\tiny}
 - \setmonofont[Contextuals={Alternate}]{FiraCode Nerd Font Mono}
 - \tikzset{pb/.style={minimum width=24mm, minimum height=16mm, text width=22mm}}

---

# Rules

## Rule 0: groups

```{=latex}
\begin{adjustbox}{max width=\linewidth,center}
\begin{tikzpicture}[node distance=5mm, pb/.style={minimum width=24mm, minimum height=16mm, text width=22mm}, zone/.style={draw=aasgrey, dashed, rounded corners=4pt, inner sep=6pt}, zonelabel/.style={font=\footnotesize\bfseries, text=aasgrey}]
  \node[neu, pb] (a) {1 student};
  \node[ok, pb, right=of a] (b) {2 students};
  \node[atk, pb, right=of b] (c) {3 students};
  \node[note, below=2mm of a] {allowed};
  \node[note, below=2mm of b] {allowed};
  \node[note, below=2mm of c, text width=40mm] {with approval};
\end{tikzpicture}
\end{adjustbox}
```

* **Alone or in pairs;** groups of three are exceptional.
* **Team name = student number.**
* **Resit:** you may keep the group of Project 1, or change its size.

## Rule 1: what to submit

```{=latex}
\begin{adjustbox}{max width=\linewidth,center}
\begin{tikzpicture}[node distance=5mm, pb/.style={minimum width=24mm, minimum height=16mm, text width=22mm}, zone/.style={draw=aasgrey, dashed, rounded corners=4pt, inner sep=6pt}, zonelabel/.style={font=\footnotesize\bfseries, text=aasgrey}]
  \node[neu, pb] (c) {Code};
  \node[neu, pb, right=of c] (d) {Dataset\\or link + script};
  \node[ok, pb, right=of d] (r) {\texttt{README.md}\\the report};
  \begin{scope}[on background layer]
    \node[zone, fit=(c)(d)(r)] (z) {};
  \end{scope}
  \node[zonelabel, anchor=south east] at (z.north east) {one \texttt{.zip} on eLearning};
\end{tikzpicture}
\end{adjustbox}
```

* **One zip file** on the eLearning platform with the code, the dataset (or a link and a download script) and `README.md`.
* **`README.md` is the report:** there is no separate PDF.

## Rule 2: the README.md follows the template

```{=latex}
\begin{adjustbox}{max width=\linewidth,center}
\begin{tikzpicture}[node distance=5mm, pb/.style={minimum width=24mm, minimum height=16mm, text width=22mm}, zone/.style={draw=aasgrey, dashed, rounded corners=4pt, inner sep=6pt}, zonelabel/.style={font=\footnotesize\bfseries, text=aasgrey}]
  \node[ok, pb] (a) {Authors\\name, nº, e-mail};
  \node[neu, pb, right=of a] (b) {Abstract\\threat model};
  \node[neu, pb, right=of b] (c) {Data, method\\and results};
  \node[atk, pb, right=of c] (e) {Attack or\\defence};
  \draw[arr] (a)--(b); \draw[arr] (b)--(c); \draw[arr] (c)--(e);
\end{tikzpicture}
\end{adjustbox}
```

* **Template:** `projects/templates/README.md`; it starts with the **identification of the authors** (name, student number, e-mail).
* **Reproducible:** install and run commands rebuild the results table; metrics beyond accuracy.
* **Resit:** add *Changes since Project 1* (one page).

## Rule 3: deadlines

```{=latex}
\begin{adjustbox}{max width=\linewidth,center}
\begin{tikzpicture}[node distance=5mm, pb/.style={minimum width=24mm, minimum height=16mm, text width=22mm}, zone/.style={draw=aasgrey, dashed, rounded corners=4pt, inner sep=6pt}, zonelabel/.style={font=\footnotesize\bfseries, text=aasgrey}]
  \node[neu, pb] (a) {Project 1\\due 18-12-2026};
  \node[ok, pb, right=of a] (b) {Resit period\\dates on eLearning};
  \node[atk, pb, right=of b] (c) {Delivery\\zip on eLearning};
  \draw[arr] (a)--(b); \draw[arr] (b)--(c);
\end{tikzpicture}
\end{adjustbox}
```

* **Resit period:** the delivery date is announced on eLearning; late deliveries are not accepted.
* **No defence,** unless the professor requests it.
* **Weight:** the project is 50% of the final grade.

# Topics

## 1. Malware detection (passive)

```{=latex}
\begin{adjustbox}{max width=\linewidth,center}
\begin{tikzpicture}[node distance=5mm, pb/.style={minimum width=24mm, minimum height=16mm, text width=22mm}, zone/.style={draw=aasgrey, dashed, rounded corners=4pt, inner sep=6pt}, zonelabel/.style={font=\footnotesize\bfseries, text=aasgrey}]
  \node[neu, pb] (n0) {File\\PE, ELF, APK};
  \node[neu, pb, right=of n0] (n1) {Features\\headers, entropy};
  \draw[arr] (n0)--(n1);
  \node[dfn, pb, right=of n1] (n2) {Model\\trees, linear};
  \draw[arr] (n1)--(n2);
  \node[neu, pb, right=of n2] (n3) {Label\\benign or malware};
  \draw[arr] (n2)--(n3);
  \node[atk, ellipse, dashed, text width=50mm, minimum height=9mm, below=11mm of n2] (at) {\textbf{Break it}\\pad or pack the file};
  \draw[arratk] (at.north) -- (n2.south);
\end{tikzpicture}
\end{adjustbox}
```

* **Task:** Classify a file from its headers and raw bytes, without running it.
* **Data:** EMBER, MalwareBazaar.
* **Watch out:** Packed files hide the real features.

## 2. Malware detection (active)

```{=latex}
\begin{adjustbox}{max width=\linewidth,center}
\begin{tikzpicture}[node distance=5mm, pb/.style={minimum width=24mm, minimum height=16mm, text width=22mm}, zone/.style={draw=aasgrey, dashed, rounded corners=4pt, inner sep=6pt}, zonelabel/.style={font=\footnotesize\bfseries, text=aasgrey}]
  \node[neu, pb] (n0) {Sample\\runs in a sandbox};
  \node[neu, pb, right=of n0] (n1) {Trace\\API calls, files};
  \draw[arr] (n0)--(n1);
  \node[dfn, pb, right=of n1] (n2) {Features\\call n-grams};
  \draw[arr] (n1)--(n2);
  \node[neu, pb, right=of n2] (n3) {Label\\benign or family};
  \draw[arr] (n2)--(n3);
  \node[atk, ellipse, dashed, text width=50mm, minimum height=9mm, below=11mm of n2] (at) {\textbf{Break it}\\sleep or mimic benign calls};
  \draw[arratk] (at.north) -- (n2.south);
\end{tikzpicture}
\end{adjustbox}
```

* **Task:** Classify a file from its behaviour inside a sandbox.
* **Data:** Joe Sandbox reports, MalwareBazaar.
* **Watch out:** Some samples detect the sandbox and stay quiet.

## 3. Binary visualization

```{=latex}
\begin{adjustbox}{max width=\linewidth,center}
\begin{tikzpicture}[node distance=5mm, pb/.style={minimum width=24mm, minimum height=16mm, text width=22mm}, zone/.style={draw=aasgrey, dashed, rounded corners=4pt, inner sep=6pt}, zonelabel/.style={font=\footnotesize\bfseries, text=aasgrey}]
  \node[neu, pb] (n0) {Bytes\\any binary};
  \node[neu, pb, right=of n0] (n1) {Image\\byte plot, Veles};
  \draw[arr] (n0)--(n1);
  \node[dfn, pb, right=of n1] (n2) {Model\\CNN or texture};
  \draw[arr] (n1)--(n2);
  \node[neu, pb, right=of n2] (n3) {Label\\class or anomaly};
  \draw[arr] (n2)--(n3);
  \node[atk, ellipse, dashed, text width=50mm, minimum height=9mm, below=11mm of n2] (at) {\textbf{Break it}\\edit bytes, keep the image};
  \draw[arratk] (at.north) -- (n2.south);
\end{tikzpicture}
\end{adjustbox}
```

* **Task:** Turn bytes into images and classify them or find anomalies.
* **Data:** MalwareBazaar, EMBER.
* **Watch out:** Image size and resizing change the result.

## 4. Mail analysis

```{=latex}
\begin{adjustbox}{max width=\linewidth,center}
\begin{tikzpicture}[node distance=5mm, pb/.style={minimum width=24mm, minimum height=16mm, text width=22mm}, zone/.style={draw=aasgrey, dashed, rounded corners=4pt, inner sep=6pt}, zonelabel/.style={font=\footnotesize\bfseries, text=aasgrey}]
  \node[neu, pb] (n0) {Email\\headers, body};
  \node[neu, pb, right=of n0] (n1) {Features\\SPF, DKIM, TF-IDF};
  \draw[arr] (n0)--(n1);
  \node[dfn, pb, right=of n1] (n2) {Model\\NB, logistic};
  \draw[arr] (n1)--(n2);
  \node[neu, pb, right=of n2] (n3) {Label\\ham, spam, phish};
  \draw[arr] (n2)--(n3);
  \node[atk, ellipse, dashed, text width=50mm, minimum height=9mm, below=11mm of n2] (at) {\textbf{Break it}\\reword, keep the payload};
  \draw[arratk] (at.north) -- (n2.south);
\end{tikzpicture}
\end{adjustbox}
```

* **Task:** Flag spam, phishing or malware mail from headers, body or both.
* **Data:** SpamAssassin corpus, MHA.
* **Watch out:** One campaign in train and test inflates the score.

## 5. Network intrusion detection

```{=latex}
\begin{adjustbox}{max width=\linewidth,center}
\begin{tikzpicture}[node distance=5mm, pb/.style={minimum width=24mm, minimum height=16mm, text width=22mm}, zone/.style={draw=aasgrey, dashed, rounded corners=4pt, inner sep=6pt}, zonelabel/.style={font=\footnotesize\bfseries, text=aasgrey}]
  \node[neu, pb] (n0) {Traffic\\PCAP};
  \node[neu, pb, right=of n0] (n1) {Flows\\bytes, duration};
  \draw[arr] (n0)--(n1);
  \node[dfn, pb, right=of n1] (n2) {Model\\forest, autoencoder};
  \draw[arr] (n1)--(n2);
  \node[neu, pb, right=of n2] (n3) {Alert\\normal or attack};
  \draw[arr] (n2)--(n3);
  \node[atk, ellipse, dashed, text width=50mm, minimum height=9mm, below=11mm of n2] (at) {\textbf{Break it}\\slow down below threshold};
  \draw[arratk] (at.north) -- (n2.south);
\end{tikzpicture}
\end{adjustbox}
```

* **Task:** Flag malicious flows in network traffic, offline or in real time.
* **Data:** CIC-IDS2017, UNSW-NB15.
* **Watch out:** Duplicate flows and unseen attacks; report PR-AUC.

## 6. Phishing URL detection

```{=latex}
\begin{adjustbox}{max width=\linewidth,center}
\begin{tikzpicture}[node distance=5mm, pb/.style={minimum width=24mm, minimum height=16mm, text width=22mm}, zone/.style={draw=aasgrey, dashed, rounded corners=4pt, inner sep=6pt}, zonelabel/.style={font=\footnotesize\bfseries, text=aasgrey}]
  \node[neu, pb] (n0) {URL\\full link with path};
  \node[neu, pb, right=of n0] (n1) {Tokens\\host, path, query};
  \draw[arr] (n0)--(n1);
  \node[dfn, pb, right=of n1] (n2) {Features\\length, symbols};
  \draw[arr] (n1)--(n2);
  \node[neu, pb, right=of n2] (n3) {Label\\benign or phish};
  \draw[arr] (n2)--(n3);
  \node[atk, ellipse, dashed, text width=50mm, minimum height=9mm, below=11mm of n2] (at) {\textbf{Break it}\\brand name in a clean host path};
  \draw[arratk] (at.north) -- (n2.south);
\end{tikzpicture}
\end{adjustbox}
```

* **Task:** Classify a full URL (host, path, query) from its text, without downloading the page.
* **Data:** PhishTank, Kaggle URL set.
* **Watch out:** One host gives many URLs: split by host or by time.

## 7. DGA detection

```{=latex}
\begin{adjustbox}{max width=\linewidth,center}
\begin{tikzpicture}[node distance=5mm, pb/.style={minimum width=24mm, minimum height=16mm, text width=22mm}, zone/.style={draw=aasgrey, dashed, rounded corners=4pt, inner sep=6pt}, zonelabel/.style={font=\footnotesize\bfseries, text=aasgrey}]
  \node[neu, pb] (n0) {Domain\\name only, no path};
  \node[neu, pb, right=of n0] (n1) {Characters\\sequence, n-grams};
  \draw[arr] (n0)--(n1);
  \node[dfn, pb, right=of n1] (n2) {Model\\char CNN, LR};
  \draw[arr] (n1)--(n2);
  \node[neu, pb, right=of n2] (n3) {Label\\human or DGA family};
  \draw[arr] (n2)--(n3);
  \node[atk, ellipse, dashed, text width=50mm, minimum height=9mm, below=11mm of n2] (at) {\textbf{Break it}\\word-list DGA, reads like English};
  \draw[arratk] (at.north) -- (n2.south);
\end{tikzpicture}
\end{adjustbox}
```

* **Task:** Detect botnet domains from the name alone, and tell DGA families apart.
* **Data:** DGArchive, Tranco.
* **Watch out:** Hold out a whole DGA family to test unseen botnets.

## 8. Web attack detection (SQLi, XSS)

```{=latex}
\begin{adjustbox}{max width=\linewidth,center}
\begin{tikzpicture}[node distance=5mm, pb/.style={minimum width=24mm, minimum height=16mm, text width=22mm}, zone/.style={draw=aasgrey, dashed, rounded corners=4pt, inner sep=6pt}, zonelabel/.style={font=\footnotesize\bfseries, text=aasgrey}]
  \node[neu, pb] (n0) {Request\\query string};
  \node[neu, pb, right=of n0] (n1) {Tokens\\SQL, HTML tags};
  \draw[arr] (n0)--(n1);
  \node[dfn, pb, right=of n1] (n2) {Model\\NB, forest};
  \draw[arr] (n1)--(n2);
  \node[neu, pb, right=of n2] (n3) {Label\\benign or attack};
  \draw[arr] (n2)--(n3);
  \node[atk, ellipse, dashed, text width=50mm, minimum height=9mm, below=11mm of n2] (at) {\textbf{Break it}\\encode the payload};
  \draw[arratk] (at.north) -- (n2.south);
\end{tikzpicture}
\end{adjustbox}
```

* **Task:** Detect injection in HTTP logs or query strings from the payload syntax.
* **Data:** SQL injection dataset, HTTP logs.
* **Watch out:** Test payloads must not copy training ones.

## 9. Android malware

```{=latex}
\begin{adjustbox}{max width=\linewidth,center}
\begin{tikzpicture}[node distance=5mm, pb/.style={minimum width=24mm, minimum height=16mm, text width=22mm}, zone/.style={draw=aasgrey, dashed, rounded corners=4pt, inner sep=6pt}, zonelabel/.style={font=\footnotesize\bfseries, text=aasgrey}]
  \node[neu, pb] (n0) {APK\\app package};
  \node[neu, pb, right=of n0] (n1) {Features\\permissions, intents};
  \draw[arr] (n0)--(n1);
  \node[dfn, pb, right=of n1] (n2) {Model\\forest, linear};
  \draw[arr] (n1)--(n2);
  \node[neu, pb, right=of n2] (n3) {Label\\benign or malware};
  \draw[arr] (n2)--(n3);
  \node[atk, ellipse, dashed, text width=50mm, minimum height=9mm, below=11mm of n2] (at) {\textbf{Break it}\\add unused permissions};
  \draw[arratk] (at.north) -- (n2.south);
\end{tikzpicture}
\end{adjustbox}
```

* **Task:** Classify APKs from the manifest (permissions, intents) and bytecode.
* **Data:** CIC-AndMal2017.
* **Watch out:** Old and new app versions: split by date.

## 10. Adversarial attack and defence

```{=latex}
\begin{adjustbox}{max width=\linewidth,center}
\begin{tikzpicture}[node distance=5mm, pb/.style={minimum width=24mm, minimum height=16mm, text width=22mm}, zone/.style={draw=aasgrey, dashed, rounded corners=4pt, inner sep=6pt}, zonelabel/.style={font=\footnotesize\bfseries, text=aasgrey}]
  \node[neu, pb] (n0) {Detector\\you train it};
  \node[neu, pb, right=of n0] (n1) {Attack\\small change};
  \draw[arr] (n0)--(n1);
  \node[dfn, pb, right=of n1] (n2) {Evasion\\rate and queries};
  \draw[arr] (n1)--(n2);
  \node[neu, pb, right=of n2] (n3) {Defence\\adversarial training};
  \draw[arr] (n2)--(n3);
  \node[atk, ellipse, dashed, text width=50mm, minimum height=9mm, below=11mm of n2] (at) {\textbf{Break it}\\report success and cost};
  \draw[arratk] (at.north) -- (n2.south);
\end{tikzpicture}
\end{adjustbox}
```

* **Task:** Evade a security classifier with a small change, then harden it.
* **Data:** any dataset above, ART.
* **Watch out:** Attack the model you can defend, not a toy.

