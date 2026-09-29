"""Chart data for Book 18, chapter 7: expected value of the two offers against the probability of leaving."""
import pathlib
from fractions import Fraction

from iv_offer import A, B, expected_value

OUT = pathlib.Path(__file__).resolve().parents[4] / "figdata" / "interviews" / "07-offers-compensation-and-non-competes"


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    rows = ["p,A,B"]
    for i in range(0, 101, 5):
        p = Fraction(i, 100)
        rows.append(f"{float(p):.2f},{float(expected_value(A, p)):.1f},{float(expected_value(B, p)):.1f}")
    (OUT / "offers.csv").write_text("\n".join(rows) + "\n")


if __name__ == "__main__":
    main()
