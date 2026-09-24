"""Chart data for Book 6, chapter 28: hit and false-alarm rates of the surveillance rules."""
import csv
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import rc_tradecontrol as m

OUT = pathlib.Path(__file__).resolve().parents[4] / "figdata/rates-credit-risk" / pathlib.Path(__file__).parents[1].name


def write(name, header, rows):
    OUT.mkdir(parents=True, exist_ok=True)
    with open(OUT / name, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(header)
        for r in rows:
            w.writerow([x if isinstance(x, str) else f"{x:.6g}" for x in r])


def main():
    s = m.surveillance()
    short = {"late booking": "late booking", "cancel/amend near reporting": "cancel near report",
             "off-market price": "off-market", "internal unmatched": "internal unmatched",
             "deferred settlement": "deferred settle", "combined": "any rule"}
    rows = [(short[k], 100 * v["hit"], 100 * v["false"]) for k, v in s["one"].items()]
    rows.append(("two rules", 100 * s["two"]["combined"]["hit"], 100 * s["two"]["combined"]["false"]))
    write("rules.csv", ["rule", "hit", "false"], rows)


if __name__ == "__main__":
    main()
