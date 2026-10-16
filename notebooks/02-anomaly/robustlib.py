"""Robustness evaluation of our own anomaly detectors (class 03_03): feature-space evasion, poisoning of the
training window, and defences. Lab use only: the detectors are the ones trained in this module on public data.

A *victim* hides a fitted detector behind `score()` and counts every query, as `attacklib` did for spam.
"""

from collections.abc import Callable
from dataclasses import dataclass
from typing import Self

import numpy as np
from scipy.stats import rankdata

from anomlib import Detector, threshold

# Features of KDD99 an attacker can change without changing what the connection does (volume and timing);
# protocol, service, flag and the content features (logins, root shells, ...) stay fixed.
MUTABLE = ["duration", "src_bytes", "dst_bytes", "count", "srv_count", "dst_host_count", "dst_host_srv_count"]


@dataclass
class Victim:
    det: Detector
    t: float  # alarm threshold (set on normal validation data)
    queries: int = 0

    @classmethod
    def build(cls, det: Detector, X_train: np.ndarray, X_val: np.ndarray, fpr: float = 0.01) -> Self:
        det.fit(X_train)
        return cls(det, threshold(det.score(X_val), fpr))

    def score(self, X: np.ndarray) -> np.ndarray:
        X = np.atleast_2d(X)
        self.queries += len(X)
        return self.det.score(X)

    def alarm(self, X: np.ndarray) -> np.ndarray:
        return self.score(X) > self.t

    @property
    def name(self) -> str:
        return self.det.name


def mimicry(X_att: np.ndarray, X_normal: np.ndarray, mutable: np.ndarray) -> np.ndarray:
    """Copy the mutable features of the nearest normal row (nearest in the *fixed* features): the attack keeps
    what it does and borrows the volume and timing of a similar normal connection (Wagner and Soto's idea)."""
    from sklearn.neighbors import NearestNeighbors

    fixed = ~mutable if (~mutable).any() else np.ones_like(mutable)  # all mutable: nearest in every feature
    nn = NearestNeighbors(n_neighbors=1).fit(X_normal[:, fixed])
    j = nn.kneighbors(X_att[:, fixed])[1][:, 0]
    out = X_att.copy()
    out[:, mutable] = X_normal[j][:, mutable]
    return out


def random_search(victim: Victim, x: np.ndarray, mutable: np.ndarray, lo: np.ndarray, hi: np.ndarray, budget: int = 200,
                  step: float = 0.5, seed: int = 0) -> tuple[np.ndarray, bool, int]:  # fmt: skip
    """Black-box evasion: change one mutable feature at a time by a random step (inside the range [lo, hi] seen in
    normal data), keep the change if the score goes down; stop below the threshold or after `budget` queries.
    Returns (x', evaded, queries used)."""
    rng = np.random.default_rng(seed)
    idx = np.flatnonzero(mutable)
    q0 = victim.queries
    best, s = x.copy(), victim.score(x)[0]
    while victim.queries - q0 < budget and s > victim.t:
        cand = best.copy()
        i = rng.choice(idx)
        cand[i] = np.clip(cand[i] + rng.normal(0, step), lo[i], hi[i])
        sc = victim.score(cand)[0]
        if sc < s:
            best, s = cand, sc
    return best, bool(s <= victim.t), victim.queries - q0


# ----------------------------------------------------------------------------------------------------- poisoning
def boiling_frog(make: Callable[[], Detector], X0: np.ndarray, target: np.ndarray, rounds: int = 20, per_round: int = 50,
                 frac: float = 0.98, fpr: float = 0.01, keep: int | None = None, seed: int = 0) -> list[dict]:  # fmt: skip
    """Online retraining under poisoning. Each round the defender refits the detector on its window of recent
    *unflagged* data; the attacker adds `per_round` points just below the current threshold, on the way from the
    normal centre towards `target`. Returns, per round, the target's score / threshold and the poison accepted."""
    rng = np.random.default_rng(seed)
    data = X0.copy()
    keep = keep or len(X0)
    log = []
    for r in range(rounds + 1):
        det = make().fit(data)
        t = threshold(det.score(data), fpr)
        log.append({"round": r, "target_ratio": float(det.score(target[None])[0] / t), "centre": data.mean(0)})
        if r == rounds:
            break
        # candidates on the segment centre -> target, keep the farthest ones that stay below the threshold
        c = data.mean(0)
        a = np.linspace(0, 1, 200)[:, None]
        line = c + a * (target - c)
        ok = line[det.score(line) < frac * t]
        p = ok[-1] if len(ok) else c
        poison = p + rng.normal(0, 0.05, (per_round, len(p)))
        poison = poison[det.score(poison) < t]  # what the defender accepts as normal
        data = np.vstack([data, poison])[-keep:]
    return log


# ------------------------------------------------------------------------------------------------------ defences
class RankEnsemble(Detector):
    """Average of the *ranks* (empirical CDF on normal validation data) of several detectors' scores: an attacker
    must now look normal to all of them at once."""

    name = "rank ensemble"

    def __init__(self, members: list[Detector], X_ref: np.ndarray | None = None):
        self.members, self.X_ref = members, X_ref

    def fit(self, X):
        for m in self.members:
            m.fit(X)
        ref = X if self.X_ref is None else self.X_ref
        self.ref = [np.sort(m.score(ref)) for m in self.members]
        return self

    def score(self, X):
        return np.mean([np.searchsorted(r, m.score(X)) / len(r) for m, r in zip(self.members, self.ref)], axis=0)


def rank_mean(*scores: np.ndarray) -> np.ndarray:
    return np.mean([rankdata(s) / len(s) for s in scores], axis=0)


def cusum(x: np.ndarray, mu: float, sd: float, k: float = 0.5) -> np.ndarray:
    """One-sided CUSUM statistic S_t = max(0, S_{t-1} + (x_t - mu)/sd - k): adds up small, persistent deviations
    that a per-point threshold never sees (Page 1954)."""
    s, out = 0.0, np.zeros(len(x))
    for i, v in enumerate(x):
        s = max(0.0, s + (v - mu) / sd - k)
        out[i] = s
    return out
