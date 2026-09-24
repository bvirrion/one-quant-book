"""Chart data for Book 6, chapter 20: Euler against standalone CVA, the proxy-spread fit, and the exposure
of the twenty-year swap."""
import csv
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import rc_xvadesk as m

OUT = pathlib.Path(__file__).resolve().parents[4] / "figdata/rates-credit-risk" / pathlib.Path(__file__).parents[1].name


def write(name, header, rows):
    OUT.mkdir(parents=True, exist_ok=True)
    with open(OUT / name, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(header)
        for r in rows:
            w.writerow([x if isinstance(x, str) else f"{x:.6g}" for x in r])


def main():
    a = m.allocation()
    names = ("swap", "cross-currency")
    write("euler.csv", ["trade", "standalone", "euler"],
          [(n, s / 1e3, e / 1e3) for n, s, e in zip(names, a["standalone"], a["euler"], strict=True)])
    rows = m.proxy_fit_table()
    for rating in ("A", "BBB", "BB"):
        write(f"proxy_{rating.lower()}.csv", ["observed", "fitted"], [(o, f) for o, f, r in rows if r == rating])
    write("ee20.csv", ["t", "ee"], m.quote_profile())


if __name__ == "__main__":
    main()
