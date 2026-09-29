"""Chart data for Book 18, chapter 13: a market maker's expected profit per arrival against the half-width,
for three shares of informed traders (the chapter's uniform-value model)."""
import pathlib
from fractions import Fraction

from iv_bets import mm_profit

OUT = pathlib.Path(__file__).resolve().parents[4] / "figdata" / "interviews" / "13-betting-and-market-making-games"


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    rows = ["h,a05,a15,a30"]
    for i in range(0, 41):
        h = Fraction(i, 2)
        vals = [float(mm_profit(h, Fraction(a, 100))) for a in (5, 15, 30)]
        rows.append(f"{float(h):.1f}," + ",".join(f"{v:.4f}" for v in vals))
    (OUT / "width.csv").write_text("\n".join(rows) + "\n")


if __name__ == "__main__":
    main()
