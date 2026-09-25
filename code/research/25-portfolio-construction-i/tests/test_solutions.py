"""Numbers gate: every numerical answer printed in Book 7, chapter 25 (text and solutions)."""
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from rs_portcons import SETTINGS, dates, decomposition, run, summary


def r(x, d=2):
    return round(float(x), d)


EXPECTED = {  # ex ante, realised, net, cost %/yr, turnover, gross, TC, vol forecast %, vol realised %
    0: (4.25, 0.92, 0.43, 100, 84, 61, 0.44, 36, 207),
    1: (1.64, 1.89, 1.39, 6.9, 5.80, 4.44, 0.97, 13.7, 14.0),
    2: (1.59, 1.72, 1.22, 6.8, 5.70, 4.35, 0.92, 13.3, 13.6),
    3: (1.41, 1.29, 0.83, 3.0, 2.50, 2.21, 0.82, 6.4, 6.6),
    4: (1.44, 1.40, 0.94, 2.8, 2.37, 2.00, 0.83, 6.1, 6.3),
    5: (1.23, 0.87, 0.46, 1.9, 1.55, 1.34, 0.71, 4.4, 4.4),
    6: (1.00, 1.94, 1.77, 0.6, 0.53, 1.01, 0.58, 3.5, 3.6),
}


def test_settings():
    assert len(dates()) == 95 and len(SETTINGS) == 7
    for k, exp in EXPECTED.items():
        s = summary(k)
        d = 0 if k == 0 else 1
        got = (r(s["ir_ex_ante"]), r(s["ir_realised"]), r(s["ir_net"]), r(100 * s["cost"], d), r(s["turnover"], 2 - 2 * (k == 0)),
               r(s["gross"], 2 - 2 * (k == 0)), r(s["tc"]), r(100 * s["vol_pred"], d), r(100 * s["vol_real"], d))
        assert got == exp, (k, got)
    n = summary(0)
    assert (r(100 * n["top2"], 0), r(100 * n["top2_max"], 0)) == (9, 16)


def test_decomposition_and_binding():
    d = decomposition(6)
    assert [r(100 * d[k], 1) for k in ("factor neutral", "name limits", "liquidity", "turnover limit")] == [7.0, 3.1, 39.4, 44.0]
    assert r(100 * d["gross limit"], 3) == 0.0 and r(100 * d["dollar neutral"], 1) == 0.0
    rows = run(6)
    avg = {k: sum(x["binding"].get(k, 0) for x in rows) / len(rows) for k in ("name limits", "liquidity", "turnover limit")}
    assert (r(avg["name limits"], 1), r(avg["liquidity"], 1), r(avg["turnover limit"], 1)) == (2.5, 28.3, 1.0)


def test_exercises():
    assert r(math.sqrt((1 + 1.77**2 / 2) / 7.9), 2) == 0.57 and r(math.sqrt((1 + 1.39**2 / 2) / 7.9), 2) == 0.5
    assert r(84 * 12 * 0.0010, 2) == 1.01 and r(5.8 * 12 * 0.0010 * 100, 1) == 7.0
    assert r(0.05 * 10e6 / 1e9 * 100, 2) == 0.05
    assert (r(0.02 / (5 * 0.04)), r(0.01 / (5 * 0.01))) == (0.1, 0.2) and r(math.sqrt(0.02**2 / 0.04 + 0.01**2 / 0.01)) == 0.14
