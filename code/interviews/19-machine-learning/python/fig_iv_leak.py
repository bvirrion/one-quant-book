"""Chart data for Book 18, chapter 19: shuffled 5-fold R^2 against purged walk-forward R^2 on 20 noise panels."""
import pathlib

from iv_ml import leak_study

OUT = pathlib.Path(__file__).resolve().parents[4] / "figdata" / "interviews" / "19-machine-learning"


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    res = leak_study(range(20))
    rows = ["seed,shuffled,walkforward"] + [f"{i},{a:.4f},{b:.4f}" for i, (a, b) in enumerate(res)]
    (OUT / "leak.csv").write_text("\n".join(rows) + "\n")


if __name__ == "__main__":
    main()
