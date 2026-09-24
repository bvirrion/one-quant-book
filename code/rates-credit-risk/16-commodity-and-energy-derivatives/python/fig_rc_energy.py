"""Chart data for Book 6, chapter 16: forward curve and storage plan, forward volatility term structure,
Kirk's error against Monte Carlo, and Henry Hub in February 2021."""
import csv
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import rc_energy as m

OUT = pathlib.Path(__file__).resolve().parents[4] / "figdata/rates-credit-risk" / pathlib.Path(__file__).parents[1].name


def write(name, header, rows):
    OUT.mkdir(parents=True, exist_ok=True)
    with open(OUT / name, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(header)
        for r in rows:
            w.writerow([x if isinstance(x, str) else f"{x:.6g}" for x in r])


def main():
    write("curve.csv", ["month", "forward", "action", "inventory"], m.curve_table())
    vols, quotes = m.vol_table()
    write("vol.csv", ["tau", "vol"], vols)
    write("volquotes.csv", ["t", "vol"], [(t, 100 * v) for t, v in sorted(quotes.items())])
    write("kirk.csv", ["k", "err", "se"], m.kirk_table())
    import datetime as dt
    jan1 = dt.date(2021, 1, 1)
    write("henryhub.csv", ["day", "price"], [((d - jan1).days, p) for d, p in m.henry_hub()])


if __name__ == "__main__":
    main()
