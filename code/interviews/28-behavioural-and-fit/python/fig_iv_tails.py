"""Chart data for Book 18, chapter 28: trading days between losses of k standard deviations, normal and fat-tailed."""
import pathlib

from iv_behave import days_between

OUT = pathlib.Path(__file__).resolve().parents[4] / "figdata" / "interviews" / "28-behavioural-and-fit"


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    rows = ["k,normal,t3,t5"]
    for i in range(10, 51):
        k = i / 10
        vals = [days_between(k), days_between(k, "t", 3), days_between(k, "t", 5)]
        rows.append(f"{k:.1f}," + ",".join(f"{v:.2f}" for v in vals))
    (OUT / "tails.csv").write_text("\n".join(rows) + "\n")


if __name__ == "__main__":
    main()
