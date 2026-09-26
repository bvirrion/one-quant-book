"""Numbers gate: every numerical answer printed in Book 11, chapter 7 (text and solutions)."""
import pathlib
import sys

from scipy.stats import norm

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
import hf_alpha as h  # noqa: E402


def r(x, d=3):
    return round(float(x), d)


def test_ics_and_coefficients():
    ic = h.ics()
    assert [r(ic[k]) for k in ("imbalance", "ofi", "flow", "lead", "own", "combined")] == [0.32, 0.285, 0.077, 0.288,
                                                                                            0.15, 0.48]
    c = h.coef_per_unit()
    assert (r(c["imbalance"], 2), r(c["ofi"], 4), r(c["flow"], 4), r(c["lead"], 2), r(c["own"], 2)) == (
        0.3, 0.0045, 0.0057, 0.34, 0.27)
    by = h.ic_by_horizon()
    assert [r(by[x]["combined"], 2) for x in h.HORIZONS] == [0.28, 0.37, 0.48, 0.54, 0.5]
    assert (r(by[0.5]["imbalance"]), r(by[10.0]["ofi"])) == (0.187, 0.372)


def test_delay_and_calibration():
    d = h.ic_by_delay()
    assert [(k, r(d[k]["ic"])) for k in (1, 10, 20, 50)] == [(1, 0.477), (10, 0.444), (20, 0.405), (50, 0.303)]
    assert (round(d[1]["ms"]), round(d[10]["ms"]), r(d[20]["ms"] / 1000, 1), r(d[50]["ms"] / 1000, 1)) == (33, 451, 0.9, 2.3)
    c = h.calibration()
    assert (r(100 * c["share_beyond_take"], 2), r(100 * c["share_beyond_skew"], 1)) == (0.01, 5.8)
    assert (r(c["pred"][-1], 2), r(c["real"][-1], 2)) == (0.31, 0.33)


def test_couplings():
    c = h.compare()
    got = [(round(v["passive_shares"]), r(v["passive_markout"]), r(v["takes"], 1), r(v["take_markout"]), r(v["pnl"], 2),
            r(v["sd"], 2)) for v in c.values()]
    assert got == [(16550, 0.294, 0.0, 0.0, -33.58, 107.68), (11050, 0.451, 0.0, 0.0, 25.58, 50.82),
                   (10867, 0.452, 4.2, 0.54, 46.17, 51.22), (10883, 0.414, 4.5, 0.722, 46.47, 36.29)]
    assert r(100 * (1 - 0.414 / 0.452), 0) == 8


def test_exercises():
    assert r(0.30 * (12 - 4) / 16, 2) == 0.15 and r(0.5 + 0.1, 1) == 0.6
    assert r(100 * 2 * norm.cdf(-0.9 / (0.48 * 0.6)), 2) == 0.18
