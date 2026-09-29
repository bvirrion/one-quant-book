"""Chart data for Book 18, chapter 17: gamma of a strike-100 option against spot, for three expiries."""
import pathlib

from iv_options import gamma

OUT = pathlib.Path(__file__).resolve().parents[4] / "figdata" / "interviews" / "17-options-and-derivatives"


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    rows = ["spot,week,quarter,year"]
    for i in range(0, 81):
        s = 80 + i * 0.5
        vals = [gamma(s, 100, 0.2, t) for t in (1 / 52, 0.25, 1.0)]
        rows.append(f"{s:.1f}," + ",".join(f"{v:.5f}" for v in vals))
    (OUT / "gamma.csv").write_text("\n".join(rows) + "\n")


if __name__ == "__main__":
    main()
