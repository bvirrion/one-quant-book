"""Numbers gate: every numerical answer printed in Book 9, chapter 23 (text and solutions)."""
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm" / "powergas"))
from firm_powergas import PowerConfig  # noqa: E402
from s2_powergas import battery_table, real, trade  # noqa: E402


def r(x, d=0):
    return round(float(x), d)


def test_real():
    x = real()
    assert (r(x["slope"], 2), r(x["corr"], 2), x["days"]) == (3.05, 0.83, 727)
    assert (x["negative"][2024], x["negative"][2025], r(x["min"][2025], 2), r(x["min"][2024], 2)) == (457, 573, -250.32,
                                                                                                        -135.45)
    assert (r(100 * x["neg_by_hour"][13], 1), x["neg_by_hour"][19], r(x["mean"][2024], 2), r(x["mean"][2025], 2)) == (
        23.4, 0.0, 78.51, 89.32)


def test_trade():
    t = trade()
    assert (r(t["per_mwh"], 2), r(t["annual"], -2), r(t["ic"], 2), r(100 * t["share"])) == (2.54, 13600, 0.36, 61)
    t = trade(PowerConfig(skill=0.3))
    assert (r(t["per_mwh"], 2), r(t["annual"], -2), r(t["ic"], 2)) == (1.08, 5800, 0.21)
    t = trade(PowerConfig(id_cost=3.0))
    assert (r(t["per_mwh"], 2), r(t["annual"], -2), r(t["ic"], 2)) == (0.54, 2900, 0.36)
    assert r(2.54 * 0.61 * 24 * 727 / 2, -2) == 13500                                      # exercise 3


def test_battery():
    b = battery_table()
    assert (r(b["da"], -2), r(b["extra"], -2), r(100 * b["days_changed"]), r(100 * b["charge_negative"], 1)) == (
        69900, 2900, 71, 24.8)
    assert r(battery_table(PowerConfig(id_cost=0.0))["extra"], -2) == 3800
    assert r(battery_table(PowerConfig(id_cost=3.0))["extra"], -2) == 1600
    b2 = battery_table(PowerConfig(cycles=2))
    assert (r(b2["da"], -2), r(b2["extra"], -2), r(b2["da"] - b["da"], -2)) == (83800, 4900, 13800)


def test_by_hand():
    assert (r(1.5 * 3.05, 1), r(2 * math.sqrt(0.88) * 100, 2)) == (4.6, 187.62)          # exercises 1, 2
    from s2_powergas import hourly
    d = hourly()
    assert r(d.loc[d["year"] == 2024, "price"].max(), 2) == 936.28
    rng = d.groupby("day")["price"].agg(lambda p: p.max() - p.min())
    assert rng.mean() > 100
