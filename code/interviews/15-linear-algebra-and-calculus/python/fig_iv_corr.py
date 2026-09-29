"""Chart data for Book 18, chapter 15: the feasible range of rho_23 against rho_12, for rho_13 = 0.5 and 0.9."""
import pathlib

from iv_linalg import third_correlation_range

OUT = pathlib.Path(__file__).resolve().parents[4] / "figdata" / "interviews" / "15-linear-algebra-and-calculus"


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    rows = ["r12,lo05,hi05,lo09,hi09"]
    for i in range(-50, 51):
        r = i / 50
        a = third_correlation_range(r, 0.5)
        b = third_correlation_range(r, 0.9)
        rows.append(f"{r:.2f},{a[0]:.4f},{a[1]:.4f},{b[0]:.4f},{b[1]:.4f}")
    (OUT / "corr.csv").write_text("\n".join(rows) + "\n")


if __name__ == "__main__":
    main()
