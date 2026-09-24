"""Chart data for Book 6, chapter 21: the historical P&L distribution, VaR and ES by method, the four-year
backtest, and Euler contributions."""
import csv
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import rc_var as m

OUT = pathlib.Path(__file__).resolve().parents[4] / "figdata/rates-credit-risk" / pathlib.Path(__file__).parents[1].name


def write(name, header, rows):
    OUT.mkdir(parents=True, exist_ok=True)
    with open(OUT / name, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(header)
        for r in rows:
            w.writerow([x if isinstance(x, str) else f"{x:.6g}" for x in r])


def main():
    write("hist.csv", ["pnl", "count"], m.histogram())
    write("methods.csv", ["method", "var99", "es975"], m.method_table())
    b = m.backtest()
    write("backtest.csv", ["day", "pnl", "var_hs", "var_ewma"],
          [(i, r[1] / 1e6, -r[2] / 1e6, -r[3] / 1e6) for i, r in enumerate(b["rows"])])
    write("exceptions.csv", ["day", "pnl"],
          [(i, r[1] / 1e6) for i, r in enumerate(b["rows"]) if r[1] < -r[3]])
    o = m.measures()
    write("euler.csv", ["factor", "contrib"],
          [(n, c / 1e6) for n, c in zip(("2y yield", "10y yield", "EURUSD", "USDJPY"), o["euler"], strict=True)])


if __name__ == "__main__":
    main()
