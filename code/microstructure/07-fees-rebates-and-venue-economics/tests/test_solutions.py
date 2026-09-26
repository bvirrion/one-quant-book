"""Numbers gate: every numerical answer printed in Book 10, chapter 7 (text and solutions)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from mx_fees import CBOE_2026, by_awareness  # noqa: E402, I001
from firm_venuefees import effective_tick, fee_adjusted, indifference_make, neutral_ask, passive_value  # noqa: E402, I001


def r(x, d=2):
    return round(float(x), d)


def test_venues():
    b = by_awareness()
    m, i = b[1.0]["MT"], b[1.0]["INV"]
    assert (r(100 * m["fill_share"], 1), r(100 * i["fill_share"], 1)) == (8.4, 28.2)
    assert (r(m["adverse"]), r(i["adverse"]), r(m["adverse_se"]), r(i["adverse_se"])) == (0.63, 0.13, 0.04, 0.04)
    assert (r(m["capture"]), r(i["capture"])) == (0.54, 0.54)
    assert (r(m["net"], 3), r(i["net"])) == (-0.092, 0.40)
    assert (r(m["value"], 3), r(i["value"], 3), r(b[1.0]["diff_se"], 3)) == (0.006, 0.057, 0.009)
    assert (r(m["queue"], -1), r(i["queue"], -1)) == (910, 510)
    assert (r(m["t_fill"], 1), r(i["t_fill"], 1)) == (8.8, 4.6)
    assert (r(100 * m["volume_share"]), r(100 * i["volume_share"])) == (22.85, 77.15)
    make_inv = 100 * CBOE_2026["INV"][0]
    assert r(indifference_make(m["fill_share"], m["net"], i["fill_share"], i["net"], make_inv)) == -0.77
    m5, i5 = b[0.5]["MT"], b[0.5]["INV"]
    assert (r(100 * m5["fill_share"], 1), r(100 * i5["fill_share"], 1), r(m5["adverse"]), r(i5["adverse"])) == \
        (14.3, 22.1, 0.33, 0.21)
    assert (r(m5["value"], 3), r(i5["value"], 3), r(b[0.5]["diff_se"], 3)) == (0.052, 0.028, 0.006)
    assert r(indifference_make(m5["fill_share"], m5["net"], i5["fill_share"], i5["net"], make_inv), 3) == 0.006
    assert (r(100 * m5["volume_share"], 1), r(m5["queue"], -1), r(i5["queue"], -1)) == (39.5, 790, 600)
    m0, i0 = b[0.0]["MT"], b[0.0]["INV"]
    assert (r(100 * m0["fill_share"], 1), r(100 * i0["fill_share"], 1), r(m0["adverse"]), r(i0["adverse"])) == \
        (19.1, 17.5, 0.31, 0.24)
    assert (r(m0["value"], 3), r(i0["value"], 3), r(100 * m0["volume_share"], 1)) == (0.074, 0.015, 52.5)


def test_exercises():
    # 1: buying 1,000 at 20.00 on the maker-taker and on the inverted venue
    a, b = fee_adjusted(20.00, 1, 0.0030), fee_adjusted(20.00, 1, -0.0002)
    assert (r(a, 4), r(b, 4), r(1000 * (a - b), 2)) == (20.003, 19.9998, 3.2)
    # 2: effective tick in cents
    assert r(100 * effective_tick(0.01, [0.0030, -0.0002]), 2) == 0.32
    # 3: values per posted share (cents)
    assert (r(passive_value(0.3, 0.5, 0.1, 0.2), 3), r(passive_value(0.1, 0.5, 0.6, -0.16), 3)) == (0.06, 0.006)
    # 4: the make fee that equalises them
    assert r(indifference_make(0.1, -0.1, 0.3, 0.4, 0.2)) == -0.7
    # 5: moving 0.20 cents from the take fee to the make side
    assert (r(neutral_ask(10.01, 0.0030, 0.0010), 4), r(neutral_ask(10.01, 0.0030, 0.0010, 0.01), 2)) == (10.012, 10.02)
    assert (r(10.012 + 0.0010, 4), r(10.01 + 0.0030, 4), r(10.012 - 0.0004, 4), r(10.01 + 0.0016, 4)) == \
        (10.013, 10.013, 10.0116, 10.0116)
    assert (r(10.01 + 0.0010, 4), r(10.02 + 0.0010, 4)) == (10.011, 10.021)


def test_exercise_7_new_cap():
    import numpy as np
    from mx_fees import two_venues
    fees = {"MT": (-0.0006, 0.0010), "INV": CBOE_2026["INV"]}
    rs = [two_venues(0.5, fees, 7200.0, s) for s in (7, 8, 9)]
    mt = {k: float(np.mean([x["MT"][k] for x in rs])) for k in ("fill_share", "adverse", "value")}
    assert (r(100 * mt["fill_share"], 1), r(mt["adverse"]), r(mt["value"], 3)) == (8.4, 0.63, -0.003)
