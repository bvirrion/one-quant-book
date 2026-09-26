"""Numbers gate: every numerical answer printed in Book 11, chapter 25 (text and solutions)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
import hf_onchain as h  # noqa: E402

fs = h.fs


def r(x, d=0):
    return round(float(x), d)


def test_arb_and_values():
    d, dx, prof = fs.optimal_arb(1000.0, 3_100_000.0, 3000.0, 0.003)
    assert (d, r(dx, 2), r(prof)) == ("sell_A", 15.05, 677)
    assert h.lvr_theory() == 28000.0 and r(fs.lvr_rate(0.04, 20e6)) == 4000
    assert fs.liquidation_value(1e6, 0.05, 20.0) == 49980.0


def test_pool_weeks():
    w = h.pool_week()
    assert [r(w[s]["lvr"], -2) for s in h.SEEDS] == [25800, 28500, 29500]
    one = w[1]
    assert (r(one["fees"], -3), r(one["hedged_pnl"], -3), r(one["arb_profit"], -2)) == (339000, 313000, 4300)
    assert [r(w[s]["arb_take"] - w[s]["lvr"], -2) for s in h.SEEDS] == [22500, 21100, 19700]
    assert r(h.gross_opportunity(), -2) == 11400 and r(5.0 * one["arbs"], -2) == 7100
    d = h.double_vol()
    assert (r(d["lvr"], -2), d["theory"], r(d["hedged_pnl"], -3)) == (96300, 112000.0, 294000)


def test_auction_and_sandwich():
    a = h.auctions()
    assert [r(100 * a[n]["share"]) for n in (2, 5, 10, 20)] == [93, 97, 98, 99]
    assert a[1]["builder"] == 0.0 and (r(a[2]["searcher"], 1), r(a[20]["searcher"], 1)) == (6.7, 1.0)
    s = h.sandwich_example()
    assert (r(s.front_in / 100, -2), s.victim_loss, r(s.gross / 100), r(s.net / 100)) == (50900, 330, 701, 60)
