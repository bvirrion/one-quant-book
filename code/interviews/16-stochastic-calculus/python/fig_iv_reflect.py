"""Chart data for Book 18, chapter 16: P(max of W on [0,1] >= a), exact against simulations with 100 and 1600
steps (discrete monitoring misses crossings between steps, so it underestimates)."""
import pathlib

from iv_stoch import max_tail, simulate_max_tail

OUT = pathlib.Path(__file__).resolve().parents[4] / "figdata" / "interviews" / "16-stochastic-calculus"


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    rows = ["a,exact,sim100,sim1600"]
    for i in range(1, 11):
        a = i * 0.25
        rows.append(
            f"{a:.2f},{max_tail(a):.4f},{simulate_max_tail(a, 100, 20_000, 11):.4f},"
            f"{simulate_max_tail(a, 1600, 20_000, 12):.4f}"
        )
    (OUT / "reflect.csv").write_text("\n".join(rows) + "\n")


if __name__ == "__main__":
    main()
