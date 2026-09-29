"""Chart data for Book 18, chapter 20: next-minute mid return by imbalance decile (mean and standard error), and
the planted relation, on the cleaned take-home dataset."""
import pathlib

from iv_case import BETA_BP, binned, clean, generate, next_returns

OUT = pathlib.Path(__file__).resolve().parents[4] / "figdata" / "interviews" / "20-research-case-studies-and-take-homes"


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    b = binned(next_returns(clean(generate())))
    rows = ["centre,mean,se,planted"] + [
        f"{r.centre:.2f},{r.mean:.4f},{r.se:.4f},{BETA_BP * r.centre:.4f}" for r in b.itertuples()
    ]
    (OUT / "case.csv").write_text("\n".join(rows) + "\n")


if __name__ == "__main__":
    main()
