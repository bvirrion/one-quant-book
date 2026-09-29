"""Chart data for Book 18, chapter 9: actual against stated coverage of intervals, for a calibrated and an
overconfident estimator (log errors with sd 1; intervals built with sd 1 or 0.5), exact and simulated."""
import pathlib

import numpy as np
from iv_fermi import hit_rate
from scipy.stats import norm

OUT = pathlib.Path(__file__).resolve().parents[4] / "figdata" / "interviews" / "09-estimation"


def simulated(stated, sd_believed, n=20_000, seed=3):
    err = np.random.default_rng(seed).standard_normal(n)
    return float(np.mean(np.abs(err) <= norm.ppf(0.5 + stated / 2) * sd_believed))


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    rows = ["stated,calibrated,overconfident,sim_over"]
    for pct in range(50, 100, 5):
        c = pct / 100
        cal, over, sim = 100 * hit_rate(c, 1, 1), 100 * hit_rate(c, 0.5, 1), 100 * simulated(c, 0.5)
        rows.append(f"{pct},{cal:.2f},{over:.2f},{sim:.2f}")
    (OUT / "calib.csv").write_text("\n".join(rows) + "\n")


if __name__ == "__main__":
    main()
