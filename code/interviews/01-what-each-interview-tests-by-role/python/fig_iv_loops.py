"""Chart data for Book 18, chapter 1: chance of passing a loop that needs every interview passed, by ability."""
import pathlib

from iv_loop import loop_pass

OUT = pathlib.Path(__file__).resolve().parents[4] / "figdata" / "interviews" / "01-what-each-interview-tests-by-role"


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    rows = ["theta,k1,k3,k5"]
    for i in range(-10, 31):
        th = i / 10
        rows.append(f"{th:.1f}," + ",".join(f"{loop_pass(th, k, k):.4f}" for k in (1, 3, 5)))
    (OUT / "loops.csv").write_text("\n".join(rows) + "\n")


if __name__ == "__main__":
    main()
