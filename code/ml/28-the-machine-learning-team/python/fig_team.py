"""Chart data for Book 12, chapter 28: median lead time against the arrival rate."""
import pathlib

import ml_team as m

OUT = pathlib.Path(__file__).resolve().parents[4] / "figdata" / "ml" / "28-the-machine-learning-team"


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    rates, c = m.rate_curve()
    with open(OUT / "rate.csv", "w") as f:
        f.write("rate,handoff,package\n")
        for i, r in enumerate(rates):
            f.write(f"{r},{c[True][i]:.2f},{c[False][i]:.2f}\n")


if __name__ == "__main__":
    main()
