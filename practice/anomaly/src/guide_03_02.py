# %% [markdown]
# # Practice guide 03_02: autoencoders, time and space
#
# **Goal.** Build an autoencoder detector in Keras 3 (JAX backend) and compare it with its linear twin (PCA), see why
# the code size matters and why it cannot be tuned without labels, build a windowed detector for a time series and beat
# (or not) a one-liner, and see how point-adjusted metrics inflate results. Every `TODO` cell must be completed; the
# `check` cells tell you whether you got it right.
#
# Read `guide_03_02.pdf` first. Time: about 2 hours. Cells marked **(given)** are complete.

# %%
import os
import sys
from pathlib import Path

os.environ.setdefault("KERAS_BACKEND", "jax")  # before importing keras
import keras
import numpy as np
import polars as pl
from matplotlib import pyplot as plt
from sklearn.decomposition import PCA

LIB = next(p for p in (Path("../../notebooks/02-anomaly"), Path("../../../notebooks/02-anomaly")) if p.exists())
sys.path.insert(0, str(LIB))  # student / solution folder
import anomlib as an
import deeplib as dl

an.table_config()
print("Keras", keras.__version__, "backend:", keras.backend.backend())
sp = an.kdd_split(seed=0)
Xtr, Xva, Xte, y = sp.X("train"), sp.X("val"), sp.X("test"), sp.y_test
cats = sp.test["category"]

# %% [markdown]
# ## Part A. An autoencoder in Keras
#
# Implement `build_ae(d, code, hidden)`: a `keras.Sequential` with an `Input((d,))`, a `Dense(hidden, relu)`, a
# `Dense(code)` (the code, linear), a `Dense(hidden, relu)` and a `Dense(d)` output. Implement
# `recon_error(model, X)`: the mean squared error **per row** (shape `(n,)`).

# %%
def build_ae(d, code=8, hidden=32):
    # <<TODO
    raise NotImplementedError
    # TODO>>
    # <<SOL
    return keras.Sequential([keras.layers.Input((d,)), keras.layers.Dense(hidden, activation="relu"),
                             keras.layers.Dense(code), keras.layers.Dense(hidden, activation="relu"),
                             keras.layers.Dense(d)])  # fmt: skip
    # SOL>>


def recon_error(model, X):
    # <<TODO
    raise NotImplementedError
    # TODO>>
    # <<SOL
    return ((model.predict(X, batch_size=4096, verbose=0) - X) ** 2).mean(axis=1)
    # SOL>>


# %%
# check
m = build_ae(71)
assert m.output_shape == (None, 71) and m.count_params() == 71 * 32 + 32 + 32 * 8 + 8 + 8 * 32 + 32 + 32 * 71 + 71
assert recon_error(m, Xva[:10]).shape == (10,)
print("autoencoder shape OK")

# %% [markdown]
# Train it on **normal** rows only (given), and compare with the linear twin: PCA with the same number of components.

# %%
def train_ae(X, code=8, hidden=32, epochs=20, seed=0, noise=0.0):
    """(given) Adam, MSE, batch 256, 10% of the rows kept for validation; noise > 0 = denoising AE."""
    keras.utils.set_random_seed(seed)
    model = build_ae(X.shape[1], code, hidden)
    model.compile(optimizer=keras.optimizers.Adam(1e-3), loss="mse")
    Xin = X + np.random.default_rng(seed).normal(0, noise, X.shape).astype(X.dtype) if noise else X
    hist = model.fit(Xin, X, epochs=epochs, batch_size=256, validation_split=0.1, verbose=0)
    return model, hist.history


ae, hist = train_ae(Xtr)
pca = PCA(8).fit(Xtr)
pca_err = lambda X: ((X - pca.inverse_transform(pca.transform(X))) ** 2).mean(1)  # noqa: E731
rows = [{"model": "autoencoder (code 8)", **an.evaluate(recon_error(ae, Xte), y, recon_error(ae, Xva))},
        {"model": "PCA (8 components)", **an.evaluate(pca_err(Xte), y, pca_err(Xva))}]  # fmt: skip
print(pl.DataFrame(rows))
plt.figure(figsize=(6, 3))
plt.plot(hist["loss"], label="train")
plt.plot(hist["val_loss"], label="validation")
plt.xlabel("epoch")
plt.ylabel("MSE")
plt.legend()
plt.tight_layout()
plt.show()

# %% [markdown]
# **Question A1.** Is the AE better than its linear twin? What do the ReLU layers add, and what would a linear AE learn?

# <<SOL
# %% [markdown]
# **Answers A.** At the same size the AE wins: AUPRC 0.54 with a code of 8 against 0.41 for PCA with 8 components.
# The ReLU layers let it bend the 8-dimensional subspace into a curved surface that fits normal traffic better. PCA
# catches up when it keeps more components (95% of the variance, class 03_01: 0.55). A linear AE trained with squared
# error learns the PCA subspace (Baldi and Hornik 1989), not necessarily the same basis.
# SOL>>

# %% [markdown]
# ## Part B. Code size and denoising
#
# Implement `sweep(codes)`: for each code size train an AE with `train_ae(Xtr, code=c, hidden=max(32, 2 * c))` and
# return a list of dicts with the code size, the AUPRC and recall at 1% FPR (`an.evaluate`) and the last validation
# MSE (`history["val_loss"][-1]`).

# %%
def sweep(codes):
    # <<TODO
    raise NotImplementedError
    # TODO>>
    # <<SOL
    rows = []
    for c in codes:
        model, h = train_ae(Xtr, code=c, hidden=max(32, 2 * c))
        r = an.evaluate(recon_error(model, Xte), y, recon_error(model, Xva))
        rows.append({"code": c, "AUPRC": r["AUPRC"], "recall": r["recall"], "val MSE": h["val_loss"][-1]})
    return rows
    # SOL>>


# %%
res = pl.DataFrame(sweep([4, 8, 32, 128]))
print(res)
dae, _ = train_ae(Xtr, noise=0.1)
print("denoising AE (code 8, noise 0.1):", {k: round(v, 3) for k, v in an.evaluate(recon_error(dae, Xte), y, recon_error(dae, Xva)).items()})

# %% [markdown]
# **Question B1.** Which code size has the best AUPRC, and which the lowest validation MSE? Could you have chosen the
# best code size without the test attacks? **B2.** Does the denoising AE help here?

# <<SOL
# %% [markdown]
# **Answers B.** A code of 32 (hidden 64) gives the best AUPRC (about 0.71, above the GMM of class 03_01); 4 is too
# small (normal rows reconstruct badly), 128 is wider than the input and starts to copy attacks too. The validation MSE
# of normal data is lowest for the large codes, so a normal-only criterion would not pick 32: we chose it by looking at
# the test attacks, which a one-class setting does not have. Report defaults, or tune on a separate labelled set. The
# denoising AE (code 8) is within the seed spread of the plain AE (about 0.55): the noise regularises but does not
# change what the bottleneck can represent.
# SOL>>

# %% [markdown]
# ## Part C. Time: a one-liner and a windowed autoencoder
#
# NAB series `nojump`: the daily rise does not happen on one day (values stay inside the normal range). Days 1-8 train,
# day 9 sets the threshold (max score + 10%). Implement
# * `seasonal_diff(x, period)`: $|x_t-x_{t-\text{period}}|$, with `np.nan` for the first `period` steps;
# * `per_step_score(err_w, w, T)`: `err_w` has shape `(N, w)` (squared error of window $i$ at each of its $w$ steps,
#   window $i$ covers steps $i..i+w-1$); return the mean, over the windows that contain step $t$, of the error at $t$.

# %%
def seasonal_diff(x, period):
    # <<TODO
    raise NotImplementedError
    # TODO>>
    # <<SOL
    return np.r_[np.full(period, np.nan), np.abs(x[period:] - x[:-period])]
    # SOL>>


def per_step_score(err_w, w, T):
    # <<TODO
    raise NotImplementedError
    # TODO>>
    # <<SOL
    s, n = np.zeros(T), np.zeros(T)
    for i, e in enumerate(err_w):
        s[i : i + w] += e
        n[i : i + w] += 1
    return s / np.maximum(n, 1)
    # SOL>>


# %%
# check
assert np.allclose(seasonal_diff(np.arange(6.0), 2)[2:], 2) and np.isnan(seasonal_diff(np.arange(6.0), 2)[:2]).all()
assert np.allclose(per_step_score(np.array([[1.0, 3.0], [5.0, 7.0]]), 2, 3), [1.0, 4.0, 7.0])
print("seasonal difference and per-step score OK")

# %%
# driver (given): conv AE over one-day windows, trained on days 1-8
D = dl.DAY
rows = []
for name in ["nojump", "flatmiddle"]:
    _, te = dl.load_nab(name)
    v, lab = te.value.to_numpy(), te.y.to_numpy()
    x = (v - v[: 8 * D].mean()) / v[: 8 * D].std()
    cae = dl.fit_window_ae(dl.conv_ae(D, 1), dl.windows(x[: 8 * D], D), epochs=30, seed=0)
    scores = {"seasonal diff": seasonal_diff(x, D),
              "conv AE": per_step_score(dl.window_error(cae, dl.windows(x, D)), D, len(x))}  # fmt: skip
    for k, s in scores.items():
        t = np.nanmax(s[8 * D : 9 * D]) * 1.1
        rows.append({"series": name, "detector": k, **dl.series_report(np.nan_to_num(s), lab, t)})
print(pl.DataFrame(rows))

# %% [markdown]
# **Question C1.** Do both detectors find the anomalies? Where do the false alarms of the seasonal difference come
# from? **C2.** Why must the window cover a whole day?

# <<SOL
# %% [markdown]
# **Answers C.** Both find the two anomalies. The seasonal difference compares each step with the same step a day
# earlier, so the day *after* the anomaly is compared with the anomalous day and raises an "echo" of about 100 false
# alarms; the conv AE raises a few (typical runs: 1 to 35). The anomaly is "no rise today": it is only visible against
# the shape of a whole normal day, so a window shorter than a day sees a quiet stretch that looks normal (an LSTM AE
# over 8-hour windows misses it, notebook 05).
# SOL>>

# %% [markdown]
# ## Part D. The point-adjust trap
#
# Implement `point_adjust(pred, y)`: if **any** point of a segment of consecutive `y == 1` is predicted, set the whole
# segment to predicted. Then compare plain and point-adjusted F1 for a **random** score on Example 2 (the plant).

# %%
def point_adjust(pred, y):
    # <<TODO
    raise NotImplementedError
    # TODO>>
    # <<SOL
    out = pred.copy()
    i = 0
    while i < len(y):
        if y[i]:
            j = i
            while j < len(y) and y[j]:
                j += 1
            if pred[i:j].any():
                out[i:j] = True
            i = j
        else:
            i += 1
    return out
    # SOL>>


# %%
# check and driver (given)
assert point_adjust(np.array([0, 1, 0, 0, 0, 0], bool), np.array([1, 1, 1, 0, 1, 1])).tolist() == [1, 1, 1, 0, 0, 0]
_, ya, events = dl.plant(seed=1, attacks=True)
rng = np.random.default_rng(0)
for name, s in [("random score", rng.random(len(ya)))]:
    pred = s > np.quantile(rng.random(len(ya)), 0.995)
    print(f"{name}: F1 = {dl.f1(pred, ya):.3f}, point-adjusted F1 = {dl.f1(point_adjust(pred, ya), ya):.3f}")

# %% [markdown]
# **Question D1.** Why does a random score reach a high point-adjusted F1? Which metrics would you report instead?

# <<SOL
# %% [markdown]
# **Answers D.** The events are long (6 to 120 steps); a random detector at 0.5% alarms almost surely flags one point
# inside a long event, and point adjust then credits the whole event: F1 jumps from about 0.01 to about 0.7. Report
# point-wise precision, recall and AUPRC, events found with their delay, and false alarms outside events, always next
# to a random and a one-liner baseline.
# SOL>>
