"""Chart data for Book 18, chapter 8: relative error of the rules of 72, 70 and 69.3 against the exact doubling time."""
import pathlib

from iv_arith import doubling_exact, doubling_rule

OUT = pathlib.Path(__file__).resolve().parents[4] / "figdata" / "interviews" / "08-mental-arithmetic"


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    rows = ["rate,r72,r70,r693"]
    for i in range(1, 26):
        r = i / 100
        t = doubling_exact(r)
        errs = [100 * (doubling_rule(r, k) - t) / t for k in (72, 70, 69.3)]
        rows.append(f"{i}," + ",".join(f"{e:.3f}" for e in errs))
    (OUT / "rule72.csv").write_text("\n".join(rows) + "\n")


if __name__ == "__main__":
    main()
