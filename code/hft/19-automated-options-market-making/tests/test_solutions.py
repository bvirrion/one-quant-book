"""Numbers gate: every numerical answer printed in Book 11, chapter 19 (text and solutions)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
import hf_options as h  # noqa: E402


def r(x, d=0):
    return round(float(x), d)


def test_quotes_and_refit():
    w = h.widths()
    a = w["atm_30d_call"]
    assert w["n"] == 170 and r(a["theo"], 2) == 2.92 and r(a["vega"], 3) == 0.114 and r(a["ask"] - a["bid"], 2) == 0.11
    assert (r(w["min_width"], 2), r(w["max_width"], 2)) == (0.01, 0.20)
    f = h.refit()
    assert r(100 * f["rms_to_true"], 3) == 0.025


def test_protection():
    t = h.protection_table()
    assert [r(t[n]["sweep_loss"]) for n in (2, 5, 10, 13, 20, 40, 10**9)] == [1980, 4950, 9899, 12867, 19773, 38718, 79370]
    assert [t[n]["day_lost"] for n in (2, 5, 10, 13, 20, 40, 10**9)] == [2441, 1052, 326, 3, 0, 0, 0]
    assert [r(t[n]["edge_lost"]) for n in (2, 5, 10, 13)] == [9764, 4208, 1304, 12]
    assert t[10**9]["day_fills"] == 8235 and t[10**9]["targets"] == 150 and r(t[13]["delta"], -3) == -13000
    assert r(t[10**9]["edge_kept"]) == 32940


def test_vol_sweep_and_exercises():
    v = h.vol_sweep()
    assert r(v[(None, 50.0)]["loss"], -2) == 16500 and r(v[(None, 50.0)]["vega"], -2) == -10600
    assert r(v[(1000.0, 50.0)]["loss"], -2) == 9900 and r(v[(1000.0, 5.0)]["loss"], -2) == 6700
    b = h.bigger_move()
    assert (r(b["protected"], -2), r(b["unprotected"], -2), b["targets"]) == (25900, 164300, 151)
