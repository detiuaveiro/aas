# %% [markdown]
# # Practice guide 03_03: testing anomaly detectors as an adversary would
#
# **Goal.** Measure the robustness of the detectors you built in guides 03_01 and 03_02: compute the price of evading
# a Mahalanobis detector, run a constrained mimicry and a budgeted black-box search against your own models, poison a
# retrained detector a little at a time, and test two defences (vetted retraining, CUSUM). Everything runs offline on
# our own models and public or synthetic data, in feature space. Every `TODO` cell must be completed; the `check`
# cells tell you whether you got it right.
#
# Read `guide_03_03.pdf` first. Time: about 2 hours. Cells marked **(given)** are complete.

# %%
import os
import sys
from pathlib import Path

os.environ.setdefault("KERAS_BACKEND", "jax")
import numpy as np
import polars as pl
from matplotlib import pyplot as plt
from scipy.stats import chi2
from sklearn.neighbors import NearestNeighbors

LIB = next(p for p in (Path("../../notebooks/02-anomaly"), Path("../../../notebooks/02-anomaly")) if p.exists())
sys.path.insert(0, str(LIB))  # student / solution folder
import anomlib as an
import deeplib as dl
import robustlib as rl

an.table_config()

# %% [markdown]
# ## Part A. The victims (given)
#
# Three detectors trained on normal KDD99 rows, each wrapped as a `Victim` that counts every query. The threshold is
# set at 1% false alarms on normal validation rows. **Mutable** features (volume and timing) may change; all the
# others (protocol, service, flag, error rates, content) are fixed, because changing them changes the attack itself.

# %%
sp = an.kdd_split(seed=0)
Xtr, Xva, Xte, y = sp.X("train"), sp.X("val"), sp.X("test"), sp.y_test
mut = np.array([n in rl.MUTABLE for n in sp.prep.names])
lo, hi = Xtr.min(0), Xtr.max(0)
Xatt, cat = Xte[y == 1], sp.test["category"].to_numpy()[y == 1]
V = {d.name: rl.Victim.build(d, Xtr, Xva) for d in [an.Mahalanobis(), an.PCARecon(), dl.AE()]}
print("mutable:", [n for n in sp.prep.names if n in rl.MUTABLE])
print({k: f"catches {v.alarm(Xatt).mean():.2f} of the test attacks" for k, v in V.items()})

# %% [markdown]
# ## Part B. Example 1: the price of evasion
#
# Point B $=(1,-1)$ must pass a Mahalanobis detector ($\rho=0.9$, unit variances) at false-positive rate 1%:
# $(x_1^2-1.8x_1x_2+x_2^2)/0.19\le t$ with $t=\chi^2_{2,0.99}$. Implement `max_x1(x2, t)`: the largest $x_1$ that
# satisfies the inequality for a given $x_2$ (solve the quadratic in $x_1$).

# %%
def max_x1(x2, t):
    # <<TODO
    raise NotImplementedError
    # TODO>>
    # <<SOL
    a, b, c = 1.0, -1.8 * x2, x2**2 - 0.19 * t
    return (-b + np.sqrt(b * b - 4 * a * c)) / (2 * a)
    # SOL>>


# %%
# check: the boundary point scores exactly t
t = chi2.ppf(0.99, 2)
x1 = max_x1(-1.0, t)
P = np.linalg.inv(an.EX1_COV)
p = np.array([x1, -1.0])
assert abs(p @ P @ p - t) < 1e-9
print(f"t = {t:.2f}; with x2 = -1 the session may send at most x1 = {x1:.2f} (B sends 1.00)")

# %% [markdown]
# **Question B1.** What does the attacker lose by staying below the threshold? Is the detector useless if it can be
# evaded?

# <<SOL
# %% [markdown]
# **Answers B.** B passes only with $x_1\le0.35$ instead of 1 (standardised log of the bytes sent): it must move less
# data per session, so the exfiltration takes more sessions and more time. The detector is not useless: it raises the
# cost of the attack and forces a slower pattern that other controls (volume over a day, CUSUM, part F) can catch.
# SOL>>

# %% [markdown]
# ## Part C. Mimicry
#
# Implement `mimicry(X_att, X_normal, mutable)`: for each attack row, find the nearest normal row using **only the
# fixed features** (`NearestNeighbors(n_neighbors=1)`), and copy that row's mutable features into the attack row.

# %%
def mimicry(X_att, X_normal, mutable):
    # <<TODO
    raise NotImplementedError
    # TODO>>
    # <<SOL
    fixed = ~mutable
    nn = NearestNeighbors(n_neighbors=1).fit(X_normal[:, fixed])
    j = nn.kneighbors(X_att[:, fixed])[1][:, 0]
    out = X_att.copy()
    out[:, mutable] = X_normal[j][:, mutable]
    return out
    # SOL>>


# %%
# check and driver (given)
Xm_all = mimicry(Xatt, Xtr, mut)
assert np.array_equal(Xm_all[:, ~mut], Xatt[:, ~mut]), "fixed features must not change"
rows = []
for k, v in V.items():
    caught = v.alarm(Xatt)
    passed = ~v.alarm(Xm_all[caught])
    rows.append({"detector": k, "caught": caught.mean(), "evaded after mimicry": passed.mean(),
                 **{c: passed[cat[caught] == c].mean() for c in an.CATEGORIES if (cat[caught] == c).any()}})  # fmt: skip
print(pl.DataFrame(rows))

# %% [markdown]
# **Question C1.** How many caught attacks evade? Which categories evade most, and why? What does this say about the
# features these detectors rely on?

# <<SOL
# %% [markdown]
# **Answers C.** Very few: about 2% for Mahalanobis and PCA and a few percent for the AE. The evasions are mostly r2l
# (and some u2r for PCA): those rows already look like normal logins and sit near the threshold. The detectors catch
# attacks by what they *do* (SYN-error rates, flags, failed logins, root shells), features the attacker cannot change
# without changing the attack; volume and timing carry little of the evidence.
# SOL>>

# %% [markdown]
# ## Part D. A black-box search with a query budget
#
# Implement `random_search(victim, x, mutable, lo, hi, budget, rng)`: start from `x` and its score; repeat while fewer
# than `budget` queries were used **and** the score is above `victim.t`: copy the current best, pick a random mutable
# feature, add a normal step with standard deviation 0.5, clip to `[lo, hi]`, score it (one query), keep it if the
# score is lower. Return `(best_x, evaded, queries_used)`. Use `victim.score(x[None])[0]` and `victim.queries`.

# %%
def random_search(victim, x, mutable, lo, hi, budget, rng):
    # <<TODO
    raise NotImplementedError
    # TODO>>
    # <<SOL
    idx = np.flatnonzero(mutable)
    q0 = victim.queries
    best, s = x.copy(), victim.score(x[None])[0]
    while victim.queries - q0 < budget and s > victim.t:
        cand = best.copy()
        i = rng.choice(idx)
        cand[i] = np.clip(cand[i] + rng.normal(0, 0.5), lo[i], hi[i])
        sc = victim.score(cand[None])[0]
        if sc < s:
            best, s = cand, sc
    return best, bool(s <= victim.t), victim.queries - q0
    # SOL>>


# %%
# check and driver (given): 40 caught attacks per detector, three budgets; then the same search with every feature free
rng = np.random.default_rng(0)
v = V["Mahalanobis"]
x0 = Xatt[np.flatnonzero(v.alarm(Xatt))[0]]
bx, ok, q = random_search(v, x0, mut, lo, hi, 30, rng)
assert q <= 30 and np.array_equal(bx[~mut], x0[~mut]), "budget or fixed features violated"
rows = []
for k in ["Mahalanobis", "PCA reconstruction"]:
    v = V[k]
    idx = np.flatnonzero(v.alarm(Xatt))[:40]
    for budget, mask, label in [(50, mut, "mutable"), (500, mut, "mutable"), (500, np.ones_like(mut), "all features")]:
        res = [random_search(v, Xatt[i], mask, lo, hi, budget, np.random.default_rng(int(i))) for i in idx]
        rows.append({"detector": k, "features": label, "budget": budget, "evasion": np.mean([r[1] for r in res])})
print(pl.DataFrame(rows))

# %% [markdown]
# **Question D1.** How does evasion grow with the budget? And when every feature is free? What limits the attacker:
# the search or the constraints? Why is a feature-space result an upper bound for real traffic?

# <<SOL
# %% [markdown]
# **Answers D.** With the constraint, evasion is 0 with 50 queries and at most 7.5% with 500 (PCA: 0); with every
# feature free the same search evades 12.5% (PCA) to 25% (Mahalanobis). The feasible region (what the attack must keep) limits the attacker, not the search. In
# feature space we may set any value inside the normal range; real traffic must also be producible by a working
# connection, so a feature-space evasion rate is an upper bound for what an attack in the problem space can achieve.
# SOL>>

# %% [markdown]
# ## Part E. Poisoning a retrained detector (the boiling frog)
#
# The defender refits a Mahalanobis detector each round on the last 500 accepted points of Example 1 (threshold at 1%
# false alarms). Implement `poison_round(det, t, data, target, n, rng)`: take 200 points on the segment from the mean
# of `data` to `target`, keep those with score below `0.98 * t`, take the **last** one (closest to the target; the
# mean if none), add `n` copies with Gaussian noise (sd 0.05), and return those that score below `t` (what the
# defender accepts).

# %%
def poison_round(det, t, data, target, n, rng):
    # <<TODO
    raise NotImplementedError
    # TODO>>
    # <<SOL
    c = data.mean(0)
    line = c + np.linspace(0, 1, 200)[:, None] * (target - c)
    ok = line[det.score(line) < 0.98 * t]
    p = ok[-1] if len(ok) else c
    poison = p + rng.normal(0, 0.05, (n, len(p)))
    return poison[det.score(poison) < t]
    # SOL>>


# %%
# driver (given): 20 rounds, without and with vetting by a frozen reference model
X0 = an.example1(500, seed=0)
target = 2 * an.EX1_POINTS["B"]
ref = an.Mahalanobis().fit(X0)
t_ref = an.threshold(ref.score(X0), fpr=0.001)
curves = {}
for vetted in [False, True]:
    rng, data, ratio = np.random.default_rng(0), X0.copy(), []
    for r in range(21):
        det = an.Mahalanobis().fit(data)
        t = an.threshold(det.score(data))
        ratio.append(float(det.score(target[None])[0] / t))
        poison = poison_round(det, t, data, target, 25, rng)
        if vetted:
            poison = poison[ref.score(poison) < t_ref]
        data = np.vstack([data, poison])[-500:]
    curves["vetted retraining" if vetted else "plain retraining"] = ratio
plt.figure(figsize=(6.5, 3.5))
for k, r in curves.items():
    plt.plot(r, "o-", label=k)
plt.axhline(1, color="k", ls="--")
plt.yscale("log")
plt.xlabel("round")
plt.ylabel("score(target) / threshold")
plt.legend()
plt.tight_layout()
plt.show()
print({k: next((i for i, x in enumerate(r) if x < 1), None) for k, r in curves.items()}, "(round the target is accepted)")

# %% [markdown]
# **Question E1.** After how many rounds is the target accepted without vetting? Why does vetting stop it? What
# legitimate change would vetting also slow down?

# <<SOL
# %% [markdown]
# **Answers E.** Without vetting the target is accepted after about 9 rounds (225 poison points, 45% of the window).
# With vetting, new points must also be normal for a frozen reference model: the poison can only fill the original
# normal region, so the model barely moves (the ratio stays near 4.5) and the target is never accepted. The price:
# genuine slow change (a new service, more traffic) is also admitted only as far as the reference allows; the reference
# itself must be refreshed by a human decision, not automatically.
# SOL>>

# %% [markdown]
# ## Part F. Slow drift and CUSUM
#
# Implement `cusum(r, mu, sd, k)`: $S_0=0$, $S_t=\max(0, S_{t-1}+(r_t-\mu)/\sigma-k)$; return the array of $S_t$.

# %%
def cusum(r, mu, sd, k=0.5):
    # <<TODO
    raise NotImplementedError
    # TODO>>
    # <<SOL
    s, out = 0.0, np.zeros(len(r))
    for i, v in enumerate(r):
        s = max(0.0, s + (v - mu) / sd - k)
        out[i] = s
    return out
    # SOL>>


# %%
# check and driver (given): the pressure sensor of Example 2 drifts in the second half of the run
assert np.allclose(cusum(np.array([0, 1, 1, -3, 2.0]), 0, 1, 0.5), [0, 0.5, 1.0, 0, 1.5])
from sklearn.linear_model import LinearRegression

rows = []
for slope in [0.1, 0.5, 2.0]:
    hours = []
    for seed in range(3):
        X, _, _ = dl.plant(seed=seed)
        half = len(X) // 2
        X = (X - X[:half].mean(0)) / X[:half].std(0)
        reg = LinearRegression().fit(np.delete(X[:half], 7, 1), X[:half, 7])
        X[half:, 7] += slope * np.arange(len(X) - half) / dl.DAY
        r = X[:, 7] - reg.predict(np.delete(X, 7, 1))
        mu, sd = r[:half].mean(), r[:half].std()
        c = cusum(r, mu, sd)
        first = lambda m: np.flatnonzero(m[half:])[0] / 12 if m[half:].any() else np.inf  # noqa: E731
        hours.append((first(np.abs(r - mu) > np.abs(r[:half] - mu).max() * 1.1), first(c > c[:half].max() * 1.1)))
    rows.append({"drift (sd/day)": slope, "per-point: median hours": float(np.median([a for a, _ in hours])),
                 "CUSUM: median hours": float(np.median([b for _, b in hours]))})  # fmt: skip
print(pl.DataFrame(rows))

# %% [markdown]
# **Question F1.** Why does CUSUM detect the drift earlier than a per-point threshold with the same false-alarm rule?
# What do $k$ and the alarm level $h$ trade off? **F2.** Which other attack of this guide would CUSUM-like monitoring
# help against?

# <<SOL
# %% [markdown]
# **Answers F.** A per-point threshold waits until one residual alone exceeds the largest normal one; a slow drift
# adds a little each step, so that takes a day or more at 0.1 sd/day. CUSUM sums the small positive deviations (minus
# $k$), so persistent evidence accumulates and it fires within hours. A larger $k$ ignores small shifts (fewer false
# alarms, misses slow drifts); a larger $h$ needs more evidence (fewer false alarms, longer delay). The same idea helps
# against the boiling frog of part E (monitor the accumulated movement of the model's centre) and against evasion by
# many small sessions (part B: accumulate the volume per host).
# SOL>>
