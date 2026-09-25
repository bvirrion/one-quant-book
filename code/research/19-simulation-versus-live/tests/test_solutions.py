"""Numbers gate: every numerical answer printed in Book 7, chapter 19 (text and solutions)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm" / "simlive"))
from firm_simlive import as_fills, implementation_shortfall, parity
from rs_simlive import alone_at_price, decomposition, effective_latency, model_calibration, steps, vanished_volume


def r(x, d=1):
    return round(float(x), d)


def test_decomposition():
    rows, mean = decomposition()
    assert (round(mean["live_lots"]), round(mean["sim_lots"])) == (597, 305)
    assert (round(100 * mean["parity_live"]), round(100 * mean["parity_sim"])) == (27, 54)
    w = steps(mean)
    assert [r(v) for _, v, _ in w] == [-50.5, -56.4, -112.8, -431.2, -490.9]
    assert [r(d) for _, _, d in w][1:] == [-5.9, -56.4, -318.3, -59.7]
    assert r(mean["chance_gap"]) == 62.8
    assert all(x["live"] < min(x["sim"], x["chance"]) for x in rows)


def test_locating_and_calibration():
    assert round(100 * vanished_volume()) == 68
    a = alone_at_price()
    assert (round(100 * a["share_alone"]), r(a["markout_alone"], 2), r(a["markout_other"], 2)) == (21, -0.85, -0.11)
    (best, lots), target = effective_latency()
    assert (best, round(lots), round(target)) == (0.0, 1898, 3582)
    m = model_calibration()
    assert (round(m["front"][0]), round(m["front"][1]), round(m["live"][0]), round(m["live"][1])) == (8886, 2207, 3582, -2587)


def test_exercises():
    live = as_fills([(10.2, 1, 50.00, 100), (14.0, -1, 50.02, 100)])
    sim = as_fills([(10.9, 1, 50.00, 100), (12.0, 1, 49.99, 100)])
    assert parity(live, sim, 1.0) == (0.5, 0.5)
    s = implementation_shortfall(1, 10_000, 20.00, as_fills([(0, 1, 20.04, 6_000)]), 20.30, 0.002)
    assert [round(s[k], 2) for k in ("execution", "opportunity", "fees", "total")] == [240.0, 1200.0, 12.0, 1452.0]
