"""Numbers in the solutions of Book 3, Chapter 24."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
import m3_business as m
from firm_tokenloan import call_bs, delta_schedule


def test_exercises():
    v, d = call_bs(0.5, 0.75, 1.0, 1.2)
    assert round(v, 4) == 0.1711 and round(d, 3) == 0.603
    fees = dict(m.fee_by_vol())
    assert round(100 * fees[0.8], 1) == 11.7 and round(100 * fees[1.6], 1) == 41.8
    s = dict(delta_schedule(m.listing_deal(), [0.5, 0.25], 0.5))
    assert round(s[0.5] - s[0.25]) == 444_621


def test_problem():
    d = m.listing_deal()
    vals = [round(n * call_bs(0.5, k, 1.0, 1.2)[0]) for n, k in d.tranches]
    assert vals == [114_052, 89_993, 60_574] and sum(vals) == 264_619
    s = m.summary()
    assert round(100 * s["fee"], 2) == 26.46 and round(100 * (s["calls_mc_usd"] / s["calls_usd"] - 1), 2) == -0.33
    assert round(100 * m.summary(0.8)["fee"], 2) == 11.67
    assert round(s["hedge_tokens"]) == 992_331
    up = dict(delta_schedule(d, [1.0], 11 / 12))[1.0]
    down = dict(delta_schedule(d, [0.25], 11 / 12))[0.25]
    assert (round(up), round(down)) == (1_400_072, 518_170)


def test_rebalancing():
    d = m.listing_deal()
    h0 = m.summary()["hedge_tokens"]
    up = dict(delta_schedule(d, [1.0], 11 / 12))[1.0]
    down = dict(delta_schedule(d, [0.25], 11 / 12))[0.25]
    assert (round((up - h0) / 1_000), round((h0 - down) / 1_000)) == (408, 474)
