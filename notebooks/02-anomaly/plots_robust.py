"""Slide plots of the class 03_03 results (evasion, poisoning, defences). Pure drawing: the demo notebooks 07-09
compute the numbers and call these functions with their own rows, one line each; the PDFs go to
`assets/figures/plots/03/`. Rows are lists of dicts (`polars.DataFrame.to_dicts()`)."""

import numpy as np
from plotlib import BLUE, GOLD, GREEN, GREY, LIGHT, RED, ellipse, fig, save, square_axes, styled

import anomlib as an

B = an.EX1_POINTS["B"]
SHORT = {
    "GMM (-log-likelihood)": "GMM",
    "PCA reconstruction": "PCA recon.",
    "kNN distance": "kNN",
    "Deep SVDD": "Deep SVDD",
}


def short(name: str) -> str:
    return SHORT.get(name, name)


@styled
def evasion_price(threshold: float, x2: float = -1.0) -> None:
    """Example 1: sessions on the line x2 = const that pass the Mahalanobis detector (d^2 <= threshold)."""
    X = an.example1(500, 0)
    c = x2**2 - 0.19 * threshold
    lo, hi = np.roots([1.0, -1.8 * x2, c])
    lo, hi = min(lo, hi), max(lo, hi)
    f, ax = fig("col", 2.1)
    ax.scatter(X[:, 0], X[:, 1], s=3, color=GREY, alpha=0.5, lw=0)
    ax.plot(*ellipse(an.EX1_MU, an.EX1_COV, threshold**0.5).T, color=BLUE, lw=1.3)
    ax.axhline(x2, color=LIGHT, lw=0.8)
    ax.plot([lo, hi], [x2, x2], color=GREEN, lw=3, solid_capstyle="butt")
    ax.scatter(*B, s=26, color=RED, marker="s", zorder=5)
    ax.annotate(
        "B: caught",
        B,
        (0.4, -3.05),
        color=RED,
        fontsize=8,
        ha="center",
        arrowprops={"arrowstyle": "-", "color": RED, "lw": 0.6},
    )
    ax.text(-3.3, 3.2, f"green: passes ($x_1\\leq{hi:.2f}$)", color=GREEN, fontsize=8, ha="left", va="top")
    square_axes(ax)
    save(f, "evasion_price")


@styled
def mimicry(rows) -> None:
    """rows: dicts with detector, caught, `evasion (mutable only)`; two panels: share caught, share that evades after mimicry."""
    keep = ["Mahalanobis", "PCA reconstruction", "autoencoder", "GMM (-log-likelihood)", "Deep SVDD"]
    d = {r["detector"]: r for r in rows}
    f, axs = fig("full", 1.15, ncols=2, sharey=True, gridspec_kw={"wspace": 0.08})
    ys = np.arange(len(keep))[::-1]
    for ax, key, col, title in (
        (axs[0], "caught", BLUE, "attacks caught"),
        (axs[1], "evasion (mutable only)", RED, "evade after mimicry (share of the caught)"),
    ):
        v = [d[k][key] for k in keep]
        ax.barh(ys, v, color=col, height=0.6)
        for y, val in zip(ys, v):
            ax.text(val + 0.01, y, f"{val:.3f}" if val < 0.2 else f"{val:.2f}", va="center", fontsize=7)
        ax.set(title=title, xlim=(0, 1.0 if key == "caught" else 0.3))
        ax.title.set_fontsize(7.5)
        ax.grid(axis="y", visible=False)
    axs[0].set_yticks(ys, [short(k) for k in keep])
    save(f, "mimicry")


@styled
def blackbox(rows) -> None:
    """rows: dicts with detector, budget, evasion; `(all features)` rows are the unconstrained search at 1,000 queries."""
    keep = {"Mahalanobis": BLUE, "PCA reconstruction": GREEN, "autoencoder": GOLD, "One-class SVM": GREY}
    f, ax = fig("full", 1.25)
    for name, col in keep.items():
        pts = sorted((r["budget"], r["evasion"]) for r in rows if r["detector"] == name)
        ax.plot(*zip(*pts), color=col, marker="o", ms=3.5, label=short(name))
        free = [r["evasion"] for r in rows if r["detector"] == f"{name} (all features)"]
        if free:
            ax.scatter([1000], free, marker="*", s=40, color=col, zorder=5)
    ax.annotate(
        "stars: all features free",
        (1000, 0.3),
        (60, 0.27),
        fontsize=7,
        color=GREY,
        arrowprops={"arrowstyle": "-", "color": GREY, "lw": 0.6},
    )
    ax.set(
        xscale="log",
        xlabel="queries per attack row",
        ylabel="share that evades",
        xticks=[50, 200, 1000],
        ylim=(-0.01, 0.34),
    )
    ax.set_xticklabels(["50", "200", "1,000"])
    ax.legend(loc="center left", bbox_to_anchor=(1.0, 0.5))
    save(f, "blackbox")


@styled
def boiling_frog(logs: dict) -> None:
    """logs: {detector: [dict(round, target_ratio), ...]}; the target is accepted below the threshold line."""
    f, ax = fig("full", 1.3)
    for (name, log), col, mk in zip(logs.items(), (BLUE, RED), "os"):
        ax.plot([r["round"] for r in log], [r["target_ratio"] for r in log], color=col, marker=mk, ms=3, label=name)
    ax.axhline(1, color=GREY, ls="--", lw=1)
    ax.text(20, 1.3, "below: the target is accepted", color=GREY, fontsize=7, ha="right")
    ax.set(yscale="log", xlabel="poisoning round (25 points each)", ylabel="score(target) / threshold")
    ax.legend(loc="lower left")
    save(f, "boiling_frog")


@styled
def slow_drift(rows) -> None:
    """rows: dicts with `drift (sd/day)`, `per-point: median hours`, `CUSUM: median hours`, `per-point: missed (of 5)`."""
    x = np.arange(len(rows))
    f, ax = fig("full", 1.25)
    pp = [r["per-point: median hours"] for r in rows]
    cu = [r["CUSUM: median hours"] for r in rows]
    for off, v, col, lab in ((-0.19, pp, BLUE, "per-point threshold"), (0.19, cu, RED, "CUSUM")):
        bars = ax.bar(
            x + off, np.array(v) - 1, 0.36, bottom=1, color=col, label=lab, lw=0
        )  # log axis: bars grow from 1
        for b, val in zip(bars, v):
            ax.text(b.get_x() + b.get_width() / 2, val * 1.08, f"{val:.1f}", ha="center", fontsize=7)
    for xi, r in zip(x, rows):
        if r["per-point: missed (of 5)"]:
            ax.text(
                xi - 0.19, 1.2, f"{r['per-point: missed (of 5)']} of 5\nnever", ha="center", fontsize=6, color="white"
            )
    ax.set_xticks(x, [f"{r['drift (sd/day)']:g}" for r in rows])
    ax.set(
        yscale="log",
        xlabel="drift of the pressure sensor (standard deviations per day)",
        ylabel="hours to alarm (median)",
        ylim=(1, 160),
    )
    ax.legend(loc="upper right")
    ax.grid(axis="x", visible=False)
    save(f, "slow_drift")


@styled
def ensembles(rows) -> None:
    """rows: dicts with detector, AUPRC, `mimicry evasion`; two panels: clean AUPRC and evasion after mimicry."""
    keep = ["Mahalanobis", "GMM (-log-likelihood)", "Deep SVDD", "rank-mean ensemble", "OR ensemble"]
    d = {r["detector"]: r for r in rows}
    f, axs = fig("full", 1.2, ncols=2, sharey=True, gridspec_kw={"wspace": 0.08})
    ys = np.arange(len(keep))[::-1]
    for ax, key, col, title, hi in (
        (axs[0], "AUPRC", BLUE, "clean AUPRC", 0.85),
        (axs[1], "mimicry evasion", RED, "evasion after mimicry", 0.2),
    ):
        v = [d[k][key] for k in keep]
        ax.barh(ys, v, color=[GREEN if "ensemble" in k else col for k in keep], height=0.6)
        for y, val in zip(ys, v):
            ax.text(val + 0.01, y, f"{val:.3f}", va="center", fontsize=7)
        ax.set(title=title, xlim=(0, hi))
        ax.title.set_fontsize(7.5)
        ax.grid(axis="y", visible=False)
    axs[0].set_yticks(ys, [short(k) for k in keep])
    save(f, "ensembles")


@styled
def robust_features(rows) -> None:
    """rows: assess() rows named `<detector> (all features)` and `<detector> (fixed features)` with recall and mimicry evasion."""
    dets = list(dict.fromkeys(r["detector"].rsplit(" (", 1)[0] for r in rows))
    d = {r["detector"]: r for r in rows}
    f, ax = fig("full", 1.3)
    x = np.arange(len(dets))
    for off, tag, col, lab in (
        (-0.19, "all features", BLUE, "all 71 features"),
        (0.19, "fixed features", GREEN, "64 fixed features"),
    ):
        v = [d[f"{k} ({tag})"]["recall"] for k in dets]
        bars = ax.bar(x + off, v, 0.36, color=col, label=lab, lw=0)
        for b, val in zip(bars, v):
            ax.text(b.get_x() + b.get_width() / 2, val + 0.02, f"{val:.2f}", ha="center", fontsize=7)
    ax.set_xticks(x, [f"{short(k)}\nevasion {d[f'{k} (all features)']['mimicry evasion']:.3f}→0" for k in dets])
    ax.set(ylabel="recall at 1% false alarms", ylim=(0, 1.15))
    ax.legend(loc="upper center", ncol=2, bbox_to_anchor=(0.5, 1.25))
    ax.grid(axis="x", visible=False)
    save(f, "robust_features")


@styled
def vetting(plain, vetted) -> None:
    """Lists of score(target) / threshold per round: without and with vetted retraining (Example 1, 20 rounds)."""
    f, ax = fig("full", 1.3)
    ax.plot(range(len(plain)), plain, color=RED, marker="s", ms=3, label="retrain on everything")
    ax.plot(range(len(vetted)), vetted, color=GREEN, marker="o", ms=3, label="retrain on vetted points")
    ax.axhline(1, color=GREY, ls="--", lw=1)
    ax.text(20, 1.3, "below: the target is accepted", color=GREY, fontsize=7, ha="right")
    ax.set(yscale="log", xlabel="poisoning round (25 points each)", ylabel="score(target) / threshold")
    ax.legend(loc="lower left")
    save(f, "vetting")
