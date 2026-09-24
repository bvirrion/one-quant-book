"""Chart data for Book 6, chapter 27: the day's attribution, and the unexplained P&L against the size of
the rate move."""
import csv
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import rc_pnlexplain as m

OUT = pathlib.Path(__file__).resolve().parents[4] / "figdata/rates-credit-risk" / pathlib.Path(__file__).parents[1].name


def write(name, header, rows):
    OUT.mkdir(parents=True, exist_ok=True)
    with open(OUT / name, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(header)
        for r in rows:
            w.writerow([x if isinstance(x, str) else f"{x:.6g}" for x in r])


def main():
    d = m.day()
    rows = [("delta", d["desk"]["delta"] / 1e3, d["full"]["delta"] / 1e3),
            ("vanna", 0.0, d["full"]["vanna"] / 1e3),
            ("unexplained", d["unexplained_desk"] / 1e3, d["unexplained_full"] / 1e3)]
    write("attribution.csv", ["term", "desk", "full"], rows)
    write("unexplained.csv", ["bp", "desk", "full"], [(a, b / 1e3, c / 1e3) for a, b, c in m.unexplained_by_move()])


if __name__ == "__main__":
    main()
