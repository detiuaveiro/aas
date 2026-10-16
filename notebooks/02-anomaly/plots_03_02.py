"""Illustration figures of the class 03_02 slides that no demo notebook draws (toy data) ->
assets/figures/plots/03/*.pdf

    python plots_03_02.py            # every illustration
    python plots_03_02.py ae_vs_pca  # only these (names = function names)

The result plots (deep detectors, code size, explanations, NAB, water plant) are stored by the demo notebooks 04-06
with one line each (`plots_deep.<name>(...)`): run the demos to refresh them.
"""

import sys

import matplotlib.pyplot as plt
import numpy as np
from plotlib import BLUE, COL, GREY, RED, save
from sklearn.decomposition import PCA
from sklearn.neural_network import MLPRegressor


def ae_vs_pca() -> None:
    """Toy data on a curved one-dimensional structure: a linear code (PCA, 1 unit) against an AE with a 1-unit code."""
    rng = np.random.default_rng(0)
    t = rng.uniform(-1.3, 1.3, 400)
    X = np.c_[t, 0.9 * t**2 - 0.4] + rng.normal(0, 0.04, (400, 2))
    pc = PCA(1).fit(X)
    lin = pc.inverse_transform(pc.transform(X))
    ae = MLPRegressor(hidden_layer_sizes=(16, 1, 16), activation="tanh", max_iter=4000, random_state=0, tol=1e-6).fit(
        X, X
    )
    rec = ae.predict(X)
    e_lin, e_ae = float(((X - lin) ** 2).sum(1).mean()), float(((X - rec) ** 2).sum(1).mean())
    f, axs = plt.subplots(1, 2, figsize=(COL * 2 + 0.1, 1.9), sharey=True, gridspec_kw={"wspace": 0.08})
    for ax, r, col, name, e in (
        (axs[0], lin, BLUE, "linear code: PCA", e_lin),
        (axs[1], rec, RED, "AE: code of 1 unit, tanh layers", e_ae),
    ):
        ax.scatter(X[:, 0], X[:, 1], s=3, color=GREY, alpha=0.5, lw=0)
        o = np.argsort(r[:, 0])
        ax.plot(r[o, 0], r[o, 1], color=col, lw=1.8)
        ax.set(title=name, xticks=[], yticks=[], aspect="equal")
        ax.set_xlabel(f"mean squared error {e:.3f}", fontsize=7)
        ax.grid(False)
    save(f, "ae_vs_pca")
    print("ae_vs_pca mse: PCA", round(e_lin, 4), "AE", round(e_ae, 4))


FIGURES = [ae_vs_pca]

if __name__ == "__main__":
    import plotlib

    plotlib.setup()
    want = set(sys.argv[1:])
    for fn in FIGURES:
        if not want or fn.__name__ in want:
            fn()
