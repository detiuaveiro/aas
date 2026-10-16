"""Deep anomaly detectors of class 03_02 (Keras 3 on the JAX backend) and the time-series helpers.

Every detector follows the `anomlib.Detector` interface: fit on normal data, score = higher is more anomalous.
"""

import os

os.environ.setdefault("KERAS_BACKEND", "jax")  # before importing keras

import keras
import numpy as np
import pandas as pd

from anomlib import DATA, Detector


# ------------------------------------------------------------------------------------------------ dense autoencoders
def dense_ae(n_in: int, latent: int = 8, hidden: int = 32, l1: float = 0.0) -> keras.Model:
    """Encoder n_in -> hidden -> latent, decoder latent -> hidden -> n_in. `l1 > 0`: sparse AE (L1 on the code)."""
    reg = keras.regularizers.L1(l1) if l1 > 0 else None
    return keras.Sequential(
        [
            keras.layers.Input((n_in,)),
            keras.layers.Dense(hidden, activation="relu"),
            keras.layers.Dense(latent, activation="relu" if l1 > 0 else None, activity_regularizer=reg, name="code"),
            keras.layers.Dense(hidden, activation="relu"),
            keras.layers.Dense(n_in),
        ]
    )


class AE(Detector):
    """Reconstruction-error detector. `noise > 0`: denoising AE (Gaussian noise on the input during training only)."""

    def __init__(self, latent=8, hidden=32, l1=0.0, noise=0.0, epochs=20, seed=0, name=None):
        self.latent, self.hidden, self.l1, self.noise, self.epochs, self.seed = latent, hidden, l1, noise, epochs, seed
        self.name = name or ("sparse AE" if l1 else "denoising AE" if noise else "autoencoder")

    def fit(self, X):
        keras.utils.set_random_seed(self.seed)
        self.model = dense_ae(X.shape[1], self.latent, self.hidden, self.l1)
        self.model.compile(optimizer=keras.optimizers.Adam(1e-3), loss="mse")
        Xin = X + np.random.default_rng(self.seed).normal(0, self.noise, X.shape).astype(X.dtype) if self.noise else X
        self.history = self.model.fit(Xin, X, epochs=self.epochs, batch_size=256, validation_split=0.1, verbose=0)
        return self

    def score(self, X):
        return ((self.model.predict(X, batch_size=4096, verbose=0) - X) ** 2).mean(1)


# ------------------------------------------------------------------------------------------------ variational AE
class Sampling(keras.layers.Layer):
    """z = mu + sigma * eps; adds beta * KL(q(z|x) || N(0, I)) to the model loss."""

    def __init__(self, beta=1.0, seed=0, **kw):
        super().__init__(**kw)
        self.beta, self.gen = beta, keras.random.SeedGenerator(seed)

    def call(self, inputs, training=None):
        mu, logvar = inputs
        logvar = keras.ops.clip(logvar, -10.0, 10.0)  # exp(logvar) must not overflow
        kl = -0.5 * keras.ops.mean(keras.ops.sum(1 + logvar - mu**2 - keras.ops.exp(logvar), axis=1))
        self.add_loss(self.beta * kl)
        if not training:
            return mu
        return mu + keras.ops.exp(0.5 * logvar) * keras.random.normal(keras.ops.shape(mu), seed=self.gen)


class VAE(Detector):
    name = "variational AE"

    def __init__(self, latent=8, hidden=32, beta=1e-3, epochs=20, seed=0):
        self.latent, self.hidden, self.beta, self.epochs, self.seed = latent, hidden, beta, epochs, seed

    def fit(self, X):
        keras.utils.set_random_seed(self.seed)
        x = keras.layers.Input((X.shape[1],))
        h = keras.layers.Dense(self.hidden, activation="relu")(x)
        mu, logvar = keras.layers.Dense(self.latent)(h), keras.layers.Dense(self.latent)(h)
        z = Sampling(self.beta, self.seed)([mu, logvar])
        h2 = keras.layers.Dense(self.hidden, activation="relu")(z)
        self.model = keras.Model(x, keras.layers.Dense(X.shape[1])(h2))
        self.model.compile(optimizer=keras.optimizers.Adam(1e-3, clipnorm=1.0), loss="mse")
        self.history = self.model.fit(X, X, epochs=self.epochs, batch_size=256, validation_split=0.1, verbose=0)
        return self

    def score(self, X):
        return ((self.model.predict(X, batch_size=4096, verbose=0) - X) ** 2).mean(1)


# ------------------------------------------------------------------------------------------------ Deep SVDD
class DeepSVDD(Detector):
    """One-class deep model (Ruff et al. 2018): map normal data close to a centre c; score = ||phi(x) - c||^2.
    No biases and no bounded activations, otherwise phi(x) = c for every x is a trivial solution."""

    name = "Deep SVDD"

    def __init__(self, latent=16, hidden=64, epochs=20, seed=0):
        self.latent, self.hidden, self.epochs, self.seed = latent, hidden, epochs, seed

    def fit(self, X):
        keras.utils.set_random_seed(self.seed)
        self.phi = keras.Sequential(
            [
                keras.layers.Input((X.shape[1],)),
                keras.layers.Dense(self.hidden, activation="leaky_relu", use_bias=False),
                keras.layers.Dense(self.latent, use_bias=False),
            ]
        )
        self.c = self.phi.predict(X, batch_size=4096, verbose=0).mean(0)
        self.c[np.abs(self.c) < 0.1] = 0.1  # keep the centre away from 0 (as in the paper)
        self.phi.compile(optimizer=keras.optimizers.Adam(1e-3, weight_decay=1e-5), loss="mse")
        self.phi.fit(X, np.tile(self.c, (len(X), 1)), epochs=self.epochs, batch_size=256, verbose=0)
        return self

    def score(self, X):
        return ((self.phi.predict(X, batch_size=4096, verbose=0) - self.c) ** 2).sum(1)


# ------------------------------------------------------------------------------------------------ time series
# NAB label windows (numenta/NAB labels/combined_windows.json): a tolerance window around each true anomaly
NAB_WINDOWS = {
    "jumpsup": ("2014-04-10 16:15:00", "2014-04-12 01:45:00"),
    "jumpsdown": ("2014-04-10 16:15:00", "2014-04-12 01:45:00"),
    "nojump": ("2014-04-10 16:15:00", "2014-04-12 01:45:00"),
    "flatmiddle": ("2014-04-10 07:15:00", "2014-04-11 16:45:00"),
}
DAY = 288  # 5-minute samples per day


def load_nab(name: str = "jumpsup") -> tuple[pd.DataFrame, pd.DataFrame]:
    """NAB artificial series (5-minute samples, 14 days): `train` = art_daily_small_noise (no anomaly), `test` =
    art_daily_<name> with one anomaly; column `y` = 1 inside the NAB label window."""
    tr = pd.read_csv(DATA / "art_daily_small_noise.csv", parse_dates=["timestamp"])
    te = pd.read_csv(DATA / f"art_daily_{name}.csv", parse_dates=["timestamp"])
    te["y"] = te["timestamp"].between(*map(pd.Timestamp, NAB_WINDOWS[name])).astype(int)
    return tr, te


def series_report(s: np.ndarray, y: np.ndarray, t: float) -> dict[str, float]:
    """NAB-style reading of one series at threshold t: found (an alarm inside the window), delay (steps from the
    window start to the first alarm inside it) and false alarms (alarms outside the window)."""
    pred = s > t
    inside = np.flatnonzero(pred & (y == 1))
    return {"found": float(len(inside) > 0), "delay": float(inside[0] - np.flatnonzero(y)[0]) if len(inside) else np.nan,
            "false_alarms": float((pred & (y == 0)).sum())}  # fmt: skip


def windows(x: np.ndarray, w: int) -> np.ndarray:
    """Sliding windows (stride 1): (T, d) -> (T - w + 1, w, d); a 1-D series becomes d = 1."""
    x = x.reshape(len(x), -1)
    return np.lib.stride_tricks.sliding_window_view(x, w, axis=0).transpose(0, 2, 1).astype(np.float32)


def window_to_point(err_w: np.ndarray, w: int, T: int) -> np.ndarray:
    """Score of time step t = mean over the windows that contain t of the squared error *at t*
    (`err_w` is (N, w) per-step errors; a (N,) window error is spread over the whole window instead)."""
    s, n = np.zeros(T), np.zeros(T)
    for i, e in enumerate(err_w):
        s[i : i + w] += e
        n[i : i + w] += 1
    return s / np.maximum(n, 1)


def conv_ae(w: int, d: int, filters: int = 32) -> keras.Model:
    """1-D convolutional AE over windows (w time steps x d channels); w must be divisible by 4."""
    return keras.Sequential(
        [
            keras.layers.Input((w, d)),
            keras.layers.Conv1D(filters, 7, padding="same", strides=2, activation="relu"),
            keras.layers.Conv1D(filters // 2, 7, padding="same", strides=2, activation="relu"),
            keras.layers.Conv1DTranspose(filters // 2, 7, padding="same", strides=2, activation="relu"),
            keras.layers.Conv1DTranspose(filters, 7, padding="same", strides=2, activation="relu"),
            keras.layers.Conv1D(d, 7, padding="same"),
        ]
    )


def lstm_ae(w: int, d: int, units: int = 32) -> keras.Model:
    """LSTM encoder -> code repeated w times -> LSTM decoder."""
    return keras.Sequential(
        [
            keras.layers.Input((w, d)),
            keras.layers.LSTM(units),
            keras.layers.RepeatVector(w),
            keras.layers.LSTM(units, return_sequences=True),
            keras.layers.TimeDistributed(keras.layers.Dense(d)),
        ]
    )


def fit_window_ae(model: keras.Model, W: np.ndarray, epochs: int = 30, seed: int = 0) -> keras.Model:
    keras.utils.set_random_seed(seed)
    model.compile(optimizer=keras.optimizers.Adam(1e-3), loss="mse")
    model.fit(W, W, epochs=epochs, batch_size=128, validation_split=0.1, verbose=0,
              callbacks=[keras.callbacks.EarlyStopping(patience=5, restore_best_weights=True)])  # fmt: skip
    return model


def window_error(model: keras.Model, W: np.ndarray, per_step: bool = True) -> np.ndarray:
    """Squared reconstruction error per window and time step (N, w), averaged over channels; per_step=False: (N,)."""
    e = ((model.predict(W, batch_size=1024, verbose=0) - W) ** 2).mean(axis=2)
    return e if per_step else e.mean(1)


# ------------------------------------------------------------------------------------------------ Example 2: a plant
SENSORS = ["flow_in", "level", "pump", "valve", "flow_out", "temp_a", "temp_b", "pressure"]


def plant(T: int = 6 * DAY, seed: int = 0, attacks: bool = False) -> tuple[np.ndarray, np.ndarray, list[dict]]:
    """Example 2: 8 sensors of a small water plant driven by two hidden processes (demand: daily cycle, heat: slow
    random walk). Each sensor = its own mix of the two + noise, so sensors are correlated in *space* (each other) and
    in *time* (the cycle). With `attacks=True` the second half carries three events:
    spike (one sensor jumps), freeze (a sensor repeats a stale normal value: in range, but decoupled from the others),
    drift (a slow ramp on one sensor). Returns (X (T, 8), y (T,), events)."""
    rng = np.random.default_rng(seed)
    t = np.arange(T)
    demand = np.sin(2 * np.pi * t / DAY) + 0.3 * np.sin(4 * np.pi * t / DAY + 1)
    heat = np.cumsum(rng.normal(0, 0.02, T))
    heat -= np.convolve(heat, np.ones(DAY) / DAY, mode="same")  # keep it bounded
    mix = np.array([[1.0, 0.0], [0.8, 0.1], [0.9, 0.0], [-0.7, 0.0], [0.6, 0.3], [0.2, 1.0], [0.1, 0.9], [0.7, 0.5]])
    X = np.c_[demand, heat] @ mix.T + rng.normal(0, 0.08, (T, len(SENSORS)))
    y = np.zeros(T, dtype=int)
    events: list[dict] = []
    if attacks:
        start = T // 2
        ev = [("spike", 1, start + 60, 6), ("freeze", 3, start + DAY // 2, 72), ("drift", 7, start + 2 * DAY, 120)]
        for kind, s, a, n in ev:
            if kind == "spike":
                X[a : a + n, s] += 1.2
            elif kind == "freeze":
                X[a : a + n, s] = X[a - 1, s] + rng.normal(0, 0.08, n)  # stale value, still normal-looking
            else:
                X[a : a + n, s] += np.linspace(0, 0.9, n)
            y[a : a + n] = 1
            events.append({"kind": kind, "sensor": SENSORS[s], "start": a, "length": n})
    return X.astype(np.float32), y, events


# ------------------------------------------------------------------------------------------------ evaluation of series
def point_adjust(pred: np.ndarray, y: np.ndarray) -> np.ndarray:
    """The 'point-adjust' protocol: if any point of an anomalous segment is flagged, the whole segment counts as found.
    Shown to make even random scores look good (Kim et al. 2022); used here only to show the inflation."""
    out = pred.copy()
    i = 0
    while i < len(y):
        if y[i]:
            j = i
            while j < len(y) and y[j]:
                j += 1
            if pred[i:j].any():
                out[i:j] = 1
            i = j
        else:
            i += 1
    return out


def f1(pred: np.ndarray, y: np.ndarray) -> float:
    tp, fp, fn = int((pred & (y == 1)).sum()), int((pred & (y == 0)).sum()), int((~pred.astype(bool) & (y == 1)).sum())
    return 2 * tp / (2 * tp + fp + fn) if tp else 0.0


def events_found(pred: np.ndarray, events: list[dict]) -> dict[str, bool]:
    return {e["kind"]: bool(pred[e["start"] : e["start"] + e["length"]].any()) for e in events}
