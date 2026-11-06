# Project Title (e.g., Passive Malware Detection using Byte N-Grams)

![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)
![Python](https://img.shields.io/badge/Python-3.12%2B-blue)

This `README.md` is the report of the project.
Keep it concise, link every figure from an image file in the zip, and delete the hints in *italics*.

## Authors

| Name | Student number | E-mail |
|:--|:--|:--|
| Student Name 1 | 000001 | name1@ua.pt |
| Student Name 2 | 000002 | name2@ua.pt |

Course: Aprendizagem Aplicada à Segurança (AAS), Universidade de Aveiro. Project: 1 or 2. Team name: student number.

## 1. Abstract

*150-250 words: the security problem, the method, the main result (e.g., "F1 of 0.95 on a time-based split").*

## 2. Introduction and Threat Model

* **Problem:** what specific issue you solve, and why it matters.
* **Threat model:** who the attacker is, what they know and can change, and which error costs more (false positive or false negative).
* **Objectives:** what you built.

## 3. Related Work

*Two or three papers or tools; how your approach differs or which one you replicate.*

## 4. Data and Method

* **Data:** source, number of samples, class balance, link or download script.
* **Split:** how the test set stays free of leaks (deduplication, family or time split, seed).
* **Features:** how raw data (bytes, logs, text) becomes numerical vectors. *This is the crucial part.*
* **Models:** a trivial baseline plus at least two models or feature sets, and why.

## 5. Results

Main results table on the test set (state the split):

| Model | Precision | Recall | F1-Score |
| :--- | :---: | :---: | :---: |
| Baseline | 0.00 | 0.00 | 0.00 |
| Model A | 0.00 | 0.00 | 0.00 |
| **Model B** | 0.00 | 0.00 | **0.00** |

* Confusion matrix of the best model (figure), and PR-AUC or ROC-AUC when the classes are imbalanced.
* Error analysis: examples of false positives and false negatives, and what they cost in your setting.
* Cost of the system (features per sample, time per sample) when the topic is real-time.

## 6. Attack or Defence

*The evasion, distribution shift or hardening step you tested, and its measured effect.*

## 7. Changes since Project 1

*Project 2 only, at most one page: what is new and what the feedback asked for. Delete this section in Project 1.*

## 8. Conclusion and Future Work

*Main achievements, limits, and what you would do with six more months.*

## Installation

Python 3.12 or higher. Use a virtual environment.

```bash
python3 -m venv venv
source venv/bin/activate        # Windows: .\venv\Scripts\Activate
pip install -r requirements.txt
```

## Dataset Setup

* **Source:** [link to the dataset]
* If the data is large, download it with the provided script:

```bash
python scripts/download_data.py
```

## Usage and Reproducing the Results

Train the model, then rebuild the results table above from the raw data.
State the random seed and the runtime on your machine.

```bash
python src/train.py --input data/train.csv --output models/rf_model.pkl --seed 42
python src/evaluate.py --model models/rf_model.pkl --seed 42
```

## Use of AI Assistants and References

*Which parts an AI assistant helped with, and a list of the datasets, papers and tools cited.*

## License

MIT License, see [LICENSE](LICENSE).
