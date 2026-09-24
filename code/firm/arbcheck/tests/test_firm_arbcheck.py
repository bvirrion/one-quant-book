"""Acceptance tests of the Book 5, Chapter 1 build (static-arbitrage checker)."""
import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "parity"))
from firm_arbcheck import Quote, box_cost, box_rate, check_box, check_chain, lp_max
from firm_parity import price

F, DF, T = 100.0, math.exp(-0.03), 1.0


def chain(vols=None, width=0.05):
    out = []
    for i, k in enumerate((80.0, 90.0, 100.0, 110.0, 120.0)):
        v = 0.2 if vols is None else vols[i]
        for r in ("C", "P"):
            m = price(F, k, T, 0.03, v, r)
            out.append(Quote(k, r, m - width, m + width))
    return out


def test_clean_chain_has_no_violation():
    assert check_chain(chain(), F, DF) == []


def test_convexity_violation_is_found_with_its_edge():
    q = chain(vols=[0.2, 0.2, 0.35, 0.2, 0.2])      # the 100 strike far too dear
    kinds = {v.kind for v in check_chain(q, F, DF)}
    assert "convexity" in kinds
    assert all(v.edge > 0 for v in check_chain(q, F, DF))


def test_bound_violation():
    q = [Quote(80.0, "C", 1.0, 1.1)]                  # below discounted intrinsic value 19.41
    v = check_chain(q, F, DF)
    assert v[0].kind == "bound" and abs(v[0].edge - (DF * 20 - 1.1)) < 1e-12


def test_box_rate_and_box_check():
    q = {(x.right, x.strike): x for x in chain(width=0.0)}
    cost = box_cost(q, 90.0, 110.0)
    assert abs(cost - 20 * DF) < 1e-9 and abs(box_rate(cost, 20.0, T) - 0.03) < 1e-9
    assert check_box(q, 90.0, 110.0, DF) == []
    assert check_box(q, 90.0, 110.0, math.exp(-0.05))[0].kind == "box"


def test_lp_max_simple():
    val, x = lp_max([1.0, 1.0], np.array([[1.0, 0.0], [0.0, 1.0], [-1.0, 0.0], [0.0, -1.0], [1.0, 1.0]]),
                    np.array([1.0, 1.0, 0.0, 0.0, 1.5]))
    assert abs(val - 1.5) < 1e-12
