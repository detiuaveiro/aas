# Project Title (e.g., Passive Malware Detection using Byte N-Grams)

![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)
![Python](https://img.shields.io/badge/Python-3.12%2B-blue)

## Introduction

This repository contains the source code for the Practical Project of the **Aprendizagem Aplicada à Segurança (AAS)** course.

The objective of this project is to [briefly describe goal, e.g., classify portable executable (PE) files as benign or malicious] using [briefly describe technique, e.g., Random Forest classifiers based on header metadata].

**Authors:**
* Student Name 1 (nMec)
* Student Name 2 (nMec)

## Prerequisities

* Python 3.8 or higher
* Pip (Python Package Installer)

## Installation

It is strongly recommended to run this project inside a virtual environment to avoid dependency conflicts.

### 1. Extract the compressed file
```bash
tar xvf [compressed_file].tar.xz 
cd [your-project]
````

### 2. Create and Activate Virtual Environment

**Linux / macOS:**

```bash
python3 -m venv venv
source venv/bin/activate
```

**Windows (PowerShell):**

```powershell
python -m venv venv
.\venv\Scripts\Activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

## Dataset

This project utilizes the [Name of Dataset] dataset.

  * **Source:** [Link to dataset]
  * **Setup:** Place the dataset files in the `data/` folder. If the dataset is large, run the provided script to download it:
    ```bash
    python scripts/download_data.py
    ```

## Usage

To train the model:

```bash
python src/train.py --input data/train.csv --output models/rf_model.pkl
```

To run the classification on a new file:

```bash
python src/main.py --target suspicious_file.exe --model models/rf_model.pkl
```

## Major Results

The following table summarizes the performance of our best model ([Model Name]) on the test set (20% split).

| Class | Precision | Recall | F1-Score | Support |
| :--- | :---: | :---: | :---: | :---: |
| **Benign** | 0.98 | 0.97 | 0.97 | 1050 |
| **Malicious** | 0.96 | 0.99 | 0.97 | 980 |
| **Accuracy** | | | **0.97** | 2030 |

**Key Findings:**

  * The model achieved a low False Negative Rate (FNR), which is critical for security applications.
  * Feature extraction overhead was approximately 15ms per file.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.