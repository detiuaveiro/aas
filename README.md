# ![AAS Logo](assets/logo.svg) Aprendizagem Aplicada à Segurança (AAS)

Curricular Unit Code: [**41787**](https://www.ua.pt/pt/uc/14823) | Universidade de Aveiro

Professor: [**Mário Antunes**](https://www.ua.pt/en/p/80336171) ([`mario.antunes@ua.pt`](mailto:mario.antunes@ua.pt))

Academic Year: [**2026/2027 – 1.º Semestre**](https://www.ua.pt/file/89688)

---

## 1. Course Philosophy & Overview

**Aprendizagem Aplicada à Segurança (AAS)** explores the application of modern machine learning techniques to cybersecurity challenges. Students learn to formulate security problems as data-driven tasks, design and evaluate intelligent defensive models, and analyze adversarial robustness:

1. **Foundations of ML in Cybersecurity:** Understanding the end-to-end security pipeline, threat landscapes, asymmetric cost functions, and critical trade-offs between false positives and false negatives (ROC/AUC).
2. **Security Optimization Algorithms:** Applying gradient-based and derivative-free metaheuristics (PSO, Differential Evolution) to optimize security classifiers and decision thresholds.
3. **SPAM Detection & Text Mining:** Extracting feature representations (N-grams, TF-IDF) from unstructured messages and applying probabilistic (Naive Bayes) and ensemble classifiers to combat evolving spam campaigns.
4. **Anomaly Detection & Outlier Analysis:** Leveraging statistical baselines, distance metrics (Mahalanobis), Isolation Forests, and Autoencoders to identify intrusions and zero-day anomalies without labeled attacks.
5. **Adversarial Machine Learning & Evasion Attacks:** Analyzing how attackers evade ML models (poisoning, perturbation, model theft) and designing robust, defense-in-depth countermeasures.
6. **Malware Analysis (Static & Dynamic):** Dissecting Portable Executable (PE) headers, byte entropy, opcode distributions, and mining dynamic API call sequences for multi-class malware family attribution.
7. **Network Telemetry & Flow Analytics:** Processing large-scale PCAP files, extracting flow features, and training scalable models on intrusion benchmarks (CIC-IDS).
8. **Generative AI & LLMs in Cybersecurity:** Investigating the dual use of Large Language Models: automated vulnerability discovery, log triage, and defensive copilots versus automated exploit synthesis and prompt injection.
9. **Hands-On Grounding:** Every 3-hour class is divided into **1 hour of interactive presentation/lecture** followed by **2 hours of guided practical laboratory work**.

---

## 2. Evaluation Scheme

AAS features **Discrete Evaluation** and **Final Evaluation** options:

### Discrete Evaluation (Recommended)
* **Theoretical Component (50%):**
  * **Theoretical Test 1 (25%):** Middle of semester (Class 8 — 06 Nov 2026). Covers Modules 1 & 2 (Spam & Anomaly Detection).
  * **Theoretical Test 2 (25%):** Last class (Class 14 — 18 Dec 2026). Covers Modules 3 & 4 (Malware Detection, Advanced Topics & LLMs in Security).
* **Practical Component (50%):**
  * **Practical Project (50%):** End-to-end security machine learning project implementation on real-world threat datasets. Released Class 08 (06 Nov 2026) | Due Class 14 (18 Dec 2026).

### Final Evaluation
* **Final Exam (50%):** Scheduled during the regular exam season (*Época Normal*).
* **Comprehensive Project (50%):** Complete machine learning security project defense.

---

## 3. Detailed 14-Week Schedule (2026/2027)

Classes begin on **14 September 2026** and end on **22 December 2026**.
* **TP1:** Fridays (14 sessions)

| # | TP1 (Fri) | Lecture Topic (1h) | Practical Lab Guide (2h) | Evaluation & Milestones |
|---|:---|:---|:---|:---|
| **01** | 18-Sep | **Course Presentation & Machine Learning in Cybersecurity**<br>Threat landscape, ML pipeline in security, false positives vs. false negatives, ROC/AUC metrics. | `notebooks/00-intro/`<br>Environment setup, security dataset exploratory analysis. | Course overview |
| **02** | 25-Sep | **Optimization Algorithms for Security Models**<br>Cost functions, gradient-based vs. derivative-free optimizers (PSO, Differential Evolution) in security parameter tuning. | `slides/slides_01_ex.md` & `notebooks/00-intro/`<br>Implementing and visualizing metaheuristic optimizers. | Optimization lab |
| **03** | 02-Oct | **SPAM Detection I: Text Mining & Feature Engineering**<br>Tokenization, N-grams, TF-IDF representations, Naive Bayes probabilistic classification for spam filtering. | `notebooks/01-spam/`<br>Text pre-processing, feature extraction, and Naive Bayes baseline. | Module 1 begins |
| **04** | 09-Oct | **SPAM Detection II: Advanced Classifiers & Concept Drift**<br>Ensemble methods, SVM for text classification, handling evolving spam campaigns and concept drift. | `slides/slides_02_ex.md` & `notebooks/01-spam/`<br>Classifying spam with ensemble models; evaluating drift over time. | Module 1 wrap-up |
| **05** | 16-Oct | **Anomaly Detection I: Foundations & Statistical Methods**<br>Intrusion detection paradigms, signature vs. anomaly detection, Gaussian models, Mahalanobis distance. | `notebooks/02-anomaly/`<br>Statistical outlier detection on network telemetry. | Module 2 begins |
| **06** | 23-Oct | **Anomaly Detection II: High-Dimensional & Unsupervised Models**<br>Isolation Forests, One-Class SVMs, Local Outlier Factor (LOF), Autoencoders for anomaly scoring. | `slides/slides_03_ex.md` & `notebooks/02-anomaly/`<br>Building and benchmarking Isolation Forests and Autoencoders on netflow data. | Unsupervised lab |
| **07** | 30-Oct | **Adversarial Machine Learning & Evasion Attacks**<br>Attacking ML systems: data poisoning, adversarial perturbation, model evasion, defense-in-depth strategies. | `notebooks/02-anomaly/`<br>Simulating evasion attacks against anomaly detectors; robustness evaluation. | Mid-Term review |
| **08** | 06-Nov | **Theoretical Test 1 (1h) + Project Kickoff (2h)**<br>Written theoretical evaluation covering Modules 1 & 2, followed by Project topic introduction, dataset selection, and architecture planning. | `projects/project.md`<br>Project proposal drafting, dataset selection, and architecture planning. | **Theoretical Test 1**<br>**Project Released** |
| **09** | 13-Nov | **Malware Analysis I: PE File Structure & Static Features**<br>Portable Executable (PE) headers, sections, byte entropy, imported DLLs, opcode sequences, static signature analysis. | `notebooks/03-malware/`<br>Parsing PE files with `pefile`, extracting static feature vectors. | Module 3 begins |
| **10** | 20-Nov | **Malware Analysis II: Dynamic Features & Multi-Class Classification**<br>Sandbox behavior, API call sequence mining, behavioral graphs, multi-class malware family classification (Ransomware, Trojans, Spyware). | `practice/malware/exercises.md`<br>Dynamic analysis on API call sequences; family attribution. | Multi-class lab<br>Project Checkpoint |
| **11** | 27-Nov | **Network Intrusion Detection & Flow Analytics**<br>Network flow representations, PCAP analysis, feature aggregation, CIC-IDS benchmarks, real-time alert aggregation. | `notebooks/04-extra/`<br>Processing PCAP flow records and training scalable flow classifiers. | Network analytics |
| **12** | 04-Dec | **Generative AI & LLMs in Cybersecurity**<br>Dual use of LLMs: automated vulnerability detection, security log triage, autonomous pentesting vs. automated phishing, prompt injection. | `notebooks/04-extra/`<br>Fine-tuning / prompting LLMs for CVE triage and log correlation. | GenAI & Security |
| **13** | 11-Dec | **Project Mentoring & Clinic**<br>Dedicated hands-on clinic: model optimization, ablation studies, false alarm tuning, report polishing. | `projects/`<br>One-on-one team mentoring and pipeline profiling. | Project Clinic |
| **14** | 18-Dec | **Theoretical Test 2 (1h) + Project Presentations (2h)**<br>Final theoretical evaluation covering Modules 3 & 4, followed by team project live demonstrations, defense, and peer review. | `projects/`<br>Live system demonstrations, defense, and code audit. | **Theoretical Test 2**<br>**Project Due** |

---

## 4. Repository Structure

Adopted from the streamlined educational template:
* **`slides/`**: Lecture presentations written in Pandoc Markdown, compiled into Beamer PDFs using the `metropolis` theme.
* **`practice/`**: 2-hour laboratory guides written in Pandoc Markdown, compiled into clean A4 PDFs.
* **`projects/`**: Specification, guidelines, and rubrics for the Security Project.
* **`notebooks/`**: Interactive Jupyter notebooks with runnable code for each practical lab session:
  * `00-intro/`: Optimization and introductory models
  * `01-spam/`: Spam detection and text mining
  * `02-anomaly/`: Anomaly detection and unsupervised models
  * `03-malware/`: Static and dynamic malware analysis
  * `04-extra/`: Advanced topics, network flow, and LLMs in security
* **`datasets/`**: Reference dataset loaders and samples.
* **`Makefile`**: Master build coordinator featuring parallel execution and a visual progress bar.
* **`Makefile.inc`**: Shared compilation engine caching intermediate LaTeX files in `/dev/shm` RAM disk for maximum compilation speed.
* **`.pre-commit-config.yaml`**: Pre-commit quality gate verifying file formatting, linting Python and Jupyter notebooks with `ruff`, and compiling all course materials.

---

## 5. Recommended Bibliography

* **Clarence Chio and David Freeman**, *Machine Learning and Security: Protecting Systems with Data and Algorithms*, O'Reilly Media, 2018. ISBN 978-1491979907.
* **Marcus A. Maloof (Ed.)**, *Machine Learning and Data Mining for Computer Security: Methods and Applications*, Springer Science & Business Media, 2006. ISBN 978-1846280290.
* **Omar Santos**, *Network Security with NetFlow and IPFIX: Big Data Analytics for Information Security*, Cisco Press, 2015. ISBN 978-1587144387.
* **Michael Collins**, *Network Security Through Data Analysis: Building Situational Awareness*, O'Reilly Media, 2014. ISBN 978-1449357900.
* **Bill Gardner and Valerie Thomas**, *Building an Information Security Awareness Program: Defending Against Social Engineering and Technical Threats*, Elsevier, 2014. ISBN 978-0124199675.
* **Yusuf Bhaiji**, *Network Security Technologies and Solutions*, Pearson Education / Cisco Press, 2008. ISBN 978-1587052460.
* **Soma Halder and Sinan Ozdemir**, *Hands-On Machine Learning for Cybersecurity*, Packt Publishing Ltd, 2018.
* **Alessandro Parisi**, *Hands-On Artificial Intelligence for Cybersecurity*, Packt Publishing Ltd, 2019.
* **Emmanuel Tsukerman**, *Machine Learning for Cybersecurity Cookbook*, Packt Publishing Ltd, 2019.
* **John Paul Mueller and Ronald Stephens**, *Machine Learning Security Principles*, Packt Publishing Ltd, 2019.

---

## 6. License & Authors

* **Author:** Mário Antunes (`mario.antunes@ua.pt`)
* **License:** MIT License — see [LICENSE](LICENSE) for details.
