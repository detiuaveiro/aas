---
title: Aprendizagem Aplicada à Segurança
subtitle: SPAM Dectetion
author: Mário Antunes
institute: Universidade de Aveiro
date: September 26, 2025
toc: true
toc-title: "Table of Contents"
bibliography: "references.bib"
colorlinks: true
highlight-style: tango
mainfont: NotoSans
header-includes:
 - \usetheme[sectionpage=none,numbering=fraction,progressbar=frametitle]{metropolis}
 - \usepackage{longtable,booktabs}
 - \usepackage{etoolbox}
 - \AtBeginEnvironment{longtable}{\small}
 - \AtBeginEnvironment{cslreferences}{\small}
 - \AtBeginEnvironment{Shaded}{\tiny}
 - \AtBeginEnvironment{verbatim}{\tiny}
 - \setmonofont[Contextuals={Alternate}]{FiraCodeNerdFontMono-Retina}
---

# SPAM

## SPAM

* The term "spam" is internet slang that refers to unsolicited commercial email (UCE).
* The first reported case of spam occurred in 1898, when the New York Times reported unsolicited messages circulating in association with an old swindle.
* The term "spam" was coined in 1994, based on a now-legendary Monty Python's Flying Circus sketch, where a crowd of Vikings sings progressively louder choruses of "SPAM! SPAM! SPAM!"

## SPAM

![](figures/monty_python_spam.gif)

## SPAM

![](figures/spam_history.png)


## SPAM

![](figures/nigerian-prince-scam.png)


# Fight against SPAM

## Fight against SPAM

* *Huge* list of [anti-spam techniques](https://en.wikipedia.org/wiki/Anti-spam_techniques)
* From common sense to *Bayesian spam filtering*
* Unfortunately it is a costly battle

## Fight against SPAM

![](figures/spam-traffic.png)

# SPAM Detection 

## SPAM Detection

![](figures/spam.drawio.pdf)

# Binary Classification

## Binary Classification

* Binary classification is the task of classifying the elements of a set into two groups (each called class) on the basis of a classification rule. 
* For this application one message can either be spam or ham. 

![](figures/Binary-Classification.png){ width=75%}

# Text Mining 

## Text Mining

* Text mining is the process of deriving high-quality information from text. 
* Combines concepts from Machine Learning, Linguistic and statistical analysis. 
* In this area we will explore the methods used to rank words/tokens and the BoW model.


## Bag of Words (Bow) model

![](figures/bow.png)


# Natural Language Processing (NLP)

## Natural Language Processing (NLP)

* NLP gives the computers the ability to understand text. 
* Combines *Sintax* and *Semantic* into the analysis.
* One famous exemples are the Large Language Models (LLMs) that power OpenAI Chat GPT. 


# Classification Model 

## Classification Model

* SPAM detection is "considered" a toy example.
* As such, we will explore two of the simples learning models: Naive Bayes and Logistic Regression.

:::: {.columns}
::: {.column width="50%"}
![](figures/NB.png)
:::
::: {.column width="50%"}
![](figures/LogReg.png)
:::
::::

# Model Evaluation 

## Model Evaluation

* Classification model can be evaluated using a confusing matrix
* The simplest methods to evaluate a model is throuhgh accuracy: $acc = \frac{TP+TN}{TN+TN+FP+FN}$

![](figures/CM.png)

## Model Evaluation

![](figures/acc.png)
