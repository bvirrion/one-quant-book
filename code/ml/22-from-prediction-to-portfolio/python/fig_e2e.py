"""Chart data for Book 12, chapter 22: net Sharpe ratios by method and scenario; learned coefficients."""
import pathlib

import ml_e2e as m
import numpy as np

OUT = pathlib.Path(__file__).resolve().parents[4] / "figdata" / "ml" / "22-from-prediction-to-portfolio"
SHORT = ("pto", "lstrd", "dfl", "ppp", "truth")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    a, b = m.summary(m.results()), m.summary(m.overfit())
    with open(OUT / "sharpe.csv", "w") as f:
        f.write("i,method,net,sd,netover,sdover\n")
        for i, (k, s) in enumerate(zip(m.METHODS, SHORT, strict=True)):
            f.write(f"{i},{s},{a[k]['net']:.3f},{a[k]['net sd']:.3f},{b[k]['net']:.3f},{b[k]['net sd']:.3f}\n")
    with open(OUT / "coefs.csv", "w") as f:
        f.write("i,method,b1,b2\n")
        for i, (k, s) in enumerate(zip(m.METHODS, SHORT, strict=True)):
            B = np.array([r[k]["b"][:2] for r in m.results()]) * 1e3
            f.write(f"{i},{s},{B[:, 0].mean():.3f},{B[:, 1].mean():.3f}\n")


if __name__ == "__main__":
    main()
