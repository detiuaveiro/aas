---
title: Aprendizagem Aplicada à Segurança
subtitle: Practical Project AAS (Project 2, resit)
author: Mário Antunes
institute: Universidade de Aveiro
date: January 2027
---

# Introduction

This document describes the practical project of the AAS course for the second evaluation phase (*época de recurso*).
As stated at the beginning of the course, the practical project is worth 50% of the final grade.

You may continue the work of Project 1 with the same group, or start a new topic.
A group may also change size (individual or pair); groups of three need the professor's approval.
The goal is the same as in Project 1: build an application that uses machine learning to solve a privacy or security problem, and evaluate it honestly.
Each student is encouraged to propose a topic, which may be aligned with another course project, a scholarship, or the Master's dissertation.

**If you continue Project 1**, the work must go clearly beyond what you delivered: fix the problems found in the feedback, and add at least one of these:

*   a new dataset, or a harder split (by time, by family or by campaign);
*   a new model or feature set, compared with the old one on the same split;
*   an attack or a defence that was not in Project 1.

The `README.md` then has a short section *Changes since Project 1* (at most one page) that lists what is new and what the feedback asked for.

# Proposed Topics

Below are **ten** topics that set the level of ambition expected.
You may select one of these or propose a custom topic (send a short description to the professor before you start).
Each topic names the course module it builds on.

| # | Topic | Task | Builds on |
|:-|:----------------|:----------------------------------|:----------|
| 1 | **Malware detection (passive)** | Classify a file as malicious from headers and raw bytes, without executing it. | Malware |
| 2 | **Malware detection (active)** | Classify a file from its behaviour in a sandbox (API calls, files, network). | Malware |
| 3 | **Binary visualization** | Turn bytes into images (e.g. with *Veles*) and classify them or find anomalies. | Malware, Anomaly |
| 4 | **Mail analysis** | Flag spam, phishing or malware mail from headers, body or both. | Spam |
| 5 | **Network intrusion detection** | Flag malicious flows in network traffic (NIDS), offline or in real time. | Anomaly, Flows |
| 6 | **Phishing URL detection** | Classify a URL from lexical features only, without downloading the page. | Spam |
| 7 | **DGA detection** | Tell algorithmically generated domains from legitimate ones. | Spam, Anomaly |
| 8 | **Web attack detection** | Detect SQL injection or XSS in HTTP logs or query strings. | Spam |
| 9 | **Android malware** | Classify APKs from the manifest (permissions, intents) and bytecode. | Malware |
| 10 | **Adversarial attack and defence** | Evade a security classifier with a small change, then harden it. | Spam, Anomaly |

Whatever the topic, the project must contain the following.

1.  **A threat model:** who the attacker is, what they know and can change, and which error (false positive or false negative) costs more in your setting.
2.  **A baseline:** a trivial rule or a simple model (majority class, keyword rule, logistic regression), so that every number has a reference.
3.  **At least two models or two feature sets**, compared on the same split.
4.  **A defence or an attack:** a detector project tests at least one evasion or one distribution shift; an adversarial project builds the detector it attacks.

Projects that only run a model from a tutorial on a clean Kaggle file, with a random split, are graded as incomplete.

# Requirements and Deadline

The project is done individually or in pairs (groups of three are exceptional and need the professor's approval).
Use your student number(s) as the project/team name.

**The deadline is set for the resit period and announced on the eLearning platform.**
Upload one compressed file to the eLearning platform before the closing time shown there.
A defence takes place only if the professor requests it.

Each submission is **one zip file** uploaded to the eLearning platform, with:

1.  **Source code:** the complete application.
2.  **Dataset:** the data, or a link and a script that downloads it (do not include very large files).
3.  **README.md:** this file *is the report*.
    It follows `templates/README.md` and starts with the identification of the authors (name, student number, e-mail).
    A reader must install the dependencies and reproduce the main results table with the commands given there.

There is no separate PDF report.
Put the figures as image files in the zip and link them from `README.md`.

## Evaluation protocol

Evaluation must go beyond accuracy.

*   Report the confusion matrix, precision, recall and F1-score; add PR-AUC or ROC-AUC when the classes are imbalanced.
*   Give the number of samples per class and per split, and fix the random seed.
*   Split so that the test set cannot leak: remove duplicates before splitting, keep all samples of one family, campaign or session in one split, and split by time when the data has a date.
*   Never tune on the test set.
*   Discuss the errors: show examples of false positives and false negatives and say what they cost.
*   Measure the cost of the system (features per file, time per sample) when the topic is real-time.

## Grading criteria

The criteria below are looked at in the `README.md` and the code (and the defence, if requested).

| Criterion | What is looked at |
|:--------------------|:--------------------------------------|
| Problem and threat model | clear task, attacker, error costs |
| Data and features | source, size, balance, cleaning, how raw data becomes features |
| Method | baseline, justified models, comparison on one split |
| Evaluation | metrics beyond accuracy, leakage-free split, error analysis |
| Attack or defence | an evasion, shift or hardening step, measured |
| Reproducibility | README, seeds, environment file, the results table can be rerun |
| README (report) | structure, figures, honest limits |

A delivery after the closing time is not accepted in the resit period.
The code and the README must be your own work; cite every dataset, paper and tool, and state which parts an AI assistant helped with.

# Resources

The list will grow as the course progresses.
Links last checked on 6 November 2026.

**Binary visualization and malware**

1.  [Malware analysis method using visualization of binary files](https://dl.acm.org/doi/10.1145/2513228.2513294)
2.  [JOE Sandbox](https://www.joesandbox.com/), [Joe Sandbox ML](https://www.joesecurity.org/joe-sandbox-ML) and [analyses overview](https://www.joesandbox.com/analysispaged/0)
3.  [Malware Bazaar](https://bazaar.abuse.ch/browse/) (samples) and [URLhaus](https://urlhaus.abuse.ch/) (malicious URLs)
4.  [EMBER](https://github.com/elastic/ember): PE features and a benchmark for static malware detection
5.  [CIC-AndMal2017](https://www.unb.ca/cic/datasets/andmal2017.html): Android malware dataset

**Mail, URLs, domains and web**

6.  [E-Mail Header Analyzer (MHA)](https://github.com/gcsuaveiro/email-header-analyzer)
7.  [E-Mail Header SPAM detection example](https://www.kaggle.com/code/maharshipandya/email-spam-classification-98)
8.  [SpamAssassin public corpus](https://spamassassin.apache.org/old/publiccorpus/)
9. [Dataset (Phishing/Benign URLs)](https://www.kaggle.com/datasets/siddharthkumar25/malicious-and-benign-urls) and [PhishTank](https://phishtank.org/)
10. [DGArchive](https://dgarchive.caad.fkie.fraunhofer.de/) (generated domains) and [Tranco](https://tranco-list.eu/) (legitimate domains)
11. [SQL injection dataset](https://www.kaggle.com/datasets/sajid576/sql-injection-dataset)

**Network and adversarial ML**

12. [Anomaly Detection in Intrusion Detection Systems](https://github.com/detiuaveiro/anomaly_dectection_ids)
13. [CIC-IDS2017](https://www.unb.ca/cic/datasets/ids-2017.html) and [UNSW-NB15](https://research.unsw.edu.au/projects/unsw-nb15-dataset)
14. [Adversarial Robustness Toolbox](https://github.com/Trusted-AI/adversarial-robustness-toolbox)
