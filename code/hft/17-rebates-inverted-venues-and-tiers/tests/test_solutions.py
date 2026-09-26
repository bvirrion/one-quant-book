"""Numbers gate: every numerical answer printed in Book 11, chapter 17 (text and solutions)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
import hf_rebates as h  # noqa: E402

rm = h.rm


def r(x, d=2):
    return round(float(x), d)


def test_venues():
    v = h.venues()
    mt, inv = v["maker-taker"], v["inverted"]
    assert (r(mt["fill_prob"]), r(mt["sweep_share"]), r(mt["edge_per_order"]), r(mt["edge_per_fill"])) == (0.42, 0.91, -0.05, -0.13)
    assert (r(inv["fill_prob"]), r(inv["sweep_share"]), r(inv["edge_per_order"], 3)) == (0.74, 0.24, 0.005)
    b = h.by_queue()
    assert r(b["maker-taker"][2000]) == 0.40 and r(b["inverted"][20000]) == -0.24
    assert h.zero_queue() == 12800.0


def test_tier():
    t = h.tier()
    assert [r(x) for x in t["marginal"].values()] == [-0.20, -20.0, -0.29]
    c = t["chase"]
    assert (r(c["gain"] / 100, -3), r(c["cost"] / 100, -3), r(c["net"] / 100, -4)) == (584000, 504000, 80000)
    assert r(t["chase_14m"]["net"] / 100, -3) == -256000 and t["breakeven"] == 17.05e6 and t["last_day"] == 14


def test_exercises():
    assert r(21 * 18e6 * 0.20 / 100) == 756000 and r(21 * 18e6 * 0.29 / 100) == 1096200


def test_chase_curve_figure():
    c = {r["natural"]: r for r in h.chase_curve()}
    assert c[17]["net"] < 0 < c[18]["net"] and round(c[18]["net"], -4) == 80_000 and round(c[14]["net"], -3) == -256_000
    assert c[12]["gain"] > c[21]["gain"] and c[12]["cost"] - c[21]["cost"] > c[12]["gain"] - c[21]["gain"]
