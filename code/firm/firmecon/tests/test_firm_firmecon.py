import math
import pathlib
import sys

import numpy as np
import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import firm_firmecon as fe  # noqa: E402


def test_map_lines_and_profit():
    row = {"year": "2025", "rev": "10", "fees": "3", "pay": "2", "tech": "1"}
    m = {"net_revenue": [("rev", 1), ("fees", -1)], "comp": [("pay", 1)], "other_fixed": [("tech", 1)]}
    (st,) = fe.statements([row], m)
    assert st.net_revenue == 7 and st.operating_profit == 4 and st.revenue == 7
    r = fe.ratios(st)
    assert math.isclose(r["comp_ratio"], 2 / 7) and math.isclose(r["operating_margin"], 4 / 7)


def test_fit_line_exact_and_errors():
    a, b, sa, sb = fe.fit_line([1, 2, 3, 4], [3, 5, 7, 9])
    assert math.isclose(a, 1) and math.isclose(b, 2) and sa < 1e-12 and sb < 1e-12
    with pytest.raises(ValueError):
        fe.fit_line([1, 2], [1, 2])


def test_breakeven_and_leverage_consistent():
    cs = fe.CostStructure(fixed=60.0, var_share=0.25)
    nr = 100.0
    x = fe.breakeven_fall(cs, nr)
    assert math.isclose(float(fe.profit(cs, nr * (1 - x))), 0.0, abs_tol=1e-12)
    lev = fe.operating_leverage(cs, nr)
    dp = float(fe.profit(cs, nr * 1.0001) / fe.profit(cs, nr)) - 1
    assert math.isclose(lev, dp / 1e-4, rel_tol=1e-9)
    with pytest.raises(ValueError):
        fe.operating_leverage(cs, 70.0)


def test_flexible_pay_lowers_leverage():
    sts = [fe.Statement(2000 + i, nr, 20 + 0.3 * nr, 30) for i, nr in enumerate([80, 100, 120, 150])]
    flex, rigid = fe.cost_structure(sts), fe.cost_structure(sts, flex_pay=False)
    assert math.isclose(flex.var_share, 0.3) and math.isclose(flex.fixed, 50.0)
    assert fe.operating_leverage(flex, 150) < fe.operating_leverage(rigid, 150)
    assert fe.breakeven_fall(flex, 150) > fe.breakeven_fall(rigid, 150)
    assert np.all(np.diff(fe.cycle(flex, 150, [-0.5, 0, 0.5])) > 0)
