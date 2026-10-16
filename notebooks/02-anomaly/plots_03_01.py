"""Illustration figures of the class 03_01 slides that no demo notebook draws (Example 1 and toy data) ->
assets/figures/plots/03/*.pdf

    python plots_03_01.py            # every illustration
    python plots_03_01.py knn lof    # only these (names = function names)

The result plots (ten detectors, per category, splits, contamination, classifiers, ROC, ICA/NMF, duplicates) are
stored by the demo notebooks 01-03 with one line each (`plots_results.<name>(...)`): run the demos to refresh them.
"""

import sys

import plots_methods as pm
import plots_stats as ps

FIGURES = [ps.kinds, ps.settings, ps.dist1d, ps.ex1_data, ps.ex1_z, ps.ex1_ellipse, ps.ex1_levels, ps.threshold, ps.baserate, ps.mcd,
           pm.knn, pm.lof, pm.lof_flood, pm.iso_cuts, pm.iso_axis, pm.ocsvm, pm.pca, pm.bss_toy, pm.kmeans_gmm, pm.dbscan]  # fmt: skip

if __name__ == "__main__":
    import plotlib

    plotlib.setup()
    want = set(sys.argv[1:])
    for f in FIGURES:
        if not want or f.__name__ in want:
            f()
