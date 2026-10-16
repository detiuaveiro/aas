"""Slide plots of the class 03_02 results (neural detectors, time series, many sensors). Pure drawing: the demo
notebooks 04-06 compute the numbers and call these functions with their own rows, one line each; the PDFs go to
`assets/figures/plots/03/`. Rows are lists of dicts (`polars.DataFrame.to_dicts()`)."""

import numpy as np
import seaborn as sns
from matplotlib.patches import Rectangle
from matplotlib.ticker import ScalarFormatter
from plotlib import BLUE, GOLD, GREEN, GREY, LIGHT, RED, fig, save, styled

SHORT = {"GMM (-log-likelihood)": "GMM", "PCA reconstruction": "PCA (linear twin)", "PCA recon (space)": "PCA reconstruction",
         "predict from others (space)": "predict from the others", "conv AE (space+time)": "conv AE (space + time)",
         "Isolation Forest (space)": "Isolation Forest", "dense AE (space)": "dense AE", "per-sensor max|z|": "per-sensor max |z|"}  # fmt: skip


def short(name: str) -> str:
    return SHORT.get(name, name)


@styled
def ae_scores(s_normal, s_attack, threshold: float) -> None:
    """Histogram of the AE score on the test set: normal rows against attacks, with the 1% false-alarm threshold."""
    f, ax = fig("full", 1.3)
    allv = np.r_[s_normal, s_attack]
    bins = np.logspace(np.log10(allv.min() + 1e-6), np.log10(allv.max()), 55)
    ax.hist(s_normal, bins, density=True, color=BLUE, alpha=0.65, label="normal", lw=0)
    ax.hist(s_attack, bins, density=True, color=RED, alpha=0.65, label="attack", lw=0)
    ax.axvline(threshold, color=GREY, ls="--", lw=1)
    ax.text(threshold * 1.15, ax.get_ylim()[1] * 0.85, "threshold\n(1% false alarms)", color=GREY, fontsize=7, va="top")
    ax.set(xscale="log", xlabel="reconstruction error = anomaly score", ylabel="density", yticks=[])
    ax.legend(loc="upper left")
    ax.grid(False)
    save(f, "ae_scores")


@styled
def deep_band(rows) -> None:
    """rows: one dict per (seed, detector) with AUPRC (3 seeds)."""
    acc: dict = {}
    for r in rows:
        acc.setdefault(r["detector"], []).append(r["AUPRC"])
    data = sorted(((np.mean(v), np.std(v, ddof=1), k) for k, v in acc.items()), reverse=True)
    f, ax = fig("full", 1.35)
    ys = np.arange(len(data))[::-1]
    cols = [GOLD if "GMM" in k else (GREEN if "PCA" in k else BLUE) for _, _, k in data]
    ax.barh(
        ys,
        [m for m, _, _ in data],
        xerr=[s for _, s, _ in data],
        color=cols,
        height=0.62,
        error_kw={"ecolor": RED, "lw": 1.1, "capsize": 2},
    )
    for y, (m, _, _) in zip(ys, data):
        ax.text(0.405, y, f"{m:.3f}", va="center", ha="left", fontsize=7, color="white")
    ax.set_yticks(ys, [short(k) for _, _, k in data])
    ax.set(xlabel="AUPRC, mean ± std over 3 seeds (gold: best classic, green: linear twin)", xlim=(0.4, 0.75))
    ax.grid(axis="y", visible=False)
    save(f, "deep_band")


@styled
def code_size(rows, gmm_auprc: float) -> None:
    """rows: dicts with `code size`, AUPRC and `val MSE` (validation MSE of normal rows)."""
    rows = sorted(rows, key=lambda r: r["code size"])
    x = [r["code size"] for r in rows]
    f, ax = fig("full", 1.5)
    ax.plot(x, [r["AUPRC"] for r in rows], color=BLUE, marker="o", ms=3.5, label="AUPRC (test attacks)")
    ax.axhline(gmm_auprc, color=GOLD, ls="--", lw=1)
    ax.text(128, gmm_auprc + 0.012, f"GMM {gmm_auprc:.3f}", color=GOLD, fontsize=7, ha="right")
    best = max(rows, key=lambda r: r["AUPRC"])
    ax.annotate(
        f"{best['AUPRC']:.3f}: picked by looking at the test attacks",
        (best["code size"], best["AUPRC"]),
        (2.2, 0.745),
        fontsize=7,
        color=BLUE,
        arrowprops={"arrowstyle": "-", "color": BLUE, "lw": 0.6},
    )
    ax.set(xscale="log", xlabel="code size", ylabel="AUPRC", ylim=(0.4, 0.78))
    ax.set_xscale("log", base=2)
    ax.set_xticks(x, [str(v) for v in x])
    ax.xaxis.set_minor_formatter(ScalarFormatter())
    ax2 = ax.twinx()
    ax2.plot(
        x, [r["val MSE"] for r in rows], color=GREY, marker="s", ms=3, ls=":", label="validation MSE (normal only)"
    )
    ax2.set(ylabel="validation MSE")
    ax2.grid(False)
    ax2.spines["right"].set_visible(True)
    h1, l1 = ax.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    ax.legend(h1 + h2, l1 + l2, loc="lower center", ncol=2, fontsize=6.8)
    save(f, "code_size")


@styled
def explain_alarm(tops: dict) -> None:
    """tops: {category: [(feature, mean squared error), ...]} the largest per-feature errors of the AE on test attacks."""
    f, axs = fig("full", 1.35, ncols=len(tops), gridspec_kw={"wspace": 0.12})
    for ax, (cat, items) in zip(axs, tops.items()):
        names, vals = zip(*items)
        ys = np.arange(len(vals))[::-1]
        ax.barh(ys, vals, color=LIGHT, height=0.7)
        for y, n, v in zip(ys, names, vals):
            ax.text(0.02 * max(vals), y, n.replace("_", " "), va="center", fontsize=6.3, color="#2C3E50")
        ax.set(title=cat, yticks=[], xticks=[], xlim=(0, max(vals) * 1.25))
        ax.set_xlabel("error")
        ax.grid(False)
    save(f, "explain_alarm")


@styled
def nab_series(series: dict) -> None:
    """series: {name: DataFrame(timestamp, value, y)}; the NAB label window is shaded."""
    f, axs = fig("full", 1.25, nrows=2, ncols=2, sharex=True, gridspec_kw={"hspace": 0.4, "wspace": 0.25})
    for ax, (name, te) in zip(axs.ravel(), series.items()):
        ax.plot(te.timestamp, te.value, lw=0.6, color=BLUE)
        ax.fill_between(te.timestamp, te.value.min(), te.value.max(), where=te.y == 1, color=RED, alpha=0.25, lw=0)
        ax.set_title(name, fontsize=7.5, loc="left", pad=1)
        ax.set(yticks=[], xticks=[])
        ax.grid(False)
    save(f, "nab_series")


@styled
def nab_scores(s_diff, s_ae, t_diff, t_ae, y) -> None:
    """The score of the seasonal difference and of the conv AE on one series, with threshold and anomaly window."""
    f, axs = fig("full", 1.1, nrows=2, sharex=True, gridspec_kw={"hspace": 0.5})
    win = np.flatnonzero(y)[[0, -1]]
    for ax, s, t, name in ((axs[0], s_diff, t_diff, "seasonal difference"), (axs[1], s_ae, t_ae, "conv AE")):
        ax.plot(s, lw=0.6, color=BLUE)
        ax.axhline(t, color=GREY, ls="--", lw=0.9)
        ax.axvspan(*win, color=RED, alpha=0.25, lw=0)
        ax.set_title(name, fontsize=7.5, loc="left", pad=1)
        ax.set(yticks=[])
        ax.grid(False)
    axs[1].set_xlabel("time step (5 min); red: the anomaly window, dashed: threshold")
    save(f, "nab_scores")


@styled
def nab_found(rows) -> None:
    """rows: dicts with series, detector, found (0/1), false_alarms: false alarms per cell, `missed` where nothing was found."""
    dets = list(dict.fromkeys(r["detector"] for r in rows))
    sers = list(dict.fromkeys(r["series"] for r in rows))
    fa = np.array(
        [[next(r["false_alarms"] for r in rows if r["series"] == s and r["detector"] == d) for d in dets] for s in sers]
    )
    fnd = np.array(
        [[next(r["found"] for r in rows if r["series"] == s and r["detector"] == d) for d in dets] for s in sers]
    )
    f, ax = fig("full", 1.35)
    sns.heatmap(
        np.log1p(fa),
        mask=fnd == 0,
        cmap=sns.light_palette(RED, as_cmap=True),
        cbar=False,
        linewidths=1,
        linecolor="white",
        ax=ax,
        vmin=0,
        vmax=np.log1p(400),
    )
    for i in range(len(sers)):
        for j in range(len(dets)):
            ax.text(
                j + 0.5,
                i + 0.5,
                "missed" if fnd[i, j] == 0 else f"found, {int(fa[i, j])}",
                ha="center",
                va="center",
                fontsize=7,
                color=GREY if fnd[i, j] == 0 else "black",
            )
            if fnd[i, j] == 0:
                ax.add_patch(Rectangle((j, i), 1, 1, fc=LIGHT, alpha=0.35, lw=0))
    ax.set_xticks(np.arange(len(dets)) + 0.5, dets)
    ax.set_yticks(np.arange(len(sers)) + 0.5, sers, rotation=0)
    ax.xaxis.tick_top()
    ax.tick_params(length=0)
    ax.grid(False)
    save(f, "nab_found")


@styled
def plant_events(Xa, events, sensors, show) -> None:
    """Sensors of the water plant in the attacked run; the three events are shaded. `show`: sensor indices."""
    f, axs = fig("full", 1.25, nrows=2, ncols=2, sharex=True, gridspec_kw={"hspace": 0.4, "wspace": 0.25})
    for ax, s in zip(axs.ravel(), show):
        ax.plot(Xa[:, s], lw=0.5, color=BLUE)
        for e in events:
            ax.axvspan(e["start"], e["start"] + e["length"], color=RED, alpha=0.3, lw=0)
        ax.set_title(sensors[s], fontsize=7.5, loc="left", pad=1)
        ax.set(yticks=[], xticks=[])
        ax.grid(False)
    save(f, "plant_events")


@styled
def space_beats(rows) -> None:
    """rows: dicts with detector, AUPRC, F1, spike/freeze/drift (bool) and `false alarms`."""
    rows = [r for r in rows if r["detector"] != "random score"]
    rows = sorted(rows, key=lambda r: r["AUPRC"])
    f, ax = fig("full", 1.35)
    ys = np.arange(len(rows))
    ax.barh(
        ys, [r["AUPRC"] for r in rows], color=[GREEN if "PCA" in r["detector"] else BLUE for r in rows], height=0.62
    )
    for y, r in zip(ys, rows):
        n = sum(bool(r[k]) for k in ("spike", "freeze", "drift"))
        ax.text(
            r["AUPRC"] + 0.01,
            y,
            f"{r['AUPRC']:.3f}   {n}/3 events, {r['false alarms']} false alarms",
            va="center",
            fontsize=7,
        )
    ax.set_yticks(ys, [short(r["detector"]) for r in rows])
    ax.set(xlabel="AUPRC (point-wise, threshold at the 99.5% quantile of the normal run)", xlim=(0, 1.0))
    ax.grid(axis="y", visible=False)
    save(f, "space_beats")


@styled
def point_adjust(rows) -> None:
    """rows: dicts with detector, F1 and `F1 point-adjusted`; a random score is included."""
    keep = ["PCA recon (space)", "conv AE (space+time)", "random score"]
    d = {r["detector"]: r for r in rows}
    f, ax = fig("full", 1.35)
    x = np.arange(len(keep))
    for i, (key, lab, col) in enumerate(
        (("F1", "F1 (point-wise)", BLUE), ("F1 point-adjusted", "F1 point-adjusted", RED))
    ):
        v = [d[k][key] for k in keep]
        bars = ax.bar(x + (i - 0.5) * 0.36, v, 0.36, color=col, label=lab, lw=0)
        for b, val in zip(bars, v):
            ax.text(b.get_x() + b.get_width() / 2, val + 0.02, f"{val:.2f}", ha="center", fontsize=7)
    ax.set_xticks(x, [short(k) for k in keep])
    ax.set(ylim=(0, 1.5), ylabel="F1")
    ax.legend(loc="upper left", ncol=2)
    ax.grid(axis="x", visible=False)
    save(f, "point_adjust")
