"""Chart data for Book 18, chapter 4: expected marks per attempted item against confidence."""
import pathlib

OUT = pathlib.Path(__file__).resolve().parents[4] / "figdata" / "interviews" / "04-online-assessments"


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    rows = ["p,w0,w025,w1"]
    for i in range(0, 101, 2):
        p = i / 100
        rows.append(f"{p:.2f},{p:.4f},{p - 0.25 * (1 - p):.4f},{p - (1 - p):.4f}")
    (OUT / "skip.csv").write_text("\n".join(rows) + "\n")


if __name__ == "__main__":
    main()
