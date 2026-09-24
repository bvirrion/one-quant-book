"""Chart data for Book 6, chapter 15: loss distributions, the mezzanine against compound correlation,
Gaussian and Student-t tails, and tranche delta ratios."""
import csv
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import rc_portcredit as m

OUT = pathlib.Path(__file__).resolve().parents[4] / "figdata/rates-credit-risk" / pathlib.Path(__file__).parents[1].name


def write(name, header, rows):
    OUT.mkdir(parents=True, exist_ok=True)
    with open(OUT / name, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(header)
        for r in rows:
            w.writerow([x if isinstance(x, str) else f"{x:.6g}" for x in r])


def main():
    d = m.loss_distribution_table()
    write("loss_dist.csv", ["k", "r05", "r25", "r50"], [(k, d[0][k], d[1][k], d[2][k]) for k in range(0, 41)])
    q = 1e4 * m.quotes()[1][2]
    write("mezz.csv", ["rho", "par", "quote"], [(r, s, q) for r, s in m.mezz_curve()])
    write("tails.csv", ["x", "gauss", "t4"], [(100 * x, g, t) for x, g, t in m.tail_table()])
    ratio = m.deltas()["ratio"]
    write("deltas.csv", ["tranche", "delta"], [(f"{100 * a:g}-{100 * b:g}", ratio[(a, b)]) for a, b in m.TRANCHES])


if __name__ == "__main__":
    main()
