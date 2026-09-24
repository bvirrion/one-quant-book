"""Chart data for Book 6, chapter 22: historical scenario losses against VaR, and the reverse stress
scenarios."""
import csv
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import rc_stress as m

OUT = pathlib.Path(__file__).resolve().parents[4] / "figdata/rates-credit-risk" / pathlib.Path(__file__).parents[1].name


def write(name, header, rows):
    OUT.mkdir(parents=True, exist_ok=True)
    with open(OUT / name, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(header)
        for r in rows:
            w.writerow([x if isinstance(x, str) else f"{x:.6g}" for x in r])


def main():
    rows = [("ten-day VaR", m.var10() / 1e6)] + [(n, -p / 1e6) for n, _, p in reversed(m.historical_table())]
    write("historical.csv", ["scenario", "loss"], rows)
    r = m.reverse()
    names = ("2y", "10y", "EURUSD", "USDJPY")
    sd = m.cov10().diagonal() ** 0.5
    write("reverse.csv", ["factor", "linear", "full"],
          [(n, a / k, b / k) for n, a, b, k in zip(names, r["x_lin"], r["x_nl"], sd, strict=True)])


if __name__ == "__main__":
    main()
