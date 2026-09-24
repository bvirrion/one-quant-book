"""Chart data for Book 6, chapter 19: the adjustment stack, the capital profile and the initial margin profile."""
import csv
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import rc_xvafund as m

OUT = pathlib.Path(__file__).resolve().parents[4] / "figdata/rates-credit-risk" / pathlib.Path(__file__).parents[1].name


def write(name, header, rows):
    OUT.mkdir(parents=True, exist_ok=True)
    with open(OUT / name, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(header)
        for r in rows:
            w.writerow([x if isinstance(x, str) else f"{x:.6g}" for x in r])


def main():
    names = {"cva": "CVA", "dva": "-DVA", "fca": "FCA", "fba": "-FBA", "mva": "MVA", "kva": "KVA", "total": "total"}
    sign = {"dva": -1, "fba": -1}
    write("stack.csv", ["item", "uncoll", "csa"],
          [(names[k], sign.get(k, 1) * a / 1e3, sign.get(k, 1) * b / 1e3) for k, a, b in m.stack_table()])
    c = m.capital_profile()
    write("capital.csv", ["t", "ccr", "cva", "total"],
          [(float(t), a / 1e3, b / 1e3, (a + b) / 1e3) for t, a, b in zip(c["t"], c["ccr"], c["cva"], strict=True)])
    write("im.csv", ["t", "im"], [(t, x / 1e6) for t, x in m.im_profile(m.NOTIONAL, 10, m.swap_rate())])


if __name__ == "__main__":
    main()
