"""Chart data for Book 6, chapter 17: exposure profiles of a swap, a cross-currency swap and their netting
set, collateralised profiles, a collateral path and wrong-way exposure."""
import csv
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import rc_exposure as m

OUT = pathlib.Path(__file__).resolve().parents[4] / "figdata/rates-credit-risk" / pathlib.Path(__file__).parents[1].name


def write(name, header, rows):
    OUT.mkdir(parents=True, exist_ok=True)
    with open(OUT / name, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(header)
        for r in rows:
            w.writerow([f"{(0.0 if abs(x) < 1e-9 else x):.5g}" for x in r])


def main():
    ps = m.profile_set()
    t = m.scenarios().times[:-1]
    g = {k: v[0] for k, v in ps.items()}
    write("profiles.csv", ["t", "swap_ee", "swap_pfe", "xccy_ee", "xccy_pfe"],
          [(t[i], g["swap"]["ee"][i] / 1e6, g["swap"]["pfe"][i] / 1e6, g["xccy"]["ee"][i] / 1e6,
            g["xccy"]["pfe"][i] / 1e6) for i in range(len(t))])
    write("netting.csv", ["t", "sum_ee", "net_ee", "net_ene"],
          [(t[i], (g["swap"]["ee"][i] + g["xccy"]["ee"][i]) / 1e6, g["net"]["ee"][i] / 1e6, g["net"]["ene"][i] / 1e6)
           for i in range(len(t))])
    write("collat.csv", ["t", "none", "csa10", "csa20", "th10"],
          [(t[i], g["net"]["ee"][i] / 1e6, g["csa10"]["ee"][i] / 1e6, g["csa20"]["ee"][i] / 1e6,
            g["csa_th"]["ee"][i] / 1e6) for i in range(len(t))])
    w = m.wrong_way()
    rows = [(w["t"][i], w["ee"][i] / 1e6, w["cee"][i] / 1e6) for i in range(1, len(w["t"]) - 1)]
    write("wwr.csv", ["t", "ee", "cee"], rows)


if __name__ == "__main__":
    main()
