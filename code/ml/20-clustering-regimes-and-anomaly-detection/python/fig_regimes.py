"""Chart data for Book 12, chapter 20: filtered and smoothed stress probabilities around a switch; clustering accuracy
against the window length."""
import pathlib

import ml_regimes as m

OUT = pathlib.Path(__file__).resolve().parents[4] / "figdata" / "ml" / "20-clustering-regimes-and-anomaly-detection"


def window():
    """The first switch into stress in the test half that the filter took at least two days to see."""
    x, s = m.series()
    xt, st = x[m.HALF:], s[m.HALF:]
    h = m.hmm(2)
    pf, ps = h.filter(xt)[:, 1], h.smooth(xt)[:, 1]
    d = m._delays(pf > 0.5, st)
    t0 = next(t for t, dd in zip(m._switches(st), d, strict=True) if dd >= 2)
    return t0, xt, st, pf, ps


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    t0, xt, st, pf, ps = window()
    with open(OUT / "switch.csv", "w") as f:
        f.write("day,ret,state,filtered,smoothed\n")
        for t in range(t0 - 30, t0 + 50):
            f.write(f"{t - t0},{100 * xt[t]:.3f},{st[t]},{pf[t]:.4f},{ps[t]:.4f}\n")
    c = m.clustering()
    with open(OUT / "clusters.csv", "w") as f:
        f.write("window,km08,hier08,km15,hier15\n")
        for L in m.WINDOWS:
            f.write(f"{L}," + ",".join(f"{c[(iv, L)][j]:.3f}" for iv in m.STRENGTHS for j in (0, 1)) + "\n")


if __name__ == "__main__":
    main()
