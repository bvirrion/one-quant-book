"""Chart data for Book 18, chapter 3: expected best of k equally skilled entries, in noise standard deviations."""
import pathlib
from math import log, sqrt

from iv_apply import expected_max_normal

OUT = pathlib.Path(__file__).resolve().parents[4] / "figdata" / "interviews" / "03-applications"
KS = [1, 2, 3, 5, 10, 20, 30, 50, 100, 200, 300, 500, 1000, 2000, 5000]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    rows = ["k,best,rule"]
    for k in KS:
        rows.append(f"{k},{expected_max_normal(k):.4f},{sqrt(2 * log(k)):.4f}")
    (OUT / "bestof.csv").write_text("\n".join(rows) + "\n")


if __name__ == "__main__":
    main()
