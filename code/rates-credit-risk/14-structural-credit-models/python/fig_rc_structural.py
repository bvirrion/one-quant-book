"""Chart data for Book 6, chapter 14: equity and debt against assets, Merton term structures,
first-passage term structures, and the model spread against the equity value."""
import csv
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import rc_structural as m

OUT = pathlib.Path(__file__).resolve().parents[4] / "figdata/rates-credit-risk" / pathlib.Path(__file__).parents[1].name


def write(name, header, rows):
    OUT.mkdir(parents=True, exist_ok=True)
    with open(OUT / name, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(header)
        for r in rows:
            w.writerow([f"{x:.4f}" for x in r])


def main():
    write("equity_debt.csv", ["v", "equity", "debt", "payoff"], m.equity_debt_table())
    lev = [m.merton_term_structure(d) for d in (0.5, 0.9, 1.2)]
    write("merton_ts.csv", ["t", "d05", "d09", "d12"], [(a[0], a[1], b[1], c[1]) for a, b, c in zip(*lev, strict=True)])
    fps = [m.fp_term_structure(L) for L in (0.6, 0.7, m.implied_barrier())]
    write("fp_ts.csv", ["t", "l60", "l70", "limp"], [(a[0], a[1], b[1], c[1]) for a, b, c in zip(*fps, strict=True)])
    write("equity_spread.csv", ["e", "spread"], m.equity_spread_curve())


if __name__ == "__main__":
    main()
