"""One figure per detector family of the class 03_01 slides (distance, isolation, boundary, reconstruction, clusters)."""

import matplotlib.pyplot as plt
import numpy as np
from plotlib import BLUE, COL, FULL, GOLD, GREEN, GREY, LIGHT, RED, circle, ellipse, save, square_axes
from plots_stats import A, B, X, cloud, points_ab
from pynnmf import nmf_hals
from sklearn.cluster import DBSCAN, KMeans
from sklearn.decomposition import PCA, FastICA
from sklearn.mixture import GaussianMixture
from sklearn.neighbors import LocalOutlierFactor, NearestNeighbors
from sklearn.svm import OneClassSVM


def knn() -> None:
    nn = NearestNeighbors(n_neighbors=5).fit(X)
    fig, ax = plt.subplots(figsize=(COL, COL))
    cloud(ax)
    for name, q, col in (("N", np.array([0.3, 0.5]), GREEN), ("A", A, RED), ("B", B, BLUE)):
        d, idx = nn.kneighbors(q[None])
        r = float(d[0, -1])
        ax.plot(*circle(q, r).T, color=col, lw=1.2)
        ax.scatter(X[idx[0], 0], X[idx[0], 1], s=7, color=col, zorder=4)
        ax.scatter(*q, s=22, color=col, zorder=5, marker="s" if name == "B" else "o")
        tx = {"N": (-3.3, 2.6), "A": (1.9, 3.2), "B": (1.6, -3.2)}[name]
        ax.annotate(
            f"{name}: {r:.2f}",
            q,
            tx,
            color=col,
            fontsize=7,
            weight="bold",
            ha="left",
            va="center",
            arrowprops={"arrowstyle": "-", "color": col, "lw": 0.6},
            bbox={"fc": "white", "ec": "none", "alpha": 0.8, "pad": 1},
        )
        print("kNN", name, round(r, 2))
    square_axes(ax)
    save(fig, "knn")


def lof_toy(seed: int = 3):
    rng = np.random.default_rng(seed)
    return np.r_[rng.normal([-2.4, 0], 0.22, (60, 2)), rng.normal([2.2, 0], 0.9, (60, 2))]


def lof() -> None:
    Xt = lof_toy()
    nn = NearestNeighbors(n_neighbors=5).fit(Xt)
    model = LocalOutlierFactor(n_neighbors=5, novelty=True).fit(Xt)
    P = np.array([-1.35, 0.35])
    rp = float(nn.kneighbors(P[None])[0][0, -1])
    cand = [
        (abs(float(nn.kneighbors(np.array([[x, y]]))[0][0, -1]) - rp), x, y)
        for x in np.linspace(1.5, 4.5, 31)
        for y in np.linspace(-2.5, 2.5, 41)
    ]
    Q = np.array(min(cand)[1:])
    fig, ax = plt.subplots(figsize=(FULL, 1.4))
    ax.scatter(Xt[:, 0], Xt[:, 1], s=5, color=GREY, alpha=0.7, lw=0)
    for name, q, col in (("P", P, RED), ("Q", Q, BLUE)):
        r = float(nn.kneighbors(q[None])[0][0, -1])
        lo = float(-model.score_samples(q[None])[0])
        ax.plot(*circle(q, r).T, color=col, lw=1.2)
        ax.scatter(*q, s=22, color=col, zorder=5)
        ax.annotate(f"{name}: LOF {lo:.1f}", q, (q[0], q[1] - r - 0.5), color=col, ha="center", weight="bold")
        print("LOF", name, "kNN", round(r, 2), "LOF", round(lo, 2))
    ax.text(-2.4, 0.9, "dense", color=GREY, ha="center")
    ax.text(2.2, 2.2, "sparse", color=GREY, ha="center")
    ax.set(xlim=(-4, 5), ylim=(-3.2, 3), aspect="equal", xticks=[], yticks=[])
    ax.grid(False)
    save(fig, "lof")


def lof_flood() -> None:
    rng = np.random.default_rng(0)  # notebook 00 part D: 60 near-identical events
    flood = np.array([3.0, -0.5]) + rng.normal(0, 0.02, (60, 2))
    fig, ax = plt.subplots(figsize=(COL, COL))
    cloud(ax)
    ax.scatter(flood[:, 0], flood[:, 1], s=7, color=RED, zorder=4)
    ax.annotate(
        "60 identical events",
        (3.0, -0.5),
        (0.6, -2.7),
        color=RED,
        fontsize=7,
        arrowprops={"arrowstyle": "-", "color": RED, "lw": 0.6},
    )
    square_axes(ax)
    save(fig, "lof_flood")


def isolate(Xs, target, rng, lo, hi):
    """Random isolation tree path of one point: the cuts (axis, value, cell lo, cell hi)."""
    cuts, idx = [], np.arange(len(Xs))
    lo, hi = lo.copy(), hi.copy()
    while len(idx) > 1:
        side = Xs[idx]
        a = rng.integers(2)
        cut = rng.uniform(side[:, a].min(), side[:, a].max())
        cuts.append((a, cut, lo.copy(), hi.copy()))
        keep = (Xs[:, a] <= cut) == (target[a] <= cut)
        idx = idx[keep[idx]]
        if target[a] <= cut:
            hi[a] = cut
        else:
            lo[a] = cut
    return cuts


def iso_cuts() -> None:
    rng = np.random.default_rng(5)
    Xs = np.r_[rng.normal(0, 0.8, (40, 2)), [[3.4, 2.7]]]
    lo, hi = Xs.min(0) - 0.2, Xs.max(0) + 0.2
    fig, axs = plt.subplots(1, 2, figsize=(FULL, 1.55), gridspec_kw={"wspace": 0.1})
    for k, (name, target, ok) in enumerate(
        (("anomaly", Xs[-1], lambda n: n <= 4), ("normal point", Xs[3], lambda n: n >= 9))
    ):
        for s in range(200):
            cuts = isolate(Xs, target, np.random.default_rng(s), lo, hi)
            if ok(len(cuts)):
                break
        ax = axs[k]
        ax.scatter(Xs[:-1, 0], Xs[:-1, 1], s=6, color=GREY, lw=0)
        ax.scatter(*Xs[-1], s=24, color=RED, zorder=5)
        if k:
            ax.scatter(*target, s=24, color=BLUE, marker="s", zorder=5)
        for a, cut, cl, ch in cuts:
            ax.plot(
                [cut, cut] if a == 0 else [cl[0], ch[0]], [cl[1], ch[1]] if a == 0 else [cut, cut], color=GOLD, lw=1
            )
        ax.set(xlim=(lo[0], hi[0]), ylim=(lo[1], hi[1]), xticks=[], yticks=[], title=f"{name}: {len(cuts)} cuts")
        ax.grid(False)
        print("iso", name, len(cuts))
    save(fig, "iso_cuts")


def iso_axis() -> None:
    w = 0.15
    fig, ax = plt.subplots(figsize=(COL, COL))
    ax.axvspan(B[0] - w, B[0] + w, color=GOLD, alpha=0.25, lw=0)
    ax.axhspan(B[1] - w, B[1] + w, color=GOLD, alpha=0.25, lw=0)
    cloud(ax)
    points_ab(ax)
    square_axes(ax)
    save(fig, "iso_axis")
    print("strips:", int((abs(X[:, 0] - B[0]) < w).sum()), int((abs(X[:, 1] - B[1]) < w).sum()))


def ocsvm() -> None:
    m = OneClassSVM(nu=0.05, gamma="scale").fit(X)
    g = np.linspace(-3.5, 3.5, 200)
    gx, gy = np.meshgrid(g, g)
    z = m.decision_function(np.c_[gx.ravel(), gy.ravel()]).reshape(gx.shape)
    out = m.decision_function(X) < 0
    fig, ax = plt.subplots(figsize=(COL, COL))
    ax.scatter(X[~out, 0], X[~out, 1], s=3, color=GREY, alpha=0.55, lw=0)
    ax.scatter(X[out, 0], X[out, 1], s=6, color=RED, lw=0, zorder=4)
    ax.contour(gx, gy, z, levels=[0], colors=[BLUE], linewidths=1.4)
    points_ab(ax)
    square_axes(ax)
    save(fig, "ocsvm")
    print(
        "ocsvm outside",
        int(out.sum()),
        "A",
        m.decision_function(A[None]).round(2),
        "B",
        m.decision_function(B[None]).round(2),
    )


def pca() -> None:
    p = PCA(1).fit(X)
    v = p.components_[0]
    fig, ax = plt.subplots(figsize=(COL, COL))
    cloud(ax)
    t = np.array([-3.4, 3.4])[:, None] * v + p.mean_
    ax.plot(t[:, 0], t[:, 1], color=BLUE, lw=1.4)
    for q, col in ((A, RED), (B, BLUE)):
        f = p.mean_ + ((q - p.mean_) @ v) * v
        ax.plot([q[0], f[0]], [q[1], f[1]], color=col, ls="--", lw=1.3)
        ax.scatter(*f, s=14, facecolors="none", edgecolors=col, zorder=4)
        print("residual", round(float(np.sum((q - f) ** 2)), 2))
    points_ab(ax)
    ax.text(-3.3, 3.0, "first direction", color=BLUE, fontsize=7)
    square_axes(ax)
    save(fig, "pca")


def bss_toy() -> None:
    """Three decompositions of the same non-Gaussian, non-negative data: PCA axes, ICA directions, NMF parts."""
    rng = np.random.default_rng(2)
    S = rng.uniform(0, 1, (400, 2))
    M = np.array([[1.0, 0.25], [0.35, 0.9]])  # true mixing: rows are the two parts
    Xm = S @ M
    pc = PCA(2).fit(Xm)
    ic = FastICA(2, whiten="unit-variance", random_state=0, max_iter=1000).fit(Xm)
    _, _, h, _ = nmf_hals(Xm, 2, n=300, seed=0, init="nndsvd")
    mean = Xm.mean(0)
    panels = (("PCA", [(mean, c * np.sqrt(ev) * 2) for c, ev in zip(pc.components_, pc.explained_variance_)]),
              ("ICA", [(mean, c / np.linalg.norm(c) * 0.6) for c in ic.mixing_.T]),
              ("NMF", [(np.zeros(2), r / np.linalg.norm(r) * 1.1) for r in h]))  # fmt: skip
    fig, axs = plt.subplots(1, 3, figsize=(FULL, 1.5), gridspec_kw={"wspace": 0.15})
    caps = (
        "orthogonal axes,\nmost variance first",
        "independent sources,\nnon-orthogonal directions",
        "non-negative parts\nthat add up",
    )
    for ax, (title, vecs), caption in zip(axs, panels, caps):
        ax.scatter(Xm[:, 0], Xm[:, 1], s=3, color=LIGHT, lw=0)
        for (o, v), col in zip(vecs, (BLUE, RED)):
            ax.annotate("", o + v, o, arrowprops={"arrowstyle": "-|>", "color": col, "lw": 1.5})
        ax.set(xlim=(-0.15, 1.5), ylim=(-0.15, 1.5), aspect="equal", xticks=[], yticks=[], title=title)
        ax.set_xlabel(caption, fontsize=7)
        ax.title.set_weight("bold")
        ax.grid(False)
    save(fig, "bss_toy")


def toy_profiles(seed: int = 2):
    rng = np.random.default_rng(seed)
    cen = np.array([[-2.6, 1.6], [2.6, 1.8], [0.0, -2.3]])
    return np.concatenate([rng.normal(c, 0.55, (70, 2)) for c in cen])


def kmeans_gmm() -> None:
    Xp = toy_profiles()
    far, between = np.array([4.0, -2.8]), np.array([0.1, 1.0])
    km = KMeans(3, n_init=10, random_state=0).fit(Xp)
    gm = GaussianMixture(3, random_state=0).fit(Xp)
    fig, axs = plt.subplots(1, 2, figsize=(FULL, 1.7), gridspec_kw={"wspace": 0.08})
    for ax in axs:
        ax.scatter(Xp[:, 0], Xp[:, 1], s=4, color=GREY, alpha=0.7, lw=0)
        ax.scatter(*far, s=22, color=RED, zorder=5)
        ax.scatter(*between, s=22, color=RED, zorder=5)
        ax.set(xlim=(-4.5, 5), ylim=(-4, 3.5), aspect="equal", xticks=[], yticks=[])
        ax.grid(False)
    ax = axs[0]
    ax.set_title("k-means")
    ax.title.set_fontsize(7.5)
    ax.scatter(km.cluster_centers_[:, 0], km.cluster_centers_[:, 1], marker="x", s=40, color=BLUE, lw=2, zorder=5)
    for q in (far, between):
        c = km.cluster_centers_[km.predict(q[None])[0]]
        ax.plot([q[0], c[0]], [q[1], c[1]], color=RED, ls="--", lw=1)
        print("kmeans dist", round(float(np.linalg.norm(q - c)), 2))
    ax = axs[1]
    ax.set_title("Gaussian mixture")
    ax.title.set_fontsize(7.5)
    for mu, cov in zip(gm.means_, gm.covariances_):
        ax.plot(*ellipse(mu, cov, 3.03).T, color=BLUE, lw=1.2)
    print(
        "gmm -log p",
        (-gm.score_samples(np.array([far, between]))).round(1),
        "typical",
        np.median(-gm.score_samples(Xp)).round(1),
    )
    save(fig, "kmeans_gmm")


def dbscan() -> None:
    Xp = toy_profiles()
    noise = np.random.default_rng(9).uniform([-4, -3.5], [4.5, 3.2], (7, 2))
    Z = np.r_[Xp, noise]
    lab = DBSCAN(eps=0.6, min_samples=6).fit_predict(Z)
    fig, ax = plt.subplots(figsize=(COL, COL))
    for k, (col, mk) in enumerate(((BLUE, "o"), (GREEN, "s"), (GOLD, "^"))):
        ax.scatter(Z[lab == k, 0], Z[lab == k, 1], s=6, color=col, marker=mk, lw=0)
    ax.scatter(Z[lab == -1, 0], Z[lab == -1, 1], s=26, color=RED, marker="x", lw=1.6, zorder=5)
    ax.plot(*circle(Z[lab == -1][0], 0.6).T, color=RED, ls="--", lw=1)
    ax.set(xlim=(-4.5, 5), ylim=(-4, 3.5), aspect="equal", xticks=[], yticks=[])
    ax.grid(False)
    save(fig, "dbscan")
    print("dbscan noise", int((lab == -1).sum()), "clusters", sorted(set(lab.tolist())))
