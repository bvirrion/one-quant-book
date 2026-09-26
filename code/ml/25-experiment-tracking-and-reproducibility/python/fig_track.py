"""Chart data for Book 12, chapter 25: the validation Sharpe ratios of the 200 tracked runs, and the benchmarks."""
import pathlib

import ml_track as m
import numpy as np

OUT = pathlib.Path(__file__).resolve().parents[4] / "figdata" / "ml" / "25-experiment-tracking-and-reproducibility"


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    v = np.array([r["metrics"]["valid sharpe"] for r in m.study()["tracker"].runs()])
    edges = np.arange(-4.0, 3.01, 0.5)
    h, _ = np.histogram(v, edges)
    with open(OUT / "sharpes.csv", "w") as f:
        f.write("x,runs\n")
        for e, c in zip(edges[:-1], h, strict=True):
            f.write(f"{e + 0.25:.2f},{c}\n")
    s = m.summary()
    with open(OUT / "marks.csv", "w") as f:
        f.write("x,y,label\n")
        f.write(f"{s['best valid']:.3f},0,champion\n{m.null_max():.3f},0,nullmax\n{s['test']:.3f},0,test\n")


if __name__ == "__main__":
    main()
