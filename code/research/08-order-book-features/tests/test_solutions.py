"""Numbers gate: every numerical answer printed in Book 7, chapter 8 (text and solutions)."""
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from rs_orderbook import (
    best_level_rates,
    cancel_feature,
    data,
    forecast_errors,
    model_up_probability,
    next_move,
    ofi_regression,
    up_probability,
)


def r(x, d=3):
    return round(float(x), d)


def test_imbalance_and_model():
    tp, f, mid = data()
    assert len(tp.msgs) == 239_528
    up = up_probability()
    assert (r(up[0]["p_up"]), r(up[9]["p_up"]), up[0]["n"], up[9]["n"]) == (0.245, 0.736, 16_564, 14_538)
    assert (r(up[0]["qb"], 1), r(up[0]["qa"], 1), r(up[9]["qb"], 1), r(up[9]["qa"], 1)) == (3.4, 55.4, 49.2, 3.1)
    assert r(up[4]["p_up"]) == 0.5 and 1 - up[0]["p_up"] > 0.75 > up[0]["p_up"]
    b, d = best_level_rates()
    assert (r(b, 2), r(d, 2)) == (2.03, 2.13)
    assert (r(model_up_probability(up[0]["qb"], up[0]["qa"], b, d)), r(model_up_probability(up[9]["qb"], up[9]["qa"], b, d))) == (
        0.017, 0.979)


def test_ofi_micro_cancel():
    o = {w: ofi_regression(w) for w in (1, 10, 60)}
    assert (round(100 * o[1]["r2"]), round(100 * o[10]["r2"]), round(100 * o[60]["r2"])) == (10, 53, 79)
    assert r(o[10]["slope"], 2) == 0.47 and o[10]["n"] == 1078 and round(o[10]["depth"]) == 2747
    fe, _ = forecast_errors()
    rel = {h: {k: v[k] / v["mid"] for k in ("wmid", "micro")} for h, v in fe.items()}
    assert (round(100 * (1 - rel[1.0]["micro"])), round(100 * (rel[1.0]["wmid"] - 1))) == (10, 27)
    assert (round(100 * (1 - rel[5.0]["wmid"])), round(100 * (1 - rel[30.0]["wmid"]))) == (12, 3)
    assert rel[5.0]["wmid"] < rel[5.0]["micro"] and rel[30.0]["wmid"] < rel[30.0]["micro"]
    c, i = cancel_feature()
    assert (r(c, 2), r(i, 2)) == (0.30, 0.25)


def test_exercises():
    assert r((700 - 300) / 1000, 1) == 0.4 and r((99.99 * 700 + 99.98 * 300) / 1000, 3) == 99.987
    assert r(11000 / 2750 * 0.47, 2) == 1.88
    tp, f, mid = data()
    nxt = next_move(mid)
    ok = ~np.isnan(nxt) & ~np.isnan(f["depth_imbalance"])
    assert r(np.corrcoef(f["depth_imbalance"][ok], nxt[ok])[0, 1]) == 0.277
    assert r(np.corrcoef(f["imbalance"][ok], nxt[ok])[0, 1]) == 0.253
