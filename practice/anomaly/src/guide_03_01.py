# %% [markdown]
# # Practice guide 03_01: classic anomaly detectors on network connections
#
# **Goal.** Build the statistical core of an anomaly detector yourself (z-score, Mahalanobis distance, a threshold set
# on normal data, average precision), compare it with the scikit-learn twins, run the classic detectors on KDD99, and
# measure why a classifier is not enough for new attacks. Every `TODO` cell must be completed; the `check` cells tell
# you whether you got it right.
#
# Read `guide_03_01.pdf` first. Time: about 2 hours. Cells marked **(given)** are complete.

# %%
import sys
from pathlib import Path

import numpy as np
import polars as pl
from sklearn.covariance import EmpiricalCovariance, LedoitWolf
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import average_precision_score

LIB = next(p for p in (Path("../../notebooks/02-anomaly"), Path("../../../notebooks/02-anomaly")) if p.exists())
sys.path.insert(0, str(LIB))  # student / solution folder
import anomlib as an

an.table_config()

# %% [markdown]
# ## Part A. Example 1 and KDD99 (given)
#
# Example 1: 500 sessions of one host, $x_1$ = log bytes sent, $x_2$ = log bytes received (standardised, correlation
# 0.9). Point A $=(2,2)$, point B $=(1,-1)$. KDD99: deduplicated, normal rows split 60/20/20, the test set holds 100
# attacks per category (u2r: 26), 1.8% of the rows.

# %%
X1 = an.example1(500, seed=0)
A, B = an.EX1_POINTS["A"], an.EX1_POINTS["B"]
sp = an.kdd_split(seed=0)
Xtr, Xva, Xte, y = sp.X("train"), sp.X("val"), sp.X("test"), sp.y_test
cats = sp.test["category"]
print("Example 1:", X1.shape, " KDD99 train/val/test:", Xtr.shape, Xva.shape, Xte.shape, " attacks in test:", int(y.sum()))

# %% [markdown]
# ## Part B. z-score and Mahalanobis distance
#
# Implement
# * `zmax(X, mu, sd)`: for each row, $\max_j |x_j-\mu_j|/\sigma_j$;
# * `mahalanobis2(X, mu, cov)`: for each row, $(\mathbf{x}-\boldsymbol\mu)^\top C^{-1}(\mathbf{x}-\boldsymbol\mu)$.
#
# Use `np.linalg.inv` (or better, `np.linalg.solve`) and `np.einsum("ij,jk,ik->i", D, P, D)` to avoid a loop.

# %%
def zmax(X, mu, sd):
    # <<TODO
    raise NotImplementedError
    # TODO>>
    # <<SOL
    return np.abs((X - mu) / sd).max(axis=1)
    # SOL>>


def mahalanobis2(X, mu, cov):
    # <<TODO
    raise NotImplementedError
    # TODO>>
    # <<SOL
    D = X - mu
    P = np.linalg.inv(cov)
    return np.einsum("ij,jk,ik->i", D, P, D)
    # SOL>>


# %%
# check: the numbers of the lecture (true parameters) and the scikit-learn twin (estimated parameters)
P2 = np.vstack([A, B])
assert np.allclose(zmax(P2, an.EX1_MU, np.ones(2)), [2, 1])
assert np.allclose(mahalanobis2(P2, an.EX1_MU, an.EX1_COV), [4.2105, 20.0], atol=1e-3)
emp = EmpiricalCovariance().fit(X1)
mine = mahalanobis2(P2, X1.mean(0), np.cov(X1.T, bias=True))
print("mine:", mine.round(3), " scikit-learn:", emp.mahalanobis(P2).round(3))
assert np.allclose(mine, emp.mahalanobis(P2))
print("z-score and Mahalanobis OK")

# %% [markdown]
# **Question B1.** Which point does each score flag, and why? Draw (on paper) the contour $\max|z|=2$ and the
# ellipse $d_M=3$ over the cloud of Example 1.

# <<SOL
# %% [markdown]
# **Answers B.** The z-score flags A (|z| = 2) and calls B normal (|z| = 1): it checks each feature against its own
# range. The Mahalanobis distance flags B ($d_M^2=20$, p-value 4.5e-5) and calls A normal ($d_M^2=4.21$, p = 0.12):
# the covariance tells it that both features grow together, so a session that sends a lot and receives little breaks
# the relation even though each value is ordinary. The z-score contour is a square; the Mahalanobis contour is an
# ellipse stretched along the diagonal $x_1=x_2$.
# SOL>>

# %% [markdown]
# ## Part C. Threshold and average precision
#
# * `threshold(s_val, fpr)`: the $(1-\text{fpr})$ quantile of the scores of **normal** validation rows.
# * `average_precision(y, s)`: sort by score (highest first); at the rank of each attack compute the precision of the
#   top-ranked rows; return the mean of those precisions. It must match `average_precision_score`.
# * `precision_at_base_rate(tpr, fpr, b)`: Bayes' rule of the lecture.

# %%
def threshold(s_val, fpr=0.01):
    # <<TODO
    raise NotImplementedError
    # TODO>>
    # <<SOL
    return float(np.quantile(s_val, 1 - fpr))
    # SOL>>


def average_precision(y, s):
    # <<TODO
    raise NotImplementedError
    # TODO>>
    # <<SOL
    order = np.argsort(-s, kind="stable")
    hits = y[order]
    precision_at_k = np.cumsum(hits) / np.arange(1, len(hits) + 1)
    return float(precision_at_k[hits == 1].mean())
    # SOL>>


def precision_at_base_rate(tpr, fpr, b):
    # <<TODO
    raise NotImplementedError
    # TODO>>
    # <<SOL
    return tpr * b / (tpr * b + fpr * (1 - b))
    # SOL>>


# %%
# check
rng = np.random.default_rng(0)
yy, ss = (rng.random(2000) < 0.05).astype(int), rng.random(2000)
ss[yy == 1] += 0.3
assert abs(average_precision(yy, ss) - average_precision_score(yy, ss)) < 1e-9
assert abs(threshold(np.arange(101.0), 0.01) - 99.0) < 1e-9
assert abs(precision_at_base_rate(0.95, 0.01, 1e-4) - 0.0094) < 1e-4
print("threshold, AP and base rate OK")

# %% [markdown]
# **Question C1.** Fill the table for TPR = 0.95. How many of 100 alarms are real at $b$ = 1/10,000 and FPR = 1%?

# %%
print(pl.DataFrame([{"base rate": f"1/{round(1 / b):,}", **{f"FPR {f}": precision_at_base_rate(0.95, f, b) for f in [0.01, 0.001]}}
                    for b in [1e-2, 1e-3, 1e-4]]))  # fmt: skip

# <<SOL
# %% [markdown]
# **Answers C.** At $b=10^{-4}$ and FPR 1% the precision is 0.0094: fewer than 1 alarm in 100 is real. Lowering the
# FPR tenfold (0.1%) raises it to 0.087, still 9 in 100. The base rate, not the detector, dominates: rare attacks need
# very low false-positive rates or a second stage (triage) after the detector.
# SOL>>

# %% [markdown]
# ## Part D. Mahalanobis on KDD99, and the classic zoo
#
# With 71 features (many one-hot columns) the sample covariance is singular. **Shrink** it:
# $\hat C=(1-\lambda)S+\lambda\,\frac{\text{tr}(S)}{d}I$. Implement `fit_shrunk(X, lam)` returning
# $(\boldsymbol\mu,\hat C)$; then compare $\lambda=0.01, 0.1$ with scikit-learn's `LedoitWolf` (which picks
# $\lambda$ from the data).

# %%
def fit_shrunk(X, lam):
    # <<TODO
    raise NotImplementedError
    # TODO>>
    # <<SOL
    mu = X.mean(0)
    S = np.cov(X.T, bias=True)
    return mu, (1 - lam) * S + lam * np.trace(S) / X.shape[1] * np.eye(X.shape[1])
    # SOL>>


# %%
# check and comparison with the twin (given)
rows = []
for lam in [0.01, 0.1]:
    mu, cov = fit_shrunk(Xtr, lam)
    rows.append({"model": f"mine, lambda={lam}", **an.evaluate(mahalanobis2(Xte, mu, cov), y, mahalanobis2(Xva, mu, cov))})
lw = LedoitWolf().fit(Xtr)
rows.append({"model": f"LedoitWolf, lambda={lw.shrinkage_:.4f}", **an.evaluate(lw.mahalanobis(Xte), y, lw.mahalanobis(Xva))})
print(pl.DataFrame(rows))

# %% [markdown]
# Now the zoo of the lecture (given): ten detectors, one protocol. Copy the AUPRC and the recall per category into
# your notes.

# %%
rows = []
for det in an.zoo(seed=0):
    det.fit(Xtr)
    s_va, s_te = det.score(Xva), det.score(Xte)
    rows.append({"detector": det.name, **an.evaluate(s_te, y, s_va), **an.recall_by_category(s_te, cats, s_va)})
print(pl.DataFrame(rows).sort("AUPRC", descending=True))

# %% [markdown]
# **Question D1.** Which category is hard for every detector, and why? Which detector misses most DoS rows, and why
# does a flood fool it? **D2.** How does the shrinkage $\lambda$ change the result, and what does `LedoitWolf` choose?

# <<SOL
# %% [markdown]
# **Answers D.** r2l (password guessing, warez downloads) is hard for every detector (best recall 0.45, PCA): the
# connection *is* a normal login, the difference is in content counts that are often zero. LOF misses most DoS rows
# (recall 0.08): the floods are dense clusters, so the local density ratio of a flood row is about 1. The Isolation
# Forest misses u2r (0.08): a few unusual content counts are not isolated quickly by random axis cuts. Shrinkage: a
# small $\lambda$ trusts the sample covariance (sharper but noisier directions), a large one pulls towards a diagonal
# model (closer to the z-score). Here $\lambda=0.01$ gives AUPRC 0.539, $\lambda=0.1$ 0.498, and LedoitWolf picks
# $\lambda=0.061$ (0.516): the Ledoit-Wolf rule minimises the error of the covariance estimate, not the detection error.
# SOL>>

# %% [markdown]
# ## Part E. The Isolation Forest score
#
# Implement `c(n)` $=2H(n-1)-2(n-1)/n$ with $H(i)=\ln i+0.5772156649$, and `iforest_score(mean_depth, n)`
# $=2^{-\text{mean\_depth}/c(n)}$.

# %%
def c(n):
    # <<TODO
    raise NotImplementedError
    # TODO>>
    # <<SOL
    return 2 * (np.log(n - 1) + 0.5772156649) - 2 * (n - 1) / n
    # SOL>>


def iforest_score(mean_depth, n=256):
    # <<TODO
    raise NotImplementedError
    # TODO>>
    # <<SOL
    return 2.0 ** (-np.asarray(mean_depth) / c(n))
    # SOL>>


# %%
# check
assert abs(c(256) - 10.2448) < 1e-3
assert abs(iforest_score(c(256)) - 0.5) < 1e-12
print("c(256) =", round(c(256), 3), " score after 4 cuts:", round(float(iforest_score(4)), 3))

# %% [markdown]
# **Question E1.** What score does a point get when it is isolated after 2 cuts? After 20? Why do the trees use small
# subsamples (256 rows)?

# <<SOL
# %% [markdown]
# **Answers E.** After 2 cuts $s=2^{-2/10.24}=0.87$ (clearly anomalous), after 20 cuts $s=0.26$ (deep in a dense
# region). Small subsamples keep trees fast and make *swamping* and *masking* rarer: a cluster of anomalies is less
# likely to be large enough in a 256-row sample to look normal, which is also why the forest resists contamination.
# SOL>>

# %% [markdown]
# ## Part F. A classifier or a one-class detector?
#
# Implement `train_without(category)`: a random forest (200 trees, `random_state=0`, `n_jobs=-1`) trained on the
# normal training rows (label 0) and the attack pool **without** `category` (label 1). Return the recall on the
# test attacks of that category at the 1% validation threshold (use `an.recall_by_category`).

# %%
Xp, cp = sp.X("pool"), sp.pool["category"].to_numpy()


def train_without(category):
    # <<TODO
    raise NotImplementedError
    # TODO>>
    # <<SOL
    keep = cp != category
    X = np.vstack([Xtr, Xp[keep]])
    labels = np.r_[np.zeros(len(Xtr)), np.ones(keep.sum())]
    rf = RandomForestClassifier(200, n_jobs=-1, random_state=0).fit(X, labels)
    s_va, s_te = rf.predict_proba(Xva)[:, 1], rf.predict_proba(Xte)[:, 1]
    return an.recall_by_category(s_te, cats, s_va)[category]
    # SOL>>


# %%
# driver (given)
pca = an.PCARecon().fit(Xtr)
one_class = an.recall_by_category(pca.score(Xte), cats, pca.score(Xva))
print(pl.DataFrame([{"unseen category": cat, "random forest": train_without(cat), "PCA (one-class)": one_class[cat]}
                    for cat in an.CATEGORIES]))  # fmt: skip

# %% [markdown]
# **Question F1.** For which unseen category does the forest fail, and why? What does that say about deploying only a
# classifier? **F2.** Propose a combination of the two kinds of detector for a real network.

# <<SOL
# %% [markdown]
# **Answers F.** Without r2l examples the forest's recall on r2l drops from 1.00 to 0.36, below the PCA detector
# (0.45) that never saw any attack; unseen dos, probe and u2r are still caught (0.96-1.00) because they resemble other
# attack kinds it knows. A classifier learns the border between normal and the attacks it saw: a new attack on the
# normal side of that border is invisible. A sensible deployment runs both: signatures and a classifier for known
# attacks (high precision), a one-class detector for the unknown (alarms triaged by an analyst), and the labels the
# analysts produce feed the classifier.
# SOL>>
