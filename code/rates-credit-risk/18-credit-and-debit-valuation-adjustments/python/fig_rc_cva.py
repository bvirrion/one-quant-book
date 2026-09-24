"""Chart data for Book 6, chapter 18: CVA by year of default, bucketed CS01, wrong-way CVA and DVA against
the bank's own spread."""
import csv
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import rc_cva as m

OUT = pathlib.Path(__file__).resolve().parents[4] / "figdata/rates-credit-risk" / pathlib.Path(__file__).parents[1].name


def write(name, header, rows):
    OUT.mkdir(parents=True, exist_ok=True)
    with open(OUT / name, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(header)
        for r in rows:
            w.writerow([x if isinstance(x, str) else f"{x:.6g}" for x in r])


def main():
    write("contrib.csv", ["year", "cva"], m.contributions())
    write("cs01.csv", ["tenor", "cs01"],
          [(f"{t:g}y", float(round(c))) for t, c in zip(m.TENORS, m.cs01(), strict=True)])
    write("wwr.csv", ["b", "cva"], [(b, c / 1e6) for b, c in m.wrong_way((0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10))])
    write("dva.csv", ["shift", "dva"], [(s, d / 1e6) for s, d in m.dva_shift(tuple(range(0, 101, 10)))])


if __name__ == "__main__":
    main()
