"""Chart data for Book 6, chapter 26: the tree validation by expiry and step, and the averaging error's
effect on the loss distribution."""
import csv
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import rc_modelval as m

OUT = pathlib.Path(__file__).resolve().parents[4] / "figdata/rates-credit-risk" / pathlib.Path(__file__).parents[1].name


def write(name, header, rows):
    OUT.mkdir(parents=True, exist_ok=True)
    with open(OUT / name, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(header)
        for r in rows:
            w.writerow([x if isinstance(x, str) else f"{x:.6g}" for x in r])


def main():
    write("validation.csv", ["expiry", "err_q", "fail_q", "err_m", "fail_m"],
          [(f"{e}y", a, b, c, d) for e, a, b, c, d in m.errors_by_expiry()])
    a = m.averaging_error()
    li = np.sort(-a["intended"]["pnl"])[::-1] / 1e6
    le = np.sort(-a["error"]["pnl"])[::-1] / 1e6
    rows = [(i + 1, x, y) for i, (x, y) in enumerate(zip(li, le, strict=True))][:40]
    write("losses.csv", ["rank", "intended", "error"], rows)


if __name__ == "__main__":
    main()
