"""Numbers gate: every numerical answer printed in Book 5, Chapter 16 (text and solutions)."""
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from dv_pathdep import (
    asian_by_fixings,
    asian_example,
    asians_by_model,
    cliquet_by_cap,
    cliquets,
    forward_smiles,
    lookback_table,
    model_paths,
    repricing_check,
    reverse_by_coupon,
)

P = model_paths()


def test_asians():
    a = asian_example()
    assert (round(a["cv"], 2), round(a["vanilla"], 2), round(100 * a["discount"])) == (5.32, 8.83, 40)
    assert (round(a["var_factor"], 3), round(math.sqrt(a["var_factor"]), 2), round(100 * math.sqrt(a["var_factor"]) * 0.2, 1)) == (
        0.376, 0.61, 12.3)
    assert round(13 * 25 / (6 * 144), 3) == 0.376
    assert (round(a["corr"], 4), round(a["beta"], 2), round(a["plain_se"], 3), round(a["cv_se"], 4), round(a["reduction"])) == (
        0.9996, 1.03, 0.025, 0.0007, 1357)
    rows = {n: (r, v) for n, r, v in asian_by_fixings()}
    assert [round(rows[n][0], 2) for n in (2, 4, 12, 252)] == [0.78, 0.68, 0.60, 0.57]
    assert [round(rows[n][1], 2) for n in (2, 4, 12, 252)] == [0.79, 0.68, 0.61, 0.58]
    m = asians_by_model(P)
    assert (round(m["lv"][0], 2), round(m["heston"][0], 2), round(m["bs"][0], 2)) == (4.34, 4.36, 4.69)
    assert abs(m["lv"][0] - m["heston"][0]) < 1.5 * math.hypot(m["lv"][1], m["heston"][1])


def test_lookbacks():
    lb = lookback_table((4, 12, 52, 252))
    assert round(lb["cont"], 2) == 15.69 and round(lb["cont"] / lb["vanilla"], 1) == 1.8
    rows = {r["n"]: (round(r["mc"], 2), round(r["shifted"], 2)) for r in lb["rows"]}
    assert rows == {252: (15.09, 15.08), 52: (14.42, 14.34), 12: (13.13, 12.84), 4: (11.55, 10.70)}
    assert round(lb["rows"][-1]["se"], 2) == 0.04
    assert round(0.5826 * 0.2 * math.sqrt(0.25), 2) == 0.06


def test_forward_smiles():
    r = repricing_check(P)
    assert (round(100 * r["market"], 2), round(100 * r["lv"], 2), round(100 * r["heston"], 2)) == (19.19, 19.19, 18.99)
    fs = forward_smiles(P)
    assert [round(100 * fs["today"][i], 1) for i in (0, 3, 6)] == [19.6, 14.9, 12.0]
    assert [round(100 * fs["lv"][i], 1) for i in (0, 3, 6)] == [23.9, 21.5, 21.3]
    assert [round(100 * fs["heston"][i], 1) for i in (0, 3, 6)] == [24.0, 18.5, 20.0]


def test_cliquets():
    c = cliquets(P)
    assert (round(100 * c["lv"]["cliquet"], 2), round(100 * c["heston"]["cliquet"], 2), round(100 * c["bs"]["cliquet"], 2)) == (
        1.53, 2.22, 1.19)
    assert round(100 * (c["heston"]["cliquet"] - c["lv"]["cliquet"]), 2) == 0.69
    assert round(100 * (c["heston"]["cliquet"] / c["lv"]["cliquet"] - 1)) == 45
    caps = {round(r[0], 3): r[1:] for r in cliquet_by_cap(P)}
    assert [round(100 * x, 2) for x in caps[0.005]] == [0.78, 1.16, 0.61]
    assert [round(100 * x, 2) for x in caps[0.05]] == [5.73, 6.12, 4.74]
    rc = reverse_by_coupon(P)
    assert [round(100 * rc[0.25][m], 2) for m in ("lv", "heston", "bs")] == [5.43, 7.56, 3.57]
    assert [round(100 * rc[0.15][m], 2) for m in ("lv", "heston", "bs")] == [1.23, 2.49, 0.58]
    assert [round(100 * rc[0.35][m], 2) for m in ("lv", "heston", "bs")] == [12.06, 14.55, 10.00]
    moves = [round(100 * (rc[0.35][m] - rc[0.15][m]), 1) for m in ("heston", "lv", "bs")]
    assert moves == [12.1, 10.8, 9.4] and round(rc[0.15]["heston"] / rc[0.15]["lv"]) == 2


def test_exercises():
    assert round(math.sqrt(45 / 96), 3) == 0.685 and round(1 / math.sqrt(3), 3) == 0.577
    assert round(math.exp(-0.01), 3) == 0.990
    sd = 0.025 * math.sqrt(100_000)
    assert round(sd, 1) == 7.9 or round(sd, 1) == 8.0
    a = asian_example()
    plain_sd, cv_sd = a["plain_se"] * math.sqrt(100_000), a["cv_se"] * math.sqrt(100_000)
    assert round(plain_sd, 1) == 8.0 and round((plain_sd / 0.001) ** 2 / 1e6) == 64
    assert round((cv_sd / 0.001) ** 2, -3) == 47_000
