"""Chart data for Book 6, chapter 25: initial margin through the first half of 2020 by model, and the
three bilateral approaches today."""
import csv
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import rc_margin as m

OUT = pathlib.Path(__file__).resolve().parents[4] / "figdata/rates-credit-risk" / pathlib.Path(__file__).parents[1].name


def write(name, header, rows):
    OUT.mkdir(parents=True, exist_ok=True)
    with open(OUT / name, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(header)
        for r in rows:
            w.writerow([x if isinstance(x, str) else f"{x:.6g}" for x in r])


def main():
    r = m.replay_2020()
    s = r["series"]
    rows = []
    for i, d in enumerate(s["date"]):
        day = (d - s["date"][0]).days
        rows.append((day, s["hs"][i] / 1e6, s["fhs"][i] / 1e6, r["buffer"][i] / 1e6, r["stressed"][i] / 1e6,
                     1.0 if r["flags"][i] else 0.0))
    write("im2020.csv", ["day", "hs", "fhs", "buffer", "stressed", "flag"], rows)
    sch = m.schedule_today()
    write("approaches.csv", ["approach", "im"],
          [("HS 10-day", m.hs10_today() / 1e6), ("sensitivity-based", m.simm_today() / 1e6),
           ("schedule (NGR 0.5)", sch["net"] / 1e6), ("schedule gross", sch["gross"] / 1e6)])


if __name__ == "__main__":
    main()
