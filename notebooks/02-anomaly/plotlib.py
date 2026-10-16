"""Plot style and save helper (matplotlib for geometry and custom charts, seaborn for distributions, categories and heatmaps) for the slide figures of one course module. Copy to notebooks/<module>/plotlib.py,
set MODULE, keep the colours of slides/header.tex (aasblue ... aasgrey).

Every figure is a PDF with a transparent background in `assets/figures/plots/<MODULE>/`; the slides include it as
`![](plots/<MODULE>/<name>.pdf)`. Sizes are in inches at the real size on the slide (text width 4.3 in, a 48% column
2.1 in), so the text of a figure is as large on the slide as it is here (6.5 to 7.5 pt). Text is placed by
matplotlib inside the figure bounds (`bbox_inches="tight"`), it cannot spill over the slide.
"""

import functools
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns

ROOT = Path(__file__).resolve().parents[2]  # repo root: this file lives in notebooks/<module>/
MODULE = "03"  # 01 intro, 02 spam, 03 anomaly, 04 malware
OUT = ROOT / "assets" / "figures" / "plots" / MODULE
BLUE, RED, GREEN, GOLD, GREY = "#1F618D", "#B03A2E", "#1E8449", "#B9770E", "#5D6D7E"
LIGHT = "#AEB6BF"
FULL, COL = 4.3, 2.15  # slide text width and a column of a two-column frame, inches


def setup() -> None:
    """Common matplotlib style: Noto Sans, small text, no top/right spines, transparent PDF."""
    mpl.rcParams.update({
        "font.family": ["Noto Sans", "DejaVu Sans"], "font.size": 8, "axes.labelsize": 8, "axes.titlesize": 8.5,
        "xtick.labelsize": 7.5, "ytick.labelsize": 7.5, "legend.fontsize": 7.5, "axes.linewidth": 0.6,
        "axes.spines.top": False, "axes.spines.right": False, "xtick.major.width": 0.6, "ytick.major.width": 0.6,
        "xtick.major.size": 2.5, "ytick.major.size": 2.5, "lines.linewidth": 1.3, "legend.frameon": False,
        "axes.grid": True, "grid.color": "#D5D8DC", "grid.linewidth": 0.4, "axes.axisbelow": True,
        "savefig.transparent": True, "pdf.fonttype": 42, "mathtext.fontset": "dejavusans",
    })  # fmt: skip
    sns.set_palette(
        [BLUE, RED, GREEN, GOLD, GREY]
    )  # seaborn functions (histplot, kdeplot, heatmap, barplot) take the deck colours


def styled(func):
    """Decorator for a plot function called from a demo notebook: the deck style applies inside the call only, so the
    notebook's own plots keep their look."""

    @functools.wraps(func)
    def wrapper(*args, **kw):
        with mpl.rc_context():
            setup()
            return func(*args, **kw)

    return wrapper


def fig(kind: str = "full", height: float = 1.6, **kw):
    """Figure at the size it has on the slide: kind "full" (text width) or "col" (a column of a two-column frame).
    Use in a demo notebook: `f, ax = plotlib.fig("col", 2.1)`; extra keywords go to plt.subplots (ncols, gridspec_kw...)."""
    return plt.subplots(figsize=(FULL if kind == "full" else COL, height), **kw)


def save(fig, name: str) -> Path:
    """Write assets/figures/plots/03/<name>.pdf (transparent) and close the figure."""
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / f"{name}.pdf"
    fig.savefig(path, transparent=True, bbox_inches="tight", pad_inches=0.03)
    plt.close(fig)
    print("wrote", path.relative_to(ROOT))
    return path


def ellipse(mu, cov, d: float, n: int = 120) -> np.ndarray:
    """Points at Mahalanobis distance d from mu."""
    w, v = np.linalg.eigh(np.asarray(cov))
    t = np.linspace(0, 2 * np.pi, n)
    return (np.asarray(mu)[:, None] + v @ (d * np.sqrt(w)[:, None] * np.stack([np.cos(t), np.sin(t)]))).T


def circle(c, r: float, n: int = 120) -> np.ndarray:
    t = np.linspace(0, 2 * np.pi, n)
    return np.stack([c[0] + r * np.cos(t), c[1] + r * np.sin(t)], 1)


def square_axes(ax, lim: float = 3.5, ticks=(-2, 0, 2)) -> None:
    """Equal-scale square axes of Example 1 (standardised log bytes sent and received)."""
    ax.set_xlim(-lim, lim)
    ax.set_ylim(-lim, lim)
    ax.set_aspect("equal")
    ax.set_xticks(ticks)
    ax.set_yticks(ticks)
    ax.set_xlabel("$x_1$ log bytes sent")
    ax.set_ylabel("$x_2$ log bytes received")
