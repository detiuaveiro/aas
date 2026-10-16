"""Shared helpers of the anomaly-detection notebooks (module 03): data, protocol, detectors and metrics.

Every detector returns a score where **higher = more anomalous**; thresholds are set on normal validation data only.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Self

import numpy as np
import pandas as pd
from pynnmf import nmf_hals
from sklearn.cluster import KMeans
from sklearn.covariance import LedoitWolf, MinCovDet
from sklearn.decomposition import PCA, FastICA
from sklearn.ensemble import IsolationForest
from sklearn.metrics import average_precision_score, roc_auc_score
from sklearn.mixture import GaussianMixture
from sklearn.neighbors import LocalOutlierFactor, NearestNeighbors
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.svm import OneClassSVM

DATA = Path(__file__).resolve().parents[2] / "datasets"

# KDD Cup 99 attack -> category (Tavallaee et al. 2009 and the original task description)
CATEGORY = {
    "back": "dos", "land": "dos", "neptune": "dos", "pod": "dos", "smurf": "dos", "teardrop": "dos",
    "ipsweep": "probe", "nmap": "probe", "portsweep": "probe", "satan": "probe",
    "ftp_write": "r2l", "guess_passwd": "r2l", "imap": "r2l", "multihop": "r2l", "phf": "r2l", "spy": "r2l",
    "warezclient": "r2l", "warezmaster": "r2l",
    "buffer_overflow": "u2r", "loadmodule": "u2r", "perl": "u2r", "rootkit": "u2r",
}  # fmt: skip
CATEGORIES = ["dos", "probe", "r2l", "u2r"]
CATEGORICAL = ["protocol_type", "service", "flag"]
# heavy-tailed counts: log1p before scaling (rates in [0, 1] are left as they are)
HEAVY = ["duration", "src_bytes", "dst_bytes", "hot", "num_failed_logins", "lnum_compromised", "lnum_root",
         "lnum_file_creations", "lnum_shells", "lnum_access_files", "count", "srv_count", "dst_host_count",
         "dst_host_srv_count"]  # fmt: skip


def load_kdd(dedupe: bool = True) -> pd.DataFrame:
    """KDD Cup 99 (10% file, 494,020 connections). `dedupe` keeps one copy of each identical row (145,585 left)."""
    df = pd.read_csv(DATA / "KDDCup99.csv.gz")
    if dedupe:
        df = df.drop_duplicates().reset_index(drop=True)
    df["category"] = df["label"].map(CATEGORY).fillna("normal")
    return df


@dataclass
class Prep:
    """One-hot for the categorical columns, log1p for heavy counts, z-scaling; fitted on normal training rows only."""

    ohe: OneHotEncoder = field(default_factory=lambda: OneHotEncoder(handle_unknown="ignore", sparse_output=False))
    scaler: StandardScaler = field(default_factory=StandardScaler)
    numeric: list[str] = field(default_factory=list)

    def _num(self, df: pd.DataFrame) -> np.ndarray:
        x = df[self.numeric].to_numpy(dtype=float).copy()
        for i, c in enumerate(self.numeric):
            if c in HEAVY:
                x[:, i] = np.log1p(x[:, i])
        return x

    def fit(self, df: pd.DataFrame) -> Self:
        self.numeric = [c for c in df.columns if c not in CATEGORICAL + ["label", "category"]]
        self.ohe.fit(df[CATEGORICAL])
        self.scaler.fit(np.hstack([self._num(df), self.ohe.transform(df[CATEGORICAL])]))
        return self

    def transform(self, df: pd.DataFrame) -> np.ndarray:
        x = np.hstack([self._num(df), self.ohe.transform(df[CATEGORICAL])])
        return self.scaler.transform(x).astype(np.float32)

    @property
    def names(self) -> list[str]:
        return self.numeric + list(self.ohe.get_feature_names_out(CATEGORICAL))


@dataclass
class Split:
    train: pd.DataFrame  # normal only (novelty setting)
    val: pd.DataFrame  # normal only: sets the threshold
    test: pd.DataFrame  # normal + attacks
    pool: pd.DataFrame  # attacks not in test: labelled examples for supervised models and attacks
    prep: Prep

    def X(self, part: str) -> np.ndarray:
        return self.prep.transform(getattr(self, part))

    @property
    def y_test(self) -> np.ndarray:
        return (self.test["category"] != "normal").to_numpy(dtype=int)


def kdd_split(df: pd.DataFrame | None = None, seed: int = 0, per_category: int = 100) -> Split:
    """Normal rows 60/20/20 into train/val/test; the test set gets up to `per_category` attacks of each category
    (u2r has only 52 unique rows), about 2% of the test set, so that each kind of attack counts."""
    df = load_kdd() if df is None else df
    rng = np.random.default_rng(seed)
    normal = df[df["category"] == "normal"]
    idx = rng.permutation(len(normal))
    n_tr, n_va = int(0.6 * len(idx)), int(0.2 * len(idx))
    train, val, test_n = (
        normal.iloc[idx[:n_tr]],
        normal.iloc[idx[n_tr : n_tr + n_va]],
        normal.iloc[idx[n_tr + n_va :]],
    )
    test_a, pool = [], []
    for cat in CATEGORIES:
        rows = df[df["category"] == cat]
        rows = rows.iloc[rng.permutation(len(rows))]
        k = min(per_category, len(rows) // 2) if cat == "u2r" else min(per_category, len(rows))
        test_a.append(rows.iloc[:k])
        pool.append(rows.iloc[k:])
    test = pd.concat([test_n, *test_a]).reset_index(drop=True)
    return Split(train.reset_index(drop=True), val.reset_index(drop=True), test, pd.concat(pool).reset_index(drop=True),
                 Prep().fit(train))  # fmt: skip


# ---------------------------------------------------------------------------------------------------------- detectors
class Detector:
    """fit(X normal) -> self; score(X) -> higher = more anomalous."""

    name = "detector"

    def fit(self, X: np.ndarray) -> Self:
        return self

    def score(self, X: np.ndarray) -> np.ndarray:
        raise NotImplementedError


class ZMax(Detector):
    name = "z-score (max |z|)"

    def fit(self, X):
        self.mu, self.sd = X.mean(0), _sd(X)
        return self

    def score(self, X):
        return np.abs((X - self.mu) / self.sd).max(1)


class DiagGauss(Detector):
    name = "Gaussian (diagonal)"

    def fit(self, X):
        self.mu, self.sd = X.mean(0), _sd(X)
        return self

    def score(self, X):
        return (((X - self.mu) / self.sd) ** 2).sum(1)


class Mahalanobis(Detector):
    """Squared Mahalanobis distance with a Ledoit-Wolf shrunk covariance (one-hot columns make the plain one singular)."""

    name = "Mahalanobis"

    def __init__(self, robust: bool = False, max_fit: int = 5000, seed: int = 0):
        self.robust, self.max_fit, self.seed = robust, max_fit, seed
        if robust:
            self.name = "Mahalanobis (MCD)"

    def fit(self, X):
        if self.robust:
            Xs = _sub(X, self.max_fit, self.seed)
            self.cov = MinCovDet(random_state=self.seed).fit(Xs)
        else:
            self.cov = LedoitWolf().fit(X)
        return self

    def score(self, X):
        return self.cov.mahalanobis(X)


class KMeansDist(Detector):
    name = "k-means distance"

    def __init__(self, k: int = 20, seed: int = 0):
        self.km = KMeans(k, n_init=3, random_state=seed)

    def fit(self, X):
        self.km.fit(X)
        return self

    def score(self, X):
        return self.km.transform(X).min(1)


class GMM(Detector):
    name = "GMM (-log-likelihood)"

    def __init__(self, k: int = 10, seed: int = 0):
        self.gm = GaussianMixture(k, covariance_type="diag", reg_covar=1e-3, random_state=seed)

    def fit(self, X):
        self.gm.fit(X)
        return self

    def score(self, X):
        return -self.gm.score_samples(X)


class KNNDist(Detector):
    name = "kNN distance"

    def __init__(self, k: int = 5, max_fit: int = 20000, seed: int = 0):
        self.k, self.max_fit, self.seed = k, max_fit, seed

    def fit(self, X):
        self.nn = NearestNeighbors(n_neighbors=self.k).fit(_sub(X, self.max_fit, self.seed))
        return self

    def score(self, X):
        return self.nn.kneighbors(X)[0][:, -1]


class LOF(Detector):
    name = "LOF"

    def __init__(self, k: int = 20, max_fit: int = 20000, seed: int = 0):
        self.lof, self.max_fit, self.seed = LocalOutlierFactor(n_neighbors=k, novelty=True), max_fit, seed

    def fit(self, X):
        self.lof.fit(_sub(X, self.max_fit, self.seed))
        return self

    def score(self, X):
        return -self.lof.score_samples(X)


class IForest(Detector):
    name = "Isolation Forest"

    def __init__(self, n: int = 200, seed: int = 0):
        self.f = IsolationForest(n_estimators=n, random_state=seed)

    def fit(self, X):
        self.f.fit(X)
        return self

    def score(self, X):
        return -self.f.score_samples(X)


class OCSVM(Detector):
    name = "One-class SVM"

    def __init__(self, nu: float = 0.01, max_fit: int = 5000, seed: int = 0):
        self.m, self.max_fit, self.seed = OneClassSVM(nu=nu, gamma="scale"), max_fit, seed

    def fit(self, X):
        self.m.fit(_sub(X, self.max_fit, self.seed))
        return self

    def score(self, X):
        return -self.m.decision_function(X)


class PCARecon(Detector):
    name = "PCA reconstruction"

    def __init__(self, var: float = 0.95):
        self.p = PCA(n_components=var, svd_solver="full")

    def fit(self, X):
        self.p.fit(X)
        return self

    def score(self, X):
        return ((X - self.p.inverse_transform(self.p.transform(X))) ** 2).sum(1)


class ICARecon(Detector):
    """FastICA with k components. mode "recon": squared reconstruction error (the same subspace as PCA with k components,
    so the same score); mode "source": the largest |source| after unit-variance whitening (a z-score in IC space)."""

    def __init__(self, k: int = 20, mode: str = "source", seed: int = 0):
        self.k, self.mode = k, mode
        self.name = f"ICA ({mode})"
        self.ica = FastICA(n_components=k, whiten="unit-variance", random_state=seed, max_iter=500, tol=1e-3)

    def fit(self, X):
        self.ica.fit(X)
        return self

    def score(self, X):
        s = self.ica.transform(X)
        if self.mode == "source":
            return np.abs(s).max(1)
        return ((X - self.ica.inverse_transform(s)) ** 2).sum(1)


class NMFRecon(Detector):
    """Non-negative matrix factorisation X = W H with k parts (pyNNMF, HALS). The rows are shifted by the training minimum;
    a new row gets its non-negative weights W with H fixed (multiplicative updates); score = squared residual."""

    name = "NMF reconstruction"

    def __init__(self, k: int = 20, n: int = 100, max_fit: int = 20000, seed: int = 0):
        self.k, self.n, self.max_fit, self.seed = k, n, max_fit, seed

    def fit(self, X):
        self.lo = X.min(0)
        v = _sub(X, self.max_fit, self.seed) - self.lo
        _, _, h, _ = nmf_hals(v.astype(np.float64), self.k, n=self.n, seed=self.seed, init="nndsvd")
        self.h = h
        return self

    def score(self, X):
        v = np.clip(X - self.lo, 0, None).astype(np.float64)
        hht = self.h @ self.h.T
        w = np.full((len(v), self.k), 0.1)
        vh = v @ self.h.T
        for _ in range(60):
            w *= vh / (w @ hht + 1e-9)
        return ((v - w @ self.h) ** 2).sum(1)


def zoo(seed: int = 0) -> list[Detector]:
    """The classic detectors of class 03_01, all with their default settings."""
    return [ZMax(), DiagGauss(), Mahalanobis(), KMeansDist(seed=seed), GMM(seed=seed), KNNDist(seed=seed),
            LOF(seed=seed), IForest(seed=seed), OCSVM(seed=seed), PCARecon()]  # fmt: skip


def _sd(X: np.ndarray) -> np.ndarray:
    """Standard deviation per feature; a feature constant on normal data gets 1 (else any change scores infinity)."""
    sd = X.std(0)
    return np.where(sd < 1e-3, 1.0, sd)


def table_config() -> None:
    """Print polars tables in full (all columns, no shape or dtype lines)."""
    import polars as pl

    pl.Config.set_tbl_cols(-1)
    pl.Config.set_tbl_rows(40)
    pl.Config.set_tbl_width_chars(220)
    pl.Config.set_tbl_hide_dataframe_shape(True)
    pl.Config.set_tbl_hide_column_data_types(True)
    pl.Config.set_float_precision(3)


def _sub(X: np.ndarray, n: int, seed: int) -> np.ndarray:
    if len(X) <= n:
        return X
    return X[np.random.default_rng(seed).choice(len(X), n, replace=False)]


# ------------------------------------------------------------------------------------------------------------ metrics
def threshold(val_scores: np.ndarray, fpr: float = 0.01) -> float:
    """Threshold = the (1 - fpr) quantile of the scores of normal validation data: about `fpr` false alarms."""
    return float(np.quantile(val_scores, 1 - fpr))


def evaluate(s_test: np.ndarray, y_test: np.ndarray, s_val: np.ndarray, fpr: float = 0.01) -> dict[str, float]:
    """AUROC, AUPRC (average precision) and the confusion metrics at the validation threshold."""
    t = threshold(s_val, fpr)
    pred = s_test > t
    tp, fp = int((pred & (y_test == 1)).sum()), int((pred & (y_test == 0)).sum())
    fn = int((~pred & (y_test == 1)).sum())
    prec = tp / (tp + fp) if tp + fp else 0.0
    rec = tp / (tp + fn) if tp + fn else 0.0
    return {"AUROC": roc_auc_score(y_test, s_test), "AUPRC": average_precision_score(y_test, s_test),
            "recall": rec, "precision": prec, "F1": 2 * prec * rec / (prec + rec) if prec + rec else 0.0,
            "FPR": fp / max(1, int((y_test == 0).sum()))}  # fmt: skip


def recall_by_category(s_test: np.ndarray, cats: pd.Series, s_val: np.ndarray, fpr: float = 0.01) -> dict[str, float]:
    t = threshold(s_val, fpr)
    return {c: float((s_test[(cats == c).to_numpy()] > t).mean()) for c in CATEGORIES}


def precision_at_base_rate(tpr: float, fpr: float, base_rate: float) -> float:
    """Bayes: P(attack | alarm) for a detector with this TPR and FPR when a share `base_rate` of events are attacks."""
    return tpr * base_rate / (tpr * base_rate + fpr * (1 - base_rate))


# ------------------------------------------------------------------------------------------------- Example 1 (2-D toy)
EX1_MU = np.array([0.0, 0.0])
EX1_COV = np.array([[1.0, 0.9], [0.9, 1.0]])
EX1_POINTS = {"A": np.array([2.0, 2.0]), "B": np.array([1.0, -1.0])}


def example1(n: int = 500, seed: int = 0) -> np.ndarray:
    """Example 1: standardised log bytes sent / received of one host's sessions (correlation 0.9)."""
    return np.random.default_rng(seed).multivariate_normal(EX1_MU, EX1_COV, size=n)
