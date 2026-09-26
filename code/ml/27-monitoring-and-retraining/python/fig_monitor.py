"""Chart data for Book 12, chapter 27: alarms per month under the slow fade, and the shadow test's p-values."""
import pathlib

import ml_monitor as m

OUT = pathlib.Path(__file__).resolve().parents[4] / "figdata" / "ml" / "27-monitoring-and-retraining"
COLS = {"feature PSI": "psi", "feature KS": "ks", "prediction PSI": "predpsi", "inside threshold": "inside",
        "IC CUSUM": "cusum"}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    r = m.alarm_rates("slow fade")
    with open(OUT / "fade.csv", "w") as f:
        f.write("day," + ",".join(COLS.values()) + "\n")
        for i in range(len(r["IC CUSUM"])):
            f.write(f"{25 * i + 12.5:.1f}," + ",".join(f"{r[k][i]:.2f}" for k in COLS) + "\n")
    paths = [m.shadow_run(s)[4][:20] for s in range(5)]
    with open(OUT / "shadow.csv", "w") as f:
        f.write("day," + ",".join(f"run{s}" for s in range(5)) + "\n")
        for t in range(20):
            f.write(f"{t + 1}," + ",".join(f"{p[t]:.4g}" for p in paths) + "\n")


if __name__ == "__main__":
    main()
