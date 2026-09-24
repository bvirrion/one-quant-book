import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import firm_pnlexplain as f


def quad(s):
    return 3.0 * s["f"] + 2.0 * s["f"] ** 2 + 5.0 * s["s"] + 0.5 * s["s"] ** 2 + 7.0 * s["f"] * s["s"] - 0.1 * s["t"]


START = {"f": 1.0, "s": 2.0, "t": 10.0}
END = {"f": 1.3, "s": 1.8, "t": 9.0}


def test_risk_based_explains_a_quadratic_exactly():
    g = f.greeks(quad, START, {"f": 1e-3, "s": 1e-3, "t": 1.0})
    r = f.risk_based(g, 0.3, -0.2, 1.0, cross=True)
    assert math.isclose(r["explained"], quad(END) - quad(START), rel_tol=1e-6)
    assert not math.isclose(f.risk_based(g, 0.3, -0.2, 1.0, cross=False)["explained"], quad(END) - quad(START),
                            rel_tol=1e-3)


def test_revaluation_adds_up_and_depends_on_order():
    a = f.revaluation_based(quad, START, END, ["f", "s", "t"])
    b = f.revaluation_based(quad, START, END, ["s", "f", "t"])
    assert math.isclose(a["total"], quad(END) - quad(START)) and math.isclose(b["total"], a["total"])
    assert not math.isclose(a["f"], b["f"])


def test_ipv_and_prudent_valuation():
    assert f.ipv([10.0, 13.0, 7.0], [10.0, 10.0, 10.0], [2.0, 2.0, 2.0]) == [(10.0, 0.0), (12.0, -1.0), (8.0, 1.0)]
    assert math.isclose(f.mpu_ava(100.0, 100.0, 1.0, 1.0), 1.2815515655, rel_tol=1e-9)
    assert math.isclose(f.mpu_ava(-100.0, 100.0, 1.0, -1.0), 1.2815515655, rel_tol=1e-9)
    assert f.aggregate_ava([2.0, 4.0]) == 3.0 and math.isclose(f.simplified_ava(1e9), 1e6)
