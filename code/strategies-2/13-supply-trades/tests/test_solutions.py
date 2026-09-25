"""Numbers gate: every numerical answer printed in Book 9, chapter 13 (text and solutions)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from s2_supply import real, results  # noqa: E402


def r(x, d=2):
    return round(float(x), d)


def test_synthetic():
    x = results()
    assert {k: (r(x[k]["mean"]), r(x[k]["t"], 1), r(x[k]["sr"]), x[k]["n"]) for k in ("both", "before", "after")} == {
        "both": (3.44, 3.1, 0.7, 239), "before": (1.71, 2.2, 0.5, 239), "after": (1.72, 2.2, 0.5, 239)}
    assert [(r(g["size"], 1), r(g["mean"])) for g in x["terciles"]] == [(24.3, 1.66), (33.2, 4.94), (41.1, 3.72)]
    assert (r(x["slope_size"]), r(x["slope_pressure"]), r(x["concession_mean"])) == (0.24, 0.16, 2.6)


def test_real():
    x = real()
    got = {b: (int(v["n"]), r(v["pre_mean"]), r(v["pre_t"], 1), r(v["post_mean"]), r(v["post_t"], 1)) for b, v in x.items()}
    assert got == {"2y": (354, -0.4, -0.9, -0.62, -1.3), "5y": (249, 1.03, 1.5, -2.16, -3.1), "7y": (200, -0.53, -0.7, -2.02, -2.1),
                   "10y": (301, 1.98, 3.0, -0.28, -0.4), "30y": (234, 2.56, 3.6, -0.81, -1.1)}
    t = x["10y"]
    assert [(r(t[f"size{k}_mean_bn"], 1), r(t[f"size{k}_pre"]), r(t[f"size{k}_post"])) for k in (1, 2, 3)] == [
        (14.5, 1.48, -1.64), (22.3, 1.69, -0.24), (36.2, 2.95, 1.44)]


def test_path():
    import csv

    from s2_supply import DATA
    rows = {int(x["day"]): x for x in csv.DictReader(open(DATA / "auctions_path.csv"))}
    assert (r(float(rows[-5]["mean_bp"])), r(float(rows[0]["mean_bp"])), r(float(rows[5]["mean_bp"])), rows[0]["n"]) == (
        0.57, 1.47, 0.4, "1338")


def test_exercises():
    import math

    from firm_supplytrade import supply_trade
    from s2_supply import market, no_giveback
    n = no_giveback()
    assert (r(n["both"]), r(n["before"]), r(n["after"])) == (1.62, 1.71, -0.09)
    cfg, sim = market()
    assert r(supply_trade(sim, cfg)["pnl"].std(ddof=1), 0) == 17.0
    assert (r(0.07 * 40, 1), r(3.44 / 17 * math.sqrt(12)), 40e9 * 0.0009 / 1e6, 40e9 * 0.0018 / 1e6) == (2.8, 0.7, 36.0, 72.0)


def test_iq6():
    assert round(4 * 5 * 5.5**2 / 2.6**2) == 89 and round(4 * 5 * 5.5**2 / 2.6**2, -1) == 90
