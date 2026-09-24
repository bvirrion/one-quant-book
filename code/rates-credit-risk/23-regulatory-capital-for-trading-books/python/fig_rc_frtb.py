"""Chart data for Book 6, chapter 23: standardised charges by component and scenario, the ES of the
twelve-month windows, and the attribution scatter."""
import csv
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import rc_frtb as m

OUT = pathlib.Path(__file__).resolve().parents[4] / "figdata/rates-credit-risk" / pathlib.Path(__file__).parents[1].name


def write(name, header, rows):
    OUT.mkdir(parents=True, exist_ok=True)
    with open(OUT / name, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(header)
        for r in rows:
            w.writerow([x if isinstance(x, str) else f"{x:.6g}" for x in r])


def main():
    s = m.standardised()
    names = {"girr": "GIRR delta", "fx_delta": "FX delta", "fx_vega": "FX vega", "fx_curv": "FX curvature"}
    write("sa.csv", ["part", "low", "medium", "high"],
          [(names[k], s["parts_low"][k] / 1e6, s["parts"][k] / 1e6, s["parts_high"][k] / 1e6) for k in names])
    d, lv = m.rv.data()
    x = m.ten_day_moves(lv)
    mask = m._masks()["all"]
    def year(s):
        y, mo, dd = (int(v) for v in s.split("-"))
        return y + (mo - 1) / 12 + (dd - 1) / 365

    rows = [(year(d[i + 259]), m.es_window(x[i:i + 250], mask) / 1e6) for i in range(0, len(x) - 250, 5)]
    write("es_windows.csv", ["end", "es"], rows)
    p = m.pla("proxy_10y")
    write("pla.csv", ["hpl", "rtpl"], [(a / 1e6, b / 1e6) for a, b in zip(p["hpl"], p["rtpl"], strict=True)])


if __name__ == "__main__":
    main()
