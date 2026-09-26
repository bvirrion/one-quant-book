"""Chart data for Book 12, chapter 24: backtest and live rank IC of the one-second forecast under each skew."""
import pathlib

import ml_featstore as m

OUT = pathlib.Path(__file__).resolve().parents[4] / "figdata" / "ml" / "24-data-and-feature-stores"


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    e = m.model_effects(1.0)
    with open(OUT / "ic.csv", "w") as f:
        f.write("i,skew,backtest,live\n")
        for i, k in enumerate(("none",) + m.SKEWS):
            f.write(f"{i},{k.replace(' ', '')},{e[k]['backtest IC']:.4f},{e[k]['live IC']:.4f}\n")


if __name__ == "__main__":
    main()
