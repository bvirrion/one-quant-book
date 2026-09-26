"""Numbers gate: every numerical answer printed in Book 11, chapter 5 (text and solutions)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
import hf_queues as h  # noqa: E402


def r(x, d=3):
    return round(float(x), d)


def test_regime_and_intensities():
    e = h.fitted()
    assert r(100 * e["one_tick"], 1) == 96.3 and e["median_queue"] == 17.0
    assert (r(e["C"][1], 2), r(e["M"][2], 2)) == (0.34, 0.55)
    assert 1.4 < e["C"][10] < 1.7 and 0.25 < e["M"][15] < 0.35
    assert (r(min(e["L"][1:16]), 1), r(max(e["L"][1:16]), 1)) == (1.3, 2.3)


def test_values():
    v = h.values()
    i10, i2, i20 = h.QS.index(10), h.QS.index(2), h.QS.index(20)
    assert (r(v["front"]["value"][i10, i2], 2), r(v["back"]["value"][i10, i2], 2)) == (0.6, 0.32)
    assert (r(v["front"]["value"][i2, i20], 2), r(v["back"]["value"][i2, i20], 2)) == (0.12, 0.12)
    assert r(v["back"]["fill"][i20, i2], 2) == 0.5
    x = h.qr.order_value(h.model(), 0, 10, 2, paths=4000, seed=6)
    assert (r(x["fill"]), r(x["value"]), r(x["adverse"], 2)) == (0.825, 0.594, -0.22)


def test_rules_in_the_market():
    c = h.compare()
    rows = [(round(x["shares"]), r(x["markout10"]), r(x["edge10"], 2), r(x["pnl"], 2), r(x["sd"], 2), round(x["messages"]))
            for x in c.values()]
    assert rows == [(11167, 0.026, 2.92, 5.33, 63.67, 365), (6900, -0.117, -8.08, -32.0, 68.41, 245),
                    (3400, 0.392, 13.33, -6.5, 23.82, 468), (4450, 0.032, 1.42, -26.5, 63.22, 448)]
    s = h.sweep()
    assert max(s, key=lambda th: s[th]["edge10"]) == 0.3 and max(s, key=lambda th: s[th]["markout10"]) == 0.4
    assert r(s[0.4]["markout10"]) == 0.484


def test_exercises():
    assert r(290 / 200, 2) == 1.45 and r(3 / 15, 1) == 0.2 and r(0.392 * 3400 * 0.01, 2) == 13.33
