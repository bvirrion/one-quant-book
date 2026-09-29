"""Chart data for Book 18, chapter 14: years of returns needed to detect an annual Sharpe ratio (one-sided 5%)."""
import pathlib

from iv_stats import years_for_power

OUT = pathlib.Path(__file__).resolve().parents[4] / "figdata" / "interviews" / "14-statistics"


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    rows = ["sr,p50,p80,p95"]
    for i in range(5, 61):
        sr = i / 20
        rows.append(f"{sr:.2f}," + ",".join(f"{years_for_power(sr, power=q):.3f}" for q in (0.5, 0.8, 0.95)))
    (OUT / "power.csv").write_text("\n".join(rows) + "\n")


if __name__ == "__main__":
    main()
