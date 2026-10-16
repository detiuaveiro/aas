"""Slide plots of the class 03_01 results. Pure drawing: the demo notebooks 01-03 compute the numbers and call these
functions with their own rows (one line each); the PDFs go to `assets/figures/plots/03/`.

Rows are lists of dicts, as `polars.DataFrame.to_dicts()` gives them."""

import numpy as np
from plotlib import BLUE, GOLD, GREEN, GREY, LIGHT, RED, fig, save, styled
from sklearn.metrics import average_precision_score, precision_recall_curve, roc_auc_score, roc_curve

import anomlib as an

CATS = an.CATEGORIES
PAL = [BLUE, RED, GOLD, GREEN]
GMM = "GMM (-log-likelihood)"
SHORT = {
    GMM: "GMM",
    "z-score (max |z|)": "z-score",
    "Gaussian (diagonal)": "diag. Gaussian",
    "k-means distance": "k-means",
    "PCA reconstruction": "PCA recon.",
}


def by(rows, key: str = "detector") -> dict:
    return {r[key]: r for r in rows}


def grouped(ax, groups, series, ylabel="", colors=PAL, width=0.8):
    n = len(series)
    for i, (name, vals) in enumerate(series):
        pos = np.arange(len(groups)) + (i - (n - 1) / 2) * width / n
        bars = ax.bar(pos, vals, width / n, color=colors[i], label=name, lw=0)
        for b, v in zip(bars, vals):
            ax.text(
                b.get_x() + b.get_width() / 2,
                v + 0.015,
                f"{v:.2f}".lstrip("0") if v < 1 else "1",
                ha="center",
                fontsize=6.5,
            )
    ax.set_xticks(np.arange(len(groups)), groups)
    ax.set(ylabel=ylabel, ylim=(0, 1.12))
    ax.grid(axis="x", visible=False)


@styled
def ten_detectors(rows) -> None:
    items = sorted((r["AUPRC"], r["detector"]) for r in rows)
    f, ax = fig("full", 1.6)
    ax.barh([SHORT.get(k, k) for _, k in items], [v for v, _ in items], color=BLUE, height=0.65)
    for i, (v, _) in enumerate(items):
        ax.text(v + 0.008, i, f"{v:.3f}", va="center", fontsize=7)
    ax.set(xlabel="AUPRC (1.8% attacks; a random score gets 0.018)", xlim=(0, 0.78))
    ax.grid(axis="y", visible=False)
    save(f, "ten_detectors")


@styled
def recall_cat(rows) -> None:
    d = by(rows)
    names = [GMM, "PCA reconstruction", "Isolation Forest", "LOF"]
    f, ax = fig("full", 1.35)
    grouped(ax, CATS, [(SHORT.get(n, n), [d[n][c] for c in CATS]) for n in names], "recall at 1% false alarms")
    ax.legend(ncol=4, loc="upper center", bbox_to_anchor=(0.5, 1.2))
    save(f, "recall_cat")


@styled
def splits(rows) -> None:
    """rows: one dict per (seed, detector) with AUPRC."""
    acc: dict = {}
    for r in rows:
        acc.setdefault(r["detector"], []).append(r["AUPRC"])
    keep = {GMM, "One-class SVM", "kNN distance", "Isolation Forest", "PCA reconstruction", "Mahalanobis"}
    data = sorted(((np.mean(v), np.std(v, ddof=1), k) for k, v in acc.items() if k in keep), reverse=True)
    f, ax = fig("full", 1.35)
    ys = np.arange(len(data))[::-1]
    ax.barh(
        ys,
        [m for m, _, _ in data],
        xerr=[s for _, s, _ in data],
        color=BLUE,
        height=0.6,
        error_kw={"ecolor": RED, "lw": 1.1, "capsize": 2},
    )
    ax.set_yticks(ys, [SHORT.get(k, k) for _, _, k in data])
    ax.set(xlabel="AUPRC, mean ± std over 3 splits", xlim=(0.4, 0.75))
    ax.grid(axis="y", visible=False)
    save(f, "splits")


@styled
def contam(rows) -> None:
    """rows: one dict per (contamination rate, detector) with AUPRC; rates 0, 0.01, 0.05."""
    f, ax = fig("full", 1.55)
    dets = list(dict.fromkeys(r["detector"] for r in rows))
    for name, col, mk in zip(dets, (BLUE, GREEN, GOLD, GREY, RED), "sD^os"):
        pts = sorted((100 * r["contamination"], r["AUPRC"]) for r in rows if r["detector"] == name)
        ax.plot(*zip(*pts), color=col, marker=mk, ms=3.5, label=name, lw=1.5 if name == "Isolation Forest" else 1.1)
    ax.set(xlabel="attacks mixed into the training rows (%)", ylabel="AUPRC", xticks=[0, 1, 5], ylim=(0, 0.72))
    ax.legend(loc="center left", bbox_to_anchor=(1.0, 0.5))
    save(f, "contam")


@styled
def clf_all(rows) -> None:
    """rows: dicts with model, AUPRC, recall, r2l, u2r (logistic regression, random forest, one-class GMM)."""
    d = by(rows, "model")
    pick = [
        ("logistic regression", "logistic regression"),
        ("random forest", "random forest"),
        (f"{GMM} (one-class)", "GMM (one-class)"),
    ]
    ser = [(label, [d[k][m] for m in ("AUPRC", "recall", "r2l", "u2r")]) for k, label in pick]
    f, ax = fig("full", 1.35)
    grouped(ax, ["AUPRC", "recall", "r2l recall", "u2r recall"], ser, "score")
    ax.legend(ncol=3, loc="upper center", bbox_to_anchor=(0.5, 1.2))
    save(f, "clf_all")


@styled
def loco(rows, one_class: dict) -> None:
    """rows: dicts with model, unseen, `recall on unseen`; one_class: recall per category of the PCA detector."""
    ser = []
    for model in dict.fromkeys(r["model"] for r in rows):
        v = {r["unseen"]: r["recall on unseen"] for r in rows if r["model"] == model}
        ser.append((model, [v[c] for c in CATS]))
    ser.append(("PCA (one-class, saw none)", [one_class[c] for c in CATS]))
    f, ax = fig("full", 1.35)
    grouped(ax, CATS, ser, "recall on the unseen category", colors=[RED, BLUE, GREEN])
    ax.legend(ncol=3, loc="upper center", bbox_to_anchor=(0.5, 1.2))
    save(f, "loco")


@styled
def fewlabels(rows, gmm_auprc: float) -> None:
    """rows: dicts with `labelled attacks`, AUPRC, r2l, u2r (one per draw)."""
    ns = sorted({r["labelled attacks"] for r in rows})
    f, ax = fig("full", 1.35)
    for m, lab, col, mk in (
        ("AUPRC", "AUPRC", BLUE, "o"),
        ("r2l", "recall r2l", RED, "s"),
        ("u2r", "recall u2r", GOLD, "^"),
    ):
        ax.plot(
            ns,
            [np.mean([r[m] for r in rows if r["labelled attacks"] == n]) for n in ns],
            color=col,
            marker=mk,
            ms=3.5,
            label=lab,
        )
    ax.axhline(gmm_auprc, color=GREY, ls="--", lw=0.9)
    ax.text(10.5, gmm_auprc - 0.1, f"GMM, no labels: AUPRC {gmm_auprc:.3f}", color=GREY, fontsize=7)
    ax.set(xscale="log", xlabel="labelled attacks (random forest)", ylabel="score", xticks=ns, ylim=(0, 1.05))
    ax.set_xticklabels([str(n) for n in ns])
    ax.legend(loc="lower right")
    save(f, "fewlabels")


@styled
def dedup(raw: dict, dedup_counts: dict) -> None:
    """raw, dedup_counts: rows per category (normal, dos, probe, r2l, u2r)."""
    f, ax = fig("full", 1.1)
    for y, c in ((1, raw), (0, dedup_counts)):
        a = sum(c[k] for k in CATS)
        ax.barh(y, c["normal"] / 1e3, color=GREEN, height=0.55, label="normal" if y else None)
        ax.barh(y, a / 1e3, left=c["normal"] / 1e3, color=RED, height=0.55, label="attacks" if y else None)
        ax.text((c["normal"] + a) / 1e3 + 6, y, f"{100 * a / (a + c['normal']):.0f}% attacks", va="center", fontsize=7)
    ax.set_yticks([1, 0], ["raw (10% file)", "deduplicated"])
    ax.set(xlabel="connections (thousands)", xlim=(0, 620))
    ax.legend(loc="lower right", ncol=2)
    ax.grid(axis="y", visible=False)
    save(f, "dedup")


@styled
def roc_vs_pr(y_test, s_test, y_bal, s_bal) -> None:
    """The same scores on the realistic test set and on a balanced one: ROC barely changes, precision does."""
    f, axs = fig("full", 1.45, ncols=2, gridspec_kw={"wspace": 0.3})
    au = {}
    for lab, col, y, s in (("1.8% attacks", RED, y_test, s_test), ("balanced pool", BLUE, y_bal, s_bal)):
        fpr, tpr, _ = roc_curve(y, s)
        pr, rc, _ = precision_recall_curve(y, s)
        axs[0].plot(fpr, tpr, color=col, label=lab)
        axs[1].plot(rc, pr, color=col, label=lab)
        au[lab] = (roc_auc_score(y, s), average_precision_score(y, s))
    a, b = au["1.8% attacks"], au["balanced pool"]
    axs[0].set(
        xscale="log",
        xlim=(1e-4, 1),
        xlabel="false-alarm rate (log)",
        ylabel="recall",
        title=f"ROC: AUROC {a[0]:.3f} / {b[0]:.3f}",
    )
    axs[1].set(xlabel="recall", ylabel="precision", title=f"PR: AUPRC {a[1]:.3f} / {b[1]:.3f}")
    axs[0].legend(loc="lower right", fontsize=7)
    axs[1].legend(loc="lower left", fontsize=7)
    save(f, "roc_vs_pr")


@styled
def bss_results(rows) -> None:
    """rows: PCA, ICA (recon), ICA (source), NMF reconstruction with AUPRC and the recall per category."""
    d = by(rows)
    order = [
        ("PCA reconstruction", "PCA"),
        ("ICA (recon)", "ICA, residual"),
        ("ICA (source)", "ICA, largest source"),
        ("NMF reconstruction", "NMF, residual"),
    ]
    f, axs = fig("full", 1.3, ncols=2, gridspec_kw={"wspace": 0.3, "width_ratios": [1, 1.6]})
    ax = axs[0]
    vals = [d[k]["AUPRC"] for k, _ in order]
    ax.barh(range(4)[::-1], vals, color=[BLUE, BLUE, LIGHT, GREEN], height=0.6)
    ax.set_yticks(range(4)[::-1], [n for _, n in order])
    for i, v in zip(range(4)[::-1], vals):
        ax.text(v + 0.01, i, f"{v:.3f}", va="center", fontsize=7)
    ax.set(xlabel="AUPRC", xlim=(0, 0.72))
    ax.grid(axis="y", visible=False)
    grouped(
        axs[1],
        CATS,
        [(n, [d[k][c] for c in CATS]) for (k, n) in (order[0], order[2], order[3])],
        "recall",
        colors=[BLUE, LIGHT, GREEN],
    )
    axs[1].legend(ncol=3, loc="upper center", bbox_to_anchor=(0.5, 1.2), fontsize=6.5)
    save(f, "bss_results")
