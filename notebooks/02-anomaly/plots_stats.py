"""Figures of the statistics section of the class 03_01 slides (Example 1 and the distribution-based family)."""

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from plotlib import BLUE, COL, FULL, GOLD, GREEN, GREY, LIGHT, RED, ellipse, save, square_axes
from scipy import stats
from sklearn.svm import SVC

import anomlib as an

X = an.example1(500, 0)
A, B = an.EX1_POINTS["A"], an.EX1_POINTS["B"]
MU, COV = an.EX1_MU, an.EX1_COV
P = np.linalg.inv(COV)


def d2(x) -> float:
    return float((x - MU) @ P @ (x - MU))


def cloud(ax, n: int = 500) -> None:
    ax.scatter(X[:n, 0], X[:n, 1], s=3, color=GREY, alpha=0.55, lw=0, zorder=2)


def points_ab(ax, label: bool = True) -> None:
    ax.scatter(*A, s=22, color=RED, zorder=5)
    ax.scatter(*B, s=22, color=BLUE, marker="s", zorder=5)
    if label:
        ax.annotate("A", A, (A[0] - 0.1, A[1] + 0.35), color=RED, weight="bold", ha="center")
        ax.annotate("B", B, (B[0] + 0.45, B[1] - 0.15), color=BLUE, weight="bold", ha="center")


def kinds() -> None:
    rng = np.random.default_rng(1)
    fig, axs = plt.subplots(1, 3, figsize=(FULL, 1.15), gridspec_kw={"wspace": 0.28})
    c = rng.normal(0, 0.6, (70, 2))
    ax = axs[0]
    ax.scatter(c[:, 0], c[:, 1], s=5, color=GREY, alpha=0.7, lw=0)
    ax.scatter([2.6], [2.4], s=24, color=RED)
    ax.set(xlabel="upload (MB)", ylabel="duration", title="point", xticks=[], yticks=[])
    h = np.arange(72)
    y = 55 + 40 * np.sin(2 * np.pi * (h - 9) / 24) + rng.normal(0, 3, h.size)
    y[51] = 78
    ax = axs[1]
    ax.plot(h, y, color=GREY, lw=0.9)
    ax.axhline(78, color=RED, ls="--", lw=0.7)
    ax.scatter([51], [78], s=24, color=RED, zorder=5)
    ax.set(xlabel="hour", ylabel="logins per minute", title="contextual", xticks=[0, 24, 48, 72], yticks=[])
    t = np.arange(120)
    s = np.sin(2 * np.pi * t / 20) + rng.normal(0, 0.05, t.size)
    s[60:80] = 0.0
    ax = axs[2]
    ax.plot(t, s, color=GREY, lw=0.9)
    ax.plot(t[60:81], s[60:81], color=RED, lw=2)
    ax.set(xlabel="time", ylabel="sensor", title="collective", xticks=[], yticks=[])
    save(fig, "kinds")


def settings() -> None:
    """The same events with different labels: what each setting learns (a border, a region, a distorted region)."""
    rng = np.random.default_rng(4)
    c = rng.normal(0, 0.6, (60, 2))
    a = np.array([[2.3, 2.0], [2.6, 1.0], [-2.2, 2.3], [2.0, -2.2], [-2.5, -1.8], [0.3, 2.8], [-1.0, -2.6]])
    fig, axs = plt.subplots(1, 3, figsize=(FULL, 1.3), gridspec_kw={"wspace": 0.2})
    for ax in axs:
        ax.set(xlim=(-3.2, 3.2), ylim=(-3.2, 3.2), xticks=[], yticks=[], aspect="equal")
        ax.grid(False)
        for sp in ax.spines.values():
            sp.set_visible(True)
            sp.set_color(LIGHT)
    gx, gy = np.meshgrid(np.linspace(-3.2, 3.2, 200), np.linspace(-3.2, 3.2, 200))
    grid = np.c_[gx.ravel(), gy.ravel()]
    ax = axs[0]  # supervised: normal and attacks, both labelled; learn the border between them
    ax.scatter(c[:, 0], c[:, 1], s=7, color=BLUE, lw=0)
    ax.scatter(a[:, 0], a[:, 1], s=16, color=RED, marker="^", lw=0)
    clf = SVC(kernel="rbf", gamma=0.4, C=10).fit(np.r_[c, a], np.r_[np.zeros(len(c)), np.ones(len(a))])
    ax.contour(gx, gy, clf.decision_function(grid).reshape(gx.shape), levels=[0], colors=[GREEN], linewidths=1.3)
    ax.set_title("supervised", weight="bold")
    ax.set_xlabel("labelled normal + attacks:\nlearns the border", fontsize=7)
    ax = axs[1]  # semi-supervised: only normal events; learn the region of normal
    ax.scatter(c[:, 0], c[:, 1], s=7, color=BLUE, lw=0)
    mu, cov = c.mean(0), np.cov(c.T)
    ax.plot(*ellipse(mu, cov, 3.03).T, color=GREEN, lw=1.3)
    ax.set_title("semi-supervised", weight="bold")
    ax.set_xlabel("normal only:\nlearns what normal is", fontsize=7)
    ax = axs[2]  # unsupervised: unlabelled mix; attacks stretch the region of normal
    allx = np.r_[c, a]
    ax.scatter(allx[:, 0], allx[:, 1], s=7, color=LIGHT, lw=0)
    ax.plot(*ellipse(allx.mean(0), np.cov(allx.T), 2.0).T, color=GREEN, lw=1.3)
    ax.set_title("unsupervised", weight="bold")
    ax.set_xlabel("unlabelled, attacks inside:\nregion of normal stretched", fontsize=7)
    fig.legend(handles=[plt.Line2D([], [], marker="o", color=BLUE, ls="", ms=3.5, label="normal"),
                        plt.Line2D([], [], marker="^", color=RED, ls="", ms=4, label="attack"),
                        plt.Line2D([], [], marker="o", color=LIGHT, ls="", ms=3.5, label="unlabelled"),
                        plt.Line2D([], [], color=GREEN, lw=1.3, label="what the detector learns")],
               loc="lower center", ncol=4, bbox_to_anchor=(0.5, -0.16), fontsize=7, handletextpad=0.3, columnspacing=1.2)  # fmt: skip
    fig.subplots_adjust(bottom=0.36)
    save(fig, "settings")


def dist1d() -> None:
    x = np.linspace(-4, 4, 400)
    fig, ax = plt.subplots(figsize=(FULL, 1.1))
    ax.plot(x, stats.norm.pdf(x), color=BLUE, lw=1.5)
    m = x >= 2
    ax.fill_between(x[m], stats.norm.pdf(x[m]), color=RED, alpha=0.3, lw=0)
    ax.scatter([0.4, -0.7, 1.0, -0.1, 0.9, -1.5], np.zeros(6) + 0.008, s=9, color=GREY, zorder=4)
    ax.scatter([3.1], [0.008], s=22, color=RED, zorder=5)
    ax.annotate(
        "rare",
        (3.1, 0.02),
        (3.1, 0.12),
        color=RED,
        ha="center",
        arrowprops={"arrowstyle": "-", "color": RED, "lw": 0.6},
    )
    ax.text(2.35, 0.065, "$P=2.3\\%$", color=RED, ha="left")
    ax.text(0, 0.43, "normal values", color=BLUE, ha="center")
    ax.set(xlabel="feature value $x$", ylabel="density", yticks=[], xticks=[-2, 0, 2], xlim=(-4, 4), ylim=(0, 0.47))
    ax.grid(False)
    save(fig, "dist1d")


def ex1_data() -> None:
    fig, ax = plt.subplots(figsize=(COL, COL))
    cloud(ax)
    points_ab(ax)
    square_axes(ax)
    save(fig, "ex1_data")


def ex1_z() -> None:
    fig, ax = plt.subplots(figsize=(COL, COL))
    cloud(ax)
    ax.plot([-2, 2, 2, -2, -2], [-2, -2, 2, 2, -2], color=GOLD, ls="--", lw=1.3)
    points_ab(ax)
    ax.text(0, -3.1, "box: $|z_j|\\leq 2$ in both features", color=GOLD, ha="center", va="center", fontsize=8)
    square_axes(ax)
    save(fig, "ex1_z")


def ex1_ellipse() -> None:
    fig, ax = plt.subplots(figsize=(COL, COL))
    cloud(ax)
    ax.plot(*ellipse(MU, COV, 3.03).T, color=BLUE, lw=1.3)
    points_ab(ax)
    ax.text(-3.3, 3.2, "ellipse: 99% of normal sessions", color=BLUE, ha="left", va="top", fontsize=7)
    square_axes(ax)
    save(fig, "ex1_ellipse")


def ex1_levels() -> None:
    fig, ax = plt.subplots(figsize=(COL, COL))
    cloud(ax)
    ax.plot(*ellipse(MU, COV, d2(A) ** 0.5).T, color=RED, lw=1.3)
    ax.plot(*ellipse(MU, COV, d2(B) ** 0.5).T, color=BLUE, lw=1.3)
    ax.text(-3.3, 3.2, "red: ellipse through A", color=RED, ha="left", va="top", fontsize=7)
    ax.text(-3.3, 2.65, "blue: ellipse through B", color=BLUE, ha="left", va="top", fontsize=7)
    points_ab(ax)
    square_axes(ax)
    save(fig, "ex1_levels")
    print("d2 A, B:", round(d2(A), 2), round(d2(B), 2))


def threshold() -> None:
    s = np.array([d2(x) for x in X])
    fig, ax = plt.subplots(figsize=(FULL, 1.35))
    sns.histplot(s, bins=np.linspace(0, 16, 25), stat="density", color=LIGHT, edgecolor="white", linewidth=0.4, ax=ax)
    xx = np.linspace(0, 16, 200)
    ax.plot(xx, np.exp(-xx / 2) / 2, color=BLUE, lw=1.4, label="$\\chi^2_2$ density")
    for (a, q), col, y in zip(((0.05, 5.99), (0.01, 9.21), (0.001, 13.82)), (GOLD, RED, "#7B241C"), (0.30, 0.25, 0.20)):
        ax.axvline(q, color=col, ls="--", lw=1)
        ax.text(q + 0.2, y, f"$\\alpha={a}$", color=col, fontsize=8)
    ax.set(xlabel="score $d_M^2$ of 500 normal sessions", ylabel="density", yticks=[], xlim=(0, 16), ylim=(0, 0.5))
    ax.legend(loc="upper right")
    ax.grid(False)
    save(fig, "threshold")
    print("empirical quantiles:", [round(float(np.quantile(s, 1 - a)), 2) for a in (0.05, 0.01, 0.001)])


def baserate() -> None:
    b = np.logspace(-5, -1, 60)
    tpr = 0.95
    fig, ax = plt.subplots(figsize=(FULL, 1.0))
    for fpr, col in ((0.01, RED), (0.001, BLUE)):
        ax.plot(b, tpr * b / (tpr * b + fpr * (1 - b)), color=col, lw=1.5, label=f"FPR {fpr:.1%}".replace(".0%", "%"))
    ax.scatter([1e-4, 1e-4], [0.0094, 0.087], s=14, color="black", zorder=5)
    ax.set(xscale="log", xlabel="base rate $b$", ylabel="$P(\\mathrm{attack}\\mid\\mathrm{alarm})$", ylim=(0, 1))
    ax.legend(loc="upper left")
    save(fig, "baserate")


def mcd() -> None:
    """Notebook 00 part C: copies of a B-like session in the training rows; Ledoit-Wolf against MCD."""
    rng = np.random.default_rng(1)
    fr, lw, mc = [0.0, 0.05, 0.10, 0.20], [], []
    for frac in fr:
        k = int(frac * len(X))
        Xc = np.vstack([X, B * 1.5 + rng.normal(0, 0.2, (k, 2))])
        lw.append(float(an.Mahalanobis().fit(Xc).score(B[None])[0]))
        mc.append(float(an.Mahalanobis(robust=True).fit(Xc).score(B[None])[0]))
    pc = [100 * f for f in fr]
    fig, ax = plt.subplots(figsize=(FULL * 0.8, 1.35))
    ax.plot(pc, lw, color=RED, marker="o", ms=3.5, label="Ledoit-Wolf")
    ax.plot(pc, mc, color=BLUE, marker="s", ms=3.5, label="MCD")
    ax.axhline(9.21, color=GREY, ls="--", lw=0.8)
    ax.text(0.3, 10.3, "threshold $t=9.21$ (1% false alarms)", color=GREY, ha="left", fontsize=7)
    ax.set(xlabel="attacks mixed into the training rows (%)", ylabel="$d_M^2(B)$", xticks=pc, ylim=(0, 36))
    ax.legend(loc="upper right", ncol=2)
    save(fig, "mcd")
    print("mcd LW", np.round(lw, 1), "MCD", np.round(mc, 1))
