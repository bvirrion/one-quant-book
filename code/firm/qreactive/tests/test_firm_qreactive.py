import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "tape"))
import firm_qreactive as qr  # noqa: E402
import firm_tape as ft  # noqa: E402

MSG, TOP = ft.MSG, ft.TOP


def test_estimate_by_hand():
    msgs = np.array([(0.0, b"A", 1, 1, 99, 200, 0, -1), (1.0, b"A", 2, 1, 99, 100, 0, -1),
                     (3.0, b"E", 1, 1, 99, 100, -1, 1), (4.0, b"X", 2, 1, 99, 100, 0, -1)], dtype=MSG)
    top = np.array([(0.0, 99, 200, 100, 500), (1.0, 99, 300, 100, 500), (3.0, 99, 200, 100, 500),
                    (4.0, 99, 100, 100, 500)], dtype=TOP)
    e = qr.estimate(msgs, top, lot=100, qmax=5, n_open=1)
    # bid queue: 2 lots for 1 s then an add of 1 lot; 3 lots for 2 s then a trade of 1; 2 lots for 1 s then a cancel of 1
    assert np.isclose(e["time"][2], 2.0) and np.isclose(e["time"][3], 2.0)
    assert np.isclose(e["L"][2], 1.0 / 2.0) and np.isclose(e["M"][3], 1.0 / 2.0) and np.isclose(e["C"][2], 1.0 / 2.0)


def test_no_market_orders_no_fill():
    m = qr.QRModel(np.full(10, 1.0), np.full(10, 0.5), np.zeros(10), np.full(10, 0.1))
    r = qr.order_value(m, 3, 5, 5, tmax=20.0, paths=300, seed=1)
    assert r["fill"] == 0.0 and r["value"] == 0.0


def test_front_fills_first_and_more_often():
    m = qr.QRModel(np.full(31, 1.5), np.full(31, 0.5), np.full(31, 0.5), np.full(31, 1 / 31))
    front = qr.order_value(m, 0, 10, 10, paths=2000, seed=2)
    back = qr.order_value(m, 9, 10, 10, paths=2000, seed=2)
    assert front["fill"] > back["fill"]
    t = qr.value_table(m, (2, 5), paths=200, seed=3)
    assert t["back"]["value"].shape == (2, 2) and np.all(np.isfinite(t["front"]["value"]))
