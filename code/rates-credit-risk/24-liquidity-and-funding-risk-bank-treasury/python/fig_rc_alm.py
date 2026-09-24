"""Chart data for Book 6, chapter 24: supervisory shocks, EVE changes, NII sensitivity, liquidity sources."""
import csv
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import rc_alm as m

OUT = pathlib.Path(__file__).resolve().parents[4] / "figdata/rates-credit-risk" / pathlib.Path(__file__).parents[1].name


def write(name, header, rows):
    OUT.mkdir(parents=True, exist_ok=True)
    with open(OUT / name, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(header)
        for r in rows:
            w.writerow([x if isinstance(x, str) else f"{x:.6g}" for x in r])


def main():
    write("shocks.csv", ["t", "pu", "pd", "su", "sd", "st", "fl"], m.shock_table())
    e = m.eve_table()["delta"]
    names = {"parallel_up": "parallel+", "parallel_down": "parallel-", "short_up": "short+",
             "short_down": "short-", "steepener": "steepener", "flattener": "flattener"}
    write("eve.csv", ["scenario", "delta"], [(names[k], v) for k, v in e.items()])
    a, b = m.nii_path(0.35), m.nii_path(0.80)
    write("nii.csv", ["bp", "beta35", "beta80"], [(x, y, z) for (x, y), (_, z) in zip(a, b, strict=True)])
    htm = 90.0 * (1 + m.htm_loss()["pct"])
    write("liquidity.csv", ["source", "amount"],
          [("cash", 15.0), ("Treasuries (market)", 25.0 + m.afs_loss()), ("MBS (market)", htm)])


if __name__ == "__main__":
    main()
