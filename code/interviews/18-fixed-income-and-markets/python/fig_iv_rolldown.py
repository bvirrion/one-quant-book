"""Chart data for Book 18, chapter 18: the synthetic curve and a five-year bond's yield now and one year later."""
import pathlib

from iv_rates import curve

OUT = pathlib.Path(__file__).resolve().parents[4] / "figdata" / "interviews" / "18-fixed-income-and-markets"


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    rows = ["t,y"] + [f"{i / 4:.2f},{100 * curve(i / 4):.4f}" for i in range(1, 121)]
    (OUT / "curve.csv").write_text("\n".join(rows) + "\n")
    pts = ["t,y", f"5,{100 * curve(5):.4f}", f"4,{100 * curve(4):.4f}"]
    (OUT / "points.csv").write_text("\n".join(pts) + "\n")


if __name__ == "__main__":
    main()
